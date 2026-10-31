#!/usr/bin/env python3
"""Kontrola konzistence dat projektu. Spouštějte po každé větší změně a před stavbou webu.

Použití: kontrola.py
Vypíše CHYBY (rozbijí web nebo jsou věcně špatně) a UPOZORNĚNÍ (něco chybí, doplnit).
Návratový kód 1, pokud jsou chyby.
"""
import datetime, json, os, re, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: data projektu tam nejsou, zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
DATA = os.path.join(ROOT, "data")
STAVY = ("doc", "lit", "prob", "fam", "unk")
DRUHY = set("NOZISGKMCLJ")


def jload(name, default):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def main():
    err, warn = [], []
    ns = {}
    try:
        exec(open(os.path.join(DATA, "domy.py"), encoding="utf-8").read(), ns)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"CHYBA: data/domy.py nejde načíst: {e}")
    OBEC, D = ns.get("OBEC", {}), ns.get("D", {})
    zaz = jload("zaznamy.json", [])
    svazky, prep, hl = jload("svazky.json", {}), jload("prepisy.json", {}), jload("zvyrazneni.json", {})
    keys = [z.get("klic") for z in zaz]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        err.append(f"zápisy se stejným klíčem: {sorted(dup)}")
    keys = set(keys)
    cited = set()

    def polozka(kde, x, nazev_pole="text"):
        st = x.get("st", "unk")
        if st not in STAVY:
            err.append(f"{kde}: neznámý stav '{st}' (povolené: {', '.join(STAVY)})")
        for r in x.get("r", []):
            cited.add(r)
            if r not in keys:
                err.append(f"{kde} cituje neexistující zápis '{r}'")
        if st == "doc" and not x.get("r"):
            warn.append(f"{kde} ({str(x.get(nazev_pole, ''))[:50]}) je 'doc', ale necituje žádný zápis")
        if st == "lit" and not (x.get("zdroj") or x.get("note") or x.get("r")):
            warn.append(f"{kde} ({str(x.get(nazev_pole, ''))[:50]}) je 'lit' – doplň 'zdroj' (kniha, strana)")

    if not OBEC.get("nazev"):
        warn.append("domy.py: OBEC nemá název")
    for i, e in enumerate(ns.get("OBEC_UDALOSTI", [])):
        if not re.search(r"\d{4}", str(e.get("rok", ""))):
            warn.append(f"událost obce č. {i + 1}: rok bez letopočtu – na webu se zařadí na konec")
        polozka(f"událost obce {e.get('rok')}", e)
    for cp, d in D.items():
        if not isinstance(cp, str):
            err.append(f"dům {cp!r}: číslo popisné piš jako text (\"30\"), ne číslo")
        if d.get("st", "unk") not in STAVY:
            err.append(f"dům {cp}: neznámý stav '{d.get('st')}'")
        for e in d.get("udalosti", []):
            polozka(f"dům {cp}, událost {e.get('rok')}", e)
        for o in d.get("drzitele", []):
            polozka(f"dům {cp}, držitel {o.get('n')}", o, "n")
            if not (o.get("od") or o.get("do")):
                warn.append(f"dům {cp}, držitel {o.get('n')}: chybí 'od' i 'do'")
        for o in d.get("obyvatele", []):
            polozka(f"dům {cp}, obyvatel {o.get('n')}", o, "n")
        if d.get("lat") is None:
            warn.append(f"dům {cp}: nemá polohu (tools/mista.py hledej \"Obec {cp}\" nebo z mapy, zapiš lat/lon)")

    for z in zaz:
        k = z.get("klic", "?")
        for f in ("klic", "druh", "datum", "nazev", "shrnuti"):
            if not z.get(f):
                err.append(f"zápis {k}: chybí pole '{f}'")
        if z.get("druh") and z["druh"] not in DRUHY:
            err.append(f"zápis {k}: neznámý druh '{z['druh']}' (povolené: {', '.join(sorted(DRUHY))})")
        if z.get("svazek") and z["svazek"] not in svazky:
            err.append(f"zápis {k}: svazek '{z['svazek']}' není v data/svazky.json")
        if not z.get("odkaz") and not svazky.get(z.get("svazek", ""), {}).get("url") and z.get("druh") != "L":
            warn.append(f"zápis {k}: chybí odkaz na snímek (pole 'odkaz')")
        if not os.path.exists(os.path.join(ROOT, "vyrezy", k + ".jpg")):
            warn.append(f"zápis {k}: chybí výřez vyrezy/{k}.jpg")
        elif k not in hl and z.get("druh") != "M":   # mapa: čtené místo ukazuje popis, rámeček je volitelný
            warn.append(f"zápis {k}: chybí rámeček (tools/ramecek.py)")
        if k not in prep and z.get("druh") != "M":   # mapa: stačí 'shrnuti', přepis a překlad nejsou nutné
            warn.append(f"zápis {k}: chybí přepis a překlad v data/prepisy.json")
        if k not in cited:
            warn.append(f"zápis {k}: necituje ho žádný dům ani událost obce (doplnit do 'r')")

    for m in jload("mapy.json", []):
        if not os.path.exists(os.path.join(ROOT, "vyrezy", m.get("img", "") + ".jpg")):
            err.append(f"mapa {m.get('img')}: chybí obrázek vyrezy/{m.get('img')}.jpg (tools/vyrez.py)")
        if not m.get("zdroj"):
            warn.append(f"mapa {m.get('img')}: chybí 'zdroj' (odkud mapa je – kvůli autorským právům)")
    for d in jload("dokumenty.json", []):
        for c in d.get("domy", []):
            if str(c) not in D:
                err.append(f"dokument {d.get('img')}: dům '{c}' není v domy.py")
    for name, e in jload("mista.json", {}).items():
        if "lat" not in e:
            warn.append(f"místo {name}: nemá souřadnice (spusťte tools/mista.py)")

    cfg = jload("web.json", {})
    if not (cfg.get("prihlaseni") or {}).get("odpoved") and not (cfg.get("prihlaseni") or {}).get("otevreny"):
        warn.append("web.json: není nastavená odpověď na přihlašovací otázku – nasazení webu skončí chybou")
    if cfg.get("hlavni_dum") and str(cfg["hlavni_dum"]) not in D:
        err.append(f"web.json: hlavni_dum '{cfg['hlavni_dum']}' není v domy.py")

    # Obyvatelé posledních ~100 let jsou možná žijící nebo jejich děti ano – soukromí (reference/soukromi.md).
    hranice = datetime.date.today().year - 100
    for cp, d in D.items():
        for o in d.get("obyvatele", []):
            roky = [int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", o.get("y", "") + " " + " ".join(o.get("f", [])))]
            if roky and min(roky) >= hranice and o.get("f"):
                warn.append(f"SOUKROMÍ (dům {cp}, {o.get('n')}): narozen(a) po {hranice} a má podrobnosti – "
                            f"žijící lidé jen se souhlasem (reference/soukromi.md)")

    ma_pribeh = os.path.exists(os.path.join(DATA, "pribeh.md")) or any(
        f.startswith("pribeh_") and f.endswith(".md") for f in os.listdir(DATA))
    if not ma_pribeh:
        hlavni = D.get(str(cfg.get("hlavni_dum", "")), {})
        if len(hlavni.get("drzitele", [])) >= 4:
            warn.append("hlavní dům má už 4+ držitele – je čas napsat příběh domu "
                        "(data/pribeh.md, reference/pribehy.md); koncept nejdřív ukaž uživateli v chatu")

    log = os.path.join(DATA, "research_log.md")
    rows = sum(1 for l in open(log, encoding="utf-8") if re.match(r"^\| \d+ \|", l)) if os.path.exists(log) else 0
    print(f"{len(D)} domů, {len(ns.get('OBEC_UDALOSTI', []))} událostí obce, {len(zaz)} zápisů, {len(svazky)} svazků, {rows} řádků deníku")
    for e in err:
        print("CHYBA:", e)
    for w in warn:
        print("upozornění:", w)
    if not err and not warn:
        print("Vše v pořádku.")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
