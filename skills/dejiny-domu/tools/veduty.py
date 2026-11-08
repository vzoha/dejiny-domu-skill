#!/usr/bin/env python3
"""Veduty, pohlednice, fotografie a mapy obce z digitálních knihoven (Česká digitální knihovna: MZK, UK, další).

Grafické sbírky a mapy MZK (Mollova sbírka, grafiky.mzk.cz, mapy.mzk.cz) i sbírky jiných knihoven v jednom hledání.
Hledá podle geografického hesla katalogu („Telč (Česko)“, „Smíchov (Praha, Česko)“), ne v názvu – „Pavlov“ by našel
portréty I. P. Pavlova. Co heslo nemá, nástroj nenajde: ručně mapy.mzk.cz a grafiky.mzk.cz (reference/portaly.md).

Použití:
  veduty.py "<obec nebo část obce>" [od-do]   – rok | druh | název | heslo | žánr | knihovna | přístup | odkaz
  veduty.py mapy <šířka> <délka> [od-do]      – mapy, které místo zakreslují (podle rozsahu mapy v katalogu)
Heslo ukáže, která ze stejnojmenných obcí to je („Pavlov (Břeclav, Česko)“). Malá ves heslo často nemá:
mapy panství, okresů a mapové listy pak najde jen hledání podle polohy (souřadnice z RÚIAN nebo mapy).
Přístup: public = volně online, onsite = jen v knihovně. Obrázek do výstupu jen volné dílo a podle podmínek knihovny
(reference/podminky.md, Kramerius MZK = souhlas); jinak popis, citace a odkaz."""
import json, os, re, sys, unicodedata, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

CDK = "https://api.ceskadigitalniknihovna.cz/search/api/client/v7.0/search"
ODKAZ = "https://www.ceskadigitalniknihovna.cz/uuid/"   # + celé pid „uuid:…“, bez prefixu web skočí na úvod
STRANA, NEJVIC = 100, 300
DRUHY = {"graphic": "obraz", "map": "mapa"}
OKOLI = (0.45, 0.7)   # mapa celá do ± ° šířky a délky od místa: okres, panství, list 1 : 75 000; ne Čechy ani Evropa
POLE = "pid,title.search,model,date.str,date_range_start.year,cdk.collection,licenses,genres.search,geographic_names.search"


def roky_dotaz(roky):
    return f" AND date_range_start.year:[{roky[0]} TO {roky[1]}]" if roky else ""


def dotaz(misto, roky=None):
    return f'geographic_names.search:"{misto}" AND model:({" OR ".join(DRUHY)})' + roky_dotaz(roky)


def dotaz_poloha(sirka, delka, roky=None):
    """Mapy, jejichž rozsah obsahuje místo a vejde se do OKOLI (ENVELOPE je západ, východ, sever, jih)."""
    ds, dd = OKOLI
    bod = f"ENVELOPE({delka}, {delka}, {sirka}, {sirka})"
    okoli = f"ENVELOPE({delka - dd}, {delka + dd}, {sirka + ds}, {sirka - ds})"
    return f'model:map AND coords.bbox:"Intersects({bod})" AND coords.bbox:"IsWithin({okoli})"' + roky_dotaz(roky)


def hledej(q):
    """Všechny strany do NEJVIC. Vrací (záznamy, celkem v knihovnách)."""
    zaznamy, celkem = [], 0
    for start in range(0, NEJVIC, STRANA):
        parametry = urllib.parse.urlencode({"q": q, "fl": POLE, "rows": STRANA, "start": start,
                                            "sort": "date_range_start.year asc"})
        with urllib.request.urlopen(f"{CDK}?{parametry}", timeout=60) as r:
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
                       heslo(z, misto), zanr(z), *knihovna_a_odkaz(z)])


def radek_mapy(z):
    return " | ".join([z.get("date.str") or "?", z.get("title.search") or "", zanr(z), *knihovna_a_odkaz(z)])


def knihovna_a_odkaz(z):
    return [",".join(z.get("cdk.collection") or []), ",".join(z.get("licenses") or []), ODKAZ + z["pid"]]


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


def souradnice(sirka, delka):
    try:
        sirka, delka = float(sirka.replace(",", ".")), float(delka.replace(",", "."))
    except ValueError:
        sys.exit(f"Souřadnice zadej jako 48.830 14.615 (šířka, délka ve stupních), ne „{sirka} {delka}“")
    if not (48 < sirka < 51.5 and 12 < delka < 19):
        sys.exit(f"{sirka} {delka} není v Česku – nejdřív šířka (48–51), pak délka (12–19)")
    return sirka, delka


def zuz_roky(celkem, zaznamy, priklad):
    if celkem > len(zaznamy):
        print(f"Knihovny mají {celkem} záznamů, nástroj vypíše nejvýš {NEJVIC} – zúž roky ({priklad} 1800-1900).")


def mapy(argv):
    sirka, delka = souradnice(*argv[:2])
    roky = roky_z(argv[2]) if len(argv) > 2 else None
    zaznamy, celkem = hledej(dotaz_poloha(sirka, delka, roky))
    if not zaznamy:
        print(f"Žádná mapa v knihovnách místo {sirka} {delka} nezakresluje (nebo nemá rozsah v katalogu).")
        return
    zuz_roky(celkem, zaznamy, f"veduty.py mapy {sirka} {delka}")
    print(f"Mapy, které místo zakreslují (od listů po okresy): {len(zaznamy)}")
    print("\n".join("  " + radek_mapy(z) for z in zaznamy))
    print("\nRozsah je z katalogu, místo bývá u okraje listu. Odkaz otevře uživatel v prohlížeči.")


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "mapy":
        if len(argv) < 4:
            sys.exit("Použití: veduty.py mapy <šířka> <délka> [od-do]")
        mapy(argv[2:])
        return
    misto, roky = argv[1], (roky_z(argv[2]) if len(argv) > 2 else None)
    zaznamy, celkem = hledej(dotaz(misto, roky))
    radky = vypis(zaznamy, misto)
    if not radky:
        print(f"V digitálních knihovnách nic s heslem „{misto}“. Mapy podle polohy: veduty.py mapy <šířka> <délka>. "
              "Ručně: mapy.mzk.cz, grafiky.mzk.cz, pohlednice a fotky muzeí: esbirky.py.")
        return
    zuz_roky(celkem, zaznamy, f'veduty.py "{misto}"')
    print("\n".join(radky).lstrip("\n"))
    print("\nOdkaz otevře uživatel v prohlížeči. public = volně online, onsite = jen v knihovně.")


if __name__ == "__main__":
    main(sys.argv)
