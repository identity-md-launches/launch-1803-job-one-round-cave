# Settlement batch review

Review a queue of 1–32 Ethereum transactions against separately retained exact
evidence hashes and independently chosen settlement policies. The whole batch
passes only when every entry passes and no sampled block height has conflicting
hashes across entries. Repeated transaction hashes reject before any evidence
file is opened, including case variants or entries with different policies.
This prevents counting a transaction twice **within this batch**.

Python 3.9+ and the standard library suffice on POSIX. From the repository root:

```sh
python3 -B line-3/tools/settlement-batch/batch.py --demo
```

When tried, this returned `batch_settlement_match`, exit 0, with two accepted
real ZTO transactions. The inherited transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`
is at index **181 of 498**, block **26190898**. A new read-only Publicnode
observation of transaction
`0x64847acc0a0d6b0a5cf61cfb26fea3ccfae61a75916ff9d01453a6c7a17b47d7`
is at index **146 of 241**, block **26194715**, with **132 confirmations**
and inclusion below the sampled finalized head. Both require 12 confirmations
and finality. Results are in `demo-result.json`; the new original provider
transcript is `second-evidence.json`, with its capture result in `live-check.json`.
The offline demo needs no network, packages, installation, account or secrets.

The second transaction was discovered with the inherited bounded
`latest_zto_transfer(RPC(RPC_URL), 2048)` ZTO Transfer filter and collected with
`tx-position.collect(policy(tx, 12, True))`. Only public read methods were used,
with the inherited explicit User-Agent and disabled proxy/redirect discovery.
The discovery filter result is not part of the retained position transcript;
the batch verifies settlement and position, **not token movement or payment**.
The observations become historical as soon as they are saved.

For your own queue, independently review a plan with exactly the structure in
`demo-manifest.json`, and run:

```sh
python3 -B line-3/tools/settlement-batch/batch.py --manifest line-3/tools/settlement-batch/demo-manifest.json
```

Each item has exactly `evidence` (a workspace-relative path), `sha256` (an
independently retained lowercase SHA-256 of exact evidence file bytes), and
`policy` (exactly `transactionHash`, integer `minimumConfirmations`, boolean
`requireFinalized`). The envelope is exactly `version: 1` and `items`.
Use your independently chosen transaction hashes and policies. Keep the plan
and expected hashes separately from incoming evidence. Replacing both evidence
and expectations defeats replacement detection. The bundled pins illustrate
retention, not independent custody or approval. The report's `manifestSha256`
identifies the exact plan bytes; it does not authenticate the plan's author.

Every pin is checked before parsing that evidence; matching bytes still need
successful strict replay. Semantic checks include mainnet, successful execution,
canonical block anchors, confirmations, finality and transaction position.
The full plan is validated before opening evidence. Malformed or unreadable
evidence yields an error row while later entries are still examined. Reports
retain input order, include compact per-entry outcomes and expose conflicting
block heights. `acceptedCount` counts individual passing rows; **only the top
level `accepted` decides the batch**, since two passing rows can conflict.
No persistent ledger or external action follows a decision.

Exit **0** means the whole batch passes; **1** means valid evidence was declined
or block anchors conflict; **2** means invalid input, unavailable evidence, or
an invalid row. No partial batch acceptance is issued. All files are read only;
the CLI writes only JSON to stdout. Each manifest/evidence file is bounded to
90,000 bytes; reports are bounded to 100,000 ASCII bytes. Safe descriptor-relative
opens refuse symlinks at all components, hidden/absolute/traversal paths, FIFOs
and directories. Strict JSON rejects duplicate keys and nonfinite values.

Run the tests:

```sh
python3 -B -m unittest discover -s line-3/tools/settlement-batch -p 'test_*.py' -v
```

All **21 tests** passed, plus **35 inherited pinned-position/tx-position tests**.
Checks cover real two-transaction replay, duplicate aliases, prevalidation before
reads, mixed outcomes, changed positions despite updated pins, policy mismatch,
strict JSON, shared-height conflicts, file boundaries and network-free replay.
Test mutations live only in memory or `test/scratch/`; they are not published as
chain observations. Source evidence remains unchanged. Compact test results are
in `../../check-results-33.json`.

Reuse requires unchanged sibling `pinned-position`, `tx-position`,
`payment-witness` and `settlement-check` modules and the inherited
`tx-position/live-evidence.json`. All are ordinary repository files.

This is historical provider evidence, not a consensus or transaction-trie proof.
Different-height anchors are not connected by an ancestry proof; different
entries may sample different heads. No current freshness, independent provider
agreement, recipient/amount authorization, or protection against later reorgs
is added. Deduplication is scoped to this manifest, not other batches or prior
payments. Nothing reads a wallet, key or environment variable, signs, sends a
transaction, pays, posts to an application, or deploys a contract.
