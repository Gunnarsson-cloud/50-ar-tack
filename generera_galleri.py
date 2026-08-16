#!/usr/bin/env python3
"""
generera_galleri.py — Skapar en lätt webb-version av de gallrade gästbilderna.

Läser fina_bilder_gaster/{portratt,grupp,handelse}, putsar (ljusare/renare),
skalar ner till max 1600 px och sparar som WebP i bilder/galleri/.
Skriver även galleri.json (manifest) som ett ev. gästgalleri kan läsa.

Kör:  python generera_galleri.py --in <mapp med fina_bilder_gaster>
"""
import argparse, json, statistics
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance

BASE = Path(__file__).parent
MAXDIM = 1600
KATEGORIER = ["portratt", "grupp", "handelse"]

def putsa(im):
    im = ImageOps.exif_transpose(im).convert("RGB")
    r, g, b = im.split()
    mr, mg, mb = (statistics.mean(list(c.getdata())[::151]) or 1 for c in (r, g, b))
    gray = (mr + mg + mb) / 3
    r = r.point([min(255, int(i*gray/mr)) for i in range(256)])
    g = g.point([min(255, int(i*gray/mg)) for i in range(256)])
    b = b.point([min(255, int(i*gray/mb)) for i in range(256)])
    im = Image.merge("RGB", (r, g, b))
    im = ImageOps.autocontrast(im, cutoff=0.4)
    im = ImageEnhance.Brightness(im).enhance(1.08)
    im = ImageEnhance.Contrast(im).enhance(1.05)
    im = ImageEnhance.Color(im).enhance(1.10)
    im = ImageEnhance.Sharpness(im).enhance(1.12)
    return im

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True, help="mapp med fina_bilder_gaster")
    ap.add_argument("--out", dest="outdir", default=str(BASE / "bilder" / "galleri"))
    args = ap.parse_args()
    indir, outdir = Path(args.indir), Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for kat in KATEGORIER:
        d = indir / kat
        if not d.is_dir():
            continue
        for i, p in enumerate(sorted(d.glob("*")), 1):
            if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".heic"}:
                continue
            try:
                im = putsa(Image.open(p))
            except Exception:
                continue
            im.thumbnail((MAXDIM, MAXDIM), Image.LANCZOS)
            namn = f"{kat}_{i:03d}.webp"
            im.save(outdir / namn, "WEBP", quality=80, method=6)
            manifest.append({"fil": f"./bilder/galleri/{namn}", "kategori": kat,
                             "bredd": im.width, "hojd": im.height})
    (BASE / "galleri.json").write_text(
        json.dumps({"antal": len(manifest), "bilder": manifest}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"Klart – {len(manifest)} webb-bilder i {outdir}")

if __name__ == "__main__":
    main()
