#!/usr/bin/env python3
"""Pohlednice z AKON (Ansichtskarten Online, Rakouská národní knihovna) 1896–1925: celá monarchie, Čechy, Morava, Slezsko.

Prohledává otevřená data ÖNB Labs (34 846 pohlednic ve volném díle, z Česka asi 1 700, hlavně města a lázně):
podle polohy (pohlednice do --km od středu obce podle RÚIAN) i podle názvu (AKON píše hlavně německy).
Plný AKON má asi dvakrát víc pohlednic, ale jen jako mapovou aplikaci: nástroj vypíše odkaz na mapu u obce
(ty v otevřených datech nejsou, obrázek jen se souhlasem ÖNB).

Použití:
  akon.py "<obec>" [od-do] [--km 3]   – id | rok | název | vzdálenost | vydavatel | odkaz
  akon.py <šířka,délka> [od-do] [--km 3]
  akon.py detail <id>                 – vše o pohlednici, obrázek a citace
Data (2 MB) stáhne poprvé do ~/.cache/dejiny-domu/akon/ a obnoví po půl roce.
Obrázky jsou volné dílo (Public Domain Mark), smí i do placeného výstupu s citací."""
import argparse, csv, io, math, os, re, sys, time, urllib.request, zipfile
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)
from nazvy import zminuje_obec   # porovnání názvů obcí (nazvy.py)

DATA = "https://labs.onb.ac.at/gitlab/labs-team/raw-metadata/raw/master/akon_postcards_public_domain.zip?inline=false"
SOUBOR = "akon_postcards_public_domain.csv"
PLATNOST = 180 * 24 * 3600
ODKAZ = "http://data.onb.ac.at/AKON/{}"         # trvalý odkaz ÖNB, vede na detail v AKON
MAPA = "https://akon.onb.ac.at/#center={}&zoom=13"
VYCHOZI_KM = 3
GEOHASH = "0123456789bcdefghjkmnpqrstuvwxyz"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "dejiny-domu", "akon")
POLOHA = re.compile(r"\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*")   # „šířka,délka“


def nacti_data():
    """Řádky CSV otevřených dat; stáhne je, když chybí nebo jsou starší než PLATNOST."""
    cesta = os.path.join(CACHE, SOUBOR)
    if not os.path.exists(cesta) or time.time() - os.path.getmtime(cesta) > PLATNOST:
        os.makedirs(CACHE, exist_ok=True)
        print("Stahuji otevřená data AKON (2 MB, jednou za půl roku)…", file=sys.stderr)
        with urllib.request.urlopen(DATA, timeout=120) as r:
            obsah = zipfile.ZipFile(io.BytesIO(r.read())).read(SOUBOR)
        with open(cesta + ".tmp", "wb") as f:
            f.write(obsah)
        os.replace(cesta + ".tmp", cesta)
    with open(cesta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def geohash(lat, lon, delka=12):
    """Geohash pro odkaz na mapu AKON (#center=…)."""
    rozsahy, znaky, bity, sudy = [[-90.0, 90.0], [-180.0, 180.0]], "", [], True
    while len(znaky) < delka:
        rozsah, hodnota = (rozsahy[1], lon) if sudy else (rozsahy[0], lat)
        stred = sum(rozsah) / 2
        bity.append(hodnota > stred)
        rozsah[0 if hodnota > stred else 1] = stred
        sudy = not sudy
        if len(bity) == 5:
            znaky += GEOHASH[int("".join("1" if b else "0" for b in bity), 2)]
            bity = []
    return znaky


def km(lat, lon, lat2, lon2):
    return math.hypot((lon2 - lon) * 111.32 * math.cos(math.radians(lat)), (lat2 - lat) * 111.32)


def rok(k):
    """Rok vydání nebo odeslání: pole year, jinak první čtyřčíslí v date/comment („gelaufen 1905“, „v. 1907“)."""
    if k.get("year"):
        return int(float(k["year"]))
    m = re.search(r"\b(1[89]\d\d)\b", (k.get("date") or "") + " " + (k.get("comment") or ""))
    return int(m.group(1)) if m else None


def datace(k):
    """„gelaufen 1905“ → „odesláno 1905“, „vor 1907“ → „před 1907“."""
    d = k.get("date") or k.get("comment") or str(rok(k) or "")
    return re.sub(r"\bv(or)?\.? ", "před ", re.sub(r"\bgel(aufen)?\b", "odesláno", d)).strip()


def poloha(k):
    try:
        return float(k["latitude"]), float(k["longitude"])
    except (KeyError, TypeError, ValueError):
        return None


def najdi(karty, lat=None, lon=None, obec=None, polomer=VYCHOZI_KM, roky=None):
    """[(vzdálenost km nebo None, karta)]: v okruhu polomer km od středu nebo s obcí v názvu, seřazené podle vzdálenosti a roku."""
    nalez = []
    for k in karty:
        r = rok(k)
        if roky and not (r and roky[0] <= r <= roky[1]):
            continue
        p = poloha(k)
        vzdalenost = km(lat, lon, *p) if p and lat is not None else None
        v_okruhu = vzdalenost is not None and vzdalenost <= polomer
        if v_okruhu or (obec and any(zminuje_obec(k.get(pole), obec) for pole in ("city", "name", "building", "other"))):
            nalez.append((vzdalenost, k))
    return sorted(nalez, key=lambda x: (x[0] if x[0] is not None else 1e9, rok(x[1]) or 0))


def nazev(k):
    return (k.get("city") or k.get("name") or "").strip()


def radek(vzdalenost, k):
    casti = [k["akon_id"], datace(k), nazev(k),
             f"{vzdalenost:.1f} km" if vzdalenost is not None else "", k.get("publisher") or "", ODKAZ.format(k["akon_id"])]
    return "  " + " | ".join(c for c in casti if c)


def citace(k):
    return (f"Österreichische Nationalbibliothek, AKON, {k['akon_id']}, {nazev(k)}, "
            f"{datace(k) or 'nedatováno'}, {ODKAZ.format(k['akon_id'])}")


def detail(karty, id_karty):
    k = next((k for k in karty if k["akon_id"].lower() == id_karty.lower()), None)
    if not k:
        sys.exit(f"Pohlednice {id_karty} v otevřených datech AKON není (plný AKON: {ODKAZ.format(id_karty)}).")
    p = poloha(k)
    radky = [("Název", nazev(k)), ("Datace", datace(k)), ("Místo podle GeoNames", k.get("name")),
             ("Poloha", f"{p[0]:.5f},{p[1]:.5f}" if p else ""), ("Budova", k.get("building")), ("Hora", k.get("mountain")),
             ("Voda", k.get("water_body")), ("Kraj", k.get("region") or k.get("admin_name_1")), ("Další", k.get("other")),
             ("Fotograf", k.get("photographer")), ("Vydavatel", " ".join(x for x in (k.get("publisher"), k.get("publisher_place")) if x)),
             ("Barevná", "ano" if k.get("color") == "True" else "ne"), ("Signatura", k.get("signature")),
             ("Inv. č.", k.get("inventory_number")), ("Odkaz", ODKAZ.format(k["akon_id"])),
             ("Obrázek", k.get("download_link")), ("Citace", citace(k)),
             ("Obrázek do výstupu", "ano, volné dílo (Public Domain Mark), s citací")]
    return [f"{n}: {v}" for n, v in radky if v]


def stred(misto):
    """(lat, lon, popis) z „šířka,délka“ nebo z názvu obce či části obce v RÚIAN; obec mimo RÚIAN → (None, None, None)."""
    if POLOHA.fullmatch(misto):
        lat, lon = (float(x) for x in misto.split(","))
        return lat, lon, misto
    import mista   # střed obce z RÚIAN; jen v projektu (mista.py jinde skončí)
    obce = mista.obec_stred(misto)
    if len(obce) > 1:
        sys.exit(f"RÚIAN má {len(obce)} obcí nebo částí jménem „{misto}“ – vyber podle PSČ a zadej šířka,délka:\n"
                 + "\n".join(f"  {n}   {y:.5f},{x:.5f}" for n, y, x in obce))
    if obce:
        popis, lat, lon = obce[0]
        return lat, lon, popis
    return None, None, None


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        if len(argv) < 3:
            sys.exit("Použití: akon.py detail <id> (např. AK111_293)")
        print("\n".join(detail(nacti_data(), argv[2])))
        return
    p = argparse.ArgumentParser(prog="akon.py", usage=__doc__)
    p.add_argument("misto")
    p.add_argument("roky", nargs="?")
    p.add_argument("--km", type=float, default=VYCHOZI_KM)
    a = p.parse_args(argv[1:])
    misto, polomer = a.misto, a.km
    roky = tuple(int(x) for x in a.roky.split("-")) if a.roky else None
    lat, lon, popis = stred(misto)
    obec = None if POLOHA.fullmatch(misto) else misto
    nalez = najdi(nacti_data(), lat, lon, obec, polomer, roky)
    if popis:
        print(f"Střed: {popis} ({lat:.5f},{lon:.5f}), okruh {polomer:g} km.")
    else:
        print(f"RÚIAN „{misto}“ nezná, hledám jen podle názvu.")
    if nalez:
        print(f"Pohlednice ve volném díle (otevřená data AKON): {len(nalez)}")
        print("\n".join(radek(v, k) for v, k in nalez))
    else:
        print("V otevřených datech AKON nic. Jsou v nich hlavně města a lázně; zkus německý název obce nebo větší --km.")
    if lat is not None:
        print(f"\nPlný AKON (asi 2× víc pohlednic) na mapě u obce: {MAPA.format(geohash(lat, lon))}\n"
              "Pohlednice jen z mapy nejsou v otevřených datech: obrázek do výstupu jen se souhlasem ÖNB, jinak popis a odkaz.")
    print("Obrázky jsou volné dílo: smí do výstupu s citací (akon.py detail <id>). Pohlednice ukáže obec,"
          " ne konkrétní dům – dům na ní ověř mapou.")


if __name__ == "__main__":
    main(sys.argv)
