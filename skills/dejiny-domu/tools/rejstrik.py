#!/usr/bin/env python3
"""Firmy, družstva a společenství vlastníků se sídlem v domě (ARES Ministerstva financí, veřejný rejstřík).

K dějinám domu po roce 1990: společenství vlastníků jednotek (SVJ) a jeho datum vzniku ≈ kdy se prodávaly
byty; bytové družstvo jako vlastník; hospoda, obchod nebo dílna, které v domě sídlí. Sídlo není doklad
vlastnictví ani bydliště. ARES podle adresy najde jen dnes zapsané subjekty, zaniklé jen podle názvu
(or.justice.cz, „Platné i neplatné“). Podnikající fyzické osoby jen spočítá, jména nevypíše (žijící lidé).

Použití:
  rejstrik.py "<část obce>" <čp>   – IČO | název | právní forma | zápis | adresa sídla | odkaz na výpis a sbírku listin
  rejstrik.py detail <IČO>         – názvy a sídla s daty, předmět činnosti, ostatní skutečnosti, spisová značka
Část obce jako v adrese („Holešovice“, „Lniště“), čp. = číslo popisné, ne orientační."""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

API = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"   # veřejné API, dokumentace /v3/api-docs
NEJVIC = 500      # subjektů v jednom domě; víc má jen kancelářská budova
POPISNE = 1       # typCisloDomovni: 1 = číslo popisné, 2 = evidenční (jiný dům se stejným číslem)
FYZICKA_OSOBA = re.compile(r"fyzick|rolník", re.I)   # právní formy lidí (101–108, zahraniční fyzická osoba…)


def cti(cesta, telo=None):
    """GET, nebo POST na vyhledávací cestu API (jen čte)."""
    data = json.dumps(telo).encode() if telo is not None else None
    pozadavek = urllib.request.Request(API + cesta, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pozadavek, timeout=60) as r:
        return json.load(r)


def domy(cast_obce, cp, nacti=cti):
    """Adresy domu → {kód části obce: [adresy]}; stejnojmenné části obce v různých obcích zvlášť."""
    odpoved = nacti("/standardizovane-adresy/vyhledat", {"typStandardizaceAdresy": "VYHOVUJICI_ADRESY",
                                                         "nazevCastiObce": cast_obce, "cisloDomovni": cp, "pocet": 50})
    vysledek = {}
    for a in odpoved.get("standardizovaneAdresy") or []:
        if a.get("typCisloDomovni", POPISNE) != POPISNE:
            continue
        vysledek.setdefault(a["kodCastiObce"], []).append(a["textovaAdresa"])
    return vysledek


def subjekty(kod_casti, cp, nacti=cti):
    """Dnes zapsané subjekty se sídlem v domě (všechny adresy domu, i z druhé ulice)."""
    nalez, start = [], 0
    while start < NEJVIC:
        odpoved = nacti("/ekonomicke-subjekty/vyhledat", {"sidlo": {"kodCastiObce": kod_casti, "cisloDomovni": cp},
                                                          "start": start, "pocet": 100})
        strana = odpoved.get("ekonomickeSubjekty") or []
        nalez += [s for s in strana if s.get("sidlo", {}).get("typCisloDomovni", POPISNE) == POPISNE]
        start += len(strana)
        if not strana or start >= (odpoved.get("pocetCelkem") or 0):
            break
    return nalez


def pravni_formy(nacti=cti):
    """Kód právní formy → český název (číselník ARES)."""
    odpoved = nacti("/ciselniky-nazevniky/vyhledat", {"kodCiselniku": "PravniForma", "zdrojCiselniku": "res"})
    nazvy = {}
    for polozka in odpoved["ciselniky"][0]["polozkyCiselniku"]:
        cesky = [n["nazev"] for n in polozka["nazev"] if n.get("kodJazyka") == "cs"]
        if cesky and polozka.get("platnostDo", "").startswith("9999"):   # u starých kódů platí dnešní název
            nazvy[polozka["kod"]] = cesky[0]
        elif cesky:
            nazvy.setdefault(polozka["kod"], cesky[0])
    return nazvy


def je_clovek(subjekt, formy):
    return bool(FYZICKA_OSOBA.search(formy.get(subjekt.get("pravniForma"), "")))


def odkaz(ico):
    return "https://or.justice.cz/ias/ui/rejstrik-$firma?" + urllib.parse.urlencode({"ico": ico, "jenPlatne": "VSECHNY"})


def radek(s, formy):
    casti = [s["ico"], s.get("obchodniJmeno"), formy.get(s.get("pravniForma"), s.get("pravniForma")),
             s.get("datumVzniku") and "od " + s["datumVzniku"], s.get("sidlo", {}).get("textovaAdresa"), odkaz(s["ico"])]
    return "  " + " | ".join(c for c in casti if c)


def obdobi(polozka):
    od, do = polozka.get("datumZapisu"), polozka.get("datumVymazu")
    return f"{od or '?'}–{do or 'dosud'}"


def detail(ico, nacti=cti):
    """Záznam veřejného rejstříku (historie názvů a sídel); subjekt mimo rejstřík (škola, obec) ze základních údajů."""
    try:
        zaznamy = nacti(f"/ekonomicke-subjekty-vr/{urllib.parse.quote(ico)}")["zaznamy"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        return zakladni_udaje(ico, nacti)
    z = next((z for z in zaznamy if z.get("primarniZaznam")), zaznamy[0])
    radky = [f"IČO: {ico}", f"Stav: {z.get('stavSubjektu', '?')}, zápis {z.get('datumZapisu') or '?'}"
             + (f", výmaz {z['datumVymazu']}" if z.get("datumVymazu") else "")]
    radky += [f"Název {obdobi(n)}: {n['hodnota']}" for n in z.get("obchodniJmeno") or []]
    radky += [f"Sídlo {obdobi(a)}: {a['adresa'].get('textovaAdresa')}" for a in z.get("adresy") or []
              if a.get("typAdresy") == "SIDLO"]
    radky += [f"Předmět činnosti {obdobi(c)}: {c['hodnota']}"
              for c in (z.get("cinnosti") or {}).get("predmetCinnosti") or []]
    radky += [f"Ostatní skutečnosti {obdobi(o)}: {o['hodnota']}" for o in z.get("ostatniSkutecnosti") or []]
    radky += [f"Spisová značka: {s.get('oddil')} {s.get('vlozka')}, {s.get('soud')}" for s in z.get("spisovaZnacka") or []
              if not s.get("datumVymazu")]
    return radky + paticka(ico)


def zakladni_udaje(ico, nacti):
    try:
        s = nacti(f"/ekonomicke-subjekty/{urllib.parse.quote(ico)}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Subjekt s IČO {ico} v ARES není.")
        raise
    radky = [f"IČO: {ico}", f"Název: {s.get('obchodniJmeno')}", f"Sídlo: {s.get('sidlo', {}).get('textovaAdresa')}",
             f"Vznik: {s.get('datumVzniku') or '?'}" + (f", zánik {s['datumZaniku']}" if s.get("datumZaniku") else ""),
             "Ve veřejném rejstříku není (škola, obec, úřad, spolek mimo rejstřík): historii sídel ARES nemá."]
    return radky + paticka(ico)


def paticka(ico):
    return [f"Výpis a sbírka listin (stanovy, prohlášení, smlouvy): {odkaz(ico)}",
            "Citace: Veřejný rejstřík a Sbírka listin, Ministerstvo spravedlnosti ČR (or.justice.cz), IČO " + ico,
            "Sídlo není doklad vlastnictví ani bydliště. Osoby ve statutárním orgánu jsou žijící lidé: do výstupu jen se souhlasem."]


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        if len(argv) < 3:
            sys.exit("Použití: rejstrik.py detail <IČO>")
        print("\n".join(detail(argv[2].replace(" ", ""))))
        return
    if len(argv) < 3 or not argv[2].isdigit():
        sys.exit('Použití: rejstrik.py "<část obce>" <číslo popisné>')
    cast_obce, cp = argv[1], int(argv[2])
    adresy = domy(cast_obce, cp)
    if not adresy:
        sys.exit(f"Dům „{cast_obce} čp. {cp}“ ARES nezná. Zadej část obce z adresy (Holešovice, ne Praha 7) "
                 "a číslo popisné, ne orientační.")
    formy = pravni_formy()
    for kod, adresy_domu in adresy.items():
        nalez = subjekty(kod, cp)
        lide = [s for s in nalez if je_clovek(s, formy)]
        firmy = [s for s in nalez if not je_clovek(s, formy)]
        print(f"Dům {cast_obce} čp. {cp}: {'; '.join(adresy_domu)}")
        if firmy:
            print(f"Firmy, družstva, společenství a další se sídlem v domě (dnes zapsané): {len(firmy)}")
            print("\n".join(radek(s, formy) for s in firmy))
        else:
            print("Firmy ani společenství vlastníků tu dnes sídlo nemají.")
        if lide:
            print(f"Podnikající fyzické osoby: {len(lide)} (jména nevypisuji, žijící lidé)")
        print()
    print("Detail a historie sídel: rejstrik.py detail <IČO>. Zaniklé firmy ARES podle adresy nenajde: "
          "or.justice.cz, název (ulice, obec), „Platné i neplatné“.\nSídlo není doklad vlastnictví ani bydliště.")


if __name__ == "__main__":
    main(sys.argv)
