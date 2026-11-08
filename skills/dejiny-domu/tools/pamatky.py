#!/usr/bin/env python3
"""Památky a evidované objekty obce z Památkového katalogu NPÚ (pamatkovykatalog.cz).

Soupis obsahuje kulturní památky i objekty, které památkáři jen evidují (kaple, mlýny, domy bez ochrany).
Když dům v katalogu není, neznamená to, že nemá historickou hodnotu.

Použití:
  pamatky.py "<obec, část obce nebo ulice>" [číslo]  – objekty (číslo = čp. nebo č. or. v adrese): id | název | adresa | ochrana | anotace
  pamatky.py detail <id>                         – vznik, stavební vývoj, popis, literatura, fotky v MIS, odkaz
Data seznamu památek jsou otevřená (CC BY 4.0): citace „NPÚ, Památkový katalog, katalogové číslo …“.
Fotky jsou dílo NPÚ – jen odkazem, do výstupu ne (reference/podminky.md)."""
import json, os, re, sys, unicodedata, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

API = "https://pamatkovykatalog.cz/api/"
WEB = "https://www.pamatkovykatalog.cz/"
LIMIT = 250   # víc katalog na jeden dotaz nevrátí („hledání je příliš obecné“)


def api(cesta):
    req = urllib.request.Request(API + cesta, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def hledej(text):
    q = urllib.parse.urlencode({"type": "soupis", "mode": "fulltext", "fulltext": text,
                                "sort": "podle-relevance", "limit": LIMIT})
    d = api(f"search/fulltext?{q}")
    return d.get("results") or [], d.get("count") or 0


def bez_diakritiky(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def odkaz(prvek):
    """Trvalý odkaz jako v katalogu: název bez diakritiky s pomlčkami a id („navesni-kaple-…-25529919“)."""
    slug = re.sub(r"[^a-z0-9]+", "-", bez_diakritiky(prvek.get("name"))).strip("-")
    return f"{WEB}{slug}-{prvek['id']}"


def ochrana(prvek):
    stavy = [f"{s['protectionType']['name']} {s.get('indexNumber') or ''}".strip()
             for s in prvek.get("legalStates") or [] if s.get("protectionType")]
    return ", ".join(dict.fromkeys(stavy)) or "evidováno, bez ochrany"   # areál má stejný stav u každé části


def v_miste(prvek, text):
    """Leží objekt v hledané obci, části obce nebo ulici (ne jen zmínka v textu jinde)?"""
    hledane = bez_diakritiky(text)
    return (any(bez_diakritiky(prvek.get(k)) == hledane for k in ("municipality", "district", "locality"))
            or re.search(rf"\b{re.escape(hledane)}\b", bez_diakritiky(prvek.get("address"))) is not None)


def adresa(prvek):
    zaklad, ulice = prvek.get("address") or "", " ".join((prvek.get("streetHouseNumber") or "").split())
    return zaklad if not ulice or ulice in zaklad else f"{zaklad}, {ulice}"


def jednim_radkem(text):
    return " ".join((text or "").split())


def ma_cislo(prvek, cislo):
    """Je v adrese objektu číslo domu (čp. i č. or., ves i ulice)?"""
    return re.search(rf"(?<!\d){re.escape(cislo)}(?!\d)", adresa(prvek)) is not None


def vypis(prvky, text, cislo=None):
    if cislo:
        prvky = [p for p in prvky if ma_cislo(p, cislo)]
    mistni = [p for p in prvky if v_miste(p, text)]
    jinde = [p for p in prvky if not v_miste(p, text)]
    radky = []
    for nadpis, skupina in ((f"V místě „{text}“ (obec, část obce, ulice)", mistni), ("Jinde (hledané slovo jen v textu)", jinde)):
        if skupina:
            radky.append(f"\n{nadpis}: {len(skupina)}")
            radky += [f"  {p['id']} | {p.get('name')} | {adresa(p)} | {ochrana(p)} | {jednim_radkem(p.get('description'))}"
                      for p in skupina]
    return radky


POLE = (("origin", "vznik"), ("author", "autor"), ("styles", "sloh"), ("propertyHistoricalDevelopment", "stavební vývoj"),
        ("history", "historie"), ("description", "popis"), ("propertySignificantElements", "významné prvky"),
        ("heritageValueEvaluation", "památková hodnota"), ("protectedSince", "chráněno od"))


def popis(d):
    radky = [f"{d.get('name')} ({(d.get('elementKind') or {}).get('name') or d.get('elementTypes') or ''})",
             f"místo: {', '.join(x for x in (d.get('municipality'), d.get('district'), d.get('cadastralArea') and 'k. ú. ' + d['cadastralArea']) if x)}",
             f"ochrana: {ochrana(d)} · katalogové číslo {d.get('catalogNumber')}"]
    if d.get("annotation"):
        radky.append(f"anotace: {d['annotation']}")
    radky += [f"{popisek}: {d[k]}" for k, popisek in POLE if d.get(k)]
    radky += [f"událost: {u.get('type')} {u.get('dating') or ''} {u.get('description') or ''}".rstrip()
              for u in d.get("events") or []]
    radky += [f"literatura: {z.get('quote')}" for z in d.get("literatureSources") or []]
    radky += [f"foto MIS: {m.get('description')} – {m.get('url')}" for m in d.get("misMedia") or []]
    if d.get("literatureAllSources"):
        radky.append(f"veškerá literatura a dokumentace (Carmen): {d['literatureAllSources']}")
    radky.append(f"odkaz: {d.get('permanentUrl') or odkaz(d)}")
    radky.append(f"citace: NPÚ, Památkový katalog, katalogové číslo {d.get('catalogNumber')} (CC BY 4.0)")
    return radky


def main(argv):
    if len(argv) > 2 and argv[1] == "detail":
        print("\n".join(popis(api(f"element/{argv[2]}"))))
        return
    if len(argv) < 2:
        sys.exit(__doc__)
    text, cislo = argv[1], (argv[2] if len(argv) > 2 else None)
    prvky, pocet = hledej(text)
    radky = vypis(prvky, text, cislo)
    if not radky:
        print(f"V katalogu nic pro „{text}“{f' číslo {cislo}' if cislo else ''}. Dům v katalogu chybět smí – "
              "neznamená to, že nemá historickou hodnotu.")
        return
    if pocet > len(prvky):
        print(f"Katalog našel {pocet} objektů, vrací {len(prvky)} – zpřesni hledání (část obce, ulice).")
    print("\n".join(radky).lstrip("\n"))
    print("\nPodrobnosti, literatura a fotky: pamatky.py detail <id>")


if __name__ == "__main__":
    main(sys.argv)
