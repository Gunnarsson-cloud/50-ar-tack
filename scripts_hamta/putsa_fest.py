"""Putsar kvarvarande festfoton: trimmar enfärgad bakgrund (samplad från hörnet),
centrerar och förstorar flaskan på ren duk 600x800. Sparar till bilder/viner_polish/ för granskning.
Rör INTE originalen."""
from PIL import Image, ImageChops
import os, glob

ACCEPT_ONLINE = {"02","04","09","14","15","16","17","19","22","23","24","25","26","29","32","34"}
CANVAS=(600,800); PAD=48
OUT="bilder/viner_polish"; os.makedirs(OUT, exist_ok=True)

def trimma(im):
    im=im.convert("RGB")
    # sampla bakgrund som medel av fyra hörn
    w,h=im.size
    pts=[(2,2),(w-3,2),(2,h-3),(w-3,h-3)]
    r=g=b=0
    for x,y in pts:
        pr,pg,pb=im.getpixel((x,y)); r+=pr; g+=pg; b+=pb
    bgcol=(r//4,g//4,b//4)
    bg=Image.new("RGB",im.size,bgcol)
    diff=ImageChops.difference(im,bg)
    diff=ImageChops.add(diff,diff,2.0,-30)  # tolerans
    bbox=diff.getbbox()
    if not bbox: return im
    # utvidga bbox lite
    l,t,rr,bb=bbox
    m=6
    return im.crop((max(0,l-m),max(0,t-m),min(w,rr+m),min(h,bb+m)))

for f in sorted(glob.glob("bilder/viner/vin_*.webp")):
    vid=os.path.basename(f)[4:6]
    if vid in ACCEPT_ONLINE: continue
    im=Image.open(f)
    tr=trimma(im)
    maxw,maxh=CANVAS[0]-2*PAD,CANVAS[1]-2*PAD
    tr.thumbnail((maxw,maxh),Image.LANCZOS)
    duk=Image.new("RGB",CANVAS,(255,255,255))
    duk.paste(tr,((CANVAS[0]-tr.width)//2,(CANVAS[1]-tr.height)//2))
    duk.save(f"{OUT}/vin_{vid}.webp","WEBP",quality=90,method=6)
    print(vid,"putsad", tr.size)
