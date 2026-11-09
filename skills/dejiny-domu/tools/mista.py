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
      "Ulice čp/čo" nebo ve městě i "Ulice čo" (číslo orientační, jak je na domě); obec za čárkou zúží výběr
      ("Husova 66, Beroun", "Na Kopečku 4, Praha").
  mista.py okoli <"Ulice čp/čo" | lat,lon> [polomer_m=80]
      všechny dnešní adresy v okolí (RÚIAN) seřazené podle čp., do poloměru; adresy jedné budovy (roh) označí; podklad pro tabulku
      adres domu v čase a pro rozlišení domů se stejnou starou adresou (reference/prameny.md → Čísla domů).
  mista.py parcely <"Osada čp" | lat,lon> [polomer_m=60] [vse]
      dnešní stavební parcely kolem domu s odstupem v metrech (E/N = na východ/sever). Podle nich najdeš dům
      na staré mapě (stejná čísla stavebních parcel). V k. ú. s jednou číselnou řadou (bez „st.“) vypíše parcely
      se zastavěnou plochou. „vse“ = i ostatní pozemkové parcely.
  mista.py pridej "Název" ["dotaz pro vyhledání"] ["popis na mapě"]
      přidá bod do data/mista.json (výchozí dotaz = "Název, Česko")
  mista.py
      dohledá souřadnice u míst, která je ještě nemají (OpenStreetMap Nominatim, 1 dotaz za sekundu),
      a vypíše seznam. Když bod nesedí, opravte lat/lon v data/mista.json ručně.
"""
import json, math, os, re, statistics, sys, time, urllib.parse, urllib.request
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
    req = urllib.request.Request(url, headers={"User-Agent": slusne.UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    time.sleep(1.1)
    return (round(float(res[0]["lat"]), 5), round(float(res[0]["lon"]), 5), res[0]["display_name"]) if res else None


RUIAN = "https://ags.cuzk.cz/arcgis/rest/services/RUIAN/Prohlizeci_sluzba_nad_daty_RUIAN/MapServer"
GEOMETRIE = "https://ags.cuzk.gov.cz/arcgis/rest/services/Utilities/Geometry/GeometryServer/project"
STAVEBNI = 1            # druhcislovanikod: 1 stavební, 2 pozemková parcela
ZASTAVENA_PLOCHA = 13   # druhpozemkukod „zastavěná plocha a nádvoří“


def cislo_parcely(a):
    """„st. 12/3“; k. ú. s jednou číselnou řadou stavební parcely nemá, „st.“ tam správně chybí."""
    cislo = f"{a['kmenovecislo']}" + (f"/{a['poddelenicisla']}" if a.get("poddelenicisla") else "")
    return ("st. " if a.get("druhcislovanikod") == STAVEBNI else "") + cislo


def sjtsk(lat, lon):
    """WGS 84 → S-JTSK (m) přes geometrickou službu ČÚZK. Bez transformace datumu 1623 by bod ujel o ~10 m."""
    g = json.dumps({"geometryType": "esriGeometryPoint", "geometries": [{"x": lon, "y": lat}]})
    q = urllib.parse.urlencode({"inSR": 4326, "outSR": 5514, "geometries": g, "f": "json",
                                "transformation": 1623, "transformForward": "false"})
    with urllib.request.urlopen(f"{GEOMETRIE}?{q}", timeout=60) as r:
        p = json.load(r)["geometries"][0]
    return p["x"], p["y"]


def ruian_q(vrstva, where, pole, geo=False):
    q = urllib.parse.urlencode({"where": where, "outFields": pole, "returnGeometry": str(geo).lower(),
                                "outSR": 4326, "f": "json"})
    with urllib.request.urlopen(f"{RUIAN}/{vrstva}/query?{q}", timeout=60) as r:
        return json.load(r).get("features", [])


def adresni_mista(dotaz, pole, obec=""):
    """Adresní místa RÚIAN pro „Osada čp“, „Ulice čp“, „Ulice čp/čo“ i „Ulice čo“, jen v obci „obec“ (je-li zadaná).
    Velikost písmen RÚIAN rozlišuje („Na kopečku“) – bez nálezu hledá znovu bez ní (pomalé, ~7 s na dotaz)."""
    d = dotaz.replace(chr(39), "")
    ulice, _, cislo = d.rpartition(" ")
    vzory = [f"{d},%"]
    if ulice and cislo.isdigit():
        vzory += [f"{ulice} %/{cislo},%",   # „Ulice čo“ – v RÚIAN je „Ulice čp/čo, Část obce, …“
                  # obec bez ulic: „č.p. 29, 39301 Pavlov“; osada pod jinou obcí: „Švihov 47, 53825 Miřetice“
                  f"č.p. {cislo}, % {ulice}", f"č.p. {cislo}, % {ulice},%"]
    for podminka in ("adresa LIKE '{}'", "UPPER(adresa) LIKE UPPER('{}')"):
        adr, videno = [], set()
        for vzor in vzory:   # všechny tvary, ne jen první: „Hlína 1, Horka“ i „č.p. 1, 66491 Hlína“ jsou různé vsi
            for a in ruian_q(1, podminka.format(vzor), pole, True):
                if a["attributes"].get("adresa", id(a)) not in videno:
                    videno.add(a["attributes"].get("adresa", id(a)))
                    adr.append(a)
        if not adr and ulice and cislo.isdigit():
            adr = ruian_q(1, podminka.format(f"%{ulice} {cislo}, %"), pole, True)
        adr = [a for a in adr if not obec or v_obci(a["attributes"]["adresa"], obec)]
        if adr:
            return adr
    return []


def adresa_a_obec(misto):
    """„Ulice čp, Obec“ → („Ulice čp“, „Obec“); bez čárky obec prázdná."""
    dotaz, _, obec = misto.partition(",")
    return dotaz.strip(), obec.strip()


def ruian(dotaz):
    ulice_cislo, obec = adresa_a_obec(dotaz)
    adr = adresni_mista(ulice_cislo, "adresa,stavebniobjekt", obec)
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
            ku = ruian_q(7, f"kod={pa['katastralniuzemi']}", "nazev")
            print(f"   parcela {cislo_parcely(pa)}, "
                  f"k. ú. {ku[0]['attributes']['nazev'] if ku else '?'} ({pa['katastralniuzemi']})")


SOUSEDNI_PSC_M = 12000   # PSČ jedné obce (Blíževedly 47104 a 47002, Opava 5 PSČ) mají středy blíž, stejnojmenné obce dál


def obec_stred(nazev):
    """Obce a části obce jménem „nazev“ → [(„Část, PSČ Obec“, lat, lon)], střed = medián jejich adresních bodů RÚIAN.
    Adresa v RÚIAN: „Ulice čp, [Část, ]PSČ Obec“ nebo „Část čp, PSČ Obec“ (část bez ulic)."""
    n = nazev.replace(chr(39), "").strip()
    body = {}
    for a in ruian_q(1, f"adresa LIKE '% {n}' OR adresa LIKE '%, {n}, %' OR adresa LIKE '{n} %'", "adresa", True):
        if not a.get("geometry"):   # pár adresních míst RÚIAN nemá polohu
            continue
        casti = a["attributes"]["adresa"].split(", ")
        psc, _, obec = casti[-1].partition(" ")
        if obec == n or (len(casti) > 2 and casti[-2] == n) or re.fullmatch(rf"{re.escape(n)} \d+[a-z]?", casti[0]):
            body.setdefault((obec, psc), []).append((a["geometry"]["y"], a["geometry"]["x"]))
    skupiny = []   # [obec, [PSČ], body]
    for (obec, psc), b in sorted(body.items()):
        stejna = next((g for g in skupiny if g[0] == obec and math.hypot(*odstup(*median(g[2]), *median(b))) < SOUSEDNI_PSC_M), None)
        if stejna:
            stejna[1].append(psc)
            stejna[2] += b
        else:
            skupiny.append([obec, [psc], b])
    return [(f"{n}, {'/'.join(pscs)} {obec}", *median(b)) for obec, pscs, b in skupiny]


POLOHA = re.compile(r"\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*")   # „šířka,délka“


def obec_nebo_poloha(misto):
    """(lat, lon, popis) z „šířka,délka“, z adresy („Ulice čp, Obec“, „Osada čp“) nebo z názvu obce či části obce
    v RÚIAN; místo mimo RÚIAN → (None, None, None). Víc stejnojmenných obcí nebo adres = skončí se seznamem,
    ať se nevybere náhodná."""
    if POLOHA.fullmatch(misto):
        lat, lon = (float(x) for x in misto.split(","))
        return lat, lon, misto
    if re.search(r"\d", misto):   # adresa domu, ne obec
        dotaz, obec = adresa_a_obec(misto)
        adresy = [a for a in adresni_mista(dotaz, "adresa", obec) if a.get("geometry")]
        if len(adresy) > 1:
            sys.exit(f"RÚIAN má {len(adresy)} míst s adresou „{misto}“ – zadej „{dotaz}, Obec“ nebo šířka,délka:\n"
                     + "\n".join(f"  {a['attributes']['adresa']}   {a['geometry']['y']:.5f},{a['geometry']['x']:.5f}" for a in adresy))
        if adresy:
            return adresy[0]["geometry"]["y"], adresy[0]["geometry"]["x"], adresy[0]["attributes"]["adresa"]
    obce = obec_stred(misto)
    if len(obce) > 1:
        sys.exit(f"RÚIAN má {len(obce)} obcí nebo částí jménem „{misto}“ – vyber podle PSČ a zadej šířka,délka:\n"
                 + "\n".join(f"  {n}   {y:.5f},{x:.5f}" for n, y, x in obce))
    if obce:
        popis, lat, lon = obce[0]
        return lat, lon, popis
    return None, None, None


def median(body):
    return statistics.median(y for y, _ in body), statistics.median(x for _, x in body)


def patri_k_nazvu(cast, obec):
    """„Praha 8“, „Beroun-Zavadilka“ i „Beroun“ patří k obci „Praha“ / „Beroun“, „Bílá Hlína“ k „Hlína“ ne."""
    cast, obec = cast.lower(), obec.lower()
    return cast == obec or cast.startswith((obec + " ", obec + "-"))


def v_obci(adresa, obec):
    """Leží adresa („Ulice čp, [Část, ]PSČ Obec“ nebo „Osada čp, PSČ Obec“) v obci nebo části „obec“?
    Porovnává celé části adresy, ne podřetězec."""
    prvni, *dalsi = adresa.split(", ")
    casti = [re.sub(r" [\d/]+[a-z]?$", "", prvni)] + [re.sub(r"^\d{5} ", "", c) for c in dalsi]
    return any(patri_k_nazvu(c, obec) for c in casti)


def stred(misto):
    """lat, lon z „lat,lon“, z jediné adresy RÚIAN („Ulice čp“, „Ulice čp, Obec“), nebo z názvu obce či části obce
    (střed jejích adresních bodů). Víc míst se stejnou adresou nebo stejnojmenných obcí = skončí, ať se nevybere náhodné."""
    if "," in misto and all(c in "0123456789., -" for c in misto):
        return tuple(float(v) for v in misto.split(","))
    dotaz, obec = adresa_a_obec(misto)
    f = [a for a in adresni_mista(dotaz, "adresa", obec) if a.get("geometry")]
    if not f and not obec and not misto.rstrip()[-1:].isdigit():
        obce = obec_stred(misto)
        if len(obce) > 1:
            sys.exit(f"RÚIAN má {len(obce)} obcí nebo částí jménem „{misto}“ – vyber podle PSČ a okresu a zadej lat,lon:\n"
                     + "\n".join(f"  {k}   {y:.5f},{x:.5f}" for k, y, x in obce))
        if obce:
            nazev, lat, lon = obce[0]
            print("střed obce:", nazev)
            return lat, lon
    if not f:
        sys.exit(f"RÚIAN „{misto}“ nezná – zadej „Ulice čp/čo“, „Ulice čp, Obec“, název obce nebo lat,lon.")
    if len(f) > 1:
        sys.exit(f"RÚIAN má {len(f)} míst s adresou „{misto}“ – vyber podle PSČ a okresu a zadej ho jako lat,lon\n"
                 f"nebo „{dotaz}, Obec“:\n"
                 + "\n".join(f"  {a['attributes']['adresa']}   {a['geometry']['y']:.5f},{a['geometry']['x']:.5f}" for a in f))
    print("střed:", f[0]["attributes"]["adresa"])
    return f[0]["geometry"]["y"], f[0]["geometry"]["x"]


def v_obdelniku(vrstva, lat, lon, polomer, dotaz):
    """Prvky vrstvy RÚIAN v obdélníku kolem středu. Obdélník je větší než kruh – vzdálenost filtruje volající."""
    dlat = polomer / 111320
    dlon = dlat / math.cos(math.radians(lat))
    q = {"geometry": f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}", "geometryType": "esriGeometryEnvelope",
         "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "returnGeometry": "true", "outSR": 4326, "f": "json", **dotaz}
    with urllib.request.urlopen(f"{RUIAN}/{vrstva}/query?{urllib.parse.urlencode(q)}", timeout=60) as r:
        res = json.load(r)
    if res.get("exceededTransferLimit"):
        print(f"POZOR: služba vrátila jen prvních {len(res.get('features', []))} prvků – zmenši poloměr")
    return res.get("features", [])


def odstup(lat, lon, lat2, lon2):
    """(na východ, na sever) v metrech."""
    return round((lon2 - lon) * 111320 * math.cos(math.radians(lat))), round((lat2 - lat) * 111320)


def okoli(misto, polomer=80):
    lat, lon = stred(misto)
    feats = v_obdelniku(1, lat, lon, polomer, {"outFields": "adresa,stavebniobjekt"})

    def cislo_popisne(adresa):   # „Ulice 12/3, Obec, …“ → 12
        c = adresa.split(",")[0].rsplit(" ", 1)[-1].split("/")[0]
        return int(c) if c.isdigit() else 0
    rows = []
    for f in feats:
        m = round(math.hypot(*odstup(lat, lon, f["geometry"]["y"], f["geometry"]["x"])))
        if m <= polomer:
            a = f["attributes"]
            rows.append((cislo_popisne(a["adresa"]), a["adresa"].split(",")[0], m, a.get("stavebniobjekt")))
    adres_budovy = {}
    for *_, so in rows:
        adres_budovy[so] = adres_budovy.get(so, 0) + 1
    for c, a, m, so in sorted(rows):
        print(f"čp. {c:<6} {a:40} {m:>4} m" + ("   ← víc adres jedné budovy" if so and adres_budovy[so] > 1 else ""))
    print(f"{len(rows)} adres do {polomer:g} m. „Víc adres jedné budovy“ = tentýž stavební objekt RÚIAN (roh nebo dva vchody);"
          " stejné čp. bez té značky může být jiná budova.")


def parcely(misto, polomer=60, vse=False):
    lat, lon = stred(misto)
    q = {"outFields": "kmenovecislo,poddelenicisla,druhcislovanikod,vymeraparcely"}
    if not vse:
        # v k. ú. s jednou číselnou řadou jsou všechny parcely pozemkové, dům poznáš jen podle druhu pozemku
        q["where"] = f"druhcislovanikod={STAVEBNI} OR druhpozemkukod={ZASTAVENA_PLOCHA}"
    rows = []
    for f in v_obdelniku(5, lat, lon, polomer, q):
        a, ring = f["attributes"], f["geometry"]["rings"][0]
        cy, cx = sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)
        rows.append((a["druhcislovanikod"] != STAVEBNI, a["kmenovecislo"], cislo_parcely(a),
                     a.get("vymeraparcely"), *odstup(lat, lon, cy, cx)))
    for _, _, c, v, e, n in sorted(rows):
        print(f"{c:12} {v or 0:>7.0f} m²   E {e:>4} m  N {n:>4} m")
    print(f"{len(rows)} parcel v okolí ±{polomer:g} m od středu. Nízká čísla stavebních parcel = starší zástavba.")


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
    import zapis
    cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    zmenena = set()
    if len(sys.argv) > 2 and sys.argv[1] == "pridej":
        name = sys.argv[2]
        cache[name] = dict(cache.get(name, {}), dotaz=sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else f"{name}, Česko")
        if len(sys.argv) > 4:
            cache[name]["popis"] = sys.argv[4]
        zmenena.add(name)
    for name, e in cache.items():
        if "lat" not in e:
            g = geocode(e.get("dotaz") or f"{name}, Česko")
            if g:
                e["lat"], e["lon"], e["osm"] = g
                zmenena.add(name)
            else:
                print("NENALEZENO:", name, "– upravte 'dotaz' nebo doplňte lat/lon ručně")
    for name in zmenena:   # sloučit pole: změny jiných míst mezitím (souběžní pomocníci) zůstanou
        zapis.zapis("mista", name, cache[name], sloucit=True)
    for n, e in cache.items():
        print(f"{n:28} {e.get('lat', '?'):>8} {e.get('lon', '?'):>8}  {e.get('osm', '')[:70]}")


if __name__ == "__main__":
    main()
