"""Läser kallor.tsv (id<TAB>url), extraherar bästa bild-URL, laddar ner,
trimmar + centrerar på 600x800 vit duk, sparar till bilder/viner_ny/vin_NN.webp.
Originalen i bilder/viner rörs INTE. urllib (ej curl/wget)."""
import re, io, os, sys, urllib.request, gzip
from PIL import Image, ImageOps, ImageChops

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
CANVAS = (600, 800); PAD = 55
OUT = "bilder/viner_ny"
LOGGA = ("ikon", "logo", "placeholder", "default", "sprite", "favicon")

def hamta(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data

def bildkandidater(html):
    c = []
    for pat in [r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
                r'"image"\s*:\s*"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"']:
        for m in re.finditer(pat, html, re.I):
            u = m.group(1)
            if u.startswith("//"): u = "https:" + u
            if u not in c: c.append(u)
    # föredra kandidat som inte är sajtlogga
    bra = [u for u in c if not any(x in u.lower() for x in LOGGA)]
    return (bra or c)

def trimma(im):
    im = im.convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -22)
    bbox = diff.getbbox()
    return im.crop(bbox) if bbox else im

def process(vid, raw):
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
    im = trimma(im)
    maxw, maxh = CANVAS[0]-2*PAD, CANVAS[1]-2*PAD
    im.thumbnail((maxw, maxh), Image.LANCZOS)
    duk = Image.new("RGB", CANVAS, (255, 255, 255))
    duk.paste(im, ((CANVAS[0]-im.width)//2, (CANVAS[1]-im.height)//2))
    os.makedirs(OUT, exist_ok=True)
    duk.save(f"{OUT}/vin_{vid}.webp", "WEBP", quality=90, method=6)

def main():
    rows = [l.strip().split("\t") for l in open("scripts_hamta/kallor.tsv", encoding="utf-8") if l.strip()]
    for vid, url in rows:
        vid = vid.zfill(2)
        try:
            html = hamta(url).decode("utf-8", "ignore")
            cands = bildkandidater(html)
            if not cands:
                print(f"{vid}  INGEN-BILD  {url}"); continue
            img_url = cands[0]
            raw = hamta(img_url)
            process(vid, raw)
            print(f"{vid}  OK  {img_url.split('/')[-1]}  ({len(raw)}B)")
        except Exception as e:
            print(f"{vid}  FEL  {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
