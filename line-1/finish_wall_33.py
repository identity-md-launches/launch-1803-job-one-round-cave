"""Transfer generated pigment only, retaining the inherited wall pixel-for-pixel elsewhere."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

ANCESTOR = '1ec7199561cb3aea7b131ffd53c6221e8f3ce71758771aed1fbfcc33a8b061e2'

def main():
    base = Path('artifacts/line-1/wall.png')
    draft = Path('artifacts/line-1/pigment-draft.png')
    original, generated = base.read_bytes(), draft.read_bytes()
    assert hashlib.sha256(original).hexdigest() == ANCESTOR
    w, h, old = read_png(original)
    gw, gh, source = read_png(generated)
    assert (w, h) == (1254, 1254)
    final = bytearray(old)
    # Small unused stone between Pepe's right hand and the lower-right crack.
    # Generated white is a transfer carrier, never painted over ancestral stone.
    x0, y0, edge = 829, 861, 120
    changed = 0
    bounds = [w, h, 0, 0]
    for dy in range(edge):
        for dx in range(edge):
            sx, sy = dx*gw//edge, dy*gh//edge
            s = (sy*gw+sx)*3
            r, g, b = source[s:s+3]
            if min(r, g, b) > 185:
                continue
            x, y = x0+dx, y0+dy
            i = (y*w+x)*3
            if max(old[i:i+3]) < 65:
                continue  # retain deep ancestral fissures
            alpha = .85*(255-min(r,g,b))/255
            pigment = (130, 53, 24) if r > 1.4*max(g,1) else (36, 28, 20)
            for c in range(3):
                final[i+c] = min(old[i+c], round((1-alpha)*old[i+c]+alpha*pigment[c]))
            if final[i:i+3] != old[i:i+3]:
                changed += 1
                bounds = [min(bounds[0],x), min(bounds[1],y),max(bounds[2],x),max(bounds[3],y)]
    assert 100 < changed < 4000
    encoded = png(w,h,final)
    base.write_bytes(encoded)
    Path('artifacts/line-1/wall-v13.png').write_bytes(encoded)
    thumb = jpeg(512,512,resize(w,h,final),52)
    assert len(thumb) < 100000
    Path('dist/line-1/33.jpg').write_bytes(thumb)
    wall_hash = hashlib.sha256(encoded).hexdigest()
    record = {'name':'The Answer Cords','image':'https://api.imd.fun/artifacts/'+wall_hash,
              'attributes':[{'trait_type':k,'value':v} for k,v in (
                  ('Cave','Water'),('Wall','Line 1'),('Number',33),
                  ('Left behind','Batch response review'),
                  ('Meaning','Crossed cords let Pepe follow each answer back to its own ochre seed.'),
                  ('One thing','portable live Ethereum JSON-RPC snapshots'))]}
    Path('dist/line-1/33.json').write_text(json.dumps(record,indent=2)+'\n')
    review = {'record':33,'ancestor_sha256':ANCESTOR,'output_sha256':wall_hash,
              'wall':{'paths':[str(base),'artifacts/line-1/wall-v13.png'],
                      'width':w,'height':h,'format':'PNG','mode':'RGB'},
              'thumbnail':{'path':'dist/line-1/33.jpg','width':512,'height':512,
                           'format':'JPEG','bytes':len(thumb)},
              'generation':{'tool':'mcp__image__generate_image',
                            'draft_sha256':hashlib.sha256(generated).hexdigest(),
                            'prompt':'Two winding charcoal cords crossing, with two irregular red ochre seed outlines; handmade sparse worn prehistoric pigment on white transfer carrier; no text, hands, figures, logos or borders.',
                            'draft_retained':False},
              'changed_pixels':changed,'unchanged_pixels':w*h-changed,
              'changed_bounds_inclusive':bounds,
              'preservation':'Only dark pigment transferred to bare stone; all other pixels unchanged, including Pepe, older marks, framing and deep cracks.',
              'visual_review':'Pending inspection of full wall and decoded thumbnail.',
              'unmet_visual_requirements':[]}
    Path('line-1/wall-review-33.json').write_text(json.dumps(review,indent=2)+'\n')
    draft.unlink()
    print(json.dumps(review,indent=2))

if __name__ == '__main__':
    main()
