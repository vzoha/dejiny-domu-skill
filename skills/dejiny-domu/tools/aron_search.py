#!/usr/bin/env python3
"""Hledání svazků na portálu ARON (SOA Zámrsk, fond Sbírka matrik Východočeského kraje).
Použití: aron_search.py "<text v popisu, např. obec>" [filtr názvu fondu] [max]
  Víc slov oddělených čárkou musí být v popisu všechna: "Vinice,Hořice" = Vinice ve farnosti Hořice
  (stejnojmenných obcí bývá víc – výsledky jsou proto seřazené podle farnosti / první obce v popisu).
Vypíše: apu_id | signatura, druh a roky | popis (obce, které svazek pokrývá).
Vypisuje i svazky bez snímků (hlavně 20. století) – jestli je svazek online, ukáže `aron_img.py <apu_id> info` (scans: 0 = není).

aron_search.py scitani "<obec>"
  Sčítací operáty obce (1857–1921) ze všech okresních archivů. Jsou ve fondech „Okresní úřad …“ (strom Sčítací
  operáty › rok › soudní okres › obec) a obec má v popisu jen svůj název – hledání slovem „sčítání“ je nenajde.
  Osada bývá pod tehdejší obcí (Švihov pod Krupínem): když nic, zkus obec, ke které osada patřila.
  Vypíše: apu_id | rok | archiv, fond, cesta | popis | snímků (0 = jen v badatelně)."""
import os, json, re, sys, time, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)

API = "https://aron.vychodoceskearchivy.cz/api/aron"

def post(path, body, tries=3):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    for attempt in range(tries):   # ARON občas neodpoví (timeout) – zkusit znovu s pauzou
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))

def search(desc, name="Sbírka matrik Východočeského kraje", maxn=500):
    out, offset = [], 0
    while True:
        d = post("/apu/listview?listType=SEARCH", {
            "filters": [{"field": "type", "operation": "EQ", "value": "ARCH_DESC"},
                        *([{"operation": "FTXF", "field": "name", "value": name}] if name else []),
                        *({"operation": "FTXF", "field": "description", "value": w.strip()}
                          for w in desc.split(",") if w.strip())],
            "sort": [], "offset": offset, "size": 100, "aggregations": []})
        items = d.get("items", [])
        out += items
        offset += len(items)
        if not items or offset >= min(d.get("count", 0), maxn):
            return out, d.get("count")

def place(desc):
    """Řadicí klíč: popis bez úvodního druhu knihy („římskokatolická matrika NAROZENÝCH, …“), tj. od farnosti / první obce."""
    parts = (desc or "").split(", ")
    while parts and re.search(r"matrika|index", parts[0]):
        parts.pop(0)
    return re.sub(r"^\(?(farnost|soudní okres) ", "", ", ".join(parts))

def detail(apu_id, tries=3):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(f"{API}/apu/{apu_id}", timeout=90) as r:
                return json.load(r)
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))

def predkove(d):
    """Popisy nadřazených úrovní od nejbližší (soudní okres, rok sčítání, Sčítací operáty, …)."""
    out, p = [], d.get("parent")
    while isinstance(p, dict):
        out.append(p.get("description") or "")
        p = p.get("parent")
    return out

def scitani(obec):
    items, _ = search(obec, name=None, maxn=400)
    obec_l = obec.lower()
    kandidati = []
    for i in items:
        popis = (i.get("description") or "").strip()
        p = popis.lower()
        jmeno_obce = p == obec_l or p.startswith(obec_l + " (") or p.startswith(obec_l + " -")
        if (jmeno_obce and re.search(r", 1[89]\d\d$", i["name"])) or ("sčítání lidu" in p and obec_l in p):
            kandidati.append(i)
    radky = []
    for i in kandidati:
        d = detail(i["id"])
        cesta = predkove(d)
        rok = next((m.group(1) for c in cesta for m in [re.search(r"Sčítání lidu (1[89]\d\d)", c or "")] if m), None)
        if not rok and not any("sčítací" in (c or "").lower() for c in cesta) and "sčítání lidu" not in (i.get("description") or "").lower():
            continue
        rok = rok or (re.search(r"(1[89]\d\d)", i["name"]) or [None, "?"])[1]
        snimku = sum(1 for dao in d.get("digitalObjects", []) for f in dao.get("files", []) if f.get("type") == "TILE")
        fond = i["name"].split(", inv", 1)[0].split(", poř", 1)[0]
        radky.append((rok, i.get("description") or "", f'{i["id"]} | {rok} | {fond} › '
                      + " › ".join(c for c in reversed(cesta[:2]) if c) + f' | {i.get("description")} | snímků {snimku}'))
    for _, _, r in sorted(radky):
        print(r)
    if not radky:
        print(f"Sčítání pro „{obec}“ v ARONu nenalezeno. Zkus obec, ke které osada tehdy patřila, nebo okresní archiv.")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "scitani":
        scitani(sys.argv[2])
        sys.exit()
    desc = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "Sbírka matrik Východočeského kraje"
    maxn = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    items, cnt = search(desc, name, maxn)
    print("count", cnt)
    for i in sorted(items, key=lambda i: (place(i.get("description")), i["name"])):
        n = i["name"].split(": ", 1)[-1]
        print(i["id"], "|", n.replace("Sbírka matrik Východočeského kraje, ", ""), "|", (i.get("description") or "")[:220])
