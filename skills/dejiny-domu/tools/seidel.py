#!/usr/bin/env python3
"""Fotografie z Fotoateliéru Seidel v Českém Krumlově (Fotobanka Musea Fotoateliér Seidel), Šumava a Pošumaví 1880–1960.

Dva druhy nálezů:
- místo: pohledy na obec, domy, kostel, pohlednice (obec je v popisu nebo v klíčových slovech);
- zákazník: ateliérový portrét lidí z obce – v knize zakázek je jméno a adresa často s číslem domu
  („Chromý Matěj, Slavče 19, 16. 4. 1931“). Zákazník je jen v detailu: nástroj ho načte u prvních 30 snímků.

Použití:
  seidel.py "<obec>"       – id | rok | popis | zákazník a adresa | odkaz
  seidel.py detail <id>    – vše o snímku (číslo negativu, popisek na desce, klíčová slova)
Fotky smí do výstupu jen se souhlasem muzea (prodává jen tisky, licenci nenabízí); jinak popis, citace a odkaz."""
import json, os, sys, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)
from nazvy import zminuje_obec   # porovnání názvů obcí (nazvy.py)

WEB = "https://fotobanka.seidel.cz"
API = WEB + "/api/collection"
STRAN = 5        # 20 snímků na stranu
NEJVIC_DETAILU = 30   # zákazníky hledá v detailu, každý je jeden dotaz


def cti(adresa):
    with urllib.request.urlopen(adresa, timeout=60) as r:
        return json.load(r)


def hledej(obec):
    """Snímky z prvních STRAN stran. Vrací (snímky, celkem podle webu)."""
    snimky, celkem = [], 0
    for strana in range(1, STRAN + 1):
        data = cti(f"{API}/?" + urllib.parse.urlencode({"lf": obec, "page": strana}))
        snimky += data.get("results") or []
        celkem = data.get("count") or 0
        if not data.get("next"):
            break
    return snimky, celkem


def detail_snimku(id_foto):
    try:
        return cti(f"{API}/detail/{urllib.parse.quote(id_foto)}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def zminka(s, obec):
    """Kde snímek obec zmiňuje: "zakaznik" (adresa zákazníka), "misto" (popis, klíčová slova, popisek na desce), jinak None."""
    # hledání webu je volné (Mohuřice → Moric), obec ověří slovo v adrese nebo popisu
    if zminuje_obec(s.get("adresa"), obec):
        return "zakaznik"
    if zminuje_obec(" ".join([s.get("popis") or "", s.get("text_desk") or ""] + (s.get("keywords") or [])), obec):
        return "misto"
    return None


def zakaznik(d):
    return ", ".join(x for x in (d.get("jmeno"), d.get("adresa")) if x)


def odkaz(id_foto):
    return f"{WEB}/fotobanka/detail/{id_foto}"


def roztrid(snimky, obec, nacti=detail_snimku):
    """{"misto": [...], "zakaznik": [...]}. Prvních NEJVIC_DETAILU načte celé (zákazník je jen v detailu),
    u dalších zůstane výpis hledání. Snímky, které obec nezmiňují (volné hledání webu), vypadnou."""
    skupiny = {"misto": [], "zakaznik": []}
    for i, s in enumerate(snimky):
        if i < NEJVIC_DETAILU:
            s = nacti(s["id_foto"]) or s
        kde = zminka(s, obec)
        if kde:
            skupiny[kde].append(s)
    return skupiny


def radek(s):
    casti = [s["id_foto"], s.get("rok") or s.get("datum_vznik") or "", s.get("popis") or "", zakaznik(s), odkaz(s["id_foto"])]
    return "  " + " | ".join(c for c in casti if c)


def detail(id_foto):
    d = detail_snimku(id_foto)
    if not d:
        sys.exit(f"Snímek {id_foto} ve Fotobance Seidel není.")
    radky = [("Popis", d.get("popis")), ("Rok", d.get("rok")), ("Datum", d.get("datum_vznik")),
             ("Zákazník", d.get("jmeno")), ("Adresa", d.get("adresa")), ("Popisek na desce", d.get("text_desk")),
             ("Negativ č.", d.get("negativ")), ("Technika", d.get("legacy_postup")),
             ("Klíčová slova", ", ".join(d.get("keywords") or [])), ("Odkaz", odkaz(d["id_foto"])),
             ("Citace", f"Museum Fotoateliér Seidel, Český Krumlov, negativ č. {d.get('negativ') or '?'}, "
                        f"{d.get('datum_vznik') or d.get('rok') or 'nedatováno'}, {odkaz(d['id_foto'])}"),
             ("Obrázek do výstupu", "jen se souhlasem muzea (seidel.cz, Regionální muzeum v Českém Krumlově)")]
    return [f"{k}: {v}" for k, v in radky if v]


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        if len(argv) < 3:
            sys.exit("Použití: seidel.py detail <id> (číslo z výpisu)")
        print("\n".join(detail(argv[2])))
        return
    obec = argv[1]
    snimky, celkem = hledej(obec)
    skupiny = roztrid(snimky, obec)
    if not any(skupiny.values()):
        print(f"Ve Fotobance Seidel nic k „{obec}“ (prošlo {len(snimky)} z {celkem}). Ateliér fotil hlavně "
              "Krumlovsko, Šumavu a Pošumaví; zkus i německý název obce.")
        return
    if celkem > len(snimky):
        print(f"Web našel {celkem} snímků, nástroj prošel prvních {len(snimky)}.")
    for kde, nazev in (("misto", "Obec na snímku"), ("zakaznik", "Zákazníci ateliéru z obce (portréty)")):
        if skupiny[kde]:
            print(f"\n{nazev}: {len(skupiny[kde])}")
            print("\n".join(radek(s) for s in skupiny[kde]))
    if len(snimky) > NEJVIC_DETAILU:
        print(f"\nZákazníka nástroj hledal jen v prvních {NEJVIC_DETAILU} snímcích, u dalších: seidel.py detail <id>.")
    print("\nStejnojmenné obce rozliší pošta v adrese („Slavče, P. Křemže“). Fotku otevře uživatel odkazem.\n"
          "Do výstupu popis, jméno a adresa zákazníka s citací, fotka jen se souhlasem muzea.")

if __name__ == "__main__":
    main(sys.argv)
