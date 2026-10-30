#!/usr/bin/env python3
"""Místa pro mapu na webu: okolní body (kaple, mlýn, hamr, sousední ves) v data/mista.json a poloha domů.

Použití:
  mista.py hledej "dotaz"
      vypíše souřadnice z OpenStreetMap – pro dům zkus "Horní Lhota 12, Pelhřimov" (čísla domů OSM většinou zná),
      pro obec "Horní Lhota, Pelhřimov". Výsledek zapiš do data/domy.py (lat/lon u domu nebo v OBEC) nástrojem
      pro úpravu souborů. Když OSM dům nezná, vezmi polohu z mapy (mapy.cz → pravé tlačítko → souřadnice).
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
OUT = os.path.join(ROOT, "data", "mista.json")


def geocode(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "dejiny-domu-skill/1.0 (local history map, occasional geocoding)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    time.sleep(1.1)
    return (round(float(res[0]["lat"]), 5), round(float(res[0]["lon"]), 5), res[0]["display_name"]) if res else None


def main():
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
