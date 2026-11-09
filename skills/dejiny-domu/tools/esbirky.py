#!/usr/bin/env python3
"""Fotografie, pohlednice, kresby a předměty obce ve sbírkách muzeí a galerií (eSbírky, Národní muzeum).

eSbírky spojují sbírky desítek muzeí (Národní muzeum, krajská a městská muzea). Hledání webu je volné
(„Nežetice“ najde i Sezemice a Ješetice), proto nástroj nechá jen předměty, v jejichž názvu obec je.
Předmět, který obec zmiňuje jen v popisu, tak chybí – zkus `detail` u podobných názvů nebo web.

Použití:
  esbirky.py "<obec>" [od-do]   – id | datace | název | nosič | sbírka | licence (jen název obce, bez dalších slov)
  esbirky.py detail <id>        – popis, místo, instituce, autor, licence, odkaz, citace
Licence je u každého předmětu: PDM, CC0, CC BY (-SA, -ND) = obrázek smí i do placeného výstupu s uvedením
autora a instituce; CC BY-NC… = jen nevýdělečně; bez licence = jen se souhlasem instituce. Jinak popis, citace, odkaz."""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)
from nazvy import zminuje_obec   # porovnání názvů obcí (nazvy.py)

WEB = "https://www.esbirky.cz"
STRAN = 5   # 18 předmětů na stranu, řazeno podle shody: dál už skoro jen jiné obce
VOLNE = {"PDM", "CC0", "CC_BY", "CC_BY_SA", "CC_BY_ND"}


def stranka(cesta):
    with urllib.request.urlopen(WEB + cesta, timeout=60) as r:
        return r.read().decode("utf-8")


def data_stranky(html):
    """Data, která Next.js posílá ve stránce (self.__next_f.push([1,"…"])), jako jeden text."""
    return "".join(json.loads(f'"{kus}"') for kus in re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html))


def json_za(text, klic):
    """Hodnota JSON za prvním výskytem "klic":."""
    m = re.search(rf'"{re.escape(klic)}"\s*:\s*', text)
    return json.JSONDecoder().raw_decode(text, m.end())[0] if m else None


def hledej(obec, roky=None):
    """Předměty z prvních STRAN stran hledání. Vrací (předměty, celkem podle webu)."""
    parametry = {"q": obec}
    if roky:
        parametry |= {"datingFrom": roky[0], "datingTo": roky[1]}
    predmety, celkem = [], 0
    for strana in range(1, STRAN + 1):
        data = data_stranky(stranka("/hledat?" + urllib.parse.urlencode(parametry | {"page": strana})))
        predmety += json_za(data, "items") or []
        celkem = json_za(data, "totalCount") or 0
        if strana >= (json_za(data, "numberOfPages") or 0):
            break
    return predmety, celkem


def licence(p):
    return (p.get("license") or {}).get("name") or "bez licence"


def datace(p):
    return p.get("datingNote") or "–".join(str(p[k]) for k in ("datingFrom", "datingTo") if p.get(k)) or "?"


def radek(p):
    sbirka = (p.get("currentCollection") or {}).get("name") or ""
    return " | ".join([str(p["id"]), datace(p), p.get("name") or "", p.get("mediaType") or "", sbirka, licence(p)])


def vypis(predmety, obec):
    return ["  " + radek(p) for p in predmety if zminuje_obec(p.get("name"), obec)]


def misto(p):
    zeme = (p.get("location") or {}).get("name")
    return ", ".join(x for x in (p.get("locationDetails"), zeme) if x) or "neuvedeno"


def smi_obrazek(p):
    lic = licence(p)
    if lic in VOLNE:
        return "ano, s uvedením autora, instituce a licence"
    if lic.startswith("CC_BY_NC"):
        return "jen nevýdělečně (ne do placené zakázky), jinak souhlas instituce"
    return "jen se souhlasem instituce"


def citace(p):
    instituce = (p.get("institution") or {}).get("name") or ""
    casti = [p.get("authorName"), p.get("name"), datace(p), instituce,
             f"inv. č. {p['inventoryNumber']}" if p.get("inventoryNumber") else None, f"eSbírky, {odkaz(p)}"]
    return ", ".join(c for c in casti if c and c != "?")


def odkaz(p):
    return f"{WEB}/predmet/{p.get('slug') or p['id']}"


def detail(id_):
    try:
        p = json_za(data_stranky(stranka(f"/predmet/{id_}")), "subject")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        p = None
    if not p:
        sys.exit(f"Předmět {id_} na eSbírkách není.")
    sbirka = " › ".join(c["name"] for c in p.get("collectionPath") or [])
    radky = [("Název", p.get("name")), ("Jiný název", p.get("alternativeName")), ("Popis", p.get("description")),
             ("Datace", datace(p)), ("Místo", misto(p)), ("Typ", (p.get("subjectType") or {}).get("value")),
             ("Nosič", p.get("mediaType")), ("Autor", p.get("authorName")), ("Autor snímku", p.get("mediaAuthorName")),
             ("Rozměr", p.get("dimension")), ("Instituce", (p.get("institution") or {}).get("name")),
             ("Sbírka", sbirka), ("Inv. č.", p.get("inventoryNumber")), ("Obrázků", len(p.get("images") or [])),
             ("Licence", f"{licence(p)} {p.get('licenseUrl') or ''}".strip()), ("Obrázek do výstupu", smi_obrazek(p)),
             ("Odkaz", odkaz(p)), ("Citace", citace(p))]
    return [f"{k}: {v}" for k, v in radky if v not in (None, "")]


def roky_z(arg):
    m = re.fullmatch(r"(\d{3,4})-(\d{3,4})", arg or "")
    if not m:
        sys.exit(f"Roky zadej jako 1850-1950, ne „{arg}“")
    return m.groups()


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        if len(argv) < 3 or not argv[2].isdigit():
            sys.exit("Použití: esbirky.py detail <id> (číslo z výpisu)")
        print("\n".join(detail(argv[2])))
        return
    obec, roky = argv[1], (roky_z(argv[2]) if len(argv) > 2 else None)
    predmety, celkem = hledej(obec, roky)
    radky = vypis(predmety, obec)
    if not radky:
        print(f"Na eSbírkách nic s „{obec}“ v názvu (prošlo {len(predmety)} z {celkem} podobných). "
              "Zmínku v popisu najde jen web: www.esbirky.cz.")
        return
    print(f"Předměty s „{obec}“ v názvu: {len(radky)} (z prvních {len(predmety)} z {celkem} podobných)")
    if celkem > len(predmety):
        print(f"Další strany nástroj neprochází (řazené podle shody, dál bývají jiná slova) – zúž roky "
              f"(esbirky.py \"{obec}\" 1850-1950) nebo hledej na webu.")
    print("\n".join(radky))
    print("\nStejnojmenné obce rozliší detail (popis, sbírka městského muzea). Obrázek otevře uživatel odkazem z detailu.")


if __name__ == "__main__":
    main(sys.argv)
