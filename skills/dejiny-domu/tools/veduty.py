#!/usr/bin/env python3
"""Veduty, pohlednice, fotografie a mapy obce z digitálních knihoven (Česká digitální knihovna: MZK, UK, další).

Grafické sbírky a mapy MZK (Mollova sbírka, grafiky.mzk.cz, mapy.mzk.cz) i sbírky jiných knihoven v jednom hledání.
Hledá podle geografického hesla katalogu („Telč (Česko)“, „Smíchov (Praha, Česko)“), ne v názvu – „Pavlov“ by našel
portréty I. P. Pavlova. Co heslo nemá, nástroj nenajde: ručně mapy.mzk.cz a grafiky.mzk.cz (reference/portaly.md).

Použití:
  veduty.py "<obec nebo část obce>" [od-do]   – rok | druh | název | heslo | žánr | knihovna | přístup | odkaz
Heslo ukáže, která ze stejnojmenných obcí to je („Pavlov (Břeclav, Česko)“).
Přístup: public = volně online, onsite = jen v knihovně. Obrázek do výstupu jen volné dílo a podle podmínek knihovny
(reference/podminky.md, Kramerius MZK = souhlas); jinak popis, citace a odkaz."""
import json, os, re, sys, unicodedata, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

CDK = "https://api.ceskadigitalniknihovna.cz/search/api/client/v7.0/search"
ODKAZ = "https://www.ceskadigitalniknihovna.cz/uuid/"
STRANA, NEJVIC = 100, 300
DRUHY = {"graphic": "obraz", "map": "mapa"}
POLE = "pid,title.search,model,date.str,date_range_start.year,cdk.collection,licenses,genres.search,geographic_names.search"


def dotaz(misto, roky=None):
    q = f'geographic_names.search:"{misto}" AND model:({" OR ".join(DRUHY)})'
    if roky:
        q += f" AND date_range_start.year:[{roky[0]} TO {roky[1]}]"
    return q


def hledej(misto, roky=None):
    """Všechny strany do NEJVIC. Vrací (záznamy, celkem v knihovnách)."""
    zaznamy, celkem = [], 0
    for start in range(0, NEJVIC, STRANA):
        q = urllib.parse.urlencode({"q": dotaz(misto, roky), "fl": POLE, "rows": STRANA, "start": start,
                                    "sort": "date_range_start.year asc"})
        with urllib.request.urlopen(f"{CDK}?{q}", timeout=60) as r:
            odpoved = json.load(r)["response"]
        zaznamy += odpoved["docs"]
        celkem = odpoved["numFound"]
        if len(zaznamy) >= celkem:
            break
    return zaznamy, celkem


def bez_diakritiky(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def heslo(z, misto):
    """Heslo, které je obec sama („Telč (Česko)“, „Telč (Česko : oblast)“), ne jen slovo v jiném („Telč Region“)."""
    hledane = bez_diakritiky(misto)
    return next((h for h in z.get("geographic_names.search") or []
                 if re.match(rf"{re.escape(hledane)}( \(|$)", bez_diakritiky(h))), None)


def zanr(z):
    """Poslední žánr katalogu: anglické a obecné („graphic“, „topographic maps“) jdou před českými („veduty“)."""
    zanry = [g for g in z.get("genres.search") or [] if g not in DRUHY]
    return zanry[-1] if zanry else ""


def radek(z, misto):
    return " | ".join([z.get("date.str") or "?", DRUHY.get(z.get("model"), z.get("model")), z.get("title.search") or "",
                       heslo(z, misto), zanr(z), ",".join(z.get("cdk.collection") or []),
                       ",".join(z.get("licenses") or []), ODKAZ + z["pid"].removeprefix("uuid:")])


def vypis(zaznamy, misto):
    mistni = [z for z in zaznamy if heslo(z, misto)]
    radky = []
    for model, nazev in (("graphic", "Veduty, pohlednice, fotografie"), ("map", "Mapy a plány")):
        skupina = [z for z in mistni if z.get("model") == model]
        if skupina:
            radky += [f"\n{nazev}: {len(skupina)}"] + ["  " + radek(z, misto) for z in skupina]
    return radky


def roky_z(arg):
    m = re.fullmatch(r"(\d{4})-(\d{4})", arg or "")
    if not m:
        sys.exit(f"Roky zadej jako 1800-1950, ne „{arg}“")
    return m.groups()


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    misto, roky = argv[1], (roky_z(argv[2]) if len(argv) > 2 else None)
    zaznamy, celkem = hledej(misto, roky)
    radky = vypis(zaznamy, misto)
    if not radky:
        print(f"V digitálních knihovnách nic s heslem „{misto}“. Ručně: mapy.mzk.cz, grafiky.mzk.cz, "
              "pohlednice a fotky muzeí: esbirky.py.")
        return
    if celkem > len(zaznamy):
        print(f"Knihovny mají {celkem} záznamů, nástroj vypíše nejvýš {NEJVIC} – zúž roky (veduty.py \"{misto}\" 1800-1900).")
    print("\n".join(radky).lstrip("\n"))
    print("\nOdkaz otevře uživatel v prohlížeči. public = volně online, onsite = jen v knihovně.")


if __name__ == "__main__":
    main(sys.argv)
