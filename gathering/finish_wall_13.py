#!/usr/bin/env python3
"""Transfer only new tool-generated charcoal onto vacant ancestral stone."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, jpeg, resize

ANCESTOR = '36097c8d1198329e1d360f931465d79100cc350f311d3b178dda2cd3ac11dc86'
PROMPT = ('Preserve the complete 1254 square ancestral cave, rock, framing and every older mark. '
          'Add only a small worn charcoal and ochre basket with three reeds '
          'on vacant right-hand stone, representing review of the whole container. '
          'Preserve the central broad-mouth heavy-lidded Pepe. '
          'No new hands, handprints, text, numbers, logos or borders.')


def main():
    ancestor_path = Path('artifacts/gathering/wall.png')
    target = Path('artifacts/gathering/wall-v13.png')
    ancestor, draft = ancestor_path.read_bytes(), target.read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == ANCESTOR
    w, h, old = read_png(ancestor)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (gw, gh) == (1254, 1254)
    # The generated basket sits on vacant stone to the right of ancestral Pepe.
    # Transfer NEW pigment only; never retain its regenerated substrate.
    source = (994, 540, 1140, 683)
    dest = (994, 540, 146, 143)
    x0, y0, width, height = dest
    final = bytearray(old)
    changed = 0
    for dy in range(height):
        for dx in range(width):
            x, y = x0 + dx, y0 + dy
            sx = source[0] + dx * (source[2]-source[0]) // width
            sy = source[1] + dy * (source[3]-source[1]) // height
            gi, oi = (sy*w+sx)*3, (y*w+x)*3
            r, g, b = generated[gi:gi+3]
            rock = old[oi:oi+3]
            # Preserve deep cracks and add only dark burnt-stick pigment.
            if max(rock) < 45 or max(r,g,b) > 85 or min(r,g,b) > 58:
                continue
            alpha = min(.85, max(0, (92-max(r,g,b))/48))
            if alpha < .16:
                continue
            color = (35, 27, 20)
            for c in range(3):
                final[oi+c] = min(rock[c], round(rock[c]*(1-alpha)+color[c]*alpha))
            if final[oi:oi+3] != rock:
                changed += 1
    assert changed > 300
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if not (x0 <= x < x0+width and y0 <= y < y0+height) or max(old[i:i+3]) < 45:
                assert final[i:i+3] == old[i:i+3]
    encoded = png(w,h,final)
    target.write_bytes(encoded)
    ancestor_path.write_bytes(encoded)
    quality = 52
    thumb = resize(w,h,final)
    preview = jpeg(512,512,thumb,quality)
    while len(preview) > 100000:
        quality -= 5
        assert quality >= 10
        preview = jpeg(512,512,thumb,quality)
    Path('dist/gathering/13.jpg').write_bytes(preview)
    review = dict(ancestorSha256=ANCESTOR,ancestorSize=[w,h],wallSize=[w,h],
        wallFormat='PNG',wallMode='RGB',wallSha256=hashlib.sha256(encoded).hexdigest(),
        generatedDraftSha256=hashlib.sha256(draft).hexdigest(),generatedDraftRetained=False,
        sourceRectangle=list(source),additionRectangle=list(dest),changedPixels=changed,
        unchangedPixels=w*h-changed,allPixelsOutsideAdditionUnchanged=True,deepCracksProtected=True,
        previewSize=[512,512],previewFormat='JPEG',previewBytes=len(preview),
        imageTool='image_gen.imagegen',prompt=PROMPT,
        reviewStatus='requires final visual inspection',unmetVisualRequirements=[])
    Path('gathering/wall-review-13.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
