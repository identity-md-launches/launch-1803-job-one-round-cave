#!/usr/bin/env python3
"""Check complete schema integration, detached use and deliberate rejections."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'shared/payment-evidence/'
DEMO = [BASE+'schema_payment.py',BASE+'example.transcript.json',BASE+'example.policy.json',
        BASE+'example.typed-data.json','--chain-id','1','--name','Read-only Payment Evidence',
        '--version','1','--primary-type','PaymentEvidence','--no-verifier','--expect-digest',
        '0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c',
        '--expect-bytes',BASE+'example.bytes-expectations.json',
        '--expect-schema',BASE+'example.schema-expectations.json']


def main():
    assert Path.cwd() == ROOT
    scratch = ROOT/'test/scratch/round13'
    scratch.mkdir(parents=True,exist_ok=True)
    detached = scratch/'portable'
    shutil.copytree(ROOT/BASE,detached/BASE,dirs_exist_ok=True)
    client = json.loads((ROOT/BASE/'example.typed-data.json').read_text())
    client['types']['UnreferencedNote'] = [{'name':'note','type':'string'}]
    modified = scratch/'unused.json'
    modified.write_text(json.dumps(client)+'\n')
    reject = list(DEMO); reject[3] = str(modified.relative_to(ROOT))
    cases = [
        (ROOT,0,[BASE+'test_schema_payment.py'],None),
        (ROOT,0,DEMO,BASE+'example.schema-payment.json'),
        (ROOT,1,reject,BASE+'example.schema-rejection.json'),
        (detached,0,[BASE+'test_schema_payment.py'],None),
        (detached,0,DEMO,None),
        (ROOT,1,['line-2/tools/html-review/review.py','line-2/tools/json-contract/report.contract.json',
                 'line-2/tools/rule-locator/report.invalid.json'],'gathering/invalid-review-13.html'),
        (ROOT,1,['line-4/tools/schema-review/schema_review.py','line-4/tools/schema-review/zto-unused-declaration.json',
                 '--schema-expect','line-4/tools/schema-review/zto-schema.json','--digest-expect',
                 '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'],None),
        (ROOT,0,['line-1/tools/two-source-zto/agreement.py','--verify','gathering/live-agreement-13.json'],None),
        (ROOT,0,['line-3/tools/settlement-batch/batch.py','--manifest','line-3/tools/settlement-batch/demo-manifest.json'],None),
    ]
    rows=[]
    for cwd,expected,args,save in cases:
        done=subprocess.run([sys.executable,'-B',*args],cwd=cwd,capture_output=True,text=True,
                            timeout=45,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'})
        row=dict(command=['python3','-B',*args],detached=cwd!=ROOT,expectedExit=expected,
                 exitCode=done.returncode,passed=done.returncode==expected,
                 stdout=done.stdout,stderr=done.stderr)
        rows.append(row)
        if save and row['passed']:
            assert len(done.stdout.encode())<=100000
            (ROOT/save).write_text(done.stdout)
        print('PASS' if row['passed'] else 'FAIL',args[0],done.returncode)
    encoded=json.dumps(rows,indent=2)+'\n'
    assert len(encoded.encode())<=100000
    (ROOT/'gathering/round-checks-13.json').write_text(encoded)
    return 0 if all(r['passed'] for r in rows) else 1


if __name__=='__main__':
    raise SystemExit(main())
