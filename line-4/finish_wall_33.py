"""One-time preservation of image-tool pigment; refuses any other input pair."""
import hashlib
import json
from pathlib import Path
from image_bytes import jpeg, png, read_png, resize


def main():
    folder = Path('artifacts/line-4')
    ancestor = (folder/'wall.png').read_bytes()
    generated = (folder/'wall-v13.png').read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == 'e3dcf90f0eee30956ddbe51344ead52659564eeea0e9e6c9865089ec62d66387'
    assert hashlib.sha256(generated).hexdigest() == 'fee52134b1eac7918a2cc1cf5145bf1b25405dee28a28036636e54592281d66a'
    w, h, old = read_png(ancestor)
    gw, gh, draft = read_png(generated)
    assert (w, h, gw, gh) == (1254, 1254, 1254, 1254)
    final = bytearray(old)
    changed = 0
    for y in range(309, 375):
        for x in range(1030, 1120):
            i = (y*w+x)*3
            r, g, b = draft[i:i+3]
            original = old[i:i+3]
            if sum(original) < 80:
                continue
            # Keep the two pod interiors hollow and preserve their original rock.
            if any((x-cx)**2+(y-cy)**2 < 9**2 for cx, cy in ((1053,345),(1100,354))):
                continue
            charcoal = r < 95 and g < 67 and b < 47 and r-g < 40 and sum(original)-sum((r,g,b)) > 15
            pod = any(9**2 <= (x-cx)**2+(y-cy)**2 < 19**2
                      for cx, cy in ((1053,345),(1100,354)))
            ochre = pod and r > 1.4*g and r-g > 25
            if charcoal:
                target = [v*.40 for v in original]
            elif ochre:
                target = [v*.25+p*.75 for v, p in zip(original, (r,g,b))]
            else:
                continue
            final[i:i+3] = bytes(round(v*.15+t*.85) for v,t in zip(original,target))
            changed += final[i:i+3] != original
    assert 300 < changed < 4000
    for i in range(0,len(old),3):
        if old[i:i+3] != final[i:i+3]:
            y,x = divmod(i//3,w)
            assert 1030 <= x < 1120 and 309 <= y < 375 and sum(old[i:i+3]) >= 80
    wall = png(w,h,final)
    sha = hashlib.sha256(wall).hexdigest()
    preview = jpeg(512,512,resize(w,h,final),52)
    assert len(preview) < 100_000
    for name in ('wall.png','wall-v13.png'):
        (folder/name).write_bytes(wall)
    Path('dist/line-4/33.jpg').write_bytes(preview)
    review = {
        'wall': {'paths':['artifacts/line-4/wall.png','artifacts/line-4/wall-v13.png'],
                 'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(wall),'sha256':sha},
        'preview': {'path':'dist/line-4/33.jpg','width':512,'height':512,'format':'JPEG',
                    'bytes':len(preview),'sha256':hashlib.sha256(preview).hexdigest()},
        'ancestorSha256':hashlib.sha256(ancestor).hexdigest(),
        'generatedDraftSha256':hashlib.sha256(generated).hexdigest(),
        'imageTool':'Built-in imagegen, generation 01a13d58-72fa-7d61-8551-1820b2b854a7',
        'prompt':'Preserve the inherited square cave and every painting. Add only a tiny charcoal twig ending in two hollow red-ochre seed-pod outlines on vacant upper-right stone, below the old concentric oval and above the old twig. Worn earth pigments, rock visible through pods. No letters, numbers, hands or new figures; preserve Pepe and his original five-digit hands.',
        'changedPixels':changed,'unchangedPixels':w*h-changed,
        'additionBoundsExclusive':[1030,309,1120,375],
        'preservation':'All pixels outside the new vacant-stone pigment, protected deep fissures inside and pod interiors are exact ancestral pixels. Pepe, hands, earlier paintings, water and framing are untouched.',
        'visualReview':'Pending final inspection.','unmetVisualRequirements':[],
        'limitations':['Local inspection is not independent visual certification.',
                       'The small shaded motif is subtle at thumbnail scale.',
                       'The generated full draft changed surrounding texture; only its isolated new pigment was retained.']}
    Path('line-4/wall-review-33.json').write_text(json.dumps(review,indent=2)+'\n')
    record = {'name':'The Empty Pods','image':'https://api.imd.fun/artifacts/'+sha,
              'attributes':[
                  {'trait_type':'Cave','value':'Water'},
                  {'trait_type':'Wall','value':'Line 4'},
                  {'trait_type':'Number','value':33},
                  {'trait_type':'Left behind','value':'offline EIP-712 schema reviewer'},
                  {'trait_type':'Meaning','value':'Pepe checks the shape of each pod even when it holds no seeds.'},
                  {'trait_type':'One thing','value':'offline EIP-712 typed-data digest checking'}]}
    Path('dist/line-4/33.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
