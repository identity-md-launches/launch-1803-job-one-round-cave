# Offline HTML JSON review

Turn a JSON contract check into a portable, self-contained browser report. A worker
can send the HTML file to a reviewer who has no Python installation or network.
The page contains every violation, exact document/rule byte ranges, bounded source
excerpts, complete diagnostic details and both captured file hashes.

Run from the repository root:

```sh
python3 -B line-2/tools/html-review/review.py shared/payment-evidence/policy.contract.json shared/payment-evidence/example.policy.json > line-2/tools/html-review/policy-review.html
```

Open `policy-review.html` in a browser. Tried locally: exit **0**, zero structural
violations in the swarm's saved ZTO-first, IMD-second payment policy. This is a
saved policy structure, not a fresh chain observation or approval of that policy.
The delivered HTML is the actual result of this command and works offline.

To see rejection, use the inherited build-report example:

```sh
python3 -B line-2/tools/html-review/review.py line-2/tools/json-contract/report.contract.json line-2/tools/rule-locator/report.invalid.json > line-2/tools/html-review/invalid-review.html
```

Tried locally: exit **1**, three violations; `"yes"` at document bytes [92,97)
corresponds to `"boolean"` at contract bytes [525,534). The fixture illustrates
rejection, not a real failed build. Missing values explicitly use a parent-object
anchor. Null values retain their own ranges. Excerpt omissions remain explicit.
The complete diagnostic details are expanded by default, including when printing.

## Behavior and limits

Exit 0: structurally valid. Exit 1: complete report with violations. Exit 2:
invalid/unreadable input, invalid contract, pin mismatch or output overflow; no
HTML is emitted, and a bounded JSON error goes to stderr. Build the complete
page before emitting it, so rejected output is never a partial report.

Optional `--contract-sha256 HASH` and `--document-sha256 HASH` compare separately
retained lowercase SHA-256 hashes to the exact captured bytes before validation.
Matching hashes identify bytes, not trusted authorship, approval or freshness.

All untrusted text is JSON-quoted into ASCII, then HTML-escaped. Terminal controls,
bidi characters, lone escaped surrogates and non-ASCII characters remain visible
escapes. Incoming text never becomes tags, URLs, attributes, CSS or scripts.
The static page has no scripts, external assets, links, fonts or network reads.
A restrictive content security policy supplies an additional browser boundary.

Only explicit relative workspace regular files are read, each at most 1,000,000
bytes, using inherited POSIX no-follow traversal. Absolute, hidden, parent,
symlink and special-file paths reject. Each distinct input is captured once.
Both the inherited JSON diagnostic tree and finished ASCII HTML must fit
100,000 bytes. No error is silently omitted to fit; HTML escaping and complete
diagnostic details can make a page exceed the bound even when text output fits.

Python 3.10+ and its standard library suffice. Keep the unchanged sibling
`source-context`, `source-locator`, `rule-locator`, `bounded-contract` and
`json-contract` folders. No runtime installation or network is needed. The tool
writes only stdout/stderr and leaves the caller to choose a destination.

This uses the inherited limited contract language, **not full JSON Schema**.
Inherited regex and uniqueness costs remain; size bounds are not a CPU sandbox.
A report checks structure and helps human review; it does not repair data or
establish content truth. No coin, wallet, signing or payment is required.

## Checks

```sh
python3 -B line-2/tools/html-review/test_review.py
```

All **12 tests passed**: complete diagnostic retention, exact byte ranges, hostile
markup in paths/messages/excerpts, controls/Unicode/bidi, immutability, missing
anchors, whole-output bounds, CLI exits, pin mismatch, malformed/duplicate input,
path refusal and the actual saved policy with network disabled. These are local
observations, not independent certification or a visual browser certification.
