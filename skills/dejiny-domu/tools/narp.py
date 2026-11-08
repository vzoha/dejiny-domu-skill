#!/usr/bin/env python3
"""Archivní fondy obce ve všech archivech ČR (Národní archivní portál, ústřední evidence Národního archivního dědictví).
Snímky tu nejsou, jen co existuje a kde: archiv, název fondu, roky. Podklad pro dotaz archivu (`archivni_dotazy.md`).

Použití:
  narp.py "<slovo v názvu fondu>" [max]   – fondy, seřazené podle archivu (obec, „Velkostatek Trhové Sviny“, „cech“…)
  narp.py detail <id>                     – číslo NAD, značka, přístupnost, téma, počty knih a kartonů, inventáře
Stejnojmenné obce rozliší závorka v názvu („Slavče (u Trhových Svinů)“). Archiv obce bývá v SOkA tehdejšího okresu."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import aron_search   # stejný software ARON jako SOA Zámrsk; importem se zapne i limit rychlosti (slusne.py)

API = "https://portal.nacr.cz/aron/api/aron"
ODKAZ = "https://portal.nacr.cz/aron/apu/"


def hledej(slovo, maxn=200):
    out, offset, pocet = [], 0, 0
    while True:
        d = aron_search.post("/apu/listview?listType=SEARCH", {
            "filters": [{"field": "type", "operation": "EQ", "value": "FUND"},
                        {"operation": "FTXF", "field": "name", "value": slovo}],
            "sort": [], "offset": offset, "size": 100, "aggregations": []}, api=API)
        items, pocet = d.get("items", []), d.get("count", 0)
        out += items
        offset += len(items)
        if not items or offset >= min(pocet, maxn):
            return out, pocet


def archiv_a_fond(nazev):
    """„Státní okresní archiv České Budějovice: Archiv obce Slavče 1887 — 1945“ → (archiv, fond)."""
    archiv, _, fond = (nazev or "").partition(": ")
    return (archiv, fond) if fond else ("", archiv)


def vypis_fondy(items):
    radky, posledni = [], None
    for i in sorted(items, key=lambda i: archiv_a_fond(i.get("name"))):
        archiv, fond = archiv_a_fond(i.get("name"))
        if archiv != posledni:
            radky.append(f"\n{archiv or '(archiv neuveden)'}")
            posledni = archiv
        radky.append(f"  {i['id']} | {fond}")
    return radky


def hodnota(v):
    if isinstance(v, str) and v.lstrip().startswith("{"):
        try:
            return json.loads(v)
        except ValueError:
            pass
    return v


def polozky(d):
    out = {}
    for cast in d.get("parts") or []:
        for it in cast.get("items") or []:
            out.setdefault(it.get("type"), []).append(hodnota(it.get("value")))
    return out


def roky(v):
    if not isinstance(v, dict):
        return str(v or "")
    od, do = v.get("from") or "?", v.get("to") or "?"
    return od if od == do else f"{od}–{do}"


def popis_fondu(d, nazvy_pomucek=()):
    p = polozky(d)
    prvni = lambda k: (p.get(k) or [""])[0]
    archiv, _ = archiv_a_fond(d.get("name"))
    radky = [f"{prvni('TITLE') or d.get('name')} ({roky(prvni('UNIT~DATE'))})",
             f"archiv: {archiv}",
             f"číslo NAD: {prvni('CISLO~NAD')} · značka: {prvni('FUND~MARK')} · {prvni('ACCESSIBILITY') or 'přístupnost neuvedena'}"]
    for k, popisek in (("FUND~TOPIC", "téma"), ("FUND~THEMATIC~GROUP", "skupina"), ("FUND~LENGTH", "rozsah")):
        if p.get(k):
            radky.append(f"{popisek}: {'; '.join(map(str, p[k]))}")
    jednotky = prvni("EVIDENCE~UNIT")
    if isinstance(jednotky, dict):
        for r in (jednotky.get("data") or {}).get("rows") or []:
            if len(r) >= 6 and not r[0].startswith("*"):   # „* …“ = podrobnější rozpad téže jednotky
                kusu = sum(int(x) for x in r[1:3] if str(x).isdigit())
                radky.append(f"  {r[0]}: {kusu} ({r[5]})")
    for n in nazvy_pomucek:
        radky.append(f"pomůcka: {n}")
    if not nazvy_pomucek and not p.get("FINDINGAID~REF"):
        radky.append("pomůcka: žádná (fond nezpracovaný – v archivu se ptej, co v něm je)")
    radky.append(f"odkaz: {ODKAZ}{d.get('id')}")
    return radky


def main(argv):
    if len(argv) > 2 and argv[1] == "detail":
        d = aron_search.detail(argv[2], api=API)
        pomucky = [archiv_a_fond(aron_search.detail(ref, api=API).get("name"))[1]
                   for ref in polozky(d).get("FINDINGAID~REF", [])[:5]]
        print("\n".join(popis_fondu(d, pomucky)))
        return
    if len(argv) < 2:
        sys.exit(__doc__)
    items, pocet = hledej(argv[1], int(argv[2]) if len(argv) > 2 else 200)
    if not items:
        print(f"Fond se slovem „{argv[1]}“ v názvu nenalezen. Zkus tehdejší obec nebo jiný tvar (Lhota × Lhotka).")
        return
    print(f"fondů: {pocet}" + (f" (vypisuji {len(items)}, zpřesni hledání)" if pocet > len(items) else ""))
    print("\n".join(vypis_fondy(items)))
    print("\nPodrobnosti: narp.py detail <id>. Snímky tu nejsou – fond si vyžádej v archivu (archivni_dotazy.md).")


if __name__ == "__main__":
    main(sys.argv)
