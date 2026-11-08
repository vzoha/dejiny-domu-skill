#!/usr/bin/env python3
"""Průmyslové stavby obce z Industriální topografie VCPD FA ČVUT (industrialnitopografie.cz).

Mlýny, pivovary, cihelny, továrny, doly, mosty, vodárny: dějiny objektu, datace, stav a literatura.
Vede ji Výzkumné centrum průmyslového dědictví FA ČVUT, ~4 800 objektů v celé ČR.

Použití:
  industrial.py "<obec nebo část obce>" [hledaný výraz]  – objekty: id | název | obec – část | druh | datace
  industrial.py detail <id>                              – adresa, datace, dějiny, literatura, osoby, odkaz, citace
Obsah je chráněný („všechna práva vyhrazena“): do výstupu jen zjištění vlastními slovy s citací a odkaz,
texty a fotky nepřebírat (reference/podminky.md). Nástroj jen čte: POST posílá výhradně na čtecí cesty …/filter."""
import html, json, os, re, sys, unicodedata, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

API = "https://api.databaze.fa.cvut.cz/apiPublic/industrialni-topografie/"
WEB = "https://www.industrialnitopografie.cz/cs/structures/"
STRANA, NEJVIC = 100, 300   # objektů na dotaz / nejvýš na jedno hledání (Praha má ~400)
SKUPINA_NEJVIC = 20   # větší skupinu jen spočítá: okres i ověření zmínky stojí dotaz na objekt (Beroun → 79× Berounka)


def filtr(sloupce, strana):
    """Tělo dotazu jako ho posílá web (structure/filter): sloupec obsahuje hodnotu."""
    return {"page": strana, "pageSize": STRANA, "orderBy": "addressCity;asc", "advancedFilterColumns": [],
            "filterColumns": [{"name": k, "filters": [{"combination": 0, "value": v, "operation": 1}]}
                              for k, v in sloupce.items()]}


def cti(cesta, telo=None):
    """GET, nebo POST jen na …/filter: holá cesta kolekce (structureMap) záznam založí (8. 11. 2026)."""
    if telo is not None and not cesta.endswith("/filter"):
        raise ValueError(f"POST jen na čtecí cestu …/filter, ne {cesta}")
    data = None if telo is None else json.dumps(telo).encode()
    req = urllib.request.Request(API + cesta, data=data, method="GET" if telo is None else "POST",
                                 headers={"Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r), int(r.headers.get("X-Total-Count") or 0)


def hledej(sloupce):
    """Všechny strany do NEJVIC. Vrací (objekty, celkem v databázi)."""
    objekty, celkem = [], 0
    for strana in range(NEJVIC // STRANA):
        davka, celkem = cti("structure/filter", filtr(sloupce, strana))
        objekty += davka
        if len(objekty) >= celkem or len(davka) < STRANA:
            break
    return objekty, celkem


def bez_diakritiky(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def odkaz(id_, nazev):
    """Adresa jako v mapě webu: název bez diakritiky s pomlčkami a id („mestansky-novy-pivovar-762“)."""
    slug = re.sub(r"[^a-z0-9]+", "-", bez_diakritiky(nazev)).strip("-")
    return f"{WEB}{slug}-{id_}"


def v_miste(o, misto):
    """Obec nebo část obce se jmenuje přesně tak (Březí, ne Vlachovo Březí ani Březina)."""
    hledane = bez_diakritiky(misto)
    return any(hledane == bez_diakritiky(o.get(k)) for k in ("addressCity", "addressCityDistrict"))


def podobne_misto(o, misto):
    hledane = bez_diakritiky(misto)
    return any(hledane in bez_diakritiky(o.get(k)) for k in ("addressCity", "addressCityDistrict"))


_detaily = {}


def detail(id_):
    id_ = int(id_)
    if id_ not in _detaily:
        _detaily[id_] = cti(f"structure/detail?structureId={id_}")[0]
    return _detaily[id_]


def zminuje(o, misto):
    """Fulltext API hledá i uvnitř slov a bez diakritiky („Lniště“ v adrese hrebecskedulnistezky.cz) – ověří slovo v textu."""
    d = detail(o["id"])
    texty = " ".join(str(d.get(k) or "") for k in ("nameOriginal", "descriptionPublic", "literature"))
    kmen = re.sub(r"[aeiouy]+$", "", bez_diakritiky(misto))   # i v jiném pádě (Berouna, Telči)
    return re.search(rf"\b{re.escape(kmen)}[a-z]{{0,2}}\b", bez_diakritiky(text(texty))) is not None


def datace(datings):
    def rok(d):
        od, do = d.get("yearFrom"), d.get("yearTo")
        return f"{od}–{do}" if od and do else str(od or do or "")
    return ", ".join(r for r in map(rok, datings or []) if r)


def druh(o):
    return ", ".join(x["name"] for x in o.get("okecList") or [])


def ma_vyraz(o, vyraz):
    return bez_diakritiky(vyraz) in bez_diakritiky(f"{o.get('nameOriginal')} {druh(o)}")


def radek(o, s_okresem=False):
    misto = " – ".join(x for x in (o.get("addressCity"), o.get("addressCityDistrict")) if x)
    if s_okresem and (okres := (detail(o["id"]).get("address") or {}).get("district")):
        misto += f" (okres {okres})"
    return f"  {o['id']} | {o.get('nameOriginal')} | {misto} | {druh(o)} | {datace(o.get('datings'))}"


def vypis(objekty, misto):
    mistni = [o for o in objekty if v_miste(o, misto)]
    podobne = [o for o in objekty if not v_miste(o, misto) and podobne_misto(o, misto)]
    jinde = [o for o in objekty if not podobne_misto(o, misto)]
    if len(jinde) <= SKUPINA_NEJVIC:
        jinde = [o for o in jinde if zminuje(o, misto)]
    radky = []
    if mistni:
        okresy = len(mistni) <= SKUPINA_NEJVIC
        radky += [f"\nV místě „{misto}“ (obec, část obce): {len(mistni)}"] + [radek(o, okresy) for o in mistni]
        if not okresy:
            radky.append("  okres ukáže detail (industrial.py detail <id>)")
    for nadpis, skupina in (("Obce a části s podobným názvem", podobne),
                            ("Jinde, obec zmíněná v textu", jinde)):
        if not skupina:
            continue
        radky.append(f"\n{nadpis}: {len(skupina)}")
        if len(skupina) <= SKUPINA_NEJVIC:
            radky += [radek(o) for o in skupina]
        else:
            radky.append(f"  nevypisuji, zúží je hledaný výraz (industrial.py \"{misto}\" mlýn)")
    return radky


def text(s):
    """HTML popisu na prostý text, odkazy jako „text (adresa)“."""
    s = re.sub(r'<a [^>]*href="\s*([^"]+?)\s*"[^>]*>(.*?)</a>', r"\2 (\1)", s or "", flags=re.S)
    s = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())
    return re.sub(r" ([,.;:])", r"\1", s)   # mezera po zavřeném tagu („<em>Název</em>, Praha“)


def osoby(vazby):
    return [f"{v['name']} ({v['partyRelationshipType']})" if v.get("partyRelationshipType") else v["name"]
            for v in vazby or [] if v.get("name")]


def adresa(a):
    okres = a.get("district") and f"okres {a['district']}"
    return ", ".join(x for x in (a.get("streetAndNumber"), a.get("cityDistrict"), a.get("city"), okres) if x)


def popis(d):
    radky = [f"{d.get('nameOriginal')} ({druh(d)})", f"adresa: {adresa(d.get('address') or {})}"]
    if d.get("lat") and d.get("lng"):
        radky.append(f"poloha: {d['lat']:.6f}, {d['lng']:.6f}")
    radky += [f"datace: {datace([x])}{' ' + x['description'] if x.get('description') else ''}" for x in d.get("structureDatation") or []]
    if d.get("conditionList"):
        radky.append(f"stav: {', '.join(x['name'] for x in d['conditionList'])}")
    radky += [f"památková ochrana: {d[k]}" for k in ("structureHeritageUrl", "landHeritageUrl") if d.get(k)]
    if d.get("descriptionPublic"):
        radky.append(f"dějiny (shrň vlastními slovy, necituj celé): {text(d['descriptionPublic'])}")
    if d.get("literature"):
        radky.append(f"literatura: {text(d['literature'])}")
    radky += [f"osoba / firma: {o}" for o in osoby((d.get("topPartyRelationships") or []) + (d.get("bottomPartyRelationships") or []))]
    souvisejici = [(w["id"], w.get("nameOriginal") or w.get("name")) for w in d.get("widerContexts") or [] if w.get("id")]
    radky += [f"souvisí: {nazev} – {odkaz(id_, nazev)}" for id_, nazev in souvisejici]
    if d.get("photos"):
        radky.append(f"fotky: {len(d['photos'])} na webu (jen odkazem, nepřebírat)")
    autori = ", ".join(dict.fromkeys(f"{x.get('firstname')} {x.get('surname')}".strip() for x in d.get("recordAuthors") or []))
    radky.append(f"odkaz: {odkaz(d['id'], d.get('nameOriginal'))}")
    radky.append(f"citace: {autori + ', ' if autori else ''}{d.get('nameOriginal')}, Industriální topografie VCPD FA ČVUT "
                 f"(www.industrialnitopografie.cz), [datum přístupu], {d.get('internalNumber')}")
    return radky


def main(argv):
    if len(argv) > 2 and argv[1] == "detail":
        print("\n".join(popis(detail(argv[2]))))
        return
    if len(argv) < 2:
        sys.exit(__doc__)
    misto, vyraz = argv[1], (argv[2] if len(argv) > 2 else None)
    v_obci, celkem_obec = hledej({"city": misto, **({"fulltext": vyraz} if vyraz else {})})
    zminky, celkem_text = hledej({"fulltext": misto})   # část obce (Holešovice) filtr obce nenajde
    orezano = celkem_obec > len(v_obci) or celkem_text > len(zminky)
    if vyraz:   # dvě slova ve fulltextu hledá API jako frázi – výraz se tu dohledá v názvu a druhu
        zminky = [o for o in zminky if ma_vyraz(o, vyraz)]
    objekty = list({o["id"]: o for o in v_obci + zminky}.values())
    radky = vypis(objekty, misto)
    if not radky:
        print(f"V Industriální topografii nic pro „{misto}“{f' a „{vyraz}“' if vyraz else ''}. "
              "Databáze má jen vybrané průmyslové a technické stavby.")
        return
    if orezano:
        print(f"Databáze našla víc objektů, než nástroj vypíše (nejvýš {NEJVIC} na hledání) – přidej hledaný výraz.")
    print("\n".join(radky).lstrip("\n"))
    print("\nDějiny, literatura a odkaz: industrial.py detail <id>")


if __name__ == "__main__":
    main(sys.argv)
