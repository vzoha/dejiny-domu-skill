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
      co uživatel čeká (osada patří k jiné obci, k. ú. má jméno sousední vsi). Dotaz = "Osada čp" nebo "Ulice čp".
  mista.py pridej "Název" ["dotaz pro vyhledání"] ["popis na mapě"]
      přidá bod do data/mista.json (výchozí dotaz = "Název, Česko")
  mista.py
      dohledá souřadnice u míst, která je ještě nemají (OpenStreetMap Nominatim, 1 dotaz za sekundu),
      a vypíše seznam. Když bod nesedí, opravte lat/lon v data/mista.json ručně.
"""
import json, os, sys, time, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu → zapisovalo by do skillu
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


def ruian(dotaz):
    adr = ruian_q(1, f"adresa LIKE '{dotaz.replace(chr(39), '')},%'", "adresa,stavebniobjekt", True)
    if not adr:
        sys.exit(f"RÚIAN „{dotaz}“ nezná – zkus jiný tvar (\"Osada čp\", \"Ulice čp\") nebo jen \"Osada\" v nahlizenidokn.cuzk.cz")
    for a in adr[:5]:
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


def main():
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
