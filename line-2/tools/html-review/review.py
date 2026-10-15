#!/usr/bin/env python3
"""Render fresh offline JSON contract diagnostics as a self-contained HTML page."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import sys
import types

MAX_OUTPUT_BYTES = 100_000

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module



def dependencies():
    reader = bounded_module()
    path = Path(__file__).absolute().parent.parent / 'source-context' / 'show.py'
    module = types.ModuleType('html_source_context')
    module.__file__ = str(path)
    relative = path.relative_to(Path.cwd()).as_posix()
    exec(compile(reader.read_bytes(relative), str(path), 'exec'), module.__dict__)
    return module


def quoted(value):
    # JSON quoting preserves controls and bidi characters as visible ASCII escapes.
    return html.escape(json.dumps(value, ensure_ascii=True, allow_nan=False), quote=True)


def render(report):
    parts, size = [], 0
    def add(fragment):
        nonlocal size
        size += len(fragment.encode('ascii'))
        if size > MAX_OUTPUT_BYTES:
            raise ValueError('complete HTML exceeds 100,000 bytes; no report emitted')
        parts.append(fragment)
    add('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &apos;none&apos;; '
        'style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; form-action &apos;none&apos;">'
        '<title>JSON structural review</title><style>'
        'body{font:16px system-ui;margin:2em auto;max-width:75em;padding:0 1em;color:#222;background:#fff}'
        'pre,code{white-space:pre-wrap;overflow-wrap:anywhere}article{border-top:2px solid #777;padding:1em 0}'
        'mark{background:#ffde80;color:#111}details{margin:1em 0}dt{font-weight:bold}dd{margin:0 0 1em}'
        '@media print{details{display:block}body{margin:0}}</style></head><body>'
        '<h1>JSON structural review</h1>')
    add('<p><strong>' + ('VALID' if report['valid'] else 'INVALID') + '</strong>: ' +
        str(report['error_count']) + ' structural violations.</p>')
    add('<p>Recomputed from the supplied files. Structural checks do not establish truth, '
        'approval, payment or current chain state. This is a limited contract language, not full JSON Schema.</p><dl>')
    for role in ('document', 'contract'):
        identity = report['sources'][role]
        add('<dt>' + role + '</dt><dd><code>' + quoted(identity['file']) +
            '</code><br>SHA-256 <code>' + quoted(identity['sha256']) + '</code></dd>')
    add('</dl><p>Excerpts are JSON-quoted ASCII. Escapes are display text; line and column '
        'numbers count original Unicode code points. Byte ranges are zero-based and end-exclusive. '
        'Each excerpt is bounded; omitted text is counted explicitly.</p>')
    for index, error in enumerate(report['errors'], 1):
        add('<article><h2>Violation ' + str(index) + '</h2><p>Path <code>' + quoted(error['path']) +
            '</code>; rule <code>' + quoted(error['rule']) + '</code></p><p>' + quoted(error['message']) + '</p>')
        for role in ('document', 'contract'):
            ctx = error[role + '_context']
            span = ctx['span']
            add('<h3>' + role + '</h3><p>' + quoted(ctx['kind']) + ' bytes [' +
                str(span['start']['byte_offset']) + ', ' + str(span['end']['byte_offset']) + ')</p>')
            if 'anchor_path' in ctx:
                add('<p>No token exists for the missing value. Parent object anchor: <code>' +
                    quoted(ctx['anchor_path']) + '</code></p>')
            for row in ctx['excerpts']:
                add('<pre>L' + str(row['line']) + ':C' + str(row['column']) +
                    ' before=' + quoted(row['before']) + ' selected=<mark>' +
                    quoted(row['selected']) + '</mark> after=' + quoted(row['after']) +
                    ' omitted chars=' + str(row['omitted_before_chars']) + '/' +
                    str(row['omitted_after_chars']) + '</pre>')
            if ctx['omitted_lines']:
                add('<p>Omitted interior lines: ' + str(ctx['omitted_lines']) + '</p>')
        # Keep every inherited diagnostic field available for audit without active content.
        add('<details open><summary>Complete diagnostic data</summary><pre>' +
            quoted(error) + '</pre></details></article>')
    add('</body></html>\n')
    return ''.join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract')
    parser.add_argument('document')
    parser.add_argument('--contract-sha256')
    parser.add_argument('--document-sha256')
    args = parser.parse_args(argv)
    try:
        context = dependencies()
        report = context.inspect(*context.dependencies(), args.contract, args.document,
                                 args.contract_sha256, args.document_sha256)
        # Reject oversized inherited diagnostic trees as well as rendered output.
        context.bounded_json(report)
        page = render(report)
        sys.stdout.write(page)
        return 0 if report['valid'] else 1
    except (ValueError, OSError, RecursionError, KeyError, IndexError) as exc:
        # Never leave a partial HTML report on stdout.
        sys.stderr.write(json.dumps({'status': 'input_or_output_error',
                                     'error': str(exc)[:1000]}, ensure_ascii=True) + '\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
