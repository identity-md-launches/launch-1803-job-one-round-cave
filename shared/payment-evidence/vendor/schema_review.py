#!/usr/bin/env python3
"""Inspect EIP-712 declarations, including types behind empty arrays, offline."""
import argparse
import json
import sys

from typed_digest import (ARRAY, Encoder, TypedDataError, base_type, digest,
                          keccak256, load_workspace_json, parse_hex, validate_tree)

MAX_REPORT_BYTES = 100_000
_UNSET = object()


def render(report):
    text = json.dumps(report, ensure_ascii=True, indent=2) + '\n'
    if len(text.encode('ascii')) > MAX_REPORT_BYTES:
        raise TypedDataError('schema review exceeds 100000-byte output limit')
    return text


def schema_expectations(policy):
    validate_tree(policy)
    if not isinstance(policy, dict) or set(policy) != {'primaryType', 'types'}:
        raise TypedDataError('schema expectations need exactly primaryType and types')
    encoder = Encoder(policy['types'])
    primary = policy['primaryType']
    if not isinstance(primary, str) or primary == 'EIP712Domain' or primary not in encoder.types:
        raise TypedDataError('expected primaryType must name a message struct')
    return {'primaryType': primary, 'types': encoder.types}


def review(data, policy=_UNSET, expected_digest=None):
    hashes = digest(data)  # Validate the complete request, including unused declarations.
    wanted = schema_expectations(policy) if policy is not _UNSET else None
    expected = parse_hex(expected_digest, 32) if expected_digest is not None else None
    encoder = Encoder(data['types'])
    types = encoder.types
    edges = {name: sorted({base_type(f['type']) for f in fields
                           if base_type(f['type']) in types})
             for name, fields in types.items()}

    def closure(root):
        found, pending = set(), [root]
        while pending:
            name = pending.pop()
            if name not in found:
                found.add(name)
                pending.extend(edges[name])
        return found

    domain_types = closure('EIP712Domain')
    message_types = closure(data['primaryType'])
    bound = domain_types | message_types
    instances = dict.fromkeys(types, 0)
    empty_arrays = []

    def visit(kind, value, path):
        array = ARRAY.fullmatch(kind)
        if array:
            if not value:
                empty_arrays.append({'path': path, 'declaredType': kind,
                                     'baseType': base_type(kind)})
                render({'emptyArrays': empty_arrays})
            for index, child in enumerate(value):
                visit(array.group(1), child, path + '/' + str(index))
        elif kind in types:
            instances[kind] += 1
            for field in types[kind]:
                visit(field['type'], value[field['name']], path + '/' + field['name'])

    visit('EIP712Domain', data['domain'], '/domain')
    visit(data['primaryType'], data['message'], '/message')
    declarations = []
    for name in sorted(types):
        encoding = encoder.type_encoding(name)
        declarations.append({
            'name': name, 'fields': types[name], 'directDependencies': edges[name],
            'encodeType': encoding, 'typeHash': '0x' + keccak256(encoding.encode('ascii')).hex(),
            'boundByDomainTypeHash': name in domain_types,
            'boundByMessageTypeHash': name in message_types,
            'valueInstanceCount': instances[name],
        })
        render({'declarations': declarations, 'emptyArrays': empty_arrays})
    report = {
        'reviewVersion': 1, **hashes, 'declarations': declarations,
        'unusedTypes': sorted(set(types) - bound),
        'reachableTypesWithoutValues': sorted(n for n in bound if not instances[n]),
        'emptyArrays': empty_arrays,
        'schemaExpectationProvided': wanted is not None,
        'digestExpectationProvided': expected is not None,
        'interpretation': 'Schema comparison includes every declaration, including unused types, '
                          'and preserves field order. Empty arrays still bind their declared types. '
                          'Unused declarations do not affect the EIP-712 digest. Schema agreement '
                          'does not compare values; a separately retained digest binds the encoded '
                          'domain and message. No match establishes signing approval or contract support.',
    }
    if wanted is not None:
        actual_names, wanted_names = set(types), set(wanted['types'])
        changed = [{'name': name, 'expectedFields': wanted['types'][name], 'actualFields': types[name]}
                   for name in sorted(actual_names & wanted_names)
                   if types[name] != wanted['types'][name]]
        unpinned = sorted(actual_names - wanted_names)
        absent = sorted(wanted_names - actual_names)
        primary_matches = data['primaryType'] == wanted['primaryType']
        report.update(expectedPrimaryType=wanted['primaryType'], primaryTypeMatches=primary_matches,
                      unpinnedTypes=unpinned, absentTypes=absent, changedDeclarations=changed,
                      schemaMatchesExpected=primary_matches and not unpinned and not absent and not changed)
    if expected is not None:
        report['digestMatchesExpected'] = expected.hex() == hashes['digest'][2:]
    report['checksPass'] = (None if wanted is None and expected is None else
                            report.get('schemaMatchesExpected', True) and
                            report.get('digestMatchesExpected', True))
    render(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='typed-data JSON beneath cwd')
    parser.add_argument('--schema-expect', help='separately prepared complete schema JSON beneath cwd')
    parser.add_argument('--digest-expect', help='separately retained complete 32-byte digest')
    args = parser.parse_args(argv)
    try:
        data = load_workspace_json(args.input)
        policy = load_workspace_json(args.schema_expect) if args.schema_expect is not None else _UNSET
        report = review(data, policy, args.digest_expect)
        print(render(report), end='')
        return 1 if report['checksPass'] is False else 0
    except (ValueError, OSError, RecursionError) as exc:
        print('schema-review: ' + json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
