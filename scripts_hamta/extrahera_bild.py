"""Hämtar en webbsida och skriver ut kandidat-bildURL:er (og:image + stora <img>).
Använder urllib (ej curl/wget/requests). Anropas: python extrahera_bild.py <url>"""
import sys, re, urllib.request, gzip, io

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def hamta(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data.decode("utf-8", "ignore")

def main():
    url = sys.argv[1]
    try:
        html = hamta(url)
    except Exception as e:
        print("FEL:", e); return
    cands = []
    for m in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.I):
        cands.append(("og:image", m.group(1)))
    for m in re.finditer(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)', html, re.I):
        cands.append(("twitter", m.group(1)))
    # ld+json image
    for m in re.finditer(r'"image"\s*:\s*"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html, re.I):
        cands.append(("ldjson", m.group(1)))
    seen = set()
    for tag, u in cands:
        if u.startswith("//"): u = "https:" + u
        if u not in seen:
            seen.add(u); print(tag, "|", u)

if __name__ == "__main__":
    main()
