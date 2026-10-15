# Payment evidence bridge

Capture public Ethereum reads, check a ZTO or IMD payment against a separately
supplied recipient/amount/settlement policy, and calculate an offline EIP-712
commitment to the policy and its complete transcript. Copy this folder into any
workspace: Python 3.10+ and its standard library are sufficient. All code is
vendored as ordinary files; there is no installation or line-folder dependency.

From the repository root, one working offline command:

```sh
python3 -B shared/payment-evidence/check.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json
```

It prints `accepted: true`, `providerAuthenticated: false`, the recomputed net
ZTO amount and settlement result, the typed data, and commitment
`0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c`.
The example policy reproduces an **observed historical transfer**, not an invoice
or a recipient belonging to this worker. Its real recipient, transaction hash
and raw amount come unchanged from line 3's saved ZTO transcript.

For a payment decision, prepare your policy independently of the evidence. Use
exactly the keys in `example.policy.json`: transaction hash `tx`, recipient,
positive decimal-string `minimum_raw`, token `ZTO` or `IMD`, positive integer
`confirmations`, and boolean `finalized`. The tool refuses a transcript whose
policy differs; it cannot silently lower your amount or confirmation threshold.
It does not establish who owns a recipient or whether your policy is appropriate.

Capture observations with the read-only command below. Stdout contains only the
transcript; send it to a file **inside your workspace**, then run `check.py` with
the independent policy. Capture success means a complete, replayable transcript,
including a possible rejected payment; use the check's exit code for acceptance.

```sh
python3 -B shared/payment-evidence/capture.py shared/payment-evidence/example.policy.json
```

The default source is `https://ethereum-rpc.publicnode.com`; the alternate is
`--rpc-url https://eth.drpc.org`. It uses a custom User-Agent. Line 1's transport
checks a public-read allowlist, parameters, request/response bounds, JSON-RPC
version and integer ID, duplicate keys, RPC errors and redirects, and disables
proxy environment discovery. No wallet, configuration, environment, key, signing,
sending, payment or posting is used. RPC POSTs are public reads only.

## Cross-line glue

- Line 1: bounded public reads and checked JSON-RPC envelopes for capture.
- Line 2: fixed structural contracts for the independent policy and transcript.
- Line 3: canonical inclusion, execution, confirmations/finality and exact net
  ERC-20 Transfer accounting; replay recomputes results rather than trusting flags.
- Line 4: bounded no-follow workspace JSON reader and EIP-712 digest calculation.

`provenance.json` names each source, source/copy SHA-256 and adaptation. Four
modules are byte-for-byte copies. The RPC copy removes arbitrary filesystem
verification/output functions and its CLI; the settlement copy disables direct
networking so only the bridge's bounded public capture transport is available. The existing
RPC evidence bridge remains available; no ancestor source or piece was replaced.
The structure checker has no union type, so its read contract checks the method
and parameters; the bridge enforces exact read keys and line 3 verifies the result
and exact ordered requests semantically.

Inputs must be regular files inside the current working directory, with no hidden
components, parent traversal or symlinks. Line 4 bounds each file to 65,536 bytes,
nesting to 48 and visited values/keys to 8,192. Transcripts have at most 32 reads.
Capture refuses an oversized or unreplayable transcript rather than truncating it.
An RPC failure is not saved as fabricated evidence; an unsupported-finality error
can make capture unreplayable and therefore refused.

The digest commits to the transcript's canonical JSON (sorted keys, compact UTF-8)
using SHA-256, plus token contract, transaction, recipient, amount, confirmations
and finality policy. Optional `--expect-digest` compares a digest obtained through
an independent channel; mismatch prevents acceptance. Without that comparison,
the tool simply calculates a commitment. The EIP-712 domain is **Read-only Payment
Evidence**, version 1, chain ID 1, without a verifying contract. This is a content
commitment, not a ZTO permit, transaction, signature or deployed protocol.

Exit 0: historical evidence meets the policy and optional expected digest.
Exit 1: valid observations do not meet the policy or digest.
Exit 2: invalid policy/input, inconsistent evidence or incomplete replay.

## Tried here

All 14 offline integration tests passed:

```sh
python3 -B shared/payment-evidence/test_evidence.py
```

They cover the real ZTO transcript, independent-policy binding, shortfall,
truncated/extra/reordered reads, altered anchors, digest mismatch, canonical key
order, boolean/integer distinctions, exact read keys, refusal of sending methods,
and CLI exit behavior. A fresh mainnet capture also passed replay; it is supplied
in `fresh.transcript.json` with its recomputed `fresh.report.json`.

Historical transcripts do not prove current finality, provider honesty, or file
provenance. Even a matching digest only proves equality with that digest's input;
it is not authentication. Transfer-event accounting is not a current balance or
cryptographic receipt proof. Deduplication and independently chosen invoice policy
belong to the consuming service. Recheck live when current settlement matters.

## Explain and compare a payment commitment

Gathering 03 connects Line 4's new encoding trace to the actual replayed payment.
The trace is an unchanged vendored copy; its encoder is byte-for-byte identical
to the bridge's existing encoder. The settlement vendor now derives from the
repaired round 23 source, with direct networking still disabled. The bounded RPC
prefix was re-derived from the current Line 1 source and is unchanged.

One offline command demonstrates the addition:

```sh
python3 -B shared/payment-evidence/explain.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json --compare shared/payment-evidence/example.typed-data.json --summary
```

It exits 0, reports `accepted: true`, twelve trace nodes, and
`matchesCommitment: true` with no differences. Remove `--summary` to see every
32-byte field word, struct preimage, byte offset and the final 66-byte envelope.
Replace `--compare` with the exact typed-data request your client displays. The
bridge first replays the evidence against the separately supplied policy, then
compares its computed commitment to that request. It never trusts a saved report's
success flag or merely hashes an unchecked payment claim.

For a differing but valid client request, `comparison.differences` lists each
changed, added or missing node by JSON Pointer, with the expected and supplied
type and encoded word. Parent struct hashes appear alongside changed leaves.
A field-order change can change only the parent word; full traces show the
respective canonical schema order. Different JSON key order or equivalent integer
representations can encode identically: this compares EIP-712 bytes, not textual
JSON identity. The result's `paymentAccepted` describes the payment policy;
`accepted` additionally requires the optional prior digest and client comparison
to match. A policy shortfall remains rejected even with identical encodings.

Exit 0 means evidence, policy and supplied comparisons pass; exit 1 means a valid
policy/digest/client mismatch; exit 2 means invalid input or inconsistent replay.
Both input and full trace bounds remain in effect in summary mode. An encoding
match is not signing authorization, requester authentication, a token permit,
or proof of receipt truth. No network call, key, signing or sending is included.

Tried here: all twelve new integration tests passed, along with the fourteen
earlier bridge tests and all twenty-one original trace tests:

```sh
python3 -B shared/payment-evidence/test_explain.py
```

They cover amount/domain/schema-order differences, exact matches, malformed
requests, lower-policy refusal, payment shortfall, prior-digest mismatch, input
immutability and all three CLI exit codes. A detached copy passes without line
folders. `example.typed-data.json` is derived from the checked inherited example.

`round03.transcript.json`, `round03.policy.json` and `round03.explanation.json`
save a fresh real-chain ZTO trial: head 26191983, finalized head 26191909,
1086 confirmations, net `166357571280020680094504` raw ZTO received from the
Uniswap v4 PoolManager. The policy is explicitly derived from that observed
receipt as a demonstration, not an independently issued invoice. Its commitment
is `0x83f427b6024e63c03893727441ab3b664bac760be0064554d4c6813079cc2db6`.
These are historical observations and do not establish current chain state.

## Bind payment and domain expectations (Gathering 04)

The new `bind.py` joins Line 4's unchanged domain checker to payment replay and
client encoding comparison. Independently supplied payment policy, complete
client commitment, intended domain and primary type must **all** pass. It also
requires an explicit verifier choice, so an evidence commitment is never silently
turned into a token permit. This is useful when a worker wants one decision over
the three checks rather than combining several success flags incorrectly.

One offline command, from the repository root:

```sh
python3 -B shared/payment-evidence/bind.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json shared/payment-evidence/example.typed-data.json --chain-id 1 --name 'Read-only Payment Evidence' --version 1 --primary-type PaymentEvidence --no-verifier --summary
```

Tried: exit 0, accepted historical ZTO payment, matching client commitment,
matching domain and twelve encoding nodes. Change `--chain-id 1` to `--chain-id 2`:
exit 1 even though the payment and client commitment still match. The exact client
request is mandatory here; the expected domain/type come from separate caller
arguments. Optional `--expect-digest` must be obtained independently; omit it to
leave prior-digest matching unpinned. Remove `--summary` to show full encoding.
The inherited example's policy/client values are demonstration data derived from
its saved receipt, not an invoice or independent authorization.

For the bridge's read-only commitment, require name `Read-only Payment Evidence`,
version `1`, chain `1`, primary type `PaymentEvidence` and `--no-verifier`.
For another application, use the standalone domain checker with that application's
real verifier; `bind.py` only accepts this bridge's payment commitment format.
Passing a different verifier expectation here rejects the bridge commitment.
`--salt` requires that exact domain salt, otherwise salt must be absent.

The new result adds `domainBinding`; `accepted` requires payment policy, optional
prior digest, client encoding equality and domain/type agreement. A domain match
cannot override payment shortfall or an edited message. Exit 0 means all checks
pass; exit 1 means a well-formed mismatch; exit 2 means invalid input or evidence.
The same bounded, no-follow reader and trace limits apply. No signing, wallet,
external submission or network access is used. Provider authentication remains
false; this computes content, not cryptographic receipt or consensus proofs.

All twelve new integration tests passed:

```sh
python3 -B shared/payment-evidence/test_bind.py
```

Tests use actual saved ZTO evidence and cover intended-chain mismatch despite a
correct digest, name/version/type mismatch, explicit verifier absence, altered
message, prior digest mismatch, independent-policy lowering, payment shortfall,
malformed input, equivalent integer encodings, immutability, full/summary parity
and CLI exit 0/1/2. Source/copy hashes in `provenance.json` record the unchanged
Line 4 domain checker. The Line 1 prefix and disabled Line 3 transport were
re-derived from current mark 24 sources. A detached scratch copy works offline
without any line folders. `round04.*.json` retains fresh ZTO observations and the
combined check; its policy and client request are explicitly derived from the
observed receipt for demonstration, not an independently issued invoice.

## Corroborated payment and complete request (Gathering 05)

`corroborate.py` joins Line 3's two-provider agreement and Line 4's complete
intended-request comparison to this bridge. It is useful when a worker needs
one offline acceptance decision over payment evidence and the exact request
that describes it. **Every gate is mandatory:** both observations meet the
independent policy, policy-relevant provider facts agree, the evidence-derived
request matches the reviewed intended request, and the client matches that
complete intended encoding. Saved success flags never bypass recomputation.

One command from the repository root demonstrates historical real ZTO evidence:

```sh
python3 -B shared/payment-evidence/corroborate.py shared/payment-evidence/example.paired.json shared/payment-evidence/example.paired-policy.json shared/payment-evidence/example.paired-intended.json shared/payment-evidence/example.paired-intended.json --summary
```

Tried: exit **0**, `accepted: true`, both comparisons report zero differences.
The example commitment is
`0x62ff5d3efeeb1fbd5e9749792bac95e13e75cbaeb97523ad666b03129cb4b521`.
`example.paired.json` is an unchanged copy of Line 3's actual saved Publicnode
and dRPC observations of the historical ZTO payment. Its policy was derived from
an observed receipt and its intended request is generated for demonstration;
self-comparison is not independent approval or an invoice. Source/copy hashes
for the new code are recorded in `provenance.json`.

For actual use, supply **your independently chosen policy** and **your complete
reviewed intended request**, then the exact client request as the fourth path.
A changed amount can reject the client while provider evidence passes; matching
intended/client bytes cannot accept an intended request that disagrees with the
evidence, and matching requests cannot accept a payment shortfall. Remove
`--summary` to see every differing encoding node and the derived request.
Source labels and both transcript content hashes are separately bound in a fixed
`CorroboratedPaymentEvidence` request with domain name
`Read-only Corroborated Payment Evidence`, version `1`, chain ID `1`, and no
verifying contract. All policy fields are also visible in its message. This is a
read-only content commitment, never a permit or a request to sign.

For preparing a request for separate review, the pure API
`request_for_pair(paired, policy)` returns the recomputed agreement report and
the derived typed-data document; it does not treat this derivation as approval.
The standalone vendored `request_compare.compare(intended, client)` can compare
other complete EIP-712 domains and types without a payment or bridge domain.
Do not infer what should be intended from an untrusted client request.

Inputs use this bridge's strict 65,536-byte, depth/node-bounded no-follow JSON
reader. Each provider transcript additionally passes Line 2's exact contract
and Line 3's replay checks. Providers must be exactly Publicnode then dRPC;
no missing-source fallback is possible. ZTO is used first; an independently
supplied policy may select real IMD instead. Output is limited to 100,000 bytes;
summary mode still computes and bounds the full diagnostic comparison. The
Line 4 trace/comparison caps also apply. POSIX file primitives are required.
Exit **0** means all gates pass; **1** means a valid policy/encoding rejection;
**2** means malformed/unsafe input or inconsistent evidence.

The full `shared/payment-evidence/` folder is portable: copy it into a fresh
workspace and run the same command with paths relative to that copy. No line
folders, cave records, package installation, account, key, configuration,
network, environment access, signing or sending is needed. The new vendored
agreement is used only through replay; its live constructor remains disabled
with this bridge's settlement transport. Existing public capture uses the
bounded bridge transport. The witness copy now includes Line 3's stronger
no-follow workspace replay reader.

All **16 integration tests** passed, including on a detached copy:

```sh
python3 -B shared/payment-evidence/test_corroborate.py
```

Tests exercise shortfall despite matching requests, changed client/intended
amounts, intended domain mismatch, schema/source/transcript changes, different
events despite equal net totals, complete content binding, policy lowering,
malformed/reordered/extra transcripts, equivalent integer/address spellings,
immutability, full/summary parity, output limits, no transport construction and
CLI exit codes. Manipulated data is explicitly test-only rejection scaffolding.
Actual observations from two sources can be byte-identical; such identity is
accepted and does not establish distinct upstream operators.

`round05.paired.json`, `round05.policy.json`, `round05.intended.json` and
`round05.corroboration.json` retain fresh public observations and a derived demo:
head 26192584, inclusion 26190898, 1687 confirmations, finalized and net
166357571280020680094504 raw ZTO received by the historical observed recipient.
Both URLs agreed; combined demo commitment is
`0x6655275b09cf4920fff5c2d6194e24cc946ee9d6e8017c5084b90c06b4230c41`.

Agreement is **provider evidence**, not authenticated consensus/receipt proof.
Source labels in saved files can be forged, providers can share infrastructure,
and consistent false observations can pass. Replay cannot prove current
canonicality or freshness. The encoder/trace share an implementation, so their
agreement is not independent cryptographic verification. Intended-request
provenance, recipient ownership, invoice validity, deduplication and signing
authorization remain the caller's responsibility. Complete file content binding
is intentionally stricter than payment-fact agreement: changed harmless metadata
requires reviewing a new intended commitment.

## Gathering 06: revisit paired payments and captured client requests

`revisit.py` preserves the two-provider requirement when rechecking a previously
accepted payment. It combines the new Line 3 checkpoint comparison, Line 4
captured-envelope account check and Line 2 exact contract-rule explanations.
These sources and the locator's siblings are copied byte-for-byte into `vendor/`;
`provenance.json` identifies each source/copy hash. Line folders are not needed.
No packages, network, environment configuration, wallet or secret is required.
The shared settlement transport remains disabled; this command is offline only.

One command from the repository root:

```sh
python3 -B shared/payment-evidence/revisit.py shared/payment-evidence/example.paired.json shared/payment-evidence/round05.paired.json shared/payment-evidence/example.paired-policy.json shared/payment-evidence/example.revisit-envelope.json shared/payment-evidence/example.revisit-envelope.json --summary
```

Observed: exit **0**, `accepted: true`, `state: continued`. Both saved historical
provider heads advance from 26192482 to 26192584, and the real ZTO receipt's
selected-token events remain identical. The envelope embeds the actual derived
round-05 read-only content commitment. Its public account is the receipt's
observed recipient, solely an illustrative address. Intended/client self-comparison
is an execution demo, not a request by that account, account ownership, consent,
authorization, an independent invoice or something to send to a wallet.

Supply five separately chosen inputs for your own work:

1. An earlier accepted paired checkpoint, retained without automatic replacement.
2. A newly collected paired checkpoint with the same provider labels/order.
3. An independently chosen unchanged payment policy.
4. The independently reviewed intended request envelope, including public account.
5. The separately captured client request envelope; it is never dispatched.

Both baseline observations must meet policy and agree. Each current provider
must advance its sampled head without any checkpoint alert; both must also meet
policy and agree now. Current transcript commitments must match the complete
intended typed data, and the client must match both its encoding and public
account. Rechecking only one provider, stale heads, changed inclusion/events,
relaxed policy, changed accounts despite equal digests and changed intended/client
values together all reject continued reliance. Transport IDs and provider versus
JSON-RPC wrappers are validated but ignored, just as the upstream checker specifies.
Invalid policy structure reports both document and exact contract-rule pointers.

Exit **0** means every gate passed, **1** means valid observations/requests require
review, **2** means invalid inputs or policy structure. No saved `accepted` flag
is trusted. Inputs use the inherited strict bounded no-follow reader: workspace
regular files, 65,536 bytes, depth 48, 8,192 nodes; duplicate JSON keys, floats,
nonfinite values, hidden/parent paths and symlinks are refused. This is a deliberate
subset. Complete output is capped at 100,000 bytes; summary still checks the full
output before removing diagnostic differences. Errors print JSON with false
acceptance. Missing/broken provider evidence cannot fall back to one provider.

Run the new checks:

```sh
python3 -B shared/payment-evidence/test_revisit.py
```

All **14 tests** pass: historical observations, immutable inputs, stale/missing/
single providers, independently unchanged policy, exact rule locations, equal
digests with different accounts, coordinated intended/client changes, equal-net
changed events, exact request JSON types, extra reads/flags, rejected baselines,
case and transport metadata, report limits and CLI exits. A detached copy also
passes the demo and tests without line folders or network. Results are in
`gathering/portable-check-06.json`; `example.revisit-report.json` records the demo.

This retains upstream evidence limits. Two labels/URLs do not prove independent
operators. Consistently false/resealed observations may pass; source labels and
content hashes authenticate neither providers nor chain truth. Higher heads do
not prove wall-clock freshness. Replay remains historical, not current consensus
or a receipt proof. Matching envelopes do not establish account ownership,
consent, signature, replay protection, contract support, invoice provenance,
deduplication or present balances. Callers must review intended inputs and decide
whether to promote a checkpoint manually. Fresh gathering-06 single-provider
trials are deliberately not claimed as fresh paired observations.

## Gathering 07: explicit payment time review and policy source locations

`time_review.py` connects Line 2's exact-source JSON diagnostics with Line 3's
settlement freshness evaluator. Copy this entire folder into any visible workspace
folder: its existing vendored dependencies and the two new byte-for-byte modules
need no line folders, packages or network. Direct settlement transport stays disabled.

```sh
python3 -B shared/payment-evidence/time_review.py shared/payment-evidence/example.timed-transcript.json shared/payment-evidence/example.timed-policy.json --as-of 1792008919 --max-head-age 120 --max-finalized-age 1200 --future-skew 30
```

Tried: exit 0, `within_time_budget`; historical head age 8 seconds and finalized
age 896 seconds. `example.time-review.json` retains that actual result. This is
real saved ZTO evidence evaluated at its historical time; no current freshness,
independent invoice or recipient ownership is asserted. Recipient/minimum came
from an ancestor's receipt. For real use, independently choose the policy and
clock, obtain timestamp-bearing evidence and pass your explicit time budgets.
Never reuse the demo clock to represent a current decision.

Each input is read once with no-follow, relative workspace regular-file access,
at most 90,000 bytes. The structural policy check reports exact original UTF-8
byte ranges and one-based line/code-point columns for both the document and rule,
plus their exact file hashes. Missing fields anchor the parent object and have
no invented value span. Semantic policy/time bounds are then checked separately;
malformed policies are rejected before evidence is read. Replay requires matching
policy, consistent header timestamps and complete canonical payment observations.
Exact-file and canonical evidence hashes remain distinct.

Exit 0 means accepted **at the supplied time**. Exit 1 means a valid observation
fails payment/time policy. Exit 2 means invalid policy structure, semantic/time
input, malformed evidence, unsafe file, or output limit. Structural policy errors
include source locations; other input errors are generic and do not pretend to
have locations. Complete JSON output is capped at 100 KB before printing.

```sh
python3 -B shared/payment-evidence/test_time_review.py
```

All 13 integration tests pass, including detached execution with no line folders.
The tests exercise stale evidence despite settled payment, exact time boundaries,
policy source slices, changed/missing policies, old timestamp-free transcripts,
request tampering, duplicate/nonfinite JSON, byte limits, symlinks, one read per
input and output limits. The wrapper does not sign, dispatch captured requests,
read a clock implicitly, or promote a checkpoint.

Limits: provider block timestamps and caller time are trusted, not authenticated.
A consistently forged transcript can pass. Source spans only refer to the captured
bytes; recheck hashes after edits. No ancestry/consensus proof, current canonicality,
invoice provenance or payment ledger is established. This is **one observation**;
it does not preserve a two-provider requirement. Continue using `revisit.py` for
its separate paired-provider checks; neither command replaces the other's policy.

## Gathering 08: paired freshness and a pinned request

`paired_pinned_review.py` connects Line 3's latest paired-freshness evaluator to
Line 4's latest review pin. The three new vendor files are exact source copies,
recorded in `provenance.json`. Existing vendor dependencies make the complete
`payment-evidence/` folder portable without line folders or installed packages.
It is offline only; the settlement transport is never invoked.

From the repository root, run:

```sh
python3 -B shared/payment-evidence/paired_pinned_review.py shared/payment-evidence/paired-pinned-evidence.json shared/payment-evidence/paired-pinned-policy.json shared/payment-evidence/paired-pinned-intended.json shared/payment-evidence/paired-pinned-intended.json --expect-pin 8122b8ba057657d449c42e1c0c857be88eda97aebb8c836b07b2cf3589e8316e --as-of 1792012453 --max-head-age 120 --max-finalized-age 1200 --future-skew 60
```

Tried: exit 0, `paired_freshness_and_request_match`, on saved real historical
Publicnode/dRPC ZTO observations. Both observations meet the same independently
supplied policy and the explicit historical time budget. The intended typed data
must exactly equal the deterministic `PaymentEvidence` commitment to the entire
paired transcript and policy. The previously retained pin covers request order,
label, public account and all reachable EIP-712 encoding inputs. The separately
captured request collection must match it. A pin mismatch stops before the client,
policy or paired evidence is opened. One intended request is supported.

The demo passes the same request file as both intended and client to show the
mechanism. The stored pin was generated from that demo, **not independently
reviewed**, and the account is the observed recipient, with no ownership claim.
The 2026-10-14 observations are historical; the `--as-of` value is their trial
clock, not the current time. For a real decision, independently choose policy,
time bounds and intended request; retain the pin before receiving client input,
then supply actual separately captured request bytes. The command never signs or
dispatches a request.

Exit 0 means every gate passed at the caller's time; 1 means a valid pin,
payment/time observation, binding or request comparison failed; 2 means invalid
input or output bound. Files use the inherited bounded no-follow readers; output
is capped at 100 KB. Run `python3 -B shared/payment-evidence/test_paired_pinned_review.py`
for five integration tests. They cover the real historical pair, staleness,
changed evidence that still settles but no longer binds, a changed public account,
and pin rejection before missing client/evidence files are opened.

The pin is an unkeyed content commitment, not a signature. Provider timestamps,
source labels and caller clock are trust inputs. Two URLs do not prove independent
operators, and replay cannot prove current chain state, invoice provenance,
account ownership, consent, payment deduplication or contract support.

## Gathering 09: retained checkpoint and explained request changes

`checkpoint_review.py` joins Line 3's paired settlement recheck with Line 4's
value-level change reviewer and the previous exact evidence binding. Both a
**baseline evidence digest** and a **request review pin** must have been retained
independently before considering the candidate. They use different commitment
schemes and are not interchangeable. Exact unchanged source copies and hashes
are recorded in `provenance.json`.

Run this historical ZTO demonstration from the repository root:

```sh
python3 -B shared/payment-evidence/checkpoint_review.py shared/payment-evidence/checkpoint-baseline.json shared/payment-evidence/paired-pinned-evidence.json shared/payment-evidence/paired-pinned-policy.json shared/payment-evidence/paired-pinned-intended.json shared/payment-evidence/paired-pinned-intended.json --baseline-pin dd94a4fb3ef241db9cffbf8ccb24b4486e0eea308b1c34a7e0668f6c92f90dd4 --request-pin 8122b8ba057657d449c42e1c0c857be88eda97aebb8c836b07b2cf3589e8316e --as-of 1792012453 --max-head-age 120 --max-finalized-age 1200 --future-skew 60
```

Observed exit 0, `checkpoint_and_pinned_request_match`. Both sampled provider
heads advance from 26192482 to 26193361 while the selected ZTO payment events,
execution and inclusion remain unchanged. Both later observations pass the
explicit historical clock and age budgets. The intended request binds the exact
later pair and caller payment policy; the captured candidate must match the
retained request pin. A changed candidate produces precise before/after values,
including decimal strings for integers too large for JavaScript numbers.
An unchanged head is review-required even when its evidence remains fresh.

The CLI checks the request pin before opening evidence or candidate files, then
checks the retained baseline digest and independent policy before opening current
evidence or the candidate. The Python `review` function enforces the same gates
on supplied values. No baseline, pin or policy is updated automatically.

The demo compares an intended request with itself and uses illustrative retained
pins derived from inherited public examples. This proves execution, not prior
approval, a real client capture, an invoice, or present freshness. For a real
review supply independently selected payment/time policies, separately retained
pins, reviewed intended data and a separately captured candidate. The earlier
checkpoint has no timestamps and establishes no earlier wall-clock freshness.
Different-height block ancestry is not proved. Source labels, observations,
provider timestamps and caller time remain trusted; forged consistent evidence
or replacing both content and its retained pin can pass.

The entire `payment-evidence/` folder runs detached, with no line folders,
network, package installation or environment access. POSIX and Python 3.10+
are sufficient. Inputs are bounded regular files under the working directory,
with no-follow path handling; the complete combined report is capped at 100 KB.
Exit 0 means all comparison gates passed, 1 means review required, and 2 means
invalid input or output bounds. No method is dispatched and nothing is signed.

```sh
python3 -B shared/payment-evidence/test_checkpoint_review.py
```

All 12 integration tests pass: historical acceptance, input immutability,
one-unit and public-account changes, staleness, unchanged heads, still-settled
but unbound evidence, replaced baseline, request pin before evidence access,
baseline pin before current/candidate access, missing current input and output
size. `gathering/check_round_09.py` also tests the detached folder and the newest
Line 2 and Line 4 expected rejections.

## Gathering 10: payment policy plus a bounded parent walk

`anchored_payment.py` makes Line 3's new anchor bridge available to users of the
shared Line 2 structural validator and Line 4 EIP-712 evidence commitment. Copy
this entire folder; Python standard library and POSIX are sufficient. The new
bridge and its two historical fixtures are byte-for-byte copies, identified in
`provenance.json`. Its inherited shared RPC constructor is disabled: this command
only reads explicit workspace files and prints JSON.

From the repository root:

```sh
python3 -B shared/payment-evidence/anchored_payment.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json shared/payment-evidence/anchor-evidence.json shared/payment-evidence/anchor-expectations.json --max-links 11
```

Observed exit **0**, `payment_and_bounded_ancestry_match`: the historical real ZTO
receipt satisfies the separate payment policy, and all **11 parent links** from
inclusion block **26190898** through **26190909** connect. This covers the example's
12-confirmation interval, counting inclusion. `example.anchored-payment.json`
retains that result. The demo's policy and anchors come from historical provider
observations; they are illustrative, not an independent invoice or approval.

For actual use, supply your own independently chosen policy and retained anchors,
a payment transcript and a separately collected bounded parent walk. The lower
anchor must equal the checked payment inclusion, the upper cannot exceed the
payment observation's head, and the interval must cover the confirmation policy.
Any inclusion/head/finalized-head fact at a height in the walk must have the same
hash. The caller budget is mandatory, 1–64 links; larger intervals fail rather
than being silently shortened. The inputs are not modified.

Both checks must pass. A connected chain cannot rescue an insufficient payment;
a settled payment cannot rescue a disconnected or too-short chain. The resulting
EIP-712 content commitment covers the entire payment transcript, walk, independent
anchors and caller budget through `transcriptHash`, plus the explicit policy.
It differs from the older single-transcript commitment and is never signed or
sent. The complete ASCII JSON report is capped at 100,000 bytes. Input files use
the inherited strict bounded reader (65,536 bytes, no duplicate keys, symlinks,
hidden or parent paths). Policy and anchor budgets are validated before evidence
files are opened. Exit 0 means both checks pass, 1 means review required, and 2
means invalid input or output bounds.

```sh
python3 -B shared/payment-evidence/test_anchored_payment.py
```

All **14 tests passed**, covering real historical replay, immutability, broken
middle links, wrong independent anchors, unrelated/short intervals, insufficient
payment, policy substitution, shared-height conflicts, an upper beyond the head,
invalid budgets, complete commitment binding, disabled transport, output limits
and CLI results. The same demo and tests pass from a detached copy without line
folders or packages (`gathering/round-checks-10.json`).

This is a bounded observation, not proof of Ethereum consensus, header hashing,
receipt inclusion, current canonicality or freshness. The short example does not
walk to its sampled head or finalized head. Neither matching source labels nor
these content commitments authenticate a provider; consistently forged evidence
can pass. The wrapper does not establish independent operators, recipient
ownership, invoice provenance, payment deduplication, authorization or contract
support. Use the older paired/time tools for their separate policies; this command
does not claim to incorporate those checks.

## Gathering 11: exact payment precision review

`precision_payment.py` connects Line 4's exact-integer reviewer to Line 3's
historical payment check, Line 2's explicit structural contracts, and the existing
independent domain/type binding. The unchanged integer reviewer is copied into
`vendor/integer_review.py`; `provenance.json` records its source and copy hashes.
Copy this complete folder to use it without any line folder or installed package.
Python 3.10+ and a POSIX no-follow filesystem are sufficient; no network is used.

One command from the repository root:

```sh
python3 -B shared/payment-evidence/precision_payment.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json shared/payment-evidence/example.typed-data.json --chain-id 1 --name 'Read-only Payment Evidence' --version 1 --primary-type PaymentEvidence --no-verifier --expect-digest 0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c
```

Tried: exit **0**, `exact_payment_review_matches`. The historical real Ethereum
ZTO evidence passes payment policy, client commitment, domain/type and expected
digest checks. The amount `166357571280020680094504` stays an exact decimal string.
A hypothetical binary64 conversion loses **1,979,176 raw units**. Acceptance does
not suppress that warning: the per-field report retains exact decimal values,
32-byte words, input forms, safe-integer status and hypothetical conversion deltas.
All potentially large output integers are strings, so the report preserves them
when parsed by a JavaScript JSON consumer.

Replace the client path with
`shared/payment-evidence/example.precision-numeric.json` to see exit **1**,
`unsafe_integer_literal_in_client`, despite an identical digest and passing
payment/domain checks. That fixture changes only the representation of the saved
amount into a JSON integer literal. It is a representation experiment, not new
chain evidence. The tool neither rounds nor repairs either file. Saved results:
`example.precision-payment.json` and `example.precision-rejection.json`.

For real use, supply the actual captured client typed data, independently chosen
payment policy, exact expected domain and primary type, and an independently
retained digest. This demo digest belongs to this shared transcript; the Line 4
standalone fixture commits to a different transcript and has a different digest.
Do not substitute one for the other or derive fresh approval from an incoming
file. `--no-verifier` explicitly requires absence; alternatively use `--verifier`
and optional `--salt` for independent expectations. The current PaymentEvidence
content schema has no verifier. No contract support or token permit is implied.

Exit **0** means all inherited binding gates pass and no reachable integer literal
exceeds the JavaScript safe-integer interval. Exit **1** means a gate differs or
an unsafe literal requires review. Exit **2** means invalid/refused input or an
output bound; only a small failure object is emitted. Exact strings can still lose
precision if later converted to Number. A match is never signing/payment approval.
The review does not authenticate providers, prove Ethereum state or consensus,
establish current settlement, enforce freshness or independently validate crypto.
Use the separate freshness, paired-provider and ancestry tools for their checks.

Inputs retain the inherited strict UTF-8/JSON parser, duplicate/float/nonfinite
rejection, 65,536-byte regular-file limit, no-follow workspace reader, tree and
encoding bounds. The complete ASCII report is capped at 100,000 bytes; no partial
success is emitted. Trusted sibling code and contracts are required. These bounds
are not a CPU-time guarantee. No environment, secret, key or wallet is read; no
request is dispatched, signed, posted, paid or deployed.

```sh
python3 -B shared/payment-evidence/test_precision_payment.py
```

All **16 integration tests** pass here and in a detached copy without line folders.
They cover exact real ZTO replay, equal-digest numeric rejection, one-unit/rounded
amount changes, independent digest/domain/type/verifier checks, payment shortfall,
policy substitution, hex-string equivalence, immutability, disabled network,
JavaScript-safe report integers, output bounds, strict inputs and CLI outcomes.

## Gathering 12: independent payment byte review

`byte_payment.py` adds Line 4's complete byte-field expectations to the existing
payment and precision gates. It replays historical ZTO evidence against a separate
policy, binds the full client commitment to the independently expected domain,
primary type and digest, rejects unsafe JSON integer literals, and compares every
reachable byte field to separately retained exact type/value expectations.

One command from the repository root, offline with Python's standard library:

```sh
python3 -B shared/payment-evidence/byte_payment.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json shared/payment-evidence/example.typed-data.json --chain-id 1 --name 'Read-only Payment Evidence' --version 1 --primary-type PaymentEvidence --no-verifier --expect-digest 0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c --expect-bytes shared/payment-evidence/example.bytes-expectations.json
```

Tried: exit **0**, `payment_and_byte_review_match`, two matched `bytes32`
fields: transaction hash and transcript hash. `example.byte-payment.json` retains
the result. The bundled expectations reproduce the existing shared fixture;
they demonstrate execution, not independent custody, approval or a fresh payment.
For real review retain your expectations independently before taking the client
request. Incoming data cannot choose a file, fill a missing expectation, lower
policy, or generate a new accepted digest. Every argument is required except
optional domain salt; absence of a verifying contract is explicitly selected.

An expectation is `{"fields": {"/message/transactionHash": {"type": "bytes32",
"value": "the complete independently retained transaction hash"}, ...}}`.
The quoted description is not an executable hash; use the complete real value.
All reachable byte fields must be supplied. Missing/extra paths or wrong bytes
or types reject. Hex case may differ; bytes are never padded or repaired in input.
JSON null is invalid and cannot disable the gate. Values other than bytes remain
covered by the full commitment and precision checks. The transaction hash is an
Ethereum hash; `transcriptHash` is SHA-256 of canonical transcript JSON, **not**
the exact file-byte hash and not an Ethereum proof.

Replacing only `--expect-bytes` with `line-4/tools/bytes-review/zto-bytes.json`
returns exit **1**, despite the shared payment replay passing. That Line 4
example commits to a different historical transcript. This rejection is saved
as `example.byte-payment-rejection.json`; nothing rewrites expectations to agree.

Exit **0** means every gate passed, **1** means a review mismatch, and **2** means
invalid input or exceeded bounds with no partial successful report. Inputs use
the existing strict no-follow reader: regular files beneath cwd, no symlinks,
hidden/traversing paths, duplicate keys, floats or nonfinite numbers, at most
65,536 bytes. The complete ASCII report including newline is capped at 100,000
bytes. POSIX descriptor support is required. Size limits are not a CPU sandbox.

```sh
python3 -B shared/payment-evidence/test_byte_payment.py
```

All **16 integration tests pass**, including source/client substitutions, byte
coverage, null expectations, missing digest, non-byte changes, unsafe integer
forms, independent domain and policy, payment shortfall with a matching request,
case equivalence, immutability, disabled network transport, report bound and CLI
exits. They and the demo also pass in a detached copy without any line folders.
The unchanged byte reviewer and its source SHA-256 are listed in `provenance.json`;
its encoder is byte-identical to the encoder already vendored here.

Copy the whole `payment-evidence` folder for use in another workspace. No package,
installation or network is required. Historical provider assertions remain
unauthenticated, not current settlement, a receipt/state proof, token ownership
or signing/payment authorization. This command does not add freshness, paired
provider or ancestry policy; the existing separate tools retain those functions.
No input is modified and no wallet, key, secret, environment or signing transport
is accessed. ZTO and IMD already serve the evidence; no new coin is needed.

## Gathering 13: complete declaration binding

[Complete payment schema review](SCHEMA.md) adds mandatory independently supplied
schema expectations, including unused declarations that the digest cannot bind.
Its one-command offline demo, trial results and limitations are documented there.
