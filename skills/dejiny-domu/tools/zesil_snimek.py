#!/usr/bin/env python3
"""Zesílený snímek pro čtení vybledlého písma (inkoust i tužka, mikrofilm i barevný sken).

Použití:
  zesil_snimek.py <snimek.jpg> [x0,y0,x1,y1] [--zvetsit N]
      x0..y1 = volitelný výřez ve zlomcích šířky a výšky (0..1), jako u vyrez.py.
      Vedle snímku uloží <jméno>_zesil.jpg (zesílený) a <jméno>_porovnani.jpg (nahoře šedý originál, dole zesílený).

Úprava: odečte pozadí (dělení rozmazanou kopií: zmizí žloutnutí, tmavé okraje mikrofilmu a nerovnoměrné osvětlení)
a pak písmo ztmaví esovitou křivkou kontrastu (slabé tahy a tužka zčernají, papír zbělá).
Čti z porovnání: zesílení zvýrazní i skvrny a tečky na papíře a ztuční přeškrtnutí, originál rozhodne.
Výřez pro web (vyrez.py) dělej z originálu. Zesílení zvětšením (--zvetsit 2) pomůže u drobného písma.
Vyzkoušeno na mikrofilmech gruntovních knih (17.–19. st.), matrikách, sčítání a barevných skenech eBadatelny;
místní kontrast (CLAHE), samotné roztažení kontrastu ani barevné kanály navíc nepomohly.
Potřebuje ImageMagick (příkaz `magick`, na Linuxu stačí `convert`).
"""
import glob, os, shutil, subprocess, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ODECTENI_POZADI = ["(", "+clone", "-blur", "0x25", ")", "-compose", "Divide_Src", "-composite"]
ZTMAVENI_PISMA = ["-contrast-stretch", "1%x5%", "-sigmoidal-contrast", "6x92%"]
ZESILENI = ["-colorspace", "Gray", *ODECTENI_POZADI, *ZTMAVENI_PISMA]


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned srozumitelnou hláškou."""
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m


def vyrez_argumenty(m, src, box):
    """Argumenty ImageMagicku pro výřez zadaný ve zlomcích stránky."""
    w, h = (int(v) for v in subprocess.run([m, src + "[0]", "-auto-orient", "-format", "%w %h", "info:"],
                                           capture_output=True, text=True, check=True).stdout.split())
    x0, y0, x1, y1 = box
    return ["-crop", f"{round((x1 - x0) * w)}x{round((y1 - y0) * h)}+{round(x0 * w)}+{round(y0 * h)}", "+repage"]


def nacti_argumenty(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    src, box, zvetsit = a.pop(0), None, 1.0
    while a:
        x = a.pop(0)
        if x == "--zvetsit":
            try:
                zvetsit = float(a.pop(0))
            except (IndexError, ValueError):
                zvetsit = 0
            if not 0 < zvetsit <= 8:
                sys.exit("--zvetsit čeká číslo od 0 do 8 (např. 2).")
        else:
            try:
                box = [float(v) for v in x.split(",")]
            except ValueError:
                box = []
            if len(box) != 4 or not all(0 <= v <= 1 for v in box) or box[0] >= box[2] or box[1] >= box[3]:
                sys.exit("Výřez zadej jako x0,y0,x1,y1 ve zlomcích 0..1 (x0<x1, y0<y1).")
    if not os.path.isfile(src):
        sys.exit(f"Soubor {src} neexistuje.")
    return src, box, zvetsit


def main():
    src, box, zvetsit = nacti_argumenty(sys.argv[1:])
    m = magick()
    base = os.path.splitext(src)[0]
    zesil, porovnani = f"{base}_zesil.jpg", f"{base}_porovnani.jpg"
    # -strip: poškozený profil ICC z portálů jinak zaplaví výstup varováními
    vstup = [src + "[0]", "-auto-orient", "-strip"] + (vyrez_argumenty(m, src, box) if box else [])
    zvetseni = ["-filter", "Lanczos", "-resize", f"{zvetsit * 100:g}%"] if zvetsit != 1 else []
    # zesílit v původním rozlišení (rozmazání pozadí počítá s velikostí tahů), zvětšit až potom
    subprocess.run([m, *vstup, *ZESILENI, *zvetseni, "-quality", "92", zesil], check=True)
    subprocess.run([m, "(", *vstup, "-colorspace", "Gray", *zvetseni, ")", zesil,
                    "-background", "white", "-splice", "0x8", "-append", "-quality", "88", porovnani], check=True)
    print(porovnani)
    print(zesil)


if __name__ == "__main__":
    main()
