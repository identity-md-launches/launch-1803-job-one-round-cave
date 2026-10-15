"""Offline regression checks; fixtures live only in disposable scratch."""
import contextlib
import copy
import hashlib
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('html_review', HERE / 'review.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Tags(HTMLParser):
    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self.feed(page)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
    def handle_data(self, data):
        self.text.append(data)

class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = m.dependencies()
        cls.deps = cls.context.dependencies()
        cls.report = cls.context.inspect(*cls.deps,
            'line-2/tools/json-contract/report.contract.json',
            'line-2/tools/rule-locator/report.invalid.json')
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = m.main(list(args))
        return code, out.getvalue(), err.getvalue()
    def test_diagnostic_count_and_bytes(self):
        page = m.render(self.report)
        self.assertEqual(page.count('<article>'), 3)
        self.assertIn('bytes [92, 97)', page)
        self.assertIn('bytes [525, 534)', page)
        self.assertTrue(page.isascii())
        self.assertLessEqual(len(page), 100000)
    def test_complete_diagnostics_retained(self):
        text = ''.join(Tags(m.render(self.report)).text)
        for error in self.report['errors']:
            self.assertIn(json.dumps(error, ensure_ascii=True), text)
    def test_no_active_markup(self):
        report = copy.deepcopy(self.report)
        payload = '</pre><script>alert(1)</script><img src="https://example.invalid/x" onerror="bad()">&'
        report['errors'][0]['message'] = payload
        report['sources']['document']['file'] = payload
        report['errors'][0]['document_context']['excerpts'][0]['selected'] = payload
        page = m.render(report)
        parsed = Tags(page)
        self.assertFalse(any(t in ('script', 'img', 'iframe', 'a', 'form') for t, _ in parsed.tags))
        self.assertIn('&lt;script&gt;', page)
        for _, attrs in parsed.tags:
            self.assertFalse(any(k.startswith('on') or k in ('href', 'src') for k in attrs))
    def test_controls_bidi_unicode(self):
        report = copy.deepcopy(self.report)
        report['errors'][0]['message'] = '\x1b[31m\u202e\u00e9\ud800'
        page = m.render(report)
        self.assertTrue(page.isascii())
        for token in ('\\u001b', '\\u202e', '\\u00e9', '\\ud800'):
            self.assertIn(token, page)
    def test_immutability(self):
        before = copy.deepcopy(self.report)
        m.render(self.report)
        self.assertEqual(before, self.report)
    def test_missing_anchor(self):
        reader, source, engine, rules = self.deps
        contract = source.Source(b'{"type":"object","properties":{"x":{"type":"boolean"}},"required":["x"]}', 'contract')
        document = source.Source(b'{}', 'document')
        report = source.locate(engine, rules, contract, document)
        for error in report['errors']:
            error['document_context'] = self.context.context(document, error['document_source'])
            error['contract_context'] = self.context.context(contract, error['contract_source'])
        page = m.render(report)
        self.assertIn('No token exists for the missing value', page)
        self.assertIn('missing_value_parent_anchor', page)
    def test_output_overflow(self):
        with patch.object(m, 'MAX_OUTPUT_BYTES', 100):
            with self.assertRaises(ValueError):
                m.render(self.report)
    def test_cli_invalid(self):
        code, out, err = self.run_cli('line-2/tools/json-contract/report.contract.json',
                                    'line-2/tools/rule-locator/report.invalid.json')
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith('<!doctype html>'))
        self.assertEqual(err, '')
    def test_saved_zto_policy_offline(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')):
            code, out, err = self.run_cli('shared/payment-evidence/policy.contract.json',
                                        'shared/payment-evidence/example.policy.json')
        self.assertEqual(code, 0)
        self.assertIn('0 structural violations', out)
        data = Path('shared/payment-evidence/example.policy.json').read_bytes()
        self.assertIn(hashlib.sha256(data).hexdigest(), out)
        self.assertEqual(err, '')
    def test_bad_pin_no_html(self):
        code, out, err = self.run_cli('line-2/tools/json-contract/report.contract.json',
            'line-2/tools/rule-locator/report.invalid.json', '--document-sha256', 'f'*64)
        self.assertEqual(code, 2)
        self.assertEqual(out, '')
        self.assertIn('mismatch', err)
    def test_cli_overflow_atomic(self):
        with patch.object(m, 'MAX_OUTPUT_BYTES', 100):
            code, out, err = self.run_cli('line-2/tools/json-contract/report.contract.json',
                                        'line-2/tools/rule-locator/report.invalid.json')
        self.assertEqual(code, 2)
        self.assertEqual(out, '')
        self.assertIn('no report emitted', err)
    def test_path_boundary_and_malformed(self):
        root = Path('test/scratch'); root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            bad = Path(tmp) / 'bad.json'; bad.write_text('{"x":1,"x":2}')
            link = Path(tmp) / 'link.json'; link.symlink_to('bad.json')
            for name in (str(bad), str(link), '../outside.json', '/etc/passwd'):
                code, out, err = self.run_cli('line-2/tools/json-contract/report.contract.json', name)
                self.assertEqual(code, 2)
                self.assertEqual(out, '')
                self.assertTrue(err)

if __name__ == '__main__':
    unittest.main()
