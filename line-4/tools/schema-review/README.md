# Offline EIP-712 schema reviewer

See exactly which declarations an EIP-712 request commits to, including types
behind empty arrays. Compare the primary type and **every** declaration with a
separately prepared schema, preserving field order. Reports dependency edges,
canonical `encodeType`, type hashes, domain/message reachability, actual struct
instance counts, empty arrays, and unused types. Python standard library only;
copy this whole folder to use it without the repository or a network.

Run from the repository root:

```sh
python3 -B line-4/tools/schema-review/schema_review.py line-4/tools/schema-review/zto-payment.json --schema-expect line-4/tools/schema-review/zto-schema.json --digest-expect 0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774
```

Tried: exit **0**, `schemaMatchesExpected`, `digestMatchesExpected`, and
`checksPass` are true. The two declarations each have one value instance and
there are no unused types. This reproduces the inherited historical commitment
to evidence of a real ZTO transfer, token
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`. No fresh chain read is claimed.
The fixture is a read-only evidence commitment, not a token permit or an assertion
that ZTO supports this schema. The demo schema and digest come from the inherited
fixture and demonstrate execution, not independent approval.

Replace the input filename with `zto-unused-declaration.json` in that command:
exit **1**, the digest still matches, but `schemaMatchesExpected` is false and
`unpinnedTypes` contains `UnreferencedNote`. The variant adds only an unreferenced
schema declaration. It is an intentional rejection example, not another chain
observation. Saved results are `example-match.json` and `example-rejection.json`.

Prepare actual expectations separately under your control, in this shape:

```json
{
  "primaryType": "Batch",
  "types": {
    "EIP712Domain": [],
    "Batch": [{"name": "items", "type": "Item[]"}],
    "Item": [{"name": "amount", "type": "uint256"}]
  }
}
```

That is a schema format example. With an empty `items` array, `Item` has zero
value instances but remains reachable and bound by the message type hash.
Changing `Item.amount` to `uint128` changes the digest even with no items.
Unused declarations, in contrast, do not enter either root's type hash. Their
addition/removal/change still fails this tool's **complete schema** comparison.
Explicitly expected unused declarations may match and remain flagged as unused.

`unpinnedTypes` are incoming declarations missing from expectations;
`absentTypes` are expected declarations missing from the request;
`changedDeclarations` shows both ordered field lists. JSON object key order is
immaterial; field array order, names, types, array dimensions and primary type
must match exactly. The expected schema is validated even if it has no actual
values. Unknown references and invalid unused declarations reject. Recursive
schemas are supported with finite values; actual cyclic Python values reject.
`valueInstanceCount` counts appearances across domain and message, not distinct
object identities. Array paths refer to parsed data, never filesystem paths.

Schema agreement alone says nothing about amounts, addresses, strings, domain
values, or other message values. Supply a separately retained `--digest-expect`
to compare all encoded domain/message contents. A digest does not bind unused
declarations or original JSON formatting. Changing both the input and its
expectations can pass; keep expectations independently. Matching does not prove
settlement, ownership, contract support, replay protection or signing approval.
This tool never signs, sends, dispatches RPC, pays, posts, reads environment
variables or accesses a wallet. It needs no key and installs nothing.

Without expectations it is inspection only: `checksPass: null`, exit **0**.
With either or both options, all requested comparisons must pass: exit **0**
for match, **1** for mismatch, **2** for invalid input, unsafe file or exceeded
bound. Explicit JSON null expectations reject. No partial report is emitted
on exit 2. The Python API has the same behavior: `review(data)` inspects,
`review(data, policy, expected_digest)` compares; an explicit null policy rejects.

The unchanged ancestor encoder is shared implementation, not independent
cryptography. [EIP-712](https://eips.ethereum.org/EIPS/eip-712) defines encoding
and dependency ordering. `provenance.json` pins source copies. The inherited
encoder accepts custom domain declarations; this is an encoding review, not a
validator of standard domain field semantics or a particular wallet's support.

Both JSON inputs must be regular no-follow files beneath cwd, each at most
65,536 bytes. Duplicate keys, invalid UTF-8/Unicode, floats, nonfinite numbers,
hidden paths, parent traversal, symlinks and special files reject. The reader
requires POSIX directory descriptors. Inherited bounds: depth 48, 8,192 nodes,
64 types, 256 fields and eight array dimensions. The complete ASCII JSON report
including its final newline is bounded to **100,000 bytes**; expansion fails
closed rather than truncating declarations. Bounds are not a full CPU sandbox.

```sh
python3 -B -m unittest discover -s line-4/tools/schema-review -v
```

Tried: **29 tests pass**. They cover hidden empty-array dependencies, unused-type
changes with an unchanged digest, recursive schemas, nested arrays, type/field
order and name substitutions, independent value/digest comparison, both roots,
strict/null policies, unsafe paths, report expansion, immutability, disabled
network and CLI exits. All 29 tests also pass in a detached folder, and all 28
ancestor encoder tests pass. Local command results are in
`line-4/check-results-33.json`; these are observations, not certification.
