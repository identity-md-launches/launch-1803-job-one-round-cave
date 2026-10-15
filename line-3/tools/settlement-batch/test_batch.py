import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('settlement_batch_test', HERE / 'batch.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.raw = (HERE / 'demo-manifest.json').read_bytes()
        self.plan = json.loads(self.raw)
        self.scratch = Path('test/scratch/settlement-batch')
        self.scratch.mkdir(parents=True, exist_ok=True)

    def cli(self, plan):
        path = self.scratch / 'manifest.json'
        path.write_text(json.dumps(plan))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = b.main(['--manifest', str(path)])
        return code, json.loads(out.getvalue())

    def mutation(self, index, change, raw_change=None):
        item = self.plan['items'][index]
        raw = Path(item['evidence']).read_bytes()
        sample = json.loads(raw)
        change(sample)
        raw = json.dumps(sample).encode() if raw_change is None else raw_change
        path = self.scratch / ('evidence-' + str(index) + '.json')
        path.write_bytes(raw)
        item.update(evidence=str(path), sha256=hashlib.sha256(raw).hexdigest())

    def test_real_two_transaction_batch(self):
        result = b.review_manifest_bytes(self.raw)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['acceptedCount'], 2)
        self.assertEqual([r['transactionIndex'] for r in result['items']], [181, 146])
        self.assertEqual(result['manifestSha256'], hashlib.sha256(self.raw).hexdigest())

    def test_single_entry_supported(self):
        self.plan['items'].pop()
        self.assertEqual(self.cli(self.plan)[0], 0)

    def test_duplicate_rejected_before_read(self):
        self.plan['items'][1] = copy.deepcopy(self.plan['items'][0])
        with patch.object(b.k, 'review_file', side_effect=AssertionError('opened')):
            with self.assertRaises(b.Error):
                b.review(self.plan)

    def test_duplicate_case_variant(self):
        self.plan['items'][1]['policy'] = copy.deepcopy(self.plan['items'][0]['policy'])
        tx = self.plan['items'][1]['policy']['transactionHash']
        self.plan['items'][1]['policy']['transactionHash'] = '0x' + tx[2:].upper()
        self.assertEqual(self.cli(self.plan)[0], 2)

    def test_duplicate_different_policy(self):
        self.plan['items'][1]['policy'] = copy.deepcopy(self.plan['items'][0]['policy'])
        self.plan['items'][1]['policy']['minimumConfirmations'] = 13
        self.assertEqual(self.cli(self.plan)[0], 2)

    def test_entire_plan_validated_before_reads(self):
        self.plan['items'][1]['sha256'] = 'bad'
        with patch.object(b.k, 'review_file', side_effect=AssertionError('opened')):
            with self.assertRaises(b.Error):
                b.review(self.plan)

    def test_mixed_pin_failure_never_partial_accepts(self):
        self.plan['items'][1]['sha256'] = self.plan['items'][0]['sha256']
        code, result = self.cli(self.plan)
        self.assertEqual(code, 1)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['acceptedCount'], 1)
        self.assertEqual(result['items'][1]['state'], 'evidence_pin_mismatch')

    def test_bad_first_row_does_not_hide_second(self):
        self.plan['items'][0]['evidence'] = 'test/scratch/settlement-batch/missing'
        code, result = self.cli(self.plan)
        self.assertEqual(code, 2)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['items'][1]['accepted'])

    def test_matching_pin_invalid_position(self):
        self.mutation(1, lambda s: s['reads'][8]['result'].update(transactionIndex='0x0'))
        code, result = self.cli(self.plan)
        self.assertEqual(code, 1)
        self.assertIn('transaction_missing_at_receipt_index', result['items'][1]['alerts'])

    def test_matching_pin_policy_mismatch(self):
        self.plan['items'][1]['policy']['minimumConfirmations'] = 13
        self.assertEqual(self.cli(self.plan)[0], 2)

    def test_matching_pin_bad_json(self):
        for raw in (b'{"version":1,"version":1}', b'{"x":NaN}', b'no json'):
            with self.subTest(raw=raw):
                self.mutation(1, lambda s: None, raw)
                code, result = self.cli(self.plan)
                self.assertEqual(code, 2)
                self.assertFalse(result['accepted'])

    def test_shared_height_conflict_rejects_aggregate(self):
        # Isolate aggregation using actual successful replay reports, then alter
        # one anchor in memory. These are test values, never saved chain evidence.
        reports = [b.k.review_file(i['evidence'], i['sha256'], i['policy'])
                   for i in self.plan['items']]
        first_head = reports[0]['positionReview']['settlement']['head']
        other_head = reports[1]['positionReview']['settlement']['head']
        other_head['number'] = first_head['number']
        with patch.object(b.k, 'review_file', side_effect=reports):
            result = b.review(self.plan)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['acceptedCount'], 2)
        self.assertEqual(result['conflictingBlockNumbers'], [first_head['number']])

    def test_equal_shared_height_allowed(self):
        reports = [b.k.review_file(i['evidence'], i['sha256'], i['policy'])
                   for i in self.plan['items']]
        reports[1]['positionReview']['settlement']['head'] = copy.deepcopy(
            reports[0]['positionReview']['settlement']['head'])
        with patch.object(b.k, 'review_file', side_effect=reports):
            self.assertTrue(b.review(self.plan)['accepted'])

    def test_manifest_exact_schema(self):
        variants = [None, {}, {'version': True, 'items': self.plan['items']},
                    dict(self.plan, accepted=True), dict(self.plan, items=[]),
                    dict(self.plan, items=self.plan['items'] * 17)]
        for plan in variants:
            with self.subTest(plan=type(plan)), self.assertRaises(b.Error):
                b.review(plan)

    def test_item_and_policy_exact_fields(self):
        for target in ('item', 'policy'):
            with self.subTest(target=target):
                plan = copy.deepcopy(self.plan)
                obj = plan['items'][0] if target == 'item' else plan['items'][0]['policy']
                obj['accepted'] = True
                self.assertEqual(self.cli(plan)[0], 2)

    def test_invalid_policies(self):
        for key, value in (('minimumConfirmations', True), ('minimumConfirmations', 0),
                           ('requireFinalized', 1), ('transactionHash', 'no hash')):
            with self.subTest(key=key, value=value):
                plan = copy.deepcopy(self.plan)
                plan['items'][0]['policy'][key] = value
                self.assertEqual(self.cli(plan)[0], 2)

    def test_unsafe_evidence_paths_before_read(self):
        for path in ('/absolute', '../x', '.hidden', 'a//b', 'a/./b', 'a/../b', 'a\\b'):
            self.plan['items'][1]['evidence'] = path
            with self.subTest(path=path), patch.object(b.k, 'review_file', side_effect=AssertionError('opened')):
                with self.assertRaises(b.Error):
                    b.review(self.plan)

    def test_manifest_parser_and_bound(self):
        for raw in (b'{"version":1,"version":1}', b'{"items":NaN}', b'\xff',
                    b' ' * 90001, bytearray(self.raw)):
            with self.subTest(kind=type(raw)), self.assertRaises(b.Error):
                b.review_manifest_bytes(raw)

    def test_no_network_no_mutation(self):
        files = [Path(i['evidence']) for i in self.plan['items']]
        before = [p.read_bytes() for p in files]
        with patch.object(b.k.p.s.RPC, 'call', side_effect=AssertionError('network')):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(b.main(['--demo']), 0)
        self.assertEqual(json.loads(out.getvalue())['count'], 2)
        self.assertEqual([p.read_bytes() for p in files], before)

    def test_file_boundary_symlink_and_directory(self):
        link = self.scratch / 'link'
        if link.is_symlink():
            link.unlink()
        link.symlink_to((HERE / 'demo-manifest.json').resolve())
        for path in (link, self.scratch):
            with self.subTest(path=str(path)), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(b.main(['--manifest', str(path)]), 2)

    def test_bounded_compact_result(self):
        self.assertLess(len(json.dumps(b.review(self.plan)).encode()), 100000)
        self.assertNotIn('reads', json.dumps(b.review(self.plan)))


if __name__ == '__main__':
    unittest.main()
