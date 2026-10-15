#!/usr/bin/env python3
"""Review a bounded saved JSON-RPC batch offline; never dispatch requests."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

B = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                       'bounded-rpc-snapshot' / 'snapshot.py'))
LIMIT = 100_000
MAX_ITEMS = 64


class ReviewError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ReviewError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def identity(value):
    require((type(value) is int and abs(value) <= 2**53-1) or
            (type(value) is str and 0 < len(value) <= 128),
            'IDs must be bounded strings or exact safe integers; no null/bool/float')
    return type(value).__name__, value


def validate_request(request):
    require(type(request) is dict and set(request) == {
        'jsonrpc', 'id', 'method', 'params'} and request['jsonrpc'] == '2.0',
        'invalid request envelope; notifications are unsupported')
    identity(request['id'])
    params = request['params']
    # Extend the inherited read validator only for EIP-1898 eth_call pins.
    if (request['method'] == 'eth_call' and type(params) is list and
            len(params) == 2 and type(params[1]) is dict):
        pin = params[1]
        require(set(pin) == {'blockHash', 'requireCanonical'} and
                type(pin['blockHash']) is str and
                B['HASH'].fullmatch(pin['blockHash']) and
                pin['requireCanonical'] is True, 'invalid canonical block-hash pin')
        params = [params[0], 'finalized']
    B['validate_request'](request['method'], params)


def review(document):
    require(len(canonical(document)) <= LIMIT, 'input exceeds canonical byte limit')
    require(type(document) is dict and set(document) == {'requests', 'responses'},
            'input must contain exactly requests and responses')
    requests, responses = document['requests'], document['responses']
    require(type(requests) is list and 1 <= len(requests) <= MAX_ITEMS,
            'requests must contain 1..64 entries')
    require(type(responses) is list and len(responses) <= MAX_ITEMS,
            'responses must be an array of at most 64 entries')
    expected = {}
    for position, request in enumerate(requests):
        validate_request(request)
        key = identity(request['id'])
        require(key not in expected, 'duplicate request ID')
        expected[key] = position
    found = {}
    for position, response in enumerate(responses):
        require(type(response) is dict and response.get('jsonrpc') == '2.0' and
                (set(response) == {'jsonrpc', 'id', 'result'} or
                 set(response) == {'jsonrpc', 'id', 'error'}),
                'invalid response envelope')
        key = identity(response['id'])
        require(key in expected, 'unexpected response ID')
        require(key not in found, 'duplicate response ID')
        if 'error' in response:
            error = response['error']
            require(type(error) is dict and {'code', 'message'} <= set(error) and
                    set(error) <= {'code', 'message', 'data'} and
                    type(error['code']) is int and type(error['message']) is str,
                    'invalid JSON-RPC error')
        found[key] = (position, response)
    entries = []
    for request in requests:
        key = identity(request['id'])
        entry = {'id': request['id'], 'method': request['method'],
                 'request_sha256': hashlib.sha256(canonical(request)).hexdigest()}
        if key not in found:
            entry.update(status='missing', response_index=None)
        else:
            index, response = found[key]
            entry.update(status='error' if 'error' in response else 'result',
                         response_index=index,
                         response_sha256=hashlib.sha256(canonical(response)).hexdigest())
            if 'error' in response:
                entry['error_code'] = response['error']['code']
        entries.append(entry)
    missing = sum(e['status'] == 'missing' for e in entries)
    errors = sum(e['status'] == 'error' for e in entries)
    result = {'schema': 'line1-batch-response-review-v1',
              'complete': missing == 0, 'all_results': missing == 0 and errors == 0,
              'request_count': len(requests), 'response_count': len(responses),
              'missing_count': missing, 'error_count': errors, 'entries': entries,
              'meaning': 'Envelope correlation only. Results are not validated Ethereum '
                         'values, authenticated state, freshness or atomic execution.'}
    require(len(canonical(result)) <= LIMIT, 'report exceeds byte limit')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='workspace-relative JSON with requests/responses arrays')
    args = parser.parse_args(argv)
    try:
        raw = B['SAFE_FILES']['read_bytes'](args.input, LIMIT)
        result = review(B['parse_json'](raw))
        output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True,
                            allow_nan=False) + '\n'
        require(len(output.encode('ascii')) <= LIMIT, 'rendered report exceeds byte limit')
        sys.stdout.write(output)
        return 0 if result['all_results'] else 1
    except (ReviewError, B['SnapshotError'], ValueError, OSError,
            TypeError, RecursionError) as exc:
        print('batch-response-review: ' + ascii(str(exc)), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
