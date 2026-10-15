"""Offline adversarial correlation tests; only workspace fixtures are read."""
import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
R = runpy.run_path(str(HERE / 'review.py'))


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((HERE / 'zto-batch.json').read_text())

    def reject(self, doc):
        with self.assertRaises((R['ReviewError'], R['B']['SnapshotError'])):
            R['review'](doc)

    def test_real_zto(self):
        result = R['review'](self.doc)
        self.assertTrue(result['all_results'])
        self.assertEqual(result['request_count'], 2)

    def test_reverse_preserves_matches(self):
        before = R['review'](self.doc)
        self.doc['responses'].reverse()
        after = R['review'](self.doc)
        for a, b in zip(before['entries'], after['entries']):
            self.assertEqual(a['id'], b['id'])
            self.assertEqual(a['response_sha256'], b['response_sha256'])
            self.assertNotEqual(a['response_index'], b['response_index'])

    def test_missing_is_visible(self):
        self.doc['responses'].pop()
        result = R['review'](self.doc)
        self.assertFalse(result['complete'])
        self.assertEqual(result['missing_count'], 1)

    def test_empty_responses(self):
        self.doc['responses'] = []
        self.assertEqual(R['review'](self.doc)['missing_count'], 2)

    def test_error_is_not_result(self):
        r = self.doc['responses'][0]
        del r['result']
        r['error'] = {'code': -32000, 'message': 'historical state unavailable'}
        result = R['review'](self.doc)
        self.assertTrue(result['complete'])
        self.assertFalse(result['all_results'])
        self.assertEqual(result['error_count'], 1)

    def test_result_null_is_still_a_result(self):
        self.doc['responses'][0]['result'] = None
        self.assertTrue(R['review'](self.doc)['all_results'])

    def test_string_integer_ids_distinct(self):
        self.doc['requests'][1]['id'] = '1'
        self.doc['responses'][1]['id'] = '1'
        self.assertTrue(R['review'](self.doc)['all_results'])

    def test_duplicate_requests(self):
        self.doc['requests'][1]['id'] = 1
        self.reject(self.doc)

    def test_duplicate_responses(self):
        self.doc['responses'][1]['id'] = 1
        self.reject(self.doc)

    def test_unexpected_id(self):
        self.doc['responses'][0]['id'] = '1'
        self.reject(self.doc)

    def test_unsafe_ids(self):
        for bad in (None, True, 1.0, 2**53, '', 'x'*129, [], {}):
            with self.subTest(bad=bad):
                d = copy.deepcopy(self.doc)
                d['requests'][0]['id'] = bad
                self.reject(d)

    def test_both_result_error(self):
        self.doc['responses'][0]['error'] = {'code': -1, 'message': 'x'}
        self.reject(self.doc)

    def test_malformed_error(self):
        r = self.doc['responses'][0]
        del r['result']
        for error in ({'code': True, 'message': 'x'}, {'code': 1}, None,
                      {'code': 1, 'message': 'x', 'extra': 1}):
            r['error'] = error
            self.reject(self.doc)

    def test_notification_rejected(self):
        del self.doc['requests'][0]['id']
        self.reject(self.doc)

    def test_write_method_rejected(self):
        self.doc['requests'][0]['method'] = 'eth_sendRawTransaction'
        self.reject(self.doc)

    def test_malformed_hash_pin(self):
        for bad in ({'blockHash': '0x12', 'requireCanonical': True},
                    {'blockHash': '0x'+'a'*64, 'requireCanonical': 1}):
            self.doc['requests'][0]['params'][1] = bad
            self.reject(self.doc)

    def test_bounds(self):
        for count in (0, 65):
            d = copy.deepcopy(self.doc)
            d['requests'] = [d['requests'][0]] * count
            self.reject(d)
        self.doc['responses'][0]['result'] = 'a'*100000
        self.reject(self.doc)

    def test_duplicate_json_keys(self):
        with self.assertRaises(R['B']['SnapshotError']):
            R['B']['parse_json'](b'{"requests":[],"requests":[]}')

    def test_non_json_number(self):
        with self.assertRaises(R['B']['SnapshotError']):
            R['B']['parse_json'](b'{"x":NaN}')

    def test_immutable(self):
        original = copy.deepcopy(self.doc)
        R['review'](self.doc)
        self.assertEqual(self.doc, original)

    def test_no_network(self):
        from unittest.mock import patch
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            self.assertTrue(R['review'](self.doc)['all_results'])

    def test_cli_success(self):
        result = subprocess.run([sys.executable, str(HERE/'review.py'),
                                 'line-1/tools/batch-response-review/zto-batch.json'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['all_results'])

    def test_cli_missing_and_error_exit_one(self):
        from unittest.mock import patch
        from contextlib import redirect_stdout
        import io
        for error in (False, True):
            d = copy.deepcopy(self.doc)
            if error:
                response = d['responses'][0]
                del response['result']
                response['error'] = {'code': -32000, 'message': 'unavailable'}
            else:
                d['responses'].pop()
            output = io.StringIO()
            with patch.dict(R['B']['SAFE_FILES'], {'read_bytes': lambda *a: json.dumps(d).encode()}):
                with redirect_stdout(output):
                    status = R['main'](['unused.json'])
            self.assertEqual(status, 1)
            self.assertFalse(json.loads(output.getvalue())['all_results'])

    def test_cli_boundary(self):
        for path in ('../outside.json', '/outside.json', '.hidden'):
            result = subprocess.run([sys.executable, str(HERE/'review.py'), path],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
