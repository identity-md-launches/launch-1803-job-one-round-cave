"""Read-only final delivery checks; writes only this round's check result."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from image_bytes import read_png


def original(name):
    return subprocess.run(['git', 'show', 'HEAD:'+name], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def main():
    root = Path.cwd()
    wall = root/'artifacts/line-3/wall-v13.png'
    data = wall.read_bytes()
    w,h,_ = read_png(data)
    assert (w,h) == (1254,1254)
    assert (root/'artifacts/line-3/wall.png').read_bytes() == data
    digest = hashlib.sha256(data).hexdigest()
    report = json.loads((root/'line-3/wall-review-33.json').read_text())
    assert report['wallSha256'] == digest
    assert report['allPixelsOutsideAdditionUnchanged']
    assert report['unmetVisualRequirements'] == []
    assert report['reviewStatus'].startswith('Visually inspected')
    records = sorted((root/'dist/line-3').glob('*.json'))
    assert len(records) == 33
    for index in range(1,33):
        path = f'dist/line-3/{index:02}.json'
        assert (root/path).read_bytes() == original(path)
    assert (root/'line-3/GOAL.md').read_bytes() == original('line-3/GOAL.md')
    record = json.loads((root/'dist/line-3/33.json').read_text())
    assert set(record) == {'name','image','attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/'+digest
    expected = [('Cave','Water'),('Wall','Line 3'),('Number',33),
                ('Left behind','settlement-batch'),
                ('Meaning','Pepe gathers separate stones and checks each before trusting the whole.'),
                ('One thing','verify Ethereum transaction settlement')]
    assert record['attributes'] == [dict(trait_type=k,value=v) for k,v in expected]
    assert type(record['attributes'][2]['value']) is int
    preview = (root/'dist/line-3/33.jpg').read_bytes()
    assert preview[:2] == b'\xff\xd8' and preview[-2:] == b'\xff\xd9'
    assert len(preview) <= 100000
    marker = preview.index(b'\xff\xc0')
    assert struct.unpack('>HH', preview[marker+5:marker+9]) == (512,512)
    assert hashlib.sha256((root/'line-3/tools/tx-position/live-evidence.json').read_bytes()).hexdigest() == \
        'b8b7c0ec53f30624c96ce598d0911d803941945332627c3bbfea0739f1ae9ae5'
    changed = subprocess.run(['git','diff','--name-only'], check=True, capture_output=True,text=True).stdout.splitlines()
    assert changed == ['line-3/USED.md'], changed
    new = subprocess.run(['git','ls-files','--others','--exclude-standard'],check=True,
                         capture_output=True,text=True).stdout.splitlines()
    for name in new:
        assert name.startswith(('line-3/','dist/line-3/','artifacts/line-3/','test/scratch/')), name
        if not name.startswith(('artifacts/','test/scratch/')):
            assert Path(name).stat().st_size <= 100000, name
    for name in ('artifacts/line-3/wall.png','artifacts/line-3/wall-v13.png'):
        assert subprocess.run(['git','ls-files','--',name],check=True,capture_output=True).stdout == b''
    result={'passed':True,'wallFormat':'PNG','wallDimensions':[w,h], 'wallSha256':digest,
            'previewFormat':'JPEG','previewDimensions':[512,512],'previewBytes':len(preview),
            'priorRecordsUnchanged':32,'goalUnchanged':True,'newRecord':33,
            'onlyAuthorizedPathsChanged':True,'newNonArtifactFilesUnder100KB':True,
            'requiredOutputsUntracked':True,'unmetVisualRequirements':[]}
    (root/'line-3/delivery-check-33.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
