"""Composite the generated, isolated pigment mark onto vacant ancestral rock."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

ROOT = Path(__file__).resolve().parent.parent
ANCESTOR = '77291465c7b6226281f261796741e13fe87b99f44f1d8fae8f2f8aafdb4c7560'
PROMPT = ('A small isolated prehistoric cave pigment mark on pure white background, for later transfer to rough stone: '
          'three distinct irregular small ochre pebbles held together by a single shallow charcoal crescent underneath, '
          'widely spaced so every pebble is separate. Sparse hand-drawn burnt-stick strokes and rough thumb daubs, '
          'flat worn Lascaux mineral pigments, yellow ochre and charcoal only. The whole mark centered with generous '
          'empty white margins. No text, letters, numerals, tally marks, signatures, logos, watermarks, borders, '
          'hands, handprints, people, frogs, photographs or 3D rendering.')


def main():
    wall = ROOT / 'artifacts/line-3/wall.png'
    target = ROOT / 'artifacts/line-3/wall-v13.png'
    ancestor = wall.read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == ANCESTOR
    w, h, old = read_png(ancestor)
    draft = target.read_bytes()
    gw, gh, generated = read_png(draft)
    assert (w, h) == (1254, 1254) and gw == gh

    def pigment(x, y):
        r, g, b = generated[(y*gw+x)*3:(y*gw+x)*3+3]
        return max(r, g, b) < 185 or (r > g*1.12 and g > 85 and b < g*.8)

    points = [(x,y) for y in range(gh) for x in range(gw) if pigment(x,y)]
    sx0, sy0 = min(x for x,y in points), min(y for x,y in points)
    sx1, sy1 = max(x for x,y in points)+1, max(y for x,y in points)+1
    # Vacant rock between the sun and guarded pebble, above the ancestral diagonal mark.
    x0, y0, width, height = 750, 240, 90, 90
    final = bytearray(old)
    changed = 0
    for dy in range(height):
        for dx in range(width):
            x, y = x0+dx, y0+dy
            i = (y*w+x)*3
            rock = old[i:i+3]
            if max(rock) < 85:
                continue
            xa = sx0+dx*(sx1-sx0)//width
            xb = sx0+(dx+1)*(sx1-sx0)//width
            ya = sy0+dy*(sy1-sy0)//height
            yb = sy0+(dy+1)*(sy1-sy0)//height
            total = [0,0,0]
            coverage = 0
            for gy in range(ya,yb):
                for gx in range(xa,xb):
                    if not pigment(gx,gy):
                        continue
                    r,g,b = generated[(gy*gw+gx)*3:(gy*gw+gx)*3+3]
                    chosen = ((183,124,41) if r > g*1.12 and g > 85 and b < g*.8 else (53,42,31))
                    for c in range(3):
                        total[c] += chosen[c]
                    coverage += 1
            if not coverage:
                continue
            alpha = .83*coverage/((xb-xa)*(yb-ya))
            light = min(1.16,max(.64,sum(rock)/(3*139)))
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha)+total[c]/coverage*light*alpha)
            changed += final[i:i+3] != rock
    assert changed > 500
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if not (x0 <= x < x0+width and y0 <= y < y0+height) or max(old[i:i+3]) < 85:
                assert final[i:i+3] == old[i:i+3]
    encoded = png(w,h,final)
    target.write_bytes(encoded)
    wall.write_bytes(encoded)
    thumbnail = resize(w,h,final)
    quality = 52
    preview = jpeg(512,512,thumbnail,quality)
    while len(preview) > 100000 and quality > 10:
        quality -= 5
        preview = jpeg(512,512,thumbnail,quality)
    assert len(preview) <= 100000
    (ROOT/'dist/line-3/33.jpg').write_bytes(preview)
    review = {'ancestorSha256': ANCESTOR, 'ancestorDimensions':[w,h],
              'wallDimensions':[w,h], 'wallFormat':'PNG', 'wallMode':'RGB',
              'wallSha256':hashlib.sha256(encoded).hexdigest(),
              'generatedDraftSha256':hashlib.sha256(draft).hexdigest(),
              'draftRetained':False, 'additionRectangle':[x0,y0,width,height],
              'changedPixels':changed, 'unchangedPixels':w*h-changed,
              'allPixelsOutsideAdditionUnchanged':True, 'deepCracksProtected':True,
              'previewDimensions':[512,512], 'previewFormat':'JPEG',
              'previewBytes':len(preview), 'previewQuality':quality,
              'imageTool':'mcp__image__generate_image', 'prompt':PROMPT,
              'reviewStatus':'requires visual inspection', 'unmetVisualRequirements':[]}
    (ROOT/'line-3/wall-review-33.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
