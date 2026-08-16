"""Laddar ner en bild-URL, trimmar vit bakgrund, centrerar på 600x800 vit duk,
sparar som webp + avif till bilder/viner/vin_NN.*  (urllib, ej curl/wget).
Anrop: python ladda_ner.py <id_tva_siffror> <bild_url>"""
import sys, io, urllib.request
from PIL import Image, ImageOps, ImageChops

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
CANVAS = (600, 800)
PAD = 60  # marginal runt flaskan

def hamta(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def trimma(im):
    """Beskär bort enfärgad ram (vit/ljus) runt motivet."""
    im = im.convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -25)  # tolerans mot ljusgrått
    bbox = diff.getbbox()
    return im.crop(bbox) if bbox else im

def main():
    vid = sys.argv[1].zfill(2)
    url = sys.argv[2]
    raw = hamta(url)
    im = Image.open(io.BytesIO(raw))
    im = ImageOps.exif_transpose(im)
    im = trimma(im)
    # skala så flaskan får plats inom duk minus marginal
    maxw, maxh = CANVAS[0] - 2 * PAD, CANVAS[1] - 2 * PAD
    im.thumbnail((maxw, maxh), Image.LANCZOS)
    duk = Image.new("RGB", CANVAS, (255, 255, 255))
    duk.paste(im, ((CANVAS[0] - im.width) // 2, (CANVAS[1] - im.height) // 2))
    outdir = sys.argv[3] if len(sys.argv) > 3 else "bilder/viner"
    import os; os.makedirs(outdir, exist_ok=True)
    bas = f"{outdir}/vin_{vid}"
    duk.save(bas + ".webp", "WEBP", quality=88, method=6)
    if outdir == "bilder/viner":
        try:
            duk.save(bas + ".avif", "AVIF", quality=62)
        except Exception as e:
            print("  (avif hoppad:", e, ")")
    print(f"OK vin_{vid}  källa={len(raw)}B  -> {bas}.webp")

if __name__ == "__main__":
    main()
