#!/usr/bin/env python3
"""
galla_bilder.py — Automatisk gallring av gästbilder.

Skannar en mapp med foton och kopierar de "fina" (skarpa bilder med tydliga
ansikten) till en separat mapp, så du slipper klicka igenom 350+ bilder för hand.

Logik:
  1. Kasta suddiga bilder  (låg skärpa = låg Laplacian-varians).
  2. Behåll bilder med minst ett tydligt ansikte (Haar-cascade, ingen nätnedladdning).
  3. Sortera i undermappar: portratt (1 ansikte), grupp (2+), handelse (skarp men 0 ansikten).

Originalen rörs ALDRIG — filerna kopieras, inte flyttas. Kör om hur många gånger du vill.
"""
import argparse, shutil, sys
from pathlib import Path

try:
    import cv2
except ImportError:
    sys.exit("cv2 saknas. Kör i Docker (se README) eller: pip install opencv-python-headless")

BILD_TYPER = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".heic"}

def skarpa(gra):
    """Laplacian-varians: högt = skarpt, lågt = suddigt."""
    return cv2.Laplacian(gra, cv2.CV_64F).var()

def analysera(gra, cascade, max_dim=1100):
    """Nedskalad analys: returnerar (antal_ansikten, skärpa).
    OBS: både skärpa och ansikten mäts på den NEDSKALADE bilden – annars blir
    Laplacian-variansen missvisande låg på stora, mjuka mobilfoton."""
    h, w = gra.shape[:2]
    if max(h, w) > max_dim:
        s = max_dim / max(h, w)
        gra = cv2.resize(gra, (int(w * s), int(h * s)))
    sharp = cv2.Laplacian(gra, cv2.CV_64F).var()
    faces = len(cascade.detectMultiScale(gra, scaleFactor=1.1, minNeighbors=5, minSize=(35, 35)))
    return faces, sharp

def main():
    ap = argparse.ArgumentParser(description="Gallra gästbilder automatiskt.")
    ap.add_argument("--in",  dest="indir",  default="/data/gaster_raw",
                    help="Mapp med råa foton (default: /data/gaster_raw)")
    ap.add_argument("--out", dest="outdir", default="/data/fina_bilder_gaster",
                    help="Målmapp för fina bilder (default: /data/fina_bilder_gaster)")
    ap.add_argument("--skarpa-min", type=float, default=140.0,
                    help="Skärpekrav för bilder UTAN ansikte (händelsebilder). Default 140")
    ap.add_argument("--blur-hard", type=float, default=45.0,
                    help="Under detta kasslas även ansiktsbilder (rejäl oskärpa). Default 45")
    ap.add_argument("--kopiera-suddiga", action="store_true",
                    help="Lägg även suddiga i undermappen _kasslade för granskning")
    args = ap.parse_args()

    indir, outdir = Path(args.indir), Path(args.outdir)
    if not indir.is_dir():
        sys.exit(f"Hittar inte inmappen: {indir}")

    # Haar-cascaden följer med opencv — ingen internetnedladdning behövs.
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    mappar = {k: outdir / k for k in ("portratt", "grupp", "handelse", "_kasslade")}
    for m in mappar.values():
        m.mkdir(parents=True, exist_ok=True)

    stat = {"portratt": 0, "grupp": 0, "handelse": 0, "suddig": 0, "fel": 0, "totalt": 0}
    filer = sorted(p for p in indir.rglob("*") if p.suffix.lower() in BILD_TYPER)
    print(f"Hittade {len(filer)} bilder i {indir}\n")

    for p in filer:
        stat["totalt"] += 1
        img = cv2.imread(str(p))
        if img is None:
            stat["fel"] += 1
            continue
        gra = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        n, sharp = analysera(gra, cascade)

        # Beslut: behåll alla bilder med ansikten (om inte rejält suddiga);
        # bilder utan ansikte behålls bara om de är skarpa (händelsebilder).
        if n >= 1 and sharp < args.blur_hard:
            mal = "suddig"
        elif n == 1:
            mal = "portratt"
        elif n >= 2:
            mal = "grupp"
        elif sharp >= args.skarpa_min:
            mal = "handelse"
        else:
            mal = "suddig"

        if mal == "suddig":
            stat["suddig"] += 1
            if args.kopiera_suddiga:
                shutil.copy2(p, mappar["_kasslade"] / p.name)
            continue
        shutil.copy2(p, mappar[mal] / p.name)
        stat[mal] += 1

    print("\n===== KLART =====")
    for k, v in stat.items():
        print(f"  {k:10}: {v}")
    print(f"\nFina bilder ligger nu i: {outdir}")

if __name__ == "__main__":
    main()
