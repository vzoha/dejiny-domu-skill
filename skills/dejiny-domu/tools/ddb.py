#!/usr/bin/env python3
"""Obrázky obce z Deutsche Digitale Bibliothek (DDB): fotky, diapozitivy, pohlednice, kresby a plány z německých muzeí,
archivů a knihoven (Foto Marburg, Humboldtova univerzita, Sudetoněmecké muzeum…), s licencí u každého předmětu.

České obce bývají v DDB pod německým názvem: zadej oba (`ddb.py "Rumburk" "Rumburg"`).

Použití:
  ddb.py "<název>" ["<další název>" …] [od-do]   – id | rok | název | místo | druh | instituce | licence | odkaz
  ddb.py detail <id>                              – popis, místo, datace, instituce, licence, obrázek, citace
Veřejné API verze 2 je bez klíče (nové klíče DDB nevydává, klíč potřebovala jen verze 1).
Metadata jsou CC0, obrázek smí do výstupu podle licence předmětu (detail)."""
import datetime, json, os, re, sys, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

API = "https://api.deutsche-digitale-bibliothek.de/2"
WEB = "https://www.deutsche-digitale-bibliothek.de/item/"
OBRAZEK = "mediatype_002"   # typ média „Bild“
NEJVIC = 100
TEXTY = ("Urkunden", "Urkunde", "Akte", "Archivale", "Text", "Band (Publikation)", "Monografie", "Kapitel", "Abschnitt",
         "Aufsatz", "Artikel (Publikation)", "Mehrbändiges Werk", "Zeitschrift", "Zeitung", "Brief", "Konferenzbeitrag",
         "Gelegenheitsschrift", "Ordensliteratur", "Flugblatt")   # skeny textů mají taky typ média „Bild“
POLE = "id,label,title,place,provider,dataprovider_fct,license,begin_time,objecttype,view"
VOLNE = re.compile(r"/by/|/by-sa/")   # CC BY, CC BY-SA
NEKOMERCNI = re.compile(r"-nc")


def api(cesta, **parametry):
    pozadavek = urllib.request.Request(f"{API}{cesta}?{urllib.parse.urlencode(parametry)}",
                                       headers={"Accept": "application/json"})
    with urllib.request.urlopen(pozadavek, timeout=60) as r:
        return json.load(r)


def dotaz(nazvy, roky=None):
    """Lucene dotaz: místo nebo název obsahuje některý z názvů, jen obrázky s digitalizátem, volitelně roky vzniku."""
    mista = " OR ".join(f'place:"{n}" OR label:"{n}"' for n in nazvy)
    bez_textu = " OR ".join(f'"{t}"' for t in TEXTY)
    q = f"({mista}) AND digitalisat:true AND type_fct:{OBRAZEK} AND -objecttype_fct:({bez_textu})"
    if roky:
        q += f" AND begin_time:[{den(roky[0], 1, 1)} TO {den(roky[1], 12, 31)}]"
    return q


def den(rok, mesic, den_):
    """DDB ukládá datum jako pořadové číslo dne od 1. 1. roku 1 (datetime.toordinal)."""
    return datetime.date(rok, mesic, den_).toordinal()


def rok(predmet):
    cas = (predmet.get("begin_time") or [None])[0]
    return datetime.date.fromordinal(int(cas)).year if cas else None


def hledej(nazvy, roky=None):
    """(nalezené předměty, celkem podle DDB)."""
    r = api("/search/index/search/select", q=dotaz(nazvy, roky), rows=NEJVIC, fl=POLE)["response"]   # nejrelevantnější
    return sorted(r["docs"], key=lambda p: rok(p) or 9999), r["numFound"]


def prvni(predmet, pole):
    v = predmet.get(pole)
    return (v[0] if isinstance(v, list) and v else v) or ""


def instituce(predmet):
    return prvni(predmet, "dataprovider_fct") or prvni(predmet, "provider")


def licence(predmet):
    return prvni(predmet, "license")


def smi_obrazek(lic):
    if not lic:
        return "jen se souhlasem instituce (licence neuvedená)"
    if NEKOMERCNI.search(lic):
        return f"jen nevýdělečně ({lic}), do placené zakázky popis, citace a odkaz"
    if "publicdomain" in lic:
        return f"ano, volné dílo (uveďte instituci a fotografa) ({lic})"
    if VOLNE.search(lic):
        return f"ano, s autorem, institucí a licencí ({lic})"
    return f"jen se souhlasem instituce ({lic})"


def zkratka_licence(lic):
    m = re.search(r"creativecommons\.org/(?:licenses|publicdomain)/([a-z-]+)", lic or "")
    if m:
        return "CC " + m.group(1).upper() if m.group(1) not in ("mark", "zero") else {"mark": "PDM", "zero": "CC0"}[m.group(1)]
    return "práva vyhrazena" if "rightsstatements.org" in (lic or "") else (lic or "bez licence")


def odkaz(id_):
    return WEB + id_


def misto(p, nazvy):
    """Místo předmětu, které obsahuje hledaný název (rozliší „Schweinitz (Kreis Jessen)“ od Trhových Svinů), jinak první."""
    mista = p.get("place") or []
    return next((m for m in mista if any(n.lower() in m.lower() for n in nazvy)), mista[0] if mista else "")


def radek(p, nazvy=()):
    nazev = prvni(p, "label") or prvni(p, "title")
    casti = [p["id"], str(rok(p) or "?"), nazev[:140] + ("…" if len(nazev) > 140 else ""), misto(p, nazvy), prvni(p, "objecttype"),
             instituce(p), zkratka_licence(licence(p)), odkaz(p["id"])]
    return "  " + " | ".join(c for c in casti if c)


def detail(id_):
    docs = api("/search/index/search/select", q=f'id:"{id_}"', rows=1, fl=POLE + ",caption_2")["response"]["docs"]
    if not docs:
        sys.exit(f"Předmět {id_} v DDB není.")
    p = docs[0]
    lic = licence(p)
    radky = [("Název", prvni(p, "label") or prvni(p, "title")), ("Místo", ", ".join(p.get("place") or [])),
             ("Rok", rok(p)), ("Druh", prvni(p, "objecttype")), ("Popis", "; ".join((p.get("view") or [])[:6])),
             ("Instituce", instituce(p)), ("Autor a práva", prvni(p, "caption_2")), ("Licence", lic),
             ("Odkaz", odkaz(p["id"])),
             ("Citace", ", ".join(str(x) for x in (prvni(p, "label") or prvni(p, "title"), rok(p), instituce(p),
                                                    zkratka_licence(lic), f"Deutsche Digitale Bibliothek, {odkaz(p['id'])}") if x)),
             ("Obrázek do výstupu", smi_obrazek(lic))]
    return [f"{n}: {v}" for n, v in radky if v]


def roky_z(text):
    m = re.fullmatch(r"(\d{3,4})-(\d{3,4})", text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        if len(argv) < 3:
            sys.exit("Použití: ddb.py detail <id> (id z výpisu)")
        print("\n".join(detail(argv[2])))
        return
    args = argv[1:]
    roky = roky_z(args[-1]) if len(args) > 1 else None
    nazvy = args[:-1] if roky else args
    predmety, celkem = hledej(nazvy, roky)
    if not predmety:
        print(f"DDB nemá obrázky k {' / '.join(nazvy)}. Zkus německý název obce (Krummau, Schweinitz).")
        return
    print(f"Obrázky v DDB: {celkem}{f', vypisuji {len(predmety)} nejrelevantnějších podle roku' if celkem > len(predmety) else ''}")
    print("\n".join(radek(p, nazvy) for p in predmety))
    print("\nStejnojmenná místa v Německu (Schweinitz u Jessenu) pozná sloupec místo, jinak detail (ddb.py detail <id>).\n"
          "Rok je datace předmětu: u fotky stavby bývá rok stavby, ne snímku (Foto Marburg: kostel 1201).\n"
          "Obrázek do výstupu podle licence: PDM, CC0, CC BY, CC BY-SA ano s autorem; NC jen nevýdělečně; jinak souhlas.")


if __name__ == "__main__":
    main(sys.argv)
