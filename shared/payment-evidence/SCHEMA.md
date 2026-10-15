# Complete payment schema review

`schema_payment.py` combines Line 4's complete declaration reviewer with the
existing Line 3 payment replay, Line 2 contracts, independent domain/full-digest
binding, exact integers and byte expectations. The new vendored reviewer is an
unchanged source copy; `provenance.json` pins it. Its encoder is byte-identical
to the existing vendored encoder. Python standard library only. Copy this whole
`payment-evidence` folder to use it without the line folders or downloads.

From the repository root, one offline command:

```sh
python3 -B shared/payment-evidence/schema_payment.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json shared/payment-evidence/example.typed-data.json --chain-id 1 --name 'Read-only Payment Evidence' --version 1 --primary-type PaymentEvidence --no-verifier --expect-digest 0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c --expect-bytes shared/payment-evidence/example.bytes-expectations.json --expect-schema shared/payment-evidence/example.schema-expectations.json
```

Tried locally: exit 0, `payment_bytes_and_schema_match` for the retained real
ZTO payment observation. This is historical evidence, not a current payment.
The separately written expectation describes the existing fixed PaymentEvidence
protocol; bundled expectations illustrate execution, not independent approval.
Supply your own independently reviewed policy, domain, digest, byte values and
complete schema. Never derive expectations from an incoming client request.

Adding an unused declaration to the client leaves its digest, domain, integer,
byte and payment checks unchanged. This combined reviewer nevertheless exits 1
because the complete schema differs. `example.schema-rejection.json` records
that regression; it is an edited example, not another chain observation.
Field array order matters; declaration object key order does not. Every type,
including unreachable types and dependencies behind empty arrays, is compared.

All gates are mandatory. Explicit null schema/byte expectations and missing
digest reject. A matching schema cannot bypass a wrong amount, domain, byte
expectation, unsafe integer representation or failed payment policy.
Exit 0 means all gates match; 1 is a reviewed mismatch; 2 is an input/output
error. The complete ASCII JSON report including newline must fit 100,000 bytes,
or no partial report is emitted. Input readers reject symlinks, traversal,
hidden paths, special files, malformed/duplicate JSON and excessive inputs.

Run `python3 -B shared/payment-evidence/test_schema_payment.py`: 13 tests passed,
including unused declarations with unchanged digest, mandatory gates, payment
shortfall, CLI statuses, disabled network, no mutation and output bounds. The
same tests and demo pass in a detached copy without line folders.

This adds no cryptographic independence: the inherited encoder is shared.
Historical provider claims are not state/consensus proofs, current settlement,
ownership, permit support or signing approval. Complete schema matching does
not authenticate expectations. No network, wallet, environment discovery,
signing, sending or payments are performed by this utility.
