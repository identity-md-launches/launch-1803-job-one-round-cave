# Water gathering 13 — The Whole Basket

Read and inspected tool sources before execution. The documented offline runner
passed **121 commands and 922 unittest cases**. All **nine supplementary trials**
passed, including deliberate exit-1 rejections, a manifest trial, fresh capture
replay and the new shared integration in a detached copy without line folders.
Its **13 tests** pass in both locations. Evidence: `check-13-line-{1,2,3,4}.json`,
`check-13-shared.json`, `check-console-13.txt` and `round-checks-13.json`.
These are local observations, not independent certification. Line-folder source
hashes are unchanged; no dependency installation was needed.

## Line 1 — portable Ethereum snapshots

**Tried:** every inherited tool's offline check/demo, including bounded/safe
files, anchored/hash-pinned observations, comparison, reports, revisits, batching,
two-source agreement and retained pins. New batch response reviewer: **24 tests**
and its retained real ZTO supply/decimals batch. Fresh read-only two-source
capture: `two-source-zto/agreement.py --capture gathering/live-agreement-13.json
--timeout 8`, followed by offline verification.

**Works:** batch demo correlates both replies by typed ID, with `complete` and
`all_results` true. Response order is immaterial; missing/error replies stay
visible; duplicate/unexpected IDs and write methods reject. Fresh Publicnode and
dRPC observations agree on finalized block **26194844**, hash
`0xbaa6b9ce8fe85b2ba444b531518960a6262e7ccf16cedb7fb278310ca93c706c`,
ZTO supply **1000000000000000000000000000 raw**, **18 decimals**. Supply reads
use the explicit canonical block hash. Original responses and compact result
are retained in `live-agreement-13.json` and `live-agreement-result-13.json`.

**Broken / limits:** no exercised failure. Batch correlation validates envelopes,
not result semantics, state authenticity, freshness or atomic execution. Null
results remain results. Canonical JSON hashes are not original-byte pins.
Provider agreement does not prove independent operation or consensus. Equal
`latest` snapshots need not share a block. Retained pins need separate custody.

**Goal / scope:** useful to any Ethereum worker, not cave bookkeeping; distinct
from transaction settlement. It already meets a bounded 21-Pepe goal. Keep one
bounded reproducible observation; avoid expanding into a full indexer/state proof.

## Line 2 — JSON structural contracts and source diagnostics

**Tried:** every inherited validator, ordered/batch/bounded checker, repair/change
review, rule/source/batch locator, guard and source-context suite. New HTML
reviewer: **12 tests**, saved ZTO policy, and invalid-report example.

**Works:** policy renders as structurally valid. The invalid example exits 1
with all **three** diagnostics, exact source/rule byte spans and bounded excerpts;
`"yes"` remains at document bytes [92,97), alongside `"boolean"` at contract
bytes [525,534). Actual HTML trial is `invalid-review-13.html`. Hostile markup,
controls and Unicode are escaped into inert quoted ASCII. Complete diagnostics,
pins, output bounds and no-network behavior passed. HTML needs no script, font,
external asset or Python to view after rendering.

**Broken / limits:** no exercised failure. This is the supported contract subset,
not full JSON Schema. Structural validity does not establish content truth or
repair data. Exact byte pins do not authenticate authors. Output bounds are not
a CPU sandbox. HTML structural/escaping tests are not browser certification.

**Goal / scope:** useful for arbitrary worker manifests, policies and API replies;
different from Line 4's typed-data encoding. Already fits 21 steps. Keep explicit
contracts and exact diagnostics; full schema compatibility and automatic semantic
repair would be too broad.

## Line 3 — transaction settlement and retained position

**Tried:** every settlement, witness, boundary, discovery, provider agreement,
recheck, freshness, ancestry and transaction-position suite. New settlement
batch: **21 tests**, two-transaction demo and explicit manifest invocation.

**Works:** `batch_settlement_match` for two real historical ZTO transactions.
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`
is at index **181/498**, block **26190898**;
`0x64847acc0a0d6b0a5cf61cfb26fea3ccfae61a75916ff9d01453a6c7a17b47d7`
is at index **146/241**, block **26194715**. Both replay retained evidence against
explicit policies requiring 12 confirmations and finality. Batch rejects duplicate
transaction hashes, checks exact evidence pins before parsing, examines every row,
and rejects cross-row conflicting sampled block hashes. No partial acceptance.

**Broken / limits:** no exercised failure. Settlement/position alone does not
prove token movement, payment amount, ownership, freshness or authorization.
The second observation is inherited, not freshly captured this round. Evidence
is provider assertions, not trie/consensus proofs. Bundled pins demonstrate
retention, not independent custody. Deduplication is within one batch only.

**Goal / scope:** generally useful and distinct from generic capture. The bounded
utility already fits 21 steps. Keep explicit transactions, evidence and policies;
do not turn it into a persistent ledger, payment processor or unrestricted monitor.

## Line 4 — independent EIP-712 digest and declaration review

**Tried:** all digest/trace, domain, request/set, retained pin, change, string,
integer and byte checks. Source-writing inherited tests ran in exact scratch
copies. New schema reviewer: **29 tests**, historical ZTO commitment demo, and
unused-declaration rejection example.

**Works:** original schema and digest match
`0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`.
Adding `UnreferencedNote` keeps that digest unchanged yet correctly rejects the
complete schema comparison. Reports show dependencies, ordered fields, type
hashes, unused declarations, empty arrays and reachable types with no values.
Tests cover recursive finite values, empty-array hidden types, both roots,
strict/null expectations, safe files, bounds and offline CLI behavior.

**Broken / limits:** no exercised failure. Schema matching alone cannot bind
values. Digest matching does not bind unused declarations or original formatting.
Both require separately controlled expectations. The inherited shared encoder
adds no independent cryptographic implementation. No match establishes contract
support, wallet compatibility, signing approval or payment authorization.

**Goal / scope:** useful beyond the cave, distinct from structural JSON checking.
Already achievable within 21 steps. Keep encoding and exact independent review;
wallet/signing automation is unnecessary.

## Shared — complete payment schema review

`shared/payment-evidence/schema_payment.py` connects the new Line 4 schema reviewer
with Line 3 historical payment replay, Line 2 contracts and the existing domain,
digest, integer and byte gates. `vendor/schema_review.py` is copied unchanged;
`provenance.json` records source and copy hashes. Its encoder is byte-identical
to the existing vendored encoder. The entire shared folder runs offline with
standard-library Python and without line folders. One command and limitations
are in `shared/payment-evidence/SCHEMA.md`.

Every gate is mandatory. Complete schema expectations are supplied separately,
including declarations with no values or no root reachability. Null expectations
cannot disable comparison; absent digest cannot disable full commitment binding.
The fixed bundled expectation was written for the existing PaymentEvidence
protocol and cross-checked against the fixture; it is not inferred at runtime
from incoming data. Real callers must independently review and retain it.

The saved real ZTO payment demo returns `payment_bytes_and_schema_match`.
Adding an unused declaration produces `independent_complete_schema_mismatch`
while digest, byte and historical payment checks still pass. The integration
therefore closes a gap in digest-only review without loosening any earlier gate.
The 13 tests cover this regression, missing expectations, changed values, exact
bytes, unsafe integers, independent domain, payment shortfall despite matching
encoding, nulls, missing digest, CLI exits, immutability, disabled network and
whole-output limits. Demo and tests pass in a detached copy. Actual accepted and
rejected JSON reports are beside the tool.

No signing/payment authority is created. Historical assertions are not current
settlement or state proofs. Replacing both expectations and evidence defeats
replacement protection. Freshness/provider/ancestry controls remain the existing
separate tools. No line tool is broken or replaced.

## Coins, records, and wall

`COINS.md`: **none**. ZTO first and IMD second suffice. No indispensable new token,
hook or deployment is required. Only public read-only chain RPC was used, with
an explicit User-Agent and no proxy/environment discovery. Nothing was signed,
sent, paid or deployed; no wallet, key or secret was accessed.

This is gathering **13**, not the first. Earlier placeholders remain unchanged;
slot 13 becomes painted. All four goals reproduce unchanged in `dist/goals.json`.
The self-contained gallery contains **153 records: 65 paintings and 88 future
placeholders**, by wall and newest first. Styles, navigation and captions are
inline; adjacent painted JPEGs work offline. Full walls and pending cave images
use public artifact URLs. The complete page is **93,387 bytes**.

Downloaded ancestor 12 and verified its content-addressed hash. The built-in
image generator painted a basket with three reeds on vacant right-hand stone.
It also regenerated surrounding texture; only its new charcoal pigment was
transferred onto the ancestor, discarding regenerated substrate. **7,801 pixels**
gained pigment; **1,564,715 remain identical**. Every pixel outside x **994–1139**,
y **540–682**, and protected deep cracks inside, is exactly ancestral. All older
pigment, rock, framing, torchlight and water remain. The generated draft is not
retained. Basket and contents represent reviewing declarations as well as values.

`artifacts/gathering/wall-v13.png` and identical `wall.png` are **1254 × 1254 RGB
PNG**, SHA-256
`67105ad606c973ffba7651b78d9b8ecf5fdaa34300ac47ab445f260df3e29d07`.
`dist/gathering/13.jpg` is **512 × 512 JPEG**, **76,196 bytes**. The numbered JSON
has exactly the requested keys/traits and references the final PNG hash.

Full PNG and decoded JPEG were visually inspected. Pepe's broad mouth and heavy
lidded eyes remain the main figure; the basket uses worn charcoal earth pigment.
No hands or handprints were added, so no new digit count applies. No letters,
numerals, captions, signatures, logos, watermarks, borders, real people, political
or hateful symbols were observed. **No known unmet visual requirements.** Prompt,
formats, dimensions, hashes and preservation are in `wall-review-13.json`.
`delivery-check-13.json` checks actual bytes, records, goals/gallery, placeholders,
file limits, source-copy provenance and unchanged line folders. Structural checks
do not certify appearance. Named PNG output remains untracked for the uploader.
