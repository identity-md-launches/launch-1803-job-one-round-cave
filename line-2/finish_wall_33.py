"""One-time additive pigment transfer; run after the installed image generator."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

base = Path('artifacts/line-2/wall.png')
target = Path('artifacts/line-2/wall-v13.png')
ancestor = base.read_bytes()
assert hashlib.sha256(ancestor).hexdigest() == '54b8b19b20221b7895e547fb2091cad17b541ee6e1e2eff858ae9c9cebd57f34'
w, h, old = read_png(ancestor)
draft = target.read_bytes()
dw, dh, generated = read_png(draft)
assert (w, h) == (1254, 1254)
# Crop includes all generated pigment, with room around the broad charcoal arc.
cx, cy, cw, ch = [round(v) for v in (dw*.12, dh*.21, dw*.79, dh*.55)]
x0, y0, width, height = 275, 340, 130, 100
final = bytearray(old)
changed = 0
for y in range(y0, y0 + height):
    for x in range(x0, x0 + width):
        i = (y*w+x)*3
        rock = old[i:i+3]
        sx = cx + (x-x0)*cw//width
        sy = cy + (y-y0)*ch//height
        j = (sy*dw+sx)*3
        r, g, b = generated[j:j+3]
        if max(rock) < 85 or (x*19+y*31)%23 == 0:
            continue
        charcoal = max(r, g, b) < 105 and sum(rock)-r-g-b > 60
        ochre = r > 70 and g < r*.60 and b < r*.35 and rock[1]-g > 20
        chalk = r > 215 and g > 215 and b > 170 and 260 < sx < 410 and 420 < sy < 590
        if charcoal or chalk:
            pigment = (48, 33, 21) if charcoal else (208, 193, 151)
            alpha = .70 if charcoal else .64
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha) + pigment[c]*alpha)
            if final[i:i+3] != old[i:i+3]:
                changed += 1
assert 500 < changed < width*height
for y in range(h):
    for x in range(w):
        i = (y*w+x)*3
        if final[i:i+3] != old[i:i+3]:
            assert x0 <= x < x0+width and y0 <= y < y0+height
            assert max(old[i:i+3]) >= 85
encoded = png(w, h, final)
base.write_bytes(encoded)
target.write_bytes(encoded)
preview = jpeg(512, 512, resize(w, h, final), 52)
assert len(preview) <= 100000
Path('dist/line-2/33.jpg').write_bytes(preview)
review = {'number': 33, 'ancestor_sha256': hashlib.sha256(ancestor).hexdigest(),
          'sha256': hashlib.sha256(encoded).hexdigest(),
          'wall': {'paths': [str(base), str(target)], 'width': w, 'height': h,
                   'format': 'PNG', 'mode': 'RGB', 'bytes': len(encoded)},
          'preview': {'path': 'dist/line-2/33.jpg', 'width': 512, 'height': 512,
                      'format': 'JPEG', 'bytes': len(preview)},
          'addition_region': {'x': x0, 'y': y0, 'width': width, 'height': height},
          'changed_pixels': changed, 'unchanged_pixels': w*h-changed,
          'outside_region_pixel_identical': True, 'dark_cracks_preserved': True,
          'generation_tool': 'mcp__image__generate',
          'draft_sha256': hashlib.sha256(draft).hexdigest(),
          'generated_dimensions': [dw, dh], 'draft_retained': False,
          'visual_review': 'pending inspection', 'unmet_visual_requirements': []}
Path('line-2/wall-review-33.json').write_text(json.dumps(review, indent=2)+'\n')
print(json.dumps(review, indent=2))
