#!/usr/bin/env python3
"""Require complete schema agreement as well as historical payment byte review."""
import argparse
import json

from byte_payment import review as byte_payment_review
from check import load
from schema_review import review as schema_review, schema_expectations

MAX_OUTPUT = 100_000


def render(report):
    text = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + '\n'
    if len(text.encode('ascii')) > MAX_OUTPUT:
        raise ValueError('complete payment schema report exceeds 100000 bytes')
    return text


def review(sample, policy, client, expected_domain, primary_type, expected_digest,
           expected_bytes, expected_schema):
    """Expectations come from the caller, never from incoming declarations."""
    schema_expectations(expected_schema)  # Explicit null cannot disable this gate.
    payment = byte_payment_review(sample, policy, client, expected_domain,
                                  primary_type, expected_digest, expected_bytes)
    schema = schema_review(client, expected_schema, expected_digest)
    alerts = list(payment['alerts'])
    if not schema['schemaMatchesExpected']:
        alerts.append('independent_complete_schema_mismatch')
    accepted = payment['accepted'] and schema['checksPass'] is True
    result = {
        'accepted': accepted,
        'state': 'payment_bytes_and_schema_match' if accepted else 'review_required',
        'alerts': alerts, 'paymentByteReview': payment, 'schemaReview': schema,
        'limitations': 'Historical provider assertions only. Expectations require independent '
                      'custody. The digest does not bind unused declarations; the separate '
                      'schema comparison does. No freshness, state proof or signing approval.'}
    render(result)
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('transcript', 'policy', 'client'):
        p.add_argument(name)
    for name in ('chain-id', 'name', 'version', 'primary-type', 'expect-digest',
                 'expect-bytes', 'expect-schema'):
        p.add_argument('--' + name, required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--verifier')
    g.add_argument('--no-verifier', action='store_true')
    p.add_argument('--salt')
    a = p.parse_args(argv)
    domain = {'chainId': a.chain_id, 'name': a.name, 'version': a.version}
    if a.verifier is not None:
        domain['verifyingContract'] = a.verifier
    if a.salt is not None:
        domain['salt'] = a.salt
    try:
        result = review(load(a.transcript), load(a.policy), load(a.client), domain,
                        a.primary_type, a.expect_digest, load(a.expect_bytes),
                        load(a.expect_schema))
        print(render(result), end='')
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, TypeError, KeyError, RecursionError):
        print('{"accepted":false,"state":"input_error"}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
