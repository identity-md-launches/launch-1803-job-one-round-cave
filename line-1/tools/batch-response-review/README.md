# Batch response review

Review a saved batch of public Ethereum reads offline, matching each reply to its
request by ID rather than array position. Missing replies and JSON-RPC errors
remain visible. Duplicate or unexpected IDs reject the input instead of silently
choosing a reply. Integer `1` and string `"1"` are different IDs.

From the repository root, Python 3 with only its standard library:

```sh
python3 -B line-1/tools/batch-response-review/review.py line-1/tools/batch-response-review/zto-batch.json
```

This prints `complete: true`, `all_results: true`, and two matched `eth_call`
entries for real ZTO totalSupply and decimals observations. The fixture extracts
requests and responses unchanged from the inherited public capture; its source
hash, capture timestamp and block hash are in `provenance.json`. It is historical,
not a fresh chain observation. Reversing the response array still matches both
response hashes to their original requests.

For your own input, supply one JSON object with exactly `requests` and `responses`
arrays. Requests must have `jsonrpc`, `id`, `method`, `params`; replies must have
`jsonrpc`, `id`, and exactly one of `result` or `error`. Supported methods and
parameters follow the existing bounded public-read validator, with canonical
EIP-1898 block-hash pins also accepted for `eth_call`. Notifications, null IDs,
boolean/fractional IDs, unsafe integers, and nonstandard envelope fields reject.
Strings are limited to 128 characters for IDs, batches to 64 entries, input and
rendered output to 100,000 bytes. Duplicate JSON object keys and non-JSON numeric
constants reject. Inputs use the inherited workspace-relative, no-follow regular
file reader. The program writes only its report to stdout and never uses a
network transport.

Exit codes: **0** every request has a result; **1** valid evidence with missing
replies or RPC errors; **2** malformed/ambiguous evidence or file failure. A null
result counts as an envelope result, and is not interpreted as successful
Ethereum execution. Error messages/data and complete result payloads remain in
the input; the report includes per-envelope canonical SHA-256 hashes and error
codes, avoiding unbounded terminal content.

## What happened when tried

All 24 offline tests passed, including response reordering, integer/string ID
separation, duplicate and foreign IDs, missing replies, RPC errors, invalid pins,
write-method rejection, duplicate JSON keys, size bounds, input immutability,
CLI exits, path boundaries and a disabled-network run. The demo matched both
historical ZTO replies. Run the checks with:

```sh
python3 -B -m unittest discover -s line-1/tools/batch-response-review -p 'test_*.py' -v
```

## Limits

This checks correlation and envelope shape, not result semantics, state proofs,
provider honesty, freshness or atomic batch execution. Request hashes identify
supplied requests; they do not establish what a provider received. Response
hashes are canonical JSON hashes, not retained original-byte pins. Bounds are
not a CPU sandbox. Keep the original transcript and an independently retained
byte hash when provenance matters. Existing hash-pinned ZTO validation is still
the tool for interpreting ZTO supply/decimals. No external package is needed;
the sibling bounded validator and safe reader must travel with this tool.
