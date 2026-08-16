# 🍷 50 år – Ett sällskap av vänner och viner

En supersnabb, mobilanpassad minnessida som förevigar **36 viner** från festen. Varje vin
presenteras som en "vän" med egen personlighet på svenska.

## Innehåll
| Fil | Vad |
|-----|-----|
| `viner.json` | Databasen — 36 viner, avlästa direkt från etiketterna (inget påhittat) |
| `index.html` | Hela sidan: inline-CSS, minimal vanilla-JS, `<picture>` + `loading="lazy"` |
| `bilder/viner/` | **36 färdiga flaskbilder** (`vin_01.webp/.avif` … `vin_36`) |
| `bygg_flaskbilder.py` | Skapar flaskbilderna genom att beskära + putsa gruppfotona IMG_9229–9231 |
| `putsa_bilder.py` | Ljusar upp och webb-optimerar valfria bilder (återanvändbar) |
| `galla_bilder.py` | Skript som gallrar 335 gästbilder automatiskt |
| `docker-compose.yml` | Nginx-webserver + gallrings-container |

---

## 1. Kör webbsidan

```bash
docker compose up webb
```
Öppna sedan **http://localhost:8080**. Nginx serverar filerna direkt — ingen byggprocess,
inga beroenden. Sidan väger bara några kB innan bilderna laddas.

> Sidan läser `viner.json` via `fetch`, så den måste öppnas via webbservern ovan
> (inte genom att dubbelklicka på HTML-filen).

### Flaskbilderna
Alla 36 finns redan i `bilder/viner/` som `vin_01…vin_36` i **AVIF + WebP** (snitt ~16 kB/st).
De är automatiskt urklippta ur de tre gruppfotona (IMG_9229–9231 – de enda vinbilder som
fanns), putsade (ljusare, renare) och centrerade på en ljus 3:4-duk.

`<picture>`-taggen väljer automatiskt AVIF → WebP. Saknas en bild visas en elegant
platshållare med "Foto på väg".

**Regenerera** (t.ex. om du justerar beskärning eller ljus):
```bash
python bygg_flaskbilder.py
```
Snittpositionerna för varje flaska ligger i `PLAN` överst i skriptet – finjustera vid behov.
Vill du hellre fota enstaka flaskor separat: lägg fotot som `bilder/viner/vin_XX.webp`
(+ `.avif`) med rätt nummer, eller kör `python putsa_bilder.py --in <mapp> --out bilder/viner
--bredd 600 --hojd 800` för att putsa och skala dem.

---

## 2. Gallra gästbilderna automatiskt

1. Lägg alla råa foton i `bilder/gaster_raw/`.
2. Kör:
```bash
docker compose run --rm galla
```
3. Skriptet skapar `bilder/fina_bilder_gaster/` med undermappar:
   - `portratt/` – exakt ett tydligt ansikte
   - `grupp/` – två eller fler ansikten
   - `handelse/` – skarp bild utan ansikte (tårta, dukning, dans…)
   - `_kasslade/` – (valfritt) suddiga bilder för granskning

**Originalen rörs aldrig** – filerna kopieras. Kör om hur ofta du vill.

### Justera känsligheten
```bash
# Släpp igenom fler bilder (lägre skärpekrav) och spara även de suddiga:
docker compose run --rm galla --skarpa-min 60 --kopiera-suddiga
```
| Flagga | Betydelse | Default |
|--------|-----------|---------|
| `--skarpa-min` | Tröskel för skärpa. Lägre = mer släpps igenom | `100` |
| `--kopiera-suddiga` | Kopiera även suddiga till `_kasslade/` | av |

> Ansiktsdetektionen använder OpenCV:s inbyggda Haar-cascade — snabb och helt lokal,
> ingen bild lämnar din dator och inget laddas ned från nätet.

---

## Designprinciper
- **Mobile first** – enkolumns-rutnät som växer till 2–3 kolumner på större skärmar.
- **Lätt** – ingen framework, ingen webfont, all CSS/JS inline. En enda `fetch`.
- **Bilder sist** – `loading="lazy"` + `decoding="async"` + fasta mått (ingen layout-hopp).
- **Tillgängligt** – filterknappar med `aria-pressed`, respekterar `prefers-reduced-motion`.

*Alla vinnamn och årgångar är avlästa direkt från fotografierna IMG_9229–9231, inklusive en
extra närbildskontroll av de två delvis skymda etiketterna (Fortellino Ripasso och Vermell).
Flaskan som syns i två gruppbilder (Poderi Colla Dardi Le Rose Barolo Bussia 2021) räknas en gång.*
