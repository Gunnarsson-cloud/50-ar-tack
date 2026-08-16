#!/usr/bin/env python3
"""
putsa_bilder.py — Ljusar upp och fräschar till bilder innan publicering.

Varje bild:
  1. Auto-orienteras (EXIF).
  2. Vitbalanseras (gray-world) så färgstick försvinner.
  3. Får auto-nivåer (autocontrast) för djup och renhet.
  4. Lyfts en aning i ljus, kontrast, mättnad och skärpa.
  5. Beskärs/skalas till målformat och sparas webb-optimerat (.webp + .avif om möjligt).

Används både för flaskbilderna (porträtt 3:4) och gästbilderna.
Kan importeras (putsa(...)) eller köras som CLI.
"""
import argparse, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance

def _gray_world(im):
    """Enkel vitbalans: skala varje kanal så medelvärdet blir neutralt."""
    r, g, b = im.split()[:3]
    import statistics
    means = [statistics.mean(list(ch.getdata())[::97]) or 1 for ch in (r, g, b)]  # gles sampling
    gray = sum(means) / 3
    lut = lambda m: [min(255, int(i * gray / m)) for i in range(256)]
    r, g, b = r.point(lut(means[0])), g.point(lut(means[1])), b.point(lut(means[2]))
    return Image.merge("RGB", (r, g, b))

def putsa(src, dst_bas, mal_wh=None, ljus=1.06, kontrast=1.08, mattnad=1.10, skarpa=1.15,
          vitbalans=True, q=82):
    """Putsar en bild och sparar dst_bas.webp (+ .avif om stöd finns). Returnerar sparade sökvägar."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if vitbalans:
            im = _gray_world(im)
        im = ImageOps.autocontrast(im, cutoff=0.5)             # rensa svarta/vita nivåer
        im = ImageEnhance.Brightness(im).enhance(ljus)
        im = ImageEnhance.Contrast(im).enhance(kontrast)
        im = ImageEnhance.Color(im).enhance(mattnad)
        im = ImageEnhance.Sharpness(im).enhance(skarpa)
        if mal_wh:
            im = ImageOps.fit(im, mal_wh, method=Image.LANCZOS, centering=(0.5, 0.4))
        dst_bas = Path(dst_bas)
        dst_bas.parent.mkdir(parents=True, exist_ok=True)
        sparade = []
        webp = dst_bas.with_suffix(".webp")
        im.save(webp, "WEBP", quality=q, method=6)
        sparade.append(webp)
        try:                                                   # AVIF om Pillow byggts med stöd
            avif = dst_bas.with_suffix(".avif")
            im.save(avif, "AVIF", quality=q)
            sparade.append(avif)
        except Exception:
            pass
    return sparade

def main():
    ap = argparse.ArgumentParser(description="Putsa och webb-optimera bilder.")
    ap.add_argument("--in", dest="indir", required=True, help="Mapp med källbilder")
    ap.add_argument("--out", dest="outdir", required=True, help="Målmapp")
    ap.add_argument("--bredd", type=int, default=0, help="Målbredd (px), 0 = behåll")
    ap.add_argument("--hojd", type=int, default=0, help="Målhöjd (px), 0 = behåll")
    ap.add_argument("--ingen-vitbalans", action="store_true")
    args = ap.parse_args()
    indir, outdir = Path(args.indir), Path(args.outdir)
    if not indir.is_dir():
        sys.exit(f"Hittar inte {indir}")
    mal = (args.bredd, args.hojd) if args.bredd and args.hojd else None
    ext = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".bmp", ".tif", ".tiff"}
    n = 0
    for p in sorted(indir.rglob("*")):
        if p.suffix.lower() not in ext:
            continue
        putsa(p, outdir / p.stem, mal_wh=mal, vitbalans=not args.ingen_vitbalans)
        n += 1
        print(f"  putsad: {p.name}")
    print(f"\nKlart – {n} bilder putsade till {outdir}")

if __name__ == "__main__":
    main()
