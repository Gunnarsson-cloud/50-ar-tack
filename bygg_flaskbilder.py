#!/usr/bin/env python3
"""
bygg_flaskbilder.py — Skapar de färdiga flaskbilderna till korten.

Pipeline per flaska:
  1. Beskär ut flaskan ur gruppfotot (manuella snittpositioner nedan).
  2. Trimmar bort grannflaskors kanter (horisontell mörkerdetektion).
  3. Putsar: gray-world-vitbalans, auto-nivåer, lyft i ljus/kontrast/mättnad/skärpa.
  4. Centrerar flaskan på en ren, ljus 3:4-duk så alla kort ser enhetliga ut.
  5. Sparar bilder/viner/vin_XX.webp (+ .avif).

Källa: de tre gruppfotona IMG_9229–9231 (enda vinbilderna som finns).
Kör:  python bygg_flaskbilder.py
"""
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageDraw

BASE = Path(__file__).parent
UT = BASE / "bilder" / "viner"; UT.mkdir(parents=True, exist_ok=True)
CANVAS = (600, 800)          # 3:4
BG_TOP, BG_BOT = (252, 249, 244), (238, 231, 220)

# snittgränser i procent (N+1 per foto) + vin-id vänster→höger (None = dublett, hoppa)
PLAN = {
    "IMG_9229.jpeg": ([1,2,3,4,5,6,7,8,9,10,11,12,13,14],
        [1.5,8.5,16,24.5,31.5,39.5,46.5,52.5,58.5,64,70,76.5,84,91.5,99]),
    "IMG_9230.jpeg": ([15,16,17,18,19,20,21,22,23,None,24,25,26,27],
        [1.5,9,16.5,24,30,37,43.5,50,57,63.5,70.5,77,83.5,91,99]),
    "IMG_9231.jpeg": ([28,29,30,31,32,33,34,35,36],
        [2,13,24.5,35,46,57,68,79,89,99]),
}

# Finjustering för enstaka flaskor: id -> (center_skift_i_andel, halv_bredd_i_andel).
# center_skift flyttar mitten (＋=höger), halv_bredd sätter beskärningens halva bredd.
# Tomt = använd automatisk halscentrering (bäst i snitt). Fyll i vid behov för enstaka flaskor.
OVERRIDE = {}

def _colmin(g, w, y0, y1):
    band = g.crop((0, int(g.height*y0), w, int(g.height*y1)))
    px = band.load(); bw, bh = band.size
    out = []
    for x in range(bw):
        m = 255
        for y in range(0, bh, 3):
            v = px[x, y]
            if v < m: m = v
        out.append(m)
    return out

def trim_sides(im, vid=None):
    """Centrera på flaskans hals och beskär till flaskans egen bredd → inga grannslivrar."""
    w, h = im.size
    g = im.convert("L")
    ov = OVERRIDE.get(vid)
    # 1) hitta halscentrum: mörk löpa i övre bandet närmast remsans mitt (halsar separeras rent)
    neck = _colmin(g, w, 0.08, 0.30)
    Tn = 150
    runs, i = [], 0
    while i < w:
        if neck[i] < Tn:
            j = i
            while j < w and neck[j] < Tn: j += 1
            if j - i > w*0.02: runs.append((i, j))
            i = j
        else:
            i += 1
    cx = w//2
    ncx = ((lambda r: (r[0]+r[1])//2)(min(runs, key=lambda r: abs((r[0]+r[1])/2 - cx)))
           if runs else cx)
    if ov:
        ncx = int(w*(0.5 + ov[0]))
    # 2) bredd: expandera från halsen i kroppsbandet tills bakgrund, med tak
    body = _colmin(g, w, 0.50, 0.82)
    Tb = 165
    cap = int(w * (ov[1] if ov else 0.46))
    L = ncx
    while L > 0 and body[L] < Tb and ncx - L < cap: L -= 1
    R = ncx
    while R < w-1 and body[R] < Tb and R - ncx < cap: R += 1
    pad = int(w*0.025)
    return im.crop((max(0, L-pad), 0, min(w, R+pad), h))

def putsa(im):
    im = im.convert("RGB")
    # gray-world-vitbalans
    r, g, b = im.split()
    import statistics
    mr, mg, mb = (statistics.mean(list(c.getdata())[::101]) or 1 for c in (r, g, b))
    gray = (mr+mg+mb)/3
    r = r.point([min(255, int(i*gray/mr)) for i in range(256)])
    g = g.point([min(255, int(i*gray/mg)) for i in range(256)])
    b = b.point([min(255, int(i*gray/mb)) for i in range(256)])
    im = Image.merge("RGB", (r, g, b))
    im = ImageOps.autocontrast(im, cutoff=0.4)
    im = ImageEnhance.Brightness(im).enhance(1.07)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.12)
    im = ImageEnhance.Sharpness(im).enhance(1.18)
    return im

def canvas_bg():
    bg = Image.new("RGB", CANVAS, BG_TOP); d = ImageDraw.Draw(bg)
    for y in range(CANVAS[1]):
        t = y/CANVAS[1]
        d.line([(0, y), (CANVAS[0], y)],
               fill=tuple(int(BG_TOP[i]+(BG_BOT[i]-BG_TOP[i])*t) for i in range(3)))
    return bg

def main():
    n = 0
    for fname, (ids, cuts) in PLAN.items():
        src = ImageOps.exif_transpose(Image.open(BASE / fname)).convert("RGB")
        w, h = src.size
        xs = [int(w*p/100) for p in cuts]
        for i, vid in enumerate(ids):
            if vid is None:
                continue
            strip = src.crop((xs[i], 0, xs[i+1], h))
            strip = trim_sides(strip, vid)
            strip = putsa(strip)
            # skala in på duk, 92 % av höjden, centrerat
            bottle = ImageOps.contain(strip, (int(CANVAS[0]*0.9), int(CANVAS[1]*0.92)), Image.LANCZOS)
            bg = canvas_bg()
            bg.paste(bottle, ((CANVAS[0]-bottle.width)//2, (CANVAS[1]-bottle.height)//2))
            bg.save(UT / f"vin_{vid:02d}.webp", "WEBP", quality=84, method=6)
            try:
                bg.save(UT / f"vin_{vid:02d}.avif", "AVIF", quality=80)
            except Exception:
                pass
            n += 1
    print(f"Klart – {n} flaskbilder skrivna till {UT}")

if __name__ == "__main__":
    main()
