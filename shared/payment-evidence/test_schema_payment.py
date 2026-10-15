"""Cross-line regression: unchanged digest must not hide unused declarations."""
import contextlib
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import schema_payment as s
from check import load, check

HERE = Path(__file__).resolve().parent
DOMAIN = {'name': 'Read-only Payment Evidence', 'version': '1', 'chainId': 1}
DIGEST = '0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c'


class SchemaPaymentTests(unittest.TestCase):
    def setUp(self):
        self.sample = load(HERE/'example.transcript.json')
        self.policy = load(HERE/'example.policy.json')
        self.client = load(HERE/'example.typed-data.json')
        self.bytes = load(HERE/'example.bytes-expectations.json')
        self.schema = load(HERE/'example.schema-expectations.json')

    def review(self, digest=DIGEST, domain=DOMAIN):
        return s.review(self.sample, self.policy, self.client, domain,
                        'PaymentEvidence', digest, self.bytes, self.schema)

    def test_real_zto_fixture(self):
        r = self.review()
        self.assertTrue(r['accepted'])
        self.assertEqual(r['state'], 'payment_bytes_and_schema_match')

    def test_unused_declaration_rejects_with_same_digest_and_payment(self):
        self.client['types']['UnreferencedNote'] = [{'name':'note','type':'string'}]
        r = self.review()
        self.assertTrue(r['paymentByteReview']['accepted'])
        self.assertTrue(r['schemaReview']['digestMatchesExpected'])
        self.assertFalse(r['accepted'])
        self.assertEqual(r['alerts'], ['independent_complete_schema_mismatch'])
        self.assertEqual(r['schemaReview']['unpinnedTypes'], ['UnreferencedNote'])

    def test_missing_expected_unused_declaration_rejects(self):
        self.schema['types']['MissingNote'] = []
        self.assertFalse(self.review()['accepted'])

    def test_schema_only_cannot_bypass_changed_value(self):
        self.client['message']['minimumRaw'] = str(int(self.policy['minimum_raw'])+1)
        r = self.review()
        self.assertTrue(r['schemaReview']['schemaMatchesExpected'])
        self.assertFalse(r['accepted'])

    def test_byte_gate_still_required(self):
        self.bytes['fields']['/message/transcriptHash']['value'] = self.policy['tx']
        r = self.review()
        self.assertTrue(r['schemaReview']['checksPass'])
        self.assertFalse(r['accepted'])

    def test_unsafe_integer_form_still_rejects(self):
        self.client['message']['minimumRaw'] = int(self.policy['minimum_raw'])
        r = self.review()
        self.assertTrue(r['schemaReview']['checksPass'])
        self.assertFalse(r['accepted'])

    def test_domain_still_required(self):
        self.assertFalse(self.review(domain={**DOMAIN,'chainId':2})['accepted'])

    def test_matching_encoding_cannot_hide_payment_shortfall(self):
        self.policy['minimum_raw'] = str(int(self.policy['minimum_raw'])+1)
        self.sample['policy'] = copy.deepcopy(self.policy)
        evidence = check(self.sample,self.policy)
        self.client = evidence['typedData']
        self.bytes['fields']['/message/transcriptHash']['value'] = self.client['message']['transcriptHash']
        r = self.review(digest=evidence['commitment']['digest'])
        self.assertTrue(r['schemaReview']['checksPass'])
        self.assertFalse(r['accepted'])

    def test_null_schema_rejects(self):
        self.schema = None
        with self.assertRaises(ValueError): self.review()

    def test_digest_required(self):
        with self.assertRaises(ValueError): self.review(digest=None)

    def test_no_network_or_mutation(self):
        original = copy.deepcopy((self.sample,self.policy,self.client,self.bytes,self.schema))
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('network')):
            self.assertTrue(self.review()['accepted'])
        self.assertEqual(original,(self.sample,self.policy,self.client,self.bytes,self.schema))

    def test_output_overflow_emits_nothing(self):
        with patch.object(s,'MAX_OUTPUT',10), contextlib.redirect_stdout(io.StringIO()) as out:
            with self.assertRaises(ValueError): self.review()
        self.assertEqual(out.getvalue(),'')

    def test_cli_match_mismatch_and_null(self):
        args = [str(HERE/'example.transcript.json'),str(HERE/'example.policy.json'),
                str(HERE/'example.typed-data.json'),'--chain-id','1','--name',DOMAIN['name'],
                '--version','1','--primary-type','PaymentEvidence','--no-verifier',
                '--expect-digest',DIGEST,'--expect-bytes',str(HERE/'example.bytes-expectations.json'),
                '--expect-schema',str(HERE/'example.schema-expectations.json')]
        for schema,code in [(self.schema,0),({**self.schema,'types':{**self.schema['types'],'Extra':[]}},1),(None,2)]:
            with patch.object(s,'load',side_effect=[self.sample,self.policy,self.client,self.bytes,schema]), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(s.main(args),code)
            self.assertEqual(json.loads(out.getvalue())['accepted'],code==0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
