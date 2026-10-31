#!/usr/bin/env python3
"""Export dat projektu (data/*) do webu ve složce web/.

Čte data/domy.py, data/zaznamy.json, data/svazky.json, data/prepisy.json, data/zvyrazneni.json,
data/mapy.json, data/mista.json, data/web.json, data/dokumenty.json a markdownové poznámky. Zapisuje
web/src/data/site.json, web/src/generated/*, web/public/{img,zdroje}, web/public/prihlaseni.html,
web/nginx.conf a web/netlify/edge-functions/brana.js.

Spouští se z web/ příkazem `npm run data` (nebo přímo `python3 -I tools/export_web.py`, na Windows `python -I -X utf8 …`).
"""
import hashlib, html, json, os, re, shutil, subprocess, sys, unicodedata
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: data projektu tam nejsou, zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
DATA = os.path.join(ROOT, "data")
WEB = os.path.join(ROOT, "web")
VYREZY = os.path.join(ROOT, "vyrezy")      # výřezy zápisů, map a dokumentů (asi 1800 px) – zobrazují se na webu
ZDROJE = os.path.join(ROOT, "zdroje")      # tytéž výřezy v plném rozlišení (proklik)

STATUS = {"doc": "doloženo pramenem", "lit": "z literatury", "prob": "pravděpodobné", "fam": "od pamětníků",
          "unk": "neznámé"}
KINDS = {"N": "křest / narození", "O": "sňatek", "Z": "úmrtí", "I": "rejstřík", "S": "sčítání lidu",
         "G": "gruntovní / pozemková kniha", "K": "katastr", "M": "mapa", "C": "kronika", "L": "literatura",
         "J": "jiný pramen"}


def jload(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_houses():
    ns = {}
    exec(open(os.path.join(DATA, "domy.py"), encoding="utf-8").read(), ns)
    for name, default in (("OBEC", {}), ("OBEC_UDALOSTI", []), ("D", {}), ("ISSUES", [])):
        ns.setdefault(name, default)
    return ns


def record_rows():
    svazky = jload("svazky.json", {})
    rows = []
    for z in jload("zaznamy.json", []):
        sv = svazky.get(z.get("svazek", ""), {})
        key = z["klic"]
        rows.append(dict(
            key=key, kind=z.get("druh", "J"), date=z.get("datum", ""), title=z.get("nazev", key),
            summary=z.get("shrnuti", ""), scan=z.get("snimek", ""),
            archive=sv.get("archiv", ""), volume=sv.get("svazek", ""), vdesc=sv.get("popis", ""),
            portal=sv.get("portal", "archivu"), url=z.get("odkaz") or sv.get("url", ""),
            img=os.path.exists(os.path.join(VYREZY, key + ".jpg")),
            full=os.path.exists(os.path.join(ZDROJE, key + ".jpg")),
        ))
    return rows


def strip_comments(md):
    """Poznámky <!-- … --> v markdownu jsou pro Clauda, ne pro web."""
    return re.sub(r"<!--.*?-->\n?", "", md, flags=re.S)


def group_buttons(md):
    """Odkaz hned pod nadpisem ## skupiny („Celý příběh … →“) přesune na konec skupiny jako tlačítko."""
    parts = re.split(r"(?m)^(?=## )", md)
    for i, part in enumerate(parts):
        m = re.match(r"(## .*\n)\s*\[([^\]]+)\]\(([^)\s]+)\)[ \t]*\n", part)
        if m:
            btn = f'<p class="group-more"><a class="btn btn-ghost" href="{html.escape(m.group(3))}">{html.escape(m.group(2))}</a></p>\n\n'
            parts[i] = m.group(1) + part[m.end():].rstrip("\n") + "\n\n" + btn
    return "".join(parts)


def slugify(text):
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def norm_answer(text):
    """Stejná normalizace jako v prihlaseni.html: bez diakritiky, malá písmena, jen a-z0-9."""
    t = unicodedata.normalize("NFD", text)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]", "", t)


def year_key(text):
    """Řadicí klíč z „1351“, „22. 7. 1351“, „asi 1600“, „1786–1820“ (první čtyřčíslí, pak den a měsíc)."""
    t = str(text or "")
    m = re.search(r"\d{4}", t)
    if not m:
        return 99999999
    parts = re.findall(r"\d+", t[:m.start()])
    d, mo = (parts + [0, 0])[:2] if len(parts) >= 2 else (0, (parts or [0])[0])
    return int(m.group(0)) * 10000 + int(mo) * 100 + int(d)


def magick_bin():   # ImageMagick 7 (magick), jinak 6 (convert) – ten ale ne na Windows, tam je convert.exe jiný program
    return shutil.which("magick") or (os.name != "nt" and shutil.which("convert")) or None


def size(path):
    w, h = subprocess.run([magick_bin(), path + "[0]", "-format", "%w %h", "info:"],
                          capture_output=True, text=True, check=True).stdout.split()
    return int(w), int(h)


def draw_boxes(src, dst, boxes, small):
    """Kopie výřezu v plném rozlišení s nakreslenými rámečky (pokud má stejný poměr stran jako webový výřez,
    na kterém se rámečky měřily). Vrací False, pak se kopíruje bez rámečků."""
    if not os.path.exists(small) or not magick_bin():
        return False
    (W, H), (w, h) = size(src), size(small)
    if abs(W / H - w / h) > 0.015 * (w / h):
        return False
    sw = max(4, round(W / 450))
    cmd = [magick_bin(), src, "-fill", "none", "-stroke", "#d7302a", "-strokewidth", str(sw)]
    for x0, y0, x1, y1 in boxes:
        cmd += ["-draw", f"rectangle {x0 * W:.0f},{y0 * H:.0f},{x1 * W:.0f},{y1 * H:.0f}"]
    subprocess.run(cmd + ["-quality", "90", dst], check=True)
    return True


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def login_files(cfg):
    """Přihlašovací brána: otázka na webu, na serveru (nginx i Netlify) jen otisk odpovědi (SHA-256).
    Stejný otisk spočítá přihlašovací stránka a uloží ho do cookie – samotná odpověď se nikam neukládá."""
    login = cfg.get("prihlaseni") or {}
    answer = norm_answer(login.get("odpoved", ""))
    tpl = open(os.path.join(WEB, "prihlaseni.sablona.html"), encoding="utf-8").read()
    if "rodokmen:" not in tpl:   # stará šablona (do 0.4.0) ukládá do cookie odpověď – s novou bránou by se nikdo nepřihlásil
        sys.exit("CHYBA: web/ má starou šablonu přihlášení. Aktualizujte projekt: python3 -I <skill>/tools/novy_projekt.py <složka projektu>")
    contact = cfg.get("kontakt") or {}
    hint = ""
    if contact.get("email"):
        hint = (f'Neznáte odpověď? Napište {html.escape(contact.get("jmeno", ""))} na '
                f'<a href="mailto:{html.escape(contact["email"])}">{html.escape(contact["email"])}</a>.')
    page = (tpl.replace("{{NAZEV}}", html.escape(cfg.get("nazev") or "Dějiny domu"))
               .replace("{{UVOD}}", html.escape(login.get("uvod") or "Tenhle web není veřejný."))
               .replace("{{OTAZKA}}", html.escape(login.get("otazka") or "Odpověď na otázku"))
               .replace("{{NAPOVEDA}}", hint))
    write(os.path.join(WEB, "public", "prihlaseni.html"), page)

    edge = os.path.join(WEB, "netlify", "edge-functions", "brana.js")
    if answer:
        digest = hashlib.sha256(("rodokmen:" + answer).encode()).hexdigest()
        nginx_map = f'  "{digest}" 1;'
        write(edge, open(os.path.join(WEB, "netlify", "brana.sablona.js"), encoding="utf-8").read().replace("{{HASH}}", digest))
    else:   # bez přihlášení – web je otevřený
        nginx_map = "  default 1;"
        if os.path.exists(edge):
            os.remove(edge)
    nginx = open(os.path.join(WEB, "nginx.sablona.conf"), encoding="utf-8").read().replace("{{ODPOVED}}", nginx_map)
    write(os.path.join(WEB, "nginx.conf"), nginx)
    return bool(answer)


def cited(x, recs):
    """Klíče zápisů z pole „r“, které opravdu existují (neexistující hlásí kontrola.py)."""
    return [r for r in x.get("r", []) if r in recs]


def owner_year(o):
    """Rok držitele pro řazení: „od“, a když je neznámé („?“), aspoň „do“."""
    return o["since"] if re.search(r"\d", o["since"]) else o["until"]


def event(e, recs):
    return dict(year=str(e.get("rok", "")), text=e.get("text", ""), st=e.get("st", "unk"), status=STATUS.get(e.get("st"), ""),
                source=e.get("zdroj", ""), records=cited(e, recs))


def main():
    ns = load_houses()
    OBEC, D, ISSUES = ns["OBEC"], ns["D"], ns["ISSUES"]
    cfg = jload("web.json", {})
    login = cfg.get("prihlaseni") or {}
    if "--nasazeni" in sys.argv and not norm_answer(login.get("odpoved", "")) and not login.get("otevreny"):
        sys.exit("CHYBA: v data/web.json není odpověď na přihlašovací otázku – web by byl otevřený komukoli.\n"
                 "Nastavte prihlaseni.odpoved, nebo (jen když to opravdu chcete) prihlaseni.otevreny: true.")
    docs_cfg = [d for d in jload("dokumenty.json", []) if not d.get("skryt")]   # "skryt": true = na web nedávat
    maps_cfg = jload("mapy.json", [])
    recs = {r["key"]: r for r in record_rows()}

    houses = {}
    for cp, d in D.items():
        slug = slugify(cp)
        people = [dict(name=o.get("n", ""), years=o.get("y", ""), role=o.get("role", ""), facts=o.get("f", []),
                       st=o.get("st", "unk"), status=STATUS.get(o.get("st"), ""), note=o.get("note", ""),
                       records=cited(o, recs)) for o in d.get("obyvatele", [])]
        owners = [dict(since=str(o.get("od", "")), until=str(o.get("do", "")), name=o.get("n", ""), how=o.get("jak", ""),
                       st=o.get("st", "unk"), status=STATUS.get(o.get("st"), ""), note=o.get("note", ""),
                       records=cited(o, recs)) for o in d.get("drzitele", [])]
        # neznámý začátek („?“ do 1820) řadí podle konce – před toho, kdo ve stejném roce začal
        owners.sort(key=lambda o: (year_key(owner_year(o)), bool(re.search(r"\d", o["since"]))))
        events = sorted((event(e, recs) for e in d.get("udalosti", [])), key=lambda e: year_key(e["year"]))
        refs = [r for x in events + owners + people for r in x["records"]]
        houses[slug] = dict(
            cp=str(cp), slug=slug, name=d.get("nazev", ""), kind=d.get("druh", ""), st=d.get("st", "unk"),
            status=STATUS.get(d.get("st"), ""), desc=d.get("popis", ""), note=d.get("note", ""),
            lat=d.get("lat"), lon=d.get("lon"), numbers=[dict(when=a, num=b) for a, b in d.get("cisla", [])],
            events=events, owners=owners, people=people, records=list(dict.fromkeys(refs)),
            docs=[dict(img=x["img"], caption=x["popis"]) for x in docs_cfg if str(cp) in [str(c) for c in x.get("domy", [])]
                  and os.path.exists(os.path.join(VYREZY, x["img"] + ".jpg"))],
        )
    houses = dict(sorted(houses.items(), key=lambda kv: (int(re.match(r"\d*", kv[1]["cp"]).group(0) or 99999), kv[1]["cp"])))

    village_events = sorted((event(e, recs) for e in ns["OBEC_UDALOSTI"]), key=lambda e: year_key(e["year"]))
    village = dict(name=OBEC.get("nazev", ""), otherNames=OBEC.get("jine_nazvy", ""), municipality=OBEC.get("obec", ""),
                   parish=OBEC.get("farnost", ""), estate=OBEC.get("panstvi", ""), desc=OBEC.get("popis", ""),
                   lat=OBEC.get("lat"), lon=OBEC.get("lon"), events=village_events)

    refs = {}
    for h in houses.values():
        for r in h["records"]:
            refs.setdefault(r, []).append(h["slug"])
    village_refs = {r for e in village_events for r in e["records"]}
    hl = jload("zvyrazneni.json", {})
    prep = jload("prepisy.json", {})
    records = []
    for key, r in recs.items():
        r = dict(r)
        r["boxes"] = hl.get(key, {}).get("boxes", [])
        tr = prep.get(key, {})
        r["orig"], r["cs"] = tr.get("orig", ""), tr.get("cs", "")
        r["kindName"] = KINDS.get(r["kind"], r["kind"])
        r["houses"] = list(dict.fromkeys(refs.get(key, [])))
        r["village"] = key in village_refs
        records.append(r)

    maps = [dict(img=m["img"], year=str(m.get("rok", "")), title=m.get("nazev", ""), source=m.get("zdroj", ""),
                 url=m.get("url", ""), desc=m.get("popis", ""), group=m.get("skupina", ""),
                 full=os.path.exists(os.path.join(ZDROJE, m["img"] + ".jpg")))
            for m in maps_cfg if os.path.exists(os.path.join(VYREZY, m["img"] + ".jpg"))]
    maps.sort(key=lambda m: year_key(m["year"]))

    places = [dict(name=n, lat=e["lat"], lon=e["lon"], desc=e.get("popis", ""), kind=e.get("druh", ""),
                   link=e.get("odkaz", ""), linkText=e.get("odkaz_text", ""), approx=bool(e.get("priblizne")))
              for n, e in jload("mista.json", {}).items() if "lat" in e]

    years = [year_key(e["year"]) // 10000 for e in village_events] + \
            [year_key(e["year"]) // 10000 for h in houses.values() for e in h["events"]] + \
            [year_key(owner_year(o)) // 10000 for h in houses.values() for o in h["owners"]]
    years = [y for y in years if y < 9999]
    stats = dict(houses=len(houses), records=len(records), maps=len(maps),
                 people=sum(len(h["people"]) for h in houses.values()),
                 owners=sum(len(h["owners"]) for h in houses.values()), oldest=min(years) if years else None)

    has_story = os.path.exists(os.path.join(DATA, "pribeh.md"))
    public_cfg = {k: v for k, v in cfg.items() if k != "prihlaseni"}
    # další příběhy: data/pribeh_<slug>.md → /pribehy/<slug>/
    extra_stories = []
    for fn in sorted(os.listdir(DATA)):
        m = re.match(r"pribeh_([a-z0-9-]+)\.md$", fn)
        if not m:
            continue
        text = strip_comments(open(os.path.join(DATA, fn), encoding="utf-8").read())
        fm = dict(re.findall(r"^(title|lead|poradi|obdobi|obrazek):\s*(.*)$", text.split("---")[1] if text.startswith("---") else "", re.M))
        extra_stories.append(dict(slug=m.group(1), title=fm.get("title", m.group(1)).strip().strip("'\""),
                                  lead=fm.get("lead", "").strip().strip("'\""), text=text,
                                  poradi=int(fm.get("poradi", "99").strip() or 99),
                                  obdobi=fm.get("obdobi", "").strip(), obrazek=fm.get("obrazek", "").strip()))
    extra_stories.sort(key=lambda st: (st["poradi"], st["slug"]))
    public_cfg["maPribeh"] = has_story or bool(extra_stories)
    public_cfg["dalsiPribehy"] = [{k: v for k, v in st.items() if k != "text"} for st in extra_stories]
    main_house = slugify(cfg.get("hlavni_dum", "")) or next(iter(houses), "")
    site = dict(config=public_cfg, village=village, houses=houses, mainHouse=main_house if main_house in houses else None,
                records=records, maps=maps, places=places, stats=stats,
                issues=[dict(title=i, text="") if isinstance(i, str) else dict(title=i[0], text=i[1]) for i in ISSUES],
                docs=[dict(img=d["img"], caption=d["popis"], houses=[slugify(c) for c in d.get("domy", []) if slugify(c) in houses],
                           group=d.get("skupina", ""), order=d.get("poradi", 99), pair=d.get("par", ""), wide=d.get("format") == "sirka",
                           full=os.path.exists(os.path.join(ZDROJE, d["img"] + ".jpg")))
                      for d in docs_cfg if os.path.exists(os.path.join(VYREZY, d["img"] + ".jpg"))])

    write(os.path.join(WEB, "src", "data", "site.json"), json.dumps(site, ensure_ascii=False, indent=1))
    gen_dir = os.path.join(WEB, "src", "generated")
    for src, dst in (("archivni_dotazy.md", "dotazy.md"), ("research_log.md", "denik.md"), ("zajimavosti.md", "zajimavosti.md")):
        path = os.path.join(DATA, src)
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        text = strip_comments(re.sub(r"^# .*\n", "", text, count=1))
        write(os.path.join(gen_dir, dst), group_buttons(text) if src == "zajimavosti.md" else text)
    story = os.path.join(DATA, "pribeh.md")
    write(os.path.join(gen_dir, "pribeh.md"), strip_comments(open(story, encoding="utf-8").read()) if has_story else "---\ntitle: Příběh\nlead: ''\n---\n")
    stories_dir = os.path.join(gen_dir, "pribehy")
    os.makedirs(stories_dir, exist_ok=True)
    for old in os.listdir(stories_dir):
        if old.endswith(".md") and old[:-3] not in {st["slug"] for st in extra_stories}:
            os.remove(os.path.join(stories_dir, old))
    for st in extra_stories:
        write(os.path.join(stories_dir, st["slug"] + ".md"), st["text"])

    gated = login_files(cfg)

    copied = 0
    zv = os.path.join(DATA, "zvyrazneni.json")
    hl_mtime = os.path.getmtime(zv) if os.path.exists(zv) else 0
    images = list(recs) + [d["img"] for d in docs_cfg] + [m["img"] for m in maps_cfg] + \
        ([cfg["uvod"]["foto"]] if cfg.get("uvod", {}).get("foto") else []) + \
        [st["obrazek"] for st in extra_stories if st.get("obrazek")]
    for sub, src_dir in (("img", VYREZY), ("zdroje", ZDROJE)):
        dst_dir = os.path.join(WEB, "public", sub)
        os.makedirs(dst_dir, exist_ok=True)
        for key in images:
            src = os.path.join(src_dir, key + ".jpg")
            dst = os.path.join(dst_dir, key + ".jpg")
            if not os.path.exists(src):
                continue
            boxes = hl.get(key, {}).get("boxes", [])
            stale = not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst) \
                or (sub == "zdroje" and boxes and hl_mtime > os.path.getmtime(dst))
            if not stale:
                continue
            if sub == "zdroje" and boxes and draw_boxes(src, dst, boxes, os.path.join(VYREZY, key + ".jpg")):
                copied += 1
                continue
            shutil.copy2(src, dst)
            copied += 1
    print(f"{len(houses)} domů, {stats['owners']} držitelů, {stats['people']} obyvatel, {len(records)} zápisů, "
          f"{len(maps)} map, {len(village_events)} událostí obce; zkopírováno {copied} obrázků; "
          f"přihlášení {'zapnuté' if gated else 'VYPNUTÉ (web je otevřený)'}")

    targets = dict(dum=houses, zdroj=recs)
    texts = {f: open(os.path.join(gen_dir, f), encoding="utf-8").read() for f in ("pribeh.md", "zajimavosti.md")}
    texts.update({f"pribeh_{st['slug']}.md": st["text"] for st in extra_stories})
    texts["web.json"] = json.dumps(cfg, ensure_ascii=False)
    broken = [(f, m.group(0)) for f, t in texts.items()
              for m in re.finditer(r"/(dum|zdroj)/([^/\s)\"'#?<>\]]+)", t) if m.group(2) not in targets[m.group(1)]]
    for f, link in dict.fromkeys(broken):
        print(f"POZOR: nefunkční odkaz {link}/ v {f} – oprav ho (adresy stránek jsou ve web/src/data/site.json)")


if __name__ == "__main__":
    main()
