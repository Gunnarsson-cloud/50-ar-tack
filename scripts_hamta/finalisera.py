"""Applicerar godkända online-bilder (webp+avif) från bilder/viner_ny till bilder/viner.
Endast ID i ACCEPT rörs. Övriga behåller sitt festfoto."""
from PIL import Image
import os

ACCEPT = ["02","04","09","14","15","16","17","19","22","23","24","25","26","29","32","34"]

for vid in ACCEPT:
    src = f"bilder/viner_ny/vin_{vid}.webp"
    if not os.path.exists(src):
        print(vid, "SAKNAS", src); continue
    im = Image.open(src).convert("RGB")
    im.save(f"bilder/viner/vin_{vid}.webp", "WEBP", quality=90, method=6)
    try:
        im.save(f"bilder/viner/vin_{vid}.avif", "AVIF", quality=62)
        print(vid, "OK webp+avif")
    except Exception as e:
        print(vid, "webp ok, avif fel:", e)
