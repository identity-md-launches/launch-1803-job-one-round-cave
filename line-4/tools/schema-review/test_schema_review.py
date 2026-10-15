"""Offline behavior, empty-container coverage, and strict boundary checks."""
import copy
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from schema_review import review, render, schema_expectations
from typed_digest import TypedDataError, digest, load_workspace_json, loads_bounded

HERE = Path(__file__).resolve().parent
EXPECTED = '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'


def policy(data):
    return copy.deepcopy({k: data[k] for k in ('primaryType', 'types')})


def empty_request():
    return {'types': {
        'EIP712Domain': [],
        'Batch': [{'name': 'items', 'type': 'Item[]'}],
        'Item': [{'name': 'amount', 'type': 'uint256'}]},
        'primaryType': 'Batch', 'domain': {}, 'message': {'items': []}}


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.data = load_workspace_json(HERE / 'zto-payment.json')

    def test_historical_zto_matches_schema_and_digest(self):
        result = review(self.data, load_workspace_json(HERE / 'zto-schema.json'), EXPECTED)
        self.assertTrue(result['checksPass'])
        self.assertEqual(result['digest'], EXPECTED)
        self.assertEqual(result['unusedTypes'], [])
        self.assertEqual(len(result['declarations']), 2)
        self.assertTrue(all(d['valueInstanceCount'] == 1 for d in result['declarations']))

    def test_inspection_has_no_pass_decision(self):
        self.assertIsNone(review(self.data)['checksPass'])
        self.assertFalse(review(self.data)['schemaExpectationProvided'])

    def test_empty_array_keeps_dependency_and_has_no_item_instance(self):
        result = review(empty_request())
        self.assertEqual(result['reachableTypesWithoutValues'], ['Item'])
        self.assertEqual(result['emptyArrays'], [
            {'path': '/message/items', 'declaredType': 'Item[]', 'baseType': 'Item'}])
        item = next(d for d in result['declarations'] if d['name'] == 'Item')
        self.assertTrue(item['boundByMessageTypeHash'])
        self.assertFalse(item['boundByDomainTypeHash'])
        self.assertEqual(item['valueInstanceCount'], 0)
        self.assertEqual(result['typeEncoding'], 'Batch(Item[] items)Item(uint256 amount)')

    def test_changed_type_behind_empty_array_rejects(self):
        data = empty_request()
        expected = policy(data)
        old_digest = digest(data)['digest']
        data['types']['Item'][0]['type'] = 'uint128'
        result = review(data, expected, old_digest)
        self.assertFalse(result['checksPass'])
        self.assertFalse(result['digestMatchesExpected'])
        self.assertEqual(result['changedDeclarations'][0]['name'], 'Item')

    def test_unused_type_addition_same_digest_schema_rejects(self):
        data = load_workspace_json(HERE / 'zto-unused-declaration.json')
        result = review(data, policy(self.data), EXPECTED)
        self.assertEqual(result['unusedTypes'], ['UnreferencedNote'])
        self.assertEqual(result['unpinnedTypes'], ['UnreferencedNote'])
        self.assertTrue(result['digestMatchesExpected'])
        self.assertFalse(result['checksPass'])

    def test_unused_type_mutation_same_digest_schema_rejects(self):
        self.data['types']['Unused'] = [{'name': 'flag', 'type': 'bool'}]
        expected = policy(self.data)
        self.data['types']['Unused'][0]['type'] = 'uint8'
        result = review(self.data, expected, EXPECTED)
        self.assertTrue(result['digestMatchesExpected'])
        self.assertFalse(result['schemaMatchesExpected'])

    def test_missing_expected_unused_type_rejects(self):
        expected = policy(self.data)
        expected['types']['Unused'] = []
        result = review(self.data, expected)
        self.assertEqual(result['absentTypes'], ['Unused'])
        self.assertFalse(result['checksPass'])

    def test_explicit_unused_expectations_can_match(self):
        self.data['types']['Unused'] = []
        result = review(self.data, policy(self.data), EXPECTED)
        self.assertTrue(result['checksPass'])
        unused = next(d for d in result['declarations'] if d['name'] == 'Unused')
        self.assertFalse(unused['boundByDomainTypeHash'])
        self.assertFalse(unused['boundByMessageTypeHash'])

    def test_field_order_is_significant_object_key_order_is_not(self):
        expected = policy(self.data)
        self.data['types'] = dict(reversed(list(self.data['types'].items())))
        self.assertTrue(review(self.data, expected)['checksPass'])
        self.data['types']['PaymentEvidence'].reverse()
        result = review(self.data, expected, EXPECTED)
        self.assertFalse(result['schemaMatchesExpected'])
        self.assertFalse(result['digestMatchesExpected'])

    def test_renaming_field_and_value_rejects(self):
        data = empty_request()
        expected = policy(data)
        data['types']['Batch'][0]['name'] = 'renamed'
        data['message'] = {'renamed': []}
        self.assertFalse(review(data, expected)['checksPass'])

    def test_primary_type_compared_independently(self):
        self.data['types']['Other'] = copy.deepcopy(self.data['types']['PaymentEvidence'])
        expected = policy(self.data)
        self.data['primaryType'] = 'Other'
        result = review(self.data, expected)
        self.assertFalse(result['primaryTypeMatches'])
        self.assertFalse(result['checksPass'])
        self.assertEqual(result['changedDeclarations'], [])

    def test_values_require_digest_comparison(self):
        expected = policy(self.data)
        self.data['message']['confirmations'] += 1
        self.assertTrue(review(self.data, expected)['checksPass'])
        result = review(self.data, expected, EXPECTED)
        self.assertTrue(result['schemaMatchesExpected'])
        self.assertFalse(result['checksPass'])

    def test_digest_only_and_hex_case(self):
        self.assertTrue(review(self.data, expected_digest='0x' + EXPECTED[2:].upper())['checksPass'])
        changed = copy.deepcopy(self.data)
        changed['message']['confirmations'] += 1
        self.assertFalse(review(changed, expected_digest=EXPECTED)['checksPass'])

    def test_recursive_schema_and_finite_values(self):
        data = {'types': {'EIP712Domain': [], 'Node': [{'name': 'children', 'type': 'Node[]'}]},
                'primaryType': 'Node', 'domain': {},
                'message': {'children': [{'children': []}]}}
        result = review(data, policy(data))
        node = next(d for d in result['declarations'] if d['name'] == 'Node')
        self.assertEqual(node['directDependencies'], ['Node'])
        self.assertEqual(node['valueInstanceCount'], 2)
        self.assertEqual(node['encodeType'], 'Node(Node[] children)')
        self.assertTrue(result['checksPass'])

    def test_mutual_recursion_reachable_behind_empty_array(self):
        data = empty_request()
        data['types']['Item'] = [{'name': 'parent', 'type': 'Batch[]'}]
        result = review(data)
        self.assertEqual(result['reachableTypesWithoutValues'], ['Item'])
        self.assertEqual(result['unusedTypes'], [])

    def test_nested_arrays_and_repeated_instances(self):
        data = empty_request()
        data['types']['Batch'][0]['type'] = 'Item[][2]'
        data['message']['items'] = [[], [{'amount': 7}, {'amount': 9}]]
        result = review(data)
        self.assertEqual(result['emptyArrays'][0]['path'], '/message/items/0')
        self.assertEqual(result['emptyArrays'][0]['declaredType'], 'Item[]')
        item = next(d for d in result['declarations'] if d['name'] == 'Item')
        self.assertEqual(item['valueInstanceCount'], 2)
        self.assertEqual(result['reachableTypesWithoutValues'], [])

    def test_domain_and_message_dependency_membership(self):
        data = empty_request()
        data['types']['EIP712Domain'] = [{'name': 'items', 'type': 'Item[]'}]
        data['domain'] = {'items': []}
        result = review(data)
        item = next(d for d in result['declarations'] if d['name'] == 'Item')
        self.assertTrue(item['boundByDomainTypeHash'])
        self.assertTrue(item['boundByMessageTypeHash'])
        self.assertEqual(len(result['emptyArrays']), 2)

    def test_invalid_expected_schema_and_explicit_null_reject(self):
        for expected in (None, [], {}, {'primaryType': 'Missing', 'types': self.data['types']},
                         {**policy(self.data), 'extra': True},
                         {'primaryType': 'EIP712Domain', 'types': self.data['types']}):
            with self.subTest(expected=expected), self.assertRaises(TypedDataError):
                review(self.data, expected)

    def test_invalid_unused_declaration_not_ignored(self):
        for kind in ('Missing', 'uint', 'bytes33', 'uint8[0]'):
            data = copy.deepcopy(self.data)
            data['types']['Unused'] = [{'name': 'x', 'type': kind}]
            with self.subTest(kind=kind), self.assertRaises(TypedDataError):
                review(data)
            with self.assertRaises(TypedDataError):
                schema_expectations(policy(data))

    def test_invalid_values_still_reject_with_matching_schema(self):
        self.data['message']['confirmations'] = True
        with self.assertRaises(TypedDataError):
            review(self.data, policy(self.data))

    def test_inputs_not_mutated_and_report_does_not_alias_inputs(self):
        expected = policy(self.data)
        before = copy.deepcopy((self.data, expected))
        result = review(self.data, expected)
        result['declarations'][0]['fields'].clear()
        self.assertEqual((self.data, expected), before)

    def test_no_network_needed(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('network disabled')):
            self.assertTrue(review(self.data, policy(self.data), EXPECTED)['checksPass'])

    def test_strict_json_reader(self):
        for raw in (b'{"types":{},"types":{}}', b'NaN', b'1.0', b'"\\ud800"'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                loads_bounded(raw)

    def test_output_limit_includes_newline(self):
        text = render({'x': 'y'})
        with patch('schema_review.MAX_REPORT_BYTES', len(text.encode('ascii'))):
            self.assertEqual(render({'x': 'y'}), text)
        with patch('schema_review.MAX_REPORT_BYTES', len(text.encode('ascii')) - 1):
            with self.assertRaisesRegex(TypedDataError, 'output limit'):
                render({'x': 'y'})

    def test_report_expansion_fails_closed(self):
        data = empty_request()
        names = ['N' + str(i) + 'x'*90 for i in range(40)]
        data['types']['Batch'] = [{'name': 'items', 'type': names[0] + '[]'}]
        del data['types']['Item']
        for i, name in enumerate(names):
            data['types'][name] = ([{'name': 'child', 'type': names[i+1] + '[]'}]
                                   if i+1 < len(names) else [])
        with self.assertRaisesRegex(TypedDataError, 'output limit'):
            review(data)

    def test_cyclic_api_value_rejects(self):
        data = empty_request()
        data['message']['items'].append(data['message'])
        with self.assertRaisesRegex(TypedDataError, 'cyclic'):
            review(data)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='schema-test-', dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def run_cli(self, file='zto-payment.json', *options):
        path = HERE / file
        return subprocess.run([sys.executable, '-B', str(HERE / 'schema_review.py'), str(path),
                               *map(str, options)], capture_output=True, text=True, timeout=20)

    def test_cli_success_rejection_and_inspection(self):
        for file, code in [('zto-payment.json', 0), ('zto-unused-declaration.json', 1)]:
            result = self.run_cli(file, '--schema-expect', HERE/'zto-schema.json', '--digest-expect', EXPECTED)
            self.assertEqual(result.returncode, code, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['checksPass'], code == 0)
            self.assertTrue(report['digestMatchesExpected'])
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(json.loads(result.stdout)['checksPass'])

    def test_cli_null_duplicate_and_unsafe_expectations(self):
        for raw in (b'null', b'{"types":{},"types":{}}'):
            path = self.folder/'bad.json'
            path.write_bytes(raw)
            result = self.run_cli('zto-payment.json', '--schema-expect', path)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertNotIn('Traceback', result.stderr)
        link = self.folder/'linked.json'
        link.symlink_to(HERE/'zto-schema.json')
        for path in (link, '../outside.json'):
            result = self.run_cli('zto-payment.json', '--schema-expect', path)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')

    def test_cli_bad_digest_no_partial_report(self):
        result = self.run_cli('zto-payment.json', '--digest-expect', 'bad\x1b[31m')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertNotIn('\x1b', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
