#!/usr/bin/env python3
"""Hřbitovní pasporty obcí na GisOnline.cz (TopGis): hroby a zemřelí se jménem, narozením, úmrtím a pohřbem.

Pokrývá 20. století, kam online archivy nesahají. Číslo popisné u hrobu není: shoda se jménem obyvatele je vodítko,
ověř ji matrikou, kronikou nebo u rodiny. Fotky náhrobků jen odkazem (autor neznámý), jména zemřelých
za posledních ~50 let na veřejný web jen se souhlasem rodiny (reference/podminky.md).

  python3 -I tools/hroby.py najdi "Brod nad Dyjí" [--alias brod-hrbitov …]   najde projekt, ověří obec podle RÚIAN
  python3 -I tools/hroby.py stahni 353 [--znovu]                              uloží data/hroby.json
  python3 -I tools/hroby.py hledej Novák [Nováková …]                          zemřelí podle příjmení

Seznam projektů GisOnline veřejný není: `najdi` zkouší jen adresy odvozené z názvu obce (app.gisonline.cz/<alias>).
Když nic nenajde, hledej na webu obce „mapa hřbitova“ nebo „hrobová místa“ – alias je konec adresy mapy.
Obce stejného jména jsou časté: projekt ber, jen když obec a okres z výpisu sedí.
"""
import argparse, datetime as dt, json, os, re, sys, unicodedata, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "hroby.json")

GISONLINE = "https://app.gisonline.cz"
RUIAN = "https://ags.cuzk.gov.cz/arcgis/rest/services/RUIAN/MapServer/identify"
VRSTVY_RUIAN = {12: "obec", 15: "okres"}
ROK = re.compile(r"1[5-9]\d\d|20\d\d")


def stahni_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dejiny-domu (skill, on user request)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def api(cesta):
    return json.loads(stahni_url(GISONLINE + cesta))


def norm(s):
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def aliasy(obec):
    s = re.sub(r"[^a-z0-9]+", "-", norm(obec)).strip("-")
    return list(dict.fromkeys([s, f"{s}-hrbitov", f"hrbitov-{s}", f"{s}-hroby", s.replace("-", "")]))


def projekt_z_aliasu(alias):
    """GisOnline mapuje alias na ID jen v HTML stránce projektu (GO={…"project":{"id":N}})."""
    m = re.search(r'"project":\{"id":(\d+)', stahni_url(f"{GISONLINE}/{urllib.parse.quote(alias)}"))
    return int(m.group(1)) if m else None


def vrstvy_hrobu(projekt):
    """Vrstvy hrobů s podřízenou tabulkou zemřelých: (vrstva, ID tabulky zemřelých)."""
    for v in projekt["layers"]["items"]:
        for sl in v.get("attributes") or []:
            if sl.get("type") == "children" and v.get("public"):
                yield v, sl["children"]["childId"]


def obec_v_bode(x, y):
    """Obec a okres podle RÚIAN v bodě S-JTSK – projekt „Pavlov“ může být jiný Pavlov, než hledáme."""
    q = urllib.parse.urlencode({
        "geometry": f"{x},{y}", "geometryType": "esriGeometryPoint", "sr": 5514,
        "layers": "all:" + ",".join(map(str, VRSTVY_RUIAN)), "tolerance": 0,
        "mapExtent": f"{x - 500},{y - 500},{x + 500},{y + 500}", "imageDisplay": "100,100,96",
        "returnGeometry": "false", "f": "json"})
    vysledky = json.loads(stahni_url(f"{RUIAN}?{q}")).get("results", [])
    return {VRSTVY_RUIAN[r["layerId"]]: r["value"] for r in vysledky if r["layerId"] in VRSTVY_RUIAN}


def najdi(a):
    nalezeno = False
    for alias in a.alias or aliasy(a.obec):
        pid = projekt_z_aliasu(alias)
        if not pid:
            print(f"  {alias}: nic")
            continue
        p = api(f"/api2/projects/{pid}")
        hroby = list(vrstvy_hrobu(p))
        kde = obec_v_bode(*p["map"]["center"])
        print(f"  {alias}: projekt {pid} „{p['title']}“, střed v obci {kde.get('obec', '?')} (okres {kde.get('okres', '?')})")
        for v, child in hroby:
            print(f"      vrstva {v['id']} „{v['title']}“, zemřelí v tabulce {child}")
        nalezeno |= bool(hroby)
    if nalezeno:
        print("\nOvěř, že obec a okres sedí, pak: python3 -I tools/hroby.py stahni <projekt>")
    else:
        print("\nPasport hřbitova nenalezen (zkus --alias podle webu obce, odkaz „mapa hřbitova“).")


def osoba(r):
    return {"jmeno": r.get("prij_jmeno"), "narozeni": r.get("narozeni"), "umrti": r.get("umrti"),
            "pohreb": r.get("pohreb"), "poradi": r.get("poradi")}


def rok(datum):
    m = ROK.search(datum or "")
    return int(m.group(0)) if m else None


def rozsah(hroby):
    roky = sorted(r for h in hroby for o in h["zemreli"] if (r := rok(o["umrti"])))
    return f"{roky[0]}–{roky[-1]}" if roky else "neznámé"


def projekt_nebo_konec():
    """`najdi` jde spustit odkudkoli; data jen v projektu – ze složky skillu by zápis šel do skillu."""
    if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):
        sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
                 f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")


def nacti():
    projekt_nebo_konec()
    with open(OUT, encoding="utf-8") as f:
        return json.load(f)


def stahni(a):
    projekt_nebo_konec()
    if os.path.exists(OUT) and not a.znovu and nacti()["zdroj"]["projekt"] == a.projekt:
        sys.exit(f"{OUT} už projekt {a.projekt} má (staženo {nacti()['zdroj']['stazeno']}); znovu jen s --znovu")
    p = api(f"/api2/projects/{a.projekt}")
    vrstvy = list(vrstvy_hrobu(p))
    if not vrstvy:
        sys.exit(f"projekt {a.projekt} „{p['title']}“ nemá veřejnou vrstvu hrobů se zemřelými")
    kde = obec_v_bode(*p["map"]["center"])
    hroby = []
    for v, child in vrstvy:
        zemreli = {}
        for f in api(f"/api2/layers/{child}")["features"]:
            r = f["properties"]
            zemreli.setdefault((r.get("parent_id") or {}).get("key"), []).append(osoba(r))
        for f in api(f"/api2/layers/{v['id']}")["features"]:
            r = f["properties"]
            hroby.append({
                "cislo": r.get("cislo_hrob"), "typ": (r.get("typ_hrobu") or {}).get("value"),
                "zemreli": sorted(zemreli.get(r.get(v["fidName"]), []), key=lambda o: o["poradi"] or 0),
                "foto": [f"{GISONLINE}/api2/files/{i}" for i in r.get("foto") or []]})
    hroby.sort(key=lambda h: [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", h["cislo"] or "")])
    out = {"zdroj": {"nazev": f"Hřbitovní pasport, {p['title'].strip()}", "url": f"{GISONLINE}/{p.get('alias') or a.projekt}",
                     "projekt": a.projekt, "obec": kde.get("obec"), "okres": kde.get("okres"),
                     "stazeno": dt.date.today().isoformat()},
           "hroby": hroby}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{OUT}: {len(hroby)} hrobů, {sum(len(h['zemreli']) for h in hroby)} zemřelých "
          f"({kde.get('obec')}, okres {kde.get('okres')}), roky úmrtí {rozsah(hroby)}")


def kmen(prijmeni):
    """Ženské tvary k mužským: Lisáková/Lisák → lisak, Norková/Norek → nork, Novotná/Novotný → novotn."""
    s = norm(prijmeni)
    for konc in ("ova", "a", "y"):
        if s.endswith(konc) and len(s) > len(konc) + 2:
            s = s[: -len(konc)]
            break
    return s[:-2] + "k" if s.endswith("ek") else s


def zemreli(data):
    """(osoba, hrob) pro všechny pohřbené."""
    return [(o, h) for h in data["hroby"] for o in h["zemreli"]]


def prijmeni_a_jmeno(o):
    """Pasport píše „Příjmení Jméno“; chybějící část = prázdný řetězec."""
    slova = (o["jmeno"] or "").split()
    return (slova[0] if slova else ""), (slova[1] if len(slova) > 1 else "")


def hledej(a):
    data = nacti()
    print(data["zdroj"]["nazev"], data["zdroj"]["url"])
    hledane = {kmen(p) for p in a.prijmeni}
    for o, h in zemreli(data):
        if kmen(prijmeni_a_jmeno(o)[0]) in hledane:
            print(f"  hrob {h['cislo']}: {o['jmeno']}  * {o['narozeni'] or '?'}  † {o['umrti'] or '?'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="prikaz", required=True)
    s = sub.add_parser("najdi"); s.add_argument("obec"); s.add_argument("--alias", action="append"); s.set_defaults(fn=najdi)
    s = sub.add_parser("stahni"); s.add_argument("projekt", type=int); s.add_argument("--znovu", action="store_true")
    s.set_defaults(fn=stahni)
    s = sub.add_parser("hledej"); s.add_argument("prijmeni", nargs="+"); s.set_defaults(fn=hledej)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
