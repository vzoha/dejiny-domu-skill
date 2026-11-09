#!/usr/bin/env python3
"""Letecké snímky (ortofoto) kolem domu po letech od 1998 – celá série se stejným výřezem.

Ukáže, jak se dům a dvůr měnily v posledních desetiletích: přístavby, zbořené stodoly, nové domy v sousedství.
Zdroje:
- ČÚZK, archivní ortofoto ČR 1998–2023 (WMS geoportal.cuzk.gov.cz/geoserver/wms_ortofoto_archiv). Každý rok se
  snímkovala jen část republiky, takže u domu bývá jen část ročníků; do 2001 černobílé. Otevřená data, CC BY 4.0,
  uvést „ČÚZK, <rok>“ – smí do PDF i na web.
- Kraje se starším nebo vlastním snímkováním (Jihočeský, Plzeňský …): jen ročníky, které ČÚZK u domu nemá.
  Licence kraje nejsou zveřejněné → jen ke čtení, do výstupu se souhlasem kraje (podminky.json).
Starší snímky: 50. léta `cuzk_archiv.py mapa cenia50`, Praha 1938–1996 `ipr_praha.py serie`.

Použití (z kořene projektu):
  ortofota.py vrstvy
      vypíše ročníky, které nástroj zná (klíč, rok, zdroj)
  ortofota.py serie <"Ulice čp, Obec" | "Obec čp" | lat,lon> [polomer_m=100] [px=1200] [--jen klic1,klic2] [--zapsat skupina]
      stáhne ročníky do pracovni/ortofota/<klic>_r<polomer>_<px>px_<X>_<Y>.jpg (X, Y = střed v S-JTSK bez znaménka);
      ročníky bez snímku u domu jen vypíše („prázdné“). Krajské vrstvy jen v kraji domu a jen roky, které ČÚZK nemá.
      --zapsat skupina   výřezy (vyrezy/, zdroje/) mapa_<skupina>_<klic> a položky v data/mapy.json se zdrojem, rokem,
                         skupinou a výřezem (pole „vyrez“, web prolíná); krajské vrstvy nezapisuje (souhlas kraje).
                         Popis doplň potom (zapis.py mapy <img> … --sloucit).
Šetři server: série = ~30 požadavků. Dům a dvůr: polomer 60–100 m, ves: 300 m. Jedna série na dům stačí.
"""
import json, os, subprocess, sys, typing, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
from platnost import jpeg_rozmery, vyrez_sjtsk  # noqa: E402
import mista  # noqa: E402
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUZK_WMS = "https://geoportal.cuzk.gov.cz/geoserver/wms_ortofoto_archiv/wms"
CUZK_URL = "https://geoportal.cuzk.gov.cz"
VUSC = f"{mista.RUIAN}/17/query"   # vyšší územní samosprávné celky = kraje
PRAZDNY_B_NA_PX = 0.05   # jednobarevný JPEG mimo snímkování má ~0.014 B/px, skutečný snímek 0.15 B/px a víc
# Krajské služby ArcGIS (MapServer/export, S-JTSK): kód kraje RÚIAN → (zkratka, název kraje, {rok: adresa služby})
JC = "https://gis.kraj-jihocesky.cz/arcgis/rest/services/podkladove/orto{}/MapServer"
PK = "https://mapy.kr-plzensky.cz/arcgis/rest/services/PODKLAD/ortofoto{}/MapServer"
JMK = "https://gis.jmk.cz/arcgis/rest/services/Ortofoto_{}/MapServer"
ZK = "https://mapy.kr-zlinsky.cz/arcgis/rest/services/ortofoto_{}/MapServer"
KRAJE = {
    35: ("jc", "Jihočeský kraj", {r: JC.format(r) for r in (2003, 2004, 2008, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025)}),
    43: ("pk", "Plzeňský kraj", {r: PK.format(r) for r in (2005, 2008, 2011)}),
    116: ("jmk", "Jihomoravský kraj", {   # okresní snímkování 1996–2001 (Brno, Znojmo, Hodonín, Blansko a Vyškov, Břeclav)
        1996: JMK.format("Brno_1996"), 1998: JMK.format("Znojmo_1998"), 1999: JMK.format("Hodonin_1999"),
        2000: [JMK.format("Blansko_2000"), JMK.format("Vyskov_2000")], 2001: JMK.format("Breclav_2001"),
        **{r: JMK.format(r) for r in (2003, 2006, 2009, 2012, 2014, 2017, 2018)}}),
    141: ("zk", "Zlínský kraj", {r: ZK.format(r) for r in (2002, 2005, 2008, 2014)}),
}


class Vrstva(typing.NamedTuple):
    rok: int
    zdroj: str
    kraj: typing.Optional[int]   # kód kraje RÚIAN, None = ČÚZK
    adresy: object               # adresa služby, nebo seznam okresních služeb téhož roku


def vrstvy():
    """klíč → Vrstva. ČÚZK první: krajský rok se stahuje jen, když ho ČÚZK u domu nemá."""
    v = {f"cuzk_{r}": Vrstva(r, "ČÚZK, archivní ortofoto ČR", None, CUZK_WMS) for r in range(1998, 2024)}
    for kod, (zkr, nazev, roky) in KRAJE.items():
        v.update({f"{zkr}_{r}": Vrstva(r, f"{nazev}, ortofoto", kod, url) for r, url in roky.items()})
    return v


def get(url, params, binary=False):
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers={"User-Agent": slusne.UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = r.read()
    return d if binary else json.loads(d)


def kraj(lat, lon):
    f = get(VUSC, {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                   "spatialRel": "esriSpatialRelIntersects", "outFields": "kod", "returnGeometry": "false",
                   "f": "json"}).get("features", [])
    return f[0]["attributes"]["kod"] if f else None


def parametry(url, bbox, px):
    obalka = ",".join(f"{v:.1f}" for v in bbox)
    if url == CUZK_WMS:
        return {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "STYLES": "",
                "SRS": "EPSG:5514", "BBOX": obalka, "WIDTH": px, "HEIGHT": px, "FORMAT": "image/jpeg"}
    return {"bbox": obalka, "bboxSR": 5514, "imageSR": 5514, "size": f"{px},{px}", "format": "jpg", "dpi": 96,
            "f": "image"}


class ChybaSluzby(Exception):
    """Služba místo snímku vrátila chybu nebo obrázek jiné velikosti."""


def snimek(d, px):
    """True = snímek, False = prázdný (mimo snímkování), jinak ChybaSluzby."""
    rozmery = jpeg_rozmery(d)
    if rozmery is None:   # WMS i ArcGIS hlásí chybu jako XML, JSON nebo HTML s kódem 200
        raise ChybaSluzby("služba nevrátila obrázek: " + d[:120].decode("utf-8", "replace").replace("\n", " "))
    if rozmery != (px, px):
        raise ChybaSluzby(f"obrázek má {rozmery[0]}×{rozmery[1]} px místo {px}×{px} (zkus menší px)")
    return len(d) >= PRAZDNY_B_NA_PX * px * px


def stahni(v, bbox, px, out):
    """Uloží snímek do out; False = žádná ze služeb roku tu nemá snímek, chyba služby → ChybaSluzby."""
    for url in v.adresy if isinstance(v.adresy, list) else [v.adresy]:
        q = parametry(url, bbox, px)
        if url == CUZK_WMS:
            d = get(url, dict(q, LAYERS=str(v.rok)), binary=True)
        else:
            d = get(url + "/export", q, binary=True)
        if snimek(d, px):
            with open(out + ".part", "wb") as f:
                f.write(d)
            os.replace(out + ".part", out)
            return True
    return False


def citace(v):
    return f"ČÚZK, {v.rok}" if v.kraj is None else f"{v.zdroj} {v.rok}"


def zapsat(hotove, sk, bbox):
    tools = os.path.dirname(os.path.abspath(__file__))
    for k, v, out in hotove:
        if v.kraj is not None:
            print(f"nezapsáno {k}: licence kraje není zveřejněná – jen ke čtení, do výstupu se souhlasem kraje")
            continue
        img = f"mapa_{sk}_{k}"
        subprocess.run([sys.executable, "-I", os.path.join(tools, "vyrez.py"), out, img], check=True,
                       stdout=subprocess.DEVNULL)
        polozka = {"img": img, "rok": str(v.rok), "nazev": "Letecký snímek (ortofoto)", "url": CUZK_URL,
                   "zdroj": f"{citace(v)}, archivní ortofoto ČR (CC BY 4.0)", "popis": "", "skupina": sk,
                   "vyrez": vyrez_sjtsk(bbox)}
        p = subprocess.run([sys.executable, "-I", os.path.join(tools, "zapis.py"), "mapy", img, "-"],
                           input=json.dumps(polozka, ensure_ascii=False), text=True, capture_output=True)
        print(p.stdout.strip() or p.stderr.strip())
        if p.returncode:
            sys.exit(f"Zápis {img} do data/mapy.json selhal – oprav chybu výše a pusť --zapsat znovu.")
    print("Doplň popisy (co je u domu vidět, co přibylo nebo zmizelo): zapis.py mapy <img> vstup.json --sloucit")


def serie(misto, polomer, px, jen=None, skupina=None):
    lat, lon = mista.stred(misto)
    x, y = mista.sjtsk(lat, lon)
    bbox = (x - polomer, y - polomer, x + polomer, y + polomer)
    vse = vrstvy()
    if jen:
        neznam = [k for k in jen if k not in vse]
        if neznam:
            sys.exit(f"Neznámé vrstvy {neznam} – seznam: ortofota.py vrstvy")
    kod_kraje = kraj(lat, lon)
    adr = os.path.join(ROOT, "pracovni", "ortofota")
    os.makedirs(adr, exist_ok=True)
    vyrez = f"r{polomer:g}_{px}px_{abs(x):.0f}_{abs(y):.0f}"   # různé domy a velikosti se nepřepíšou
    hotove, roky, chyby = [], set(), 0
    for k, v in vse.items():
        if (jen and k not in jen) or (v.kraj is not None and (v.kraj != kod_kraje or v.rok in roky)):
            continue
        out = os.path.join(adr, f"{k}_{vyrez}.jpg")
        try:
            ulozeno = stahni(v, bbox, px, out)
        except (ChybaSluzby, OSError) as e:
            print(f"CHYBA   {k:10} {e}")
            chyby += 1
            continue
        if ulozeno:
            print(f"OK      {k:10} {citace(v):34} → {os.path.relpath(out, ROOT)}")
            hotove.append((k, v, out))
            roky.add(v.rok)
        else:
            print(f"prázdné {k:10} (tady se ten rok nesnímkovalo)")
    if skupina:
        zapsat(hotove, skupina, bbox)
    print(f"Výřez S-JTSK (EPSG:5514) {', '.join(f'{v:.1f}' for v in bbox)}, {px}×{px} px – stejný pro všechny snímky.")
    if any(v.kraj is not None for _, v, _ in hotove):
        print("Krajské snímky: licence není zveřejněná – jen ke čtení, do výstupu jen se souhlasem kraje.")
    if chyby:
        sys.exit(f"Nestažené vrstvy: {chyby} (CHYBA výše) – zkus to později.")


def main():
    a = sys.argv[1:]
    if a[:1] == ["vrstvy"]:
        for k, v in vrstvy().items():
            print(f"{k:10} {v.rok}  {v.zdroj}")
        return
    if len(a) < 2 or a[0] != "serie":
        sys.exit(__doc__)
    if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: zápis by šel do skillu
        sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
                 f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
    opt = {}
    for o in ("--jen", "--zapsat"):
        if o in a:
            i = a.index(o)
            opt[o] = a[i + 1]
            a = a[:i] + a[i + 2:]
    serie(a[1], float(a[2]) if len(a) > 2 else 100, int(a[3]) if len(a) > 3 else 1200,
          opt["--jen"].split(",") if "--jen" in opt else None, opt.get("--zapsat"))


if __name__ == "__main__":
    main()
