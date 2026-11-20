import sys, re, json, io
import docx, pytesseract
from PIL import Image, ImageOps

src = sys.argv[1]; media = sys.argv[2]; out = sys.argv[3]
d = docx.Document(src)
rels = {r.rId: r.target_ref for r in d.part.rels.values() if 'image' in r.reltype}

def load(name):
    im = Image.open(f'{media}/{name}').convert('RGBA')
    bg = Image.new('RGBA', im.size, 'white'); bg.alpha_composite(im)
    return bg.convert('L')

def ocr_strip(names):
    ims = [load(n) for n in names]
    W = sum(i.width for i in ims) + 10*len(ims); H = max(i.height for i in ims)
    strip = Image.new('L', (W, H), 255); x = 0
    for i in ims:
        strip.paste(i, (x, 0)); x += i.width + 10
    strip = ImageOps.expand(strip, border=12, fill=255)
    strip = strip.resize((strip.width*4, strip.height*4), Image.LANCZOS)
    cfg = '--psm 7 -c tessedit_char_whitelist=0123456789.'
    t = pytesseract.image_to_string(strip, config=cfg).strip().replace(' ', '')
    return t

res = []
for ti, t in enumerate(d.tables):
    rows = []
    for ri, row in enumerate(t.rows):
        if ri == 0: continue
        cells = []
        for c in row.cells:
            ids = re.findall(r'r:embed="(rId\d+)"', c._tc.xml)
            names = [rels[i].split('/')[-1] for i in ids]
            cells.append({'imgs': names, 'txt': ocr_strip(names) if names else ''})
        rows.append(cells)
    res.append(rows)
json.dump(res, open(out, 'w'))
print('done', [len(r) for r in res])
