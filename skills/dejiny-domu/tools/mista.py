#!/usr/bin/env python3
"""Místa pro mapu na webu: okolní body (kaple, mlýn, hamr, sousední ves) v data/mista.json a poloha domů.

Použití:
  mista.py hledej "dotaz"
      vypíše souřadnice z OpenStreetMap – pro dům zkus "Horní Lhota 12, Pelhřimov" (čísla domů OSM většinou zná),
      pro obec "Horní Lhota, Pelhřimov". Výsledek zapiš do data/domy.py (lat/lon u domu nebo v OBEC) nástrojem
      pro úpravu souborů. Když OSM dům nezná, vezmi polohu z mapy (mapy.cz → pravé tlačítko → souřadnice).
  mista.py ruian "Horní Lhota 12"
      dům podle RÚIAN (ČÚZK, bez klíče; najde i malé osady, které OSM nezná): adresa s dnešní obcí, lat/lon,
      parcela pod domem a katastrální území. Patří do Fáze 0/1 – dnešní obec a k. ú. se často liší od toho,
      co uživatel čeká (osada patří k jiné obci, k. ú. má jméno sousední vsi). Dotaz = "Osada čp", "Ulice čp",
      "Ulice čp/čo" nebo ve městě i "Ulice čo" (číslo orientační, jak je na domě).
  mista.py okoli <"Ulice čp/čo" | lat,lon> [polomer_m=80]
  mista.py parcely <"Osada čp" | lat,lon> [polomer_m=60] [vse]
      dnešní stavební parcely kolem domu s odstupem v metrech (E/N = na východ/sever). Podle nich najdeš dům
      na staré mapě (stejná čísla stavebních parcel). „vse“ = i pozemkové parcely.
      všechny dnešní adresy v okolí (RÚIAN) seřazené podle čp. – rohové domy mají dvě adresy; podklad pro tabulku
      adres domu v čase a pro rozlišení domů se stejnou starou adresou (reference/prameny.md → Čísla domů).
  mista.py pridej "Název" ["dotaz pro vyhledání"] ["popis na mapě"]
      přidá bod do data/mista.json (výchozí dotaz = "Název, Česko")
  mista.py
      dohledá souřadnice u míst, která je ještě nemají (OpenStreetMap Nominatim, 1 dotaz za sekundu),
      a vypíše seznam. Když bod nesedí, opravte lat/lon v data/mista.json ručně.
"""
import json, math, os, sys, time, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: data projektu tam nejsou, zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
OUT = os.path.join(ROOT, "data", "mista.json")


def geocode(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "dejiny-domu-skill/1.0 (local history map, occasional geocoding)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    time.sleep(1.1)
    return (round(float(res[0]["lat"]), 5), round(float(res[0]["lon"]), 5), res[0]["display_name"]) if res else None


RUIAN = "https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Prohlizeci_sluzba_nad_daty_RUIAN/MapServer"


def ruian_q(vrstva, where, pole, geo=False):
    q = urllib.parse.urlencode({"where": where, "outFields": pole, "returnGeometry": str(geo).lower(),
                                "outSR": 4326, "f": "json"})
    with urllib.request.urlopen(f"{RUIAN}/{vrstva}/query?{q}", timeout=60) as r:
        return json.load(r).get("features", [])


def adresni_mista(dotaz, pole):
    """Adresní místa RÚIAN pro „Osada čp“, „Ulice čp“, „Ulice čp/čo“ i „Ulice čo“."""
    d = dotaz.replace(chr(39), "")
    ulice, _, cislo = d.rpartition(" ")
    dotazy = [f"adresa LIKE '{d},%'"]
    if ulice and cislo.isdigit():
        dotazy += [f"adresa LIKE '{ulice} %/{cislo},%'",   # „Ulice čo“ – v RÚIAN je „Ulice čp/čo, Část obce, …“
                   # obec bez ulic: „č.p. 29, 39301 Pavlov“; osada pod jinou obcí: „Švihov 47, 53825 Miřetice“
                   f"adresa LIKE 'č.p. {cislo}, % {ulice}'", f"adresa LIKE 'č.p. {cislo}, % {ulice},%'"]
    adr, videno = [], set()
    for q in dotazy:   # všechny tvary, ne jen první: „Hlína 1, Horka“ i „č.p. 1, 66491 Hlína“ jsou různé vsi
        for a in ruian_q(1, q, pole, True):
            if a["attributes"].get("adresa", id(a)) not in videno:
                videno.add(a["attributes"].get("adresa", id(a)))
                adr.append(a)
    if not adr and ulice and cislo.isdigit():
        adr = ruian_q(1, f"adresa LIKE '%{ulice} {cislo}, %'", pole, True)
    return adr


def ruian(dotaz):
    adr = adresni_mista(dotaz, "adresa,stavebniobjekt")
    if not adr:
        sys.exit(f"RÚIAN „{dotaz}“ nezná – zkus jiný tvar (\"Osada čp\", \"Ulice čp\") nebo jen \"Osada\" v nahlizenidokn.cuzk.cz")
    if len(adr) > 1:
        print(f"POZOR: {len(adr)} míst se stejnou adresou – vyber podle PSČ a okresu ze zadání (fara, panství, archiv)")
    for a in adr[:8]:
        at, g = a["attributes"], a["geometry"]
        print(f"{at['adresa']}   lat={g['y']:.5f}, lon={g['x']:.5f}")
        so = ruian_q(3, f"kod={at['stavebniobjekt']}", "identifikacniparcela")
        if not so or not so[0]["attributes"].get("identifikacniparcela"):
            continue
        par = ruian_q(5, f"id={int(so[0]['attributes']['identifikacniparcela'])}",
                      "kmenovecislo,poddelenicisla,druhcislovanikod,katastralniuzemi")
        if par:
            pa = par[0]["attributes"]
            cislo = f"{pa['kmenovecislo']}" + (f"/{pa['poddelenicisla']}" if pa.get("poddelenicisla") else "")
            ku = ruian_q(7, f"kod={pa['katastralniuzemi']}", "nazev")
            print(f"   parcela {'st. ' if pa.get('druhcislovanikod') == 1 else ''}{cislo}, "
                  f"k. ú. {ku[0]['attributes']['nazev'] if ku else '?'} ({pa['katastralniuzemi']})")


def okoli(misto, polomer=80):
    if "," in misto and all(c in "0123456789., -" for c in misto):
        lat, lon = (float(v) for v in misto.split(","))
    else:
        f = adresni_mista(misto, "adresa")
        if not f:
            sys.exit(f"RÚIAN „{misto}“ nezná – zadej „Ulice čp/čo“ nebo lat,lon.")
        lat, lon = f[0]["geometry"]["y"], f[0]["geometry"]["x"]
        print("střed:", f[0]["attributes"]["adresa"]
              + (f"  (POZOR: {len(f)} míst se stejnou adresou, jiné zadej jako lat,lon z mista.py ruian)" if len(f) > 1 else ""))
    dlat = polomer / 111320
    dlon = dlat / math.cos(math.radians(lat))
    q = urllib.parse.urlencode({"geometry": f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}",
                                "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                                "outFields": "adresa", "returnGeometry": "true", "outSR": 4326, "f": "json"})
    with urllib.request.urlopen(f"{RUIAN}/1/query?{q}", timeout=60) as r:
        feats = json.load(r).get("features", [])

    def cislo_popisne(adresa):   # „Ulice 12/3, Obec, …“ → 12
        c = adresa.split(",")[0].rsplit(" ", 1)[-1].split("/")[0]
        return int(c) if c.isdigit() else 0

    def metry(g):
        return round(math.hypot((g["y"] - lat) * 111320, (g["x"] - lon) * 111320 * math.cos(math.radians(lat))))
    rows = sorted((cislo_popisne(f["attributes"]["adresa"]), f["attributes"]["adresa"].split(",")[0], metry(f["geometry"]))
                  for f in feats)
    for c, a, m in rows:
        print(f"čp. {c:<6} {a:40} {m:>4} m")
    print(f"{len(rows)} adres do {polomer:g} m. Stejné čp. dvakrát = rohový dům se dvěma adresami.")


def parcely(misto, polomer=60, vse=False):
    if "," in misto and all(c in "0123456789., -" for c in misto):
        lat, lon = (float(v) for v in misto.split(","))
    else:
        f = adresni_mista(misto, "adresa")
        if not f:
            sys.exit(f"RÚIAN „{misto}“ nezná – zadej lat,lon.")
        lat, lon = f[0]["geometry"]["y"], f[0]["geometry"]["x"]
        print("střed:", f[0]["attributes"]["adresa"]
              + (f"  (POZOR: {len(f)} míst se stejnou adresou, jiné zadej jako lat,lon z mista.py ruian)" if len(f) > 1 else ""))
    dlat = polomer / 111320
    dlon = dlat / math.cos(math.radians(lat))
    q = {"geometry": f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}", "geometryType": "esriGeometryEnvelope",
         "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "kmenovecislo,poddelenicisla,druhcislovanikod,vymeraparcely",
         "returnGeometry": "true", "outSR": 4326, "f": "json"}
    if not vse:
        q["where"] = "druhcislovanikod=1"
    with urllib.request.urlopen(f"{RUIAN}/5/query?{urllib.parse.urlencode(q)}", timeout=60) as r:
        feats = json.load(r).get("features", [])
    rows = []
    for f in feats:
        a, ring = f["attributes"], f["geometry"]["rings"][0]
        cy, cx = sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)
        cislo = f"{a['kmenovecislo']}" + (f"/{a['poddelenicisla']}" if a.get("poddelenicisla") else "")
        rows.append((a["druhcislovanikod"] != 1, a["kmenovecislo"], ("st. " if a["druhcislovanikod"] == 1 else "") + cislo,
                     a.get("vymeraparcely"), round((cx - lon) * 111320 * math.cos(math.radians(lat))), round((cy - lat) * 111320)))
    for _, _, c, v, e, n in sorted(rows):
        print(f"{c:12} {v or 0:>7.0f} m²   E {e:>4} m  N {n:>4} m")
    print(f"{len(rows)} parcel do {polomer:g} m od středu. Nízká čísla stavebních parcel = starší zástavba.")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "parcely":
        parcely(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "vse" else 60, "vse" in sys.argv[3:])
        return
    if len(sys.argv) > 2 and sys.argv[1] == "okoli":
        okoli(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 80)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "ruian":
        ruian(sys.argv[2])
        return
    if len(sys.argv) > 2 and sys.argv[1] == "hledej":
        g = geocode(sys.argv[2])
        print(f"lat={g[0]}, lon={g[1]}   {g[2]}" if g else "NENALEZENO – zkus jiný dotaz nebo polohu z mapy")
        return
    cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    if len(sys.argv) > 2 and sys.argv[1] == "pridej":
        name = sys.argv[2]
        cache[name] = dict(cache.get(name, {}), dotaz=sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else f"{name}, Česko")
        if len(sys.argv) > 4:
            cache[name]["popis"] = sys.argv[4]
    for name, e in cache.items():
        if "lat" not in e:
            g = geocode(e.get("dotaz") or f"{name}, Česko")
            if g:
                e["lat"], e["lon"], e["osm"] = g
            else:
                print("NENALEZENO:", name, "– upravte 'dotaz' nebo doplňte lat/lon ručně")
    json.dump(cache, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    for n, e in cache.items():
        print(f"{n:28} {e.get('lat', '?'):>8} {e.get('lon', '?'):>8}  {e.get('osm', '')[:70]}")


if __name__ == "__main__":
    main()
