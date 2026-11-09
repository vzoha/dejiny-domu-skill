#!/usr/bin/env python3
"""Obrázky obce z Europeany (sbírky evropských muzeí, knihoven a archivů), s licencí u každého předmětu.

Hledá v okolí obce podle polohy z RÚIAN (předměty se souřadnicemi) i podle názvů (český, německý):
fotky, pohlednice, kresby a mapy. České památky z NPÚ najde i mis.py, Deutsche Fotothek a Foto Marburg i ddb.py;
Europeana přidá hlavně rakouská, maďarská a další zahraniční muzea a Mapovou sbírku PřF UK.

Použití:
  europeana.py "<obec>" ["<německý název>" …] [od-do] [--km 2] [--volne] [--npu]
      – id | rok | název | instituce | licence | odkaz; --volne = jen licence pro placený výstup,
        --npu = i fotky a evidenční listy NPÚ (jinak je vynechá, podrobněji je ukáže mis.py)
  europeana.py detail <id>      – popis, místo, datace, autor, instituce, licence, obrázek, citace
Potřebuje API klíč (zdarma): formulář na https://pro.europeana.eu/page/get-api, klíč přijde e-mailem;
ulož ho do ~/.config/europeana/api-key nebo do proměnné EUROPEANA_API_KEY."""
import argparse, json, math, os, re, sys, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

API = "https://api.europeana.eu/record/v2"
WEB = "https://www.europeana.eu/item"
KLIC = os.path.join(os.path.expanduser("~"), ".config", "europeana", "api-key")
VYCHOZI_KM = 2
NPU = "The National Heritage Institute"   # památky NPÚ (MIS) najde podrobněji mis.py, v Europeaně zahltí okolí
NEJVIC = 100
VOLNE = re.compile(r"publicdomain|/by/|/by-sa/|NoC-")          # PDM, CC0, CC BY, CC BY-SA, bez autorských práv
NEKOMERCNI = re.compile(r"-nc|NoC-NC")


def klic():
    k = os.environ.get("EUROPEANA_API_KEY") or (open(KLIC, encoding="utf-8").read().strip() if os.path.exists(KLIC) else "")
    if not k:
        sys.exit("Europeana potřebuje API klíč (zdarma): formulář https://pro.europeana.eu/page/get-api, "
                 f"klíč přijde e-mailem. Ulož ho do {KLIC} nebo do proměnné EUROPEANA_API_KEY.")
    return k


def api(cesta, parametry):
    """GET na API; klíč v hlavičce, ne v adrese. parametry = [(název, hodnota)] (qf se opakuje)."""
    pozadavek = urllib.request.Request(f"{API}{cesta}?{urllib.parse.urlencode(parametry)}", headers={"X-Api-Key": klic()})
    try:
        with urllib.request.urlopen(pozadavek, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit(f"Europeana odmítla API klíč – zkontroluj {KLIC}.")
        raise


def dotaz(nazvy, lat=None, lon=None, polomer=VYCHOZI_KM):
    """Lucene dotaz: některý z názvů nebo souřadnice místa v obdélníku kolem středu obce."""
    casti = [f'"{n}"' for n in nazvy]
    if lat is not None:
        dlat = polomer / 111.32
        dlon = dlat / math.cos(math.radians(lat))
        casti.append(f"(pl_wgs84_pos_lat:[{lat - dlat:.4f} TO {lat + dlat:.4f}] AND "
                     f"pl_wgs84_pos_long:[{lon - dlon:.4f} TO {lon + dlon:.4f}])")
    return " OR ".join(casti)


def filtry(roky=None, jen_volne=False, s_npu=False):
    f = [("qf", "TYPE:IMAGE")]
    if not s_npu:
        f.append(("qf", f'-DATA_PROVIDER:"{NPU}"'))
    if roky:
        f.append(("qf", f"YEAR:[{roky[0]} TO {roky[1]}]"))
    if jen_volne:
        f.append(("reusability", "open"))
    return f


def hledej(nazvy, lat=None, lon=None, polomer=VYCHOZI_KM, roky=None, jen_volne=False, s_npu=False):
    """(předměty seřazené podle roku, celkem podle Europeany)."""
    r = api("/search.json", [("query", dotaz(nazvy, lat, lon, polomer)), ("rows", NEJVIC), ("profile", "standard")]
            + filtry(roky, jen_volne, s_npu))
    return sorted(r.get("items", []), key=lambda p: rok(p) or 9999), r.get("totalResults", 0)


def prvni(predmet, pole):
    v = predmet.get(pole)
    return " ".join(str((v[0] if isinstance(v, list) and v else v) or "").split())


def rok(predmet):
    m = re.search(r"\b(1[0-9]\d\d|20\d\d)\b", str(prvni(predmet, "year")))
    return int(m.group(1)) if m else None


def zkratka_licence(lic):
    m = re.search(r"creativecommons\.org/(?:licenses|publicdomain)/([a-z-]+)", lic or "")
    if m:
        return {"mark": "PDM", "zero": "CC0"}.get(m.group(1), "CC " + m.group(1).upper())
    m = re.search(r"rightsstatements\.org/vocab/([A-Za-z-]+)/", lic or "")
    return {"InC": "práva vyhrazena", "InC-EDU": "jen vzdělávání"}.get(m.group(1), m.group(1)) if m else (lic or "?")


def smi_obrazek(lic):
    if not lic:
        return "jen se souhlasem instituce (licence neuvedená)"
    if NEKOMERCNI.search(lic):
        return f"jen nevýdělečně ({zkratka_licence(lic)}), do placené zakázky popis, citace a odkaz"
    if "publicdomain" in lic or "NoC-" in lic:
        return f"ano, volné dílo (uveďte instituci) ({zkratka_licence(lic)})"
    if VOLNE.search(lic):
        return f"ano, s autorem, institucí a licencí ({zkratka_licence(lic)})"
    return f"jen se souhlasem instituce ({zkratka_licence(lic)})"


def odkaz(id_):
    return WEB + id_


def radek(p):
    nazev = prvni(p, "title")
    casti = [p["id"], str(rok(p) or "?"), nazev[:120] + ("…" if len(nazev) > 120 else ""), prvni(p, "dataProvider"),
             zkratka_licence(prvni(p, "rights")), odkaz(p["id"])]
    return "  " + " | ".join(c for c in casti if c)


def text(hodnoty):
    """{"cs": [...], "def": [...]} → první text v pořadí cs, de, en, ostatní."""
    for jazyk in ("cs", "de", "en", "def", *hodnoty):
        if hodnoty.get(jazyk):
            return hodnoty[jazyk][0]
    return ""


def popisek(objekt, hodnota):
    """URI agenta, místa, organizace nebo pojmu → jeho název; jiný text vrátí beze změny."""
    for druh in ("agents", "places", "organizations", "concepts"):
        for entita in objekt.get(druh) or []:
            if entita.get("about") == hodnota:
                nazev = text(entita.get("prefLabel") or {})
                cast = text(entita.get("isPartOf") or {})
                return f"{nazev} ({cast})" if cast and druh == "places" else nazev
    return "" if hodnota.startswith("http") else hodnota


def pole(objekt, nazev):
    """Hodnoty pole ze všech proxy záznamu, URI přeložené na názvy, bez opakování."""
    hodnoty = []
    for proxy in objekt.get("proxies", []):
        for seznam in (proxy.get(nazev) or {}).values():
            hodnoty += [h for h in (popisek(objekt, x) for x in seznam) if h and h not in hodnoty]
    return " ".join("; ".join(hodnoty).split())[:500]


def detail(id_):
    if not re.fullmatch(r"/?\d+/[\w.-]+", id_):
        sys.exit("Použití: europeana.py detail <id> (id z výpisu, např. /2020706/HA904465)")
    id_ = "/" + id_.lstrip("/")
    try:
        o = api(f"{id_}.json", [])["object"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Předmět {id_} v Europeaně není.")
        raise
    agregace = (o.get("aggregations") or [{}])[0]
    lic = text(agregace.get("edmRights") or {})
    instituce = popisek(o, text(agregace.get("edmDataProvider") or {}))
    nazev, datace, autor = pole(o, "dcTitle") or pole(o, "dcDescription")[:120], pole(o, "dcDate") or pole(o, "dctermsCreated"), pole(o, "dcCreator")
    radky = [("Název", nazev), ("Popis", pole(o, "dcDescription")), ("Datace", datace), ("Autor", autor),
             ("Místo", pole(o, "dctermsSpatial")), ("Druh", pole(o, "dcType")), ("Instituce", instituce),
             ("Na webu instituce", agregace.get("edmIsShownAt")), ("Obrázek", agregace.get("edmIsShownBy")),
             ("Licence", lic), ("Odkaz", odkaz(id_)),
             ("Citace", ", ".join(x for x in (autor, nazev, datace, instituce, zkratka_licence(lic), f"Europeana, {odkaz(id_)}") if x)),
             ("Obrázek do výstupu", smi_obrazek(lic))]
    return [f"{n}: {v}" for n, v in radky if v]


def roky_z(text):
    m = re.fullmatch(r"(\d{3,4})-(\d{3,4})", text or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        print("\n".join(detail(argv[2] if len(argv) > 2 else "")))
        return
    p = argparse.ArgumentParser(prog="europeana.py", usage=__doc__)
    p.add_argument("nazvy", nargs="+")
    p.add_argument("--km", type=float, default=VYCHOZI_KM)
    p.add_argument("--volne", action="store_true")
    p.add_argument("--npu", action="store_true")
    a = p.parse_args(argv[1:])
    roky = roky_z(a.nazvy[-1]) if len(a.nazvy) > 1 else None
    nazvy = a.nazvy[:-1] if roky else a.nazvy
    import mista   # střed obce z RÚIAN; jen v projektu (mista.py jinde skončí)
    lat, lon, popis = mista.obec_nebo_poloha(nazvy[0])
    predmety, celkem = hledej(nazvy, lat, lon, a.km, roky, a.volne, a.npu)
    print(f"Okolí {a.km:g} km od: {popis} ({lat:.5f},{lon:.5f}) a názvy {', '.join(nazvy)}." if popis else
          f"RÚIAN „{nazvy[0]}“ nezná, hledám jen podle názvů {', '.join(nazvy)}.")
    if not predmety:
        print("Europeana nemá obrázky. Zkus německý název obce nebo větší --km.")
        return
    print(f"Obrázky v Europeaně: {celkem}{f', vypisuji {len(predmety)} nejrelevantnějších podle roku' if celkem > len(predmety) else ''}")
    print("\n".join(radek(p) for p in predmety))
    print(f"\n{'' if a.npu else 'Bez NPÚ (podrobněji mis.py, tady --npu). '}Deutsche Fotothek a Foto Marburg najde i ddb.py.\n"
          "Obrázek do výstupu podle licence (europeana.py detail <id>): PDM, CC0, CC BY, CC BY-SA ano; NC a „práva vyhrazena“ ne.")


if __name__ == "__main__":
    main(sys.argv)
