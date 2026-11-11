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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from platnost import chyba_odkazu, chyba_odpovedi, chyby_vyhrad, chyba_polohy, chyba_vyrezu, chyby_adres_domu, chyby_cisel_domu, cislo_domu, nemozna_data, obracene_rozpeti, obraceny_interval, proc_neprolinat, skupiny_map  # noqa: E402
STAVY = ("doc", "lit", "prob", "fam", "unk")
DRUHY = set("NOZISGKMCLJ")


def jload(name, default):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8-sig")) if os.path.exists(p) else default


def main():
    if sys.argv[1:2] in (["-h"], ["--help"]):
        sys.exit(__doc__)
    err, warn = [], []
    ns = {}
    try:
        exec(open(os.path.join(DATA, "domy.py"), encoding="utf-8-sig").read(), ns)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"CHYBA: data/domy.py nejde načíst: {e}")
    OBEC, D = ns.get("OBEC", {}), ns.get("D", {})
    zaz = jload("zaznamy.json", [])
    svazky, prep, hl = jload("svazky.json", {}), jload("prepisy.json", {}), jload("zvyrazneni.json", {})
    keys = [z.get("klic") for z in zaz]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        err.append(f"zápisy se stejným klíčem: {sorted(dup)}")
    for k, p in prep.items():
        if not isinstance(p, dict) or set(p) - {"orig", "cs"}:
            err.append(f"přepis {k}: povolené klíče jsou jen 'orig' a 'cs' (reference/data.md), je tam {sorted(p) if isinstance(p, dict) else p!r}")
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
        chyby, upozorneni = chyby_vyhrad(x)
        err.extend(f"{kde}: {c}" for c in chyby)
        warn.extend(f"{kde}: {u}" for u in upozorneni)
        if st == "doc" and not x.get("r"):
            warn.append(f"{kde} ({str(x.get(nazev_pole, ''))[:50]}) je 'doc', ale necituje žádný zápis")
        if st == "lit" and not (x.get("zdroj") or x.get("note") or x.get("r")):
            warn.append(f"{kde} ({str(x.get(nazev_pole, ''))[:50]}) je 'lit' – doplň 'zdroj' (kniha, strana)")

    if not OBEC.get("nazev"):
        warn.append("domy.py: OBEC nemá název")
    if c := chyba_polohy(OBEC):
        err.append(f"OBEC: {c}")
    err += chyby_adres_domu(D)
    c, u = chyby_cisel_domu(D)
    err += c
    warn += u

    def data_v(kde, *hodnoty):
        for h in hodnoty:
            for dt in nemozna_data(h):
                err.append(f"{kde}: datum {dt} v kalendáři není (oprav podle pramenu)")
    for i, e in enumerate(ns.get("OBEC_UDALOSTI", [])):
        if not re.search(r"\d{4}", str(e.get("rok", ""))):
            warn.append(f"událost obce č. {i + 1}: rok bez letopočtu – na webu se zařadí na konec")
        polozka(f"událost obce {e.get('rok')}", e)
        data_v(f"událost obce {e.get('rok')}", e.get("rok"), e.get("text"))
    for cp, d in D.items():
        if not isinstance(cp, str):
            err.append(f"dům {cp!r}: klíč domu piš jako text (\"30\"), ne číslo")
        if d.get("st", "unk") not in STAVY:
            err.append(f"dům {cp}: neznámý stav '{d.get('st')}'")
        for e in d.get("udalosti", []):
            polozka(f"dům {cp}, událost {e.get('rok')}", e)
            data_v(f"dům {cp}, událost {e.get('rok')}", e.get("rok"), e.get("text"))
        for o in d.get("drzitele", []):
            polozka(f"dům {cp}, držitel {o.get('n')}", o, "n")
            data_v(f"dům {cp}, držitel {o.get('n')}", o.get("od"), o.get("do"), o.get("jak"))
            if not (o.get("od") or o.get("do")):
                warn.append(f"dům {cp}, držitel {o.get('n')}: chybí 'od' i 'do'")
            elif obraceny_interval(o.get("od"), o.get("do")):
                err.append(f"dům {cp}, držitel {o.get('n')}: 'od' {o['od']} je po 'do' {o['do']} (prohozené?)")
        for o in d.get("obyvatele", []):
            polozka(f"dům {cp}, obyvatel {o.get('n')}", o, "n")
            data_v(f"dům {cp}, obyvatel {o.get('n')}", o.get("y"), *o.get("f", []))
            if obracene_rozpeti(o.get("y")):
                err.append(f"dům {cp}, obyvatel {o.get('n')}: roky {o['y']} jsou pozpátku")
        if d.get("lat") is None and d.get("lon") is None:
            warn.append(f"dům {cp}: nemá polohu (tools/mista.py hledej \"{d.get('cast') or 'Obec'} {cislo_domu(cp, d)}\" nebo z mapy, zapiš lat/lon)")
        elif c := chyba_polohy(d):
            err.append(f"dům {cp}: {c}")

    for z in zaz:
        k = z.get("klic", "?")
        for f in ("klic", "druh", "datum", "nazev", "shrnuti"):
            if not z.get(f):
                err.append(f"zápis {k}: chybí pole '{f}'")
        if z.get("druh") and z["druh"] not in DRUHY:
            err.append(f"zápis {k}: neznámý druh '{z['druh']}' (povolené: {', '.join(sorted(DRUHY))})")
        if c := chyba_odkazu(z.get("odkaz")):
            err.append(f"zápis {k}: {c}")
        elif re.search(r"\s", str(z.get("odkaz", "")).strip()):   # „…/detail/3888 (snímek 166)“: odkaz pak nikam nevede
            err.append(f"zápis {k}: odkaz obsahuje mezeru – jen adresa, číslo snímku patří do pole 'snimek'")
        data_v(f"zápis {k}", z.get("datum"))
        if z.get("svazek") and z["svazek"] not in svazky:
            err.append(f"zápis {k}: svazek '{z['svazek']}' není v data/svazky.json")
        sv = svazky.get(z.get("svazek", ""), {})
        if not z.get("odkaz") and not sv.get("url") and not sv.get("soukrome") and z.get("druh") != "L":
            warn.append(f"zápis {k}: chybí odkaz na snímek (pole 'odkaz')")
        if not os.path.exists(os.path.join(ROOT, "vyrezy", k + ".jpg")):
            warn.append(f"zápis {k}: chybí výřez vyrezy/{k}.jpg")
        elif k not in hl and z.get("druh") != "M":   # mapa: čtené místo ukazuje popis, rámeček je volitelný
            warn.append(f"zápis {k}: chybí rámeček (tools/ramecek.py)")
        if k not in prep and z.get("druh") != "M":   # mapa: stačí 'shrnuti', přepis a překlad nejsou nutné
            warn.append(f"zápis {k}: chybí přepis a překlad v data/prepisy.json")
        if k not in cited:
            warn.append(f"zápis {k}: necituje ho žádný dům ani událost obce (doplnit do 'r')")

    for k, sv in svazky.items():
        if c := chyba_odkazu(sv.get("url")):
            err.append(f"svazek {k}: {c}")
    mapy = jload("mapy.json", [])
    for m in mapy:
        if c := chyba_odkazu(m.get("url")):
            err.append(f"mapa {m.get('img')}: {c}")
        if c := chyba_vyrezu(m.get("vyrez")):
            err.append(f"mapa {m.get('img')}: {c}")
        if not os.path.exists(os.path.join(ROOT, "vyrezy", m.get("img", "") + ".jpg")):
            err.append(f"mapa {m.get('img')}: chybí obrázek vyrezy/{m.get('img')}.jpg (tools/vyrez.py)")
        if not m.get("zdroj"):
            warn.append(f"mapa {m.get('img')}: chybí 'zdroj' (odkud mapa je – kvůli autorským právům)")
    for g, ms in skupiny_map([m for m in mapy if not chyba_vyrezu(m.get("vyrez"))]).items():
        if duvod := proc_neprolinat(ms, os.path.join(ROOT, "vyrezy")):
            warn.append(f"mapy skupiny {g}: web je ukáže vedle sebe, ne prolnuté – {duvod} (reference/data.md)")
    for d in jload("dokumenty.json", []):
        for c in d.get("domy", []):
            if str(c) not in D:
                err.append(f"dokument {d.get('img')}: dům '{c}' není v domy.py")
    for name, e in jload("mista.json", {}).items():
        if e.get("lat") is None and e.get("lon") is None:
            warn.append(f"místo {name}: nemá souřadnice (spusťte tools/mista.py)")
        elif c := chyba_polohy(e):
            err.append(f"místo {name}: {c}")
        if c := chyba_odkazu(e.get("odkaz")):
            err.append(f"místo {name}: {c}")

    cfg = jload("web.json", {})
    if c := chyba_odpovedi(cfg.get("prihlaseni")):
        err.append(f"web.json: {c}")
    elif not (cfg.get("prihlaseni") or {}).get("odpoved") and not (cfg.get("prihlaseni") or {}).get("otevreny"):
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

    # podmínky archivů: obrázky, které se bez souhlasu nesmí zveřejnit (tools/podminky.py, reference/podminky.md)
    import podminky
    root = os.path.dirname(DATA)
    otevreny = bool((cfg.get("prihlaseni") or {}).get("otevreny"))
    vd = os.path.join(root, "vyrezy")
    bez_souhlasu = {}   # zpráva (archiv a důvod) → obrázky; po archivech, ať stovky snímků z jednoho archivu nejsou stovky řádků
    for fn in sorted(os.listdir(vd)) if os.path.isdir(vd) else []:
        if not fn.endswith(".jpg"):
            continue
        stav, zprava = podminky.posoud_obrazek(root, fn[:-4])
        if stav == "souhlas":
            bez_souhlasu.setdefault(zprava, []).append(fn[:-4])
        elif stav == "pozor" and "nevýdělečně" in zprava:
            warn.append(f"PODMÍNKY ({fn[:-4]}): {zprava}")
    for zprava, klice in bez_souhlasu.items():
        warn.append(f"PODMÍNKY ({len(klice)} obrázků: {', '.join(klice[:5])}{', …' if len(klice) > 5 else ''}): {zprava}"
                    + (" Na otevřeném webu je u nich jen přepis a odkaz." if otevreny else " Až web otevřeš, bude u nich jen přepis a odkaz."))

    log = os.path.join(DATA, "research_log.md")
    rows = sum(1 for l in open(log, encoding="utf-8-sig") if re.match(r"^\| \d+ \|", l)) if os.path.exists(log) else 0
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
