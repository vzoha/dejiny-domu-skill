#!/usr/bin/env python3
"""Válečné hroby a pomníky padlých obce a padlí vojáci podle jména (Centrální evidence válečných hrobů MO,
evidencevh.mo.gov.cz).

Pomník padlých na návsi nese jména mužů z vesnice (1. světová válka, často i oběti 2. světové války). Evidence má
jména přepsaná s rokem narození a úmrtí a místem smrti, k pomníku polohu a nápis. Evidence padlých (~50 000 vojáků
rakousko-uherské armády z kartoték VÚA) má u člověka domovskou obec, okres, útvar, datum a místo smrti a prameny.
Číslo domu evidence nemá: shodu s obyvatelem domu ověř podle jména, věku a obce.

Použití (z kořene projektu):
  valecne_hroby.py obec "<Obec>" [--orp <ORP>]
      pomníky, desky a hroby v obci: poloha (ulice, část obce, GPS), druh, popis a nápis, jména připomenutých.
      Hledá podle názvu obce, ne části obce (Lniště je v obci Slavče – obec vypíše `mista.py ruian "Osada čp"`).
      Stejnojmenné obce rozliší --orp (obec s rozšířenou působností, vypíše se u každého hrobu).
  valecne_hroby.py padli <Příjmení> [Jméno] [--obec <Obec>]
      padlí ze 1. světové války podle příjmení (jak je v kartotéce, často německy: Bilder, Lisak); u prvních 20
      detail (domovská obec, okres, útvar, smrt, prameny). --obec projde detaily až 100 lidí a nechá jen ty s obcí
      v místě narození nebo domovské obci (obec bývá německy).
Fotky v evidenci nahrávají úřady a nemají licenci → do výstupu jen odkaz. Jména a údaje s citací smí.
Šetři server: obec = 1 + 2 dotazy na hrob, padlí = 1 + detail na osobu.
"""
import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
from nazvy import bez_diakritiky, zminuje_obec  # noqa: E402
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)

B = "https://evidencevh.mo.gov.cz/Evidence"
STRANKA = {"sort": "", "page": 1, "pageSize": 100, "group": ""}   # stránkování seznamů Kendo (jako web)
DETAILU_PADLYCH = 20          # bez --obec: přehled
DETAILU_PADLYCH_OBEC = 100    # s --obec se obec pozná až z detailu
CITACE = "Centrální evidence válečných hrobů, Ministerstvo obrany ČR (evidencevh.mo.gov.cz)"


def otevri(url, data=None):
    """Server občas vrátí 500 u záznamu, který o pár sekund později jde – dvakrát zopakuje s pauzou."""
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": slusne.UA})
    for pokus in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code != 500 or pokus == 2:
                raise
            time.sleep(5)


def seznam(cesta, **filtr):
    """Hledání webu (POST jen čte); vrací (celkem, položky první stránky)."""
    d = json.loads(otevri(f"{B}/{cesta}", {**STRANKA, **filtr}))
    return d["Total"], d["Data"]


def pole(stranka):
    """Pole detailu {popisek: hodnota}. Pole = <div> s <label>; hodnota v <input value>, v odkazech (prameny
    s adresou Digitální studovny VÚA) nebo v textu."""
    vysledek = {}
    for m in re.finditer(r'<label[^>]*>(.*?)</label>(.*?)</div>', stranka, re.S):
        popisek = prosty_text(m.group(1))
        usek = re.sub(r"<script.*?</script>", "", m.group(2), flags=re.S)
        hodnoty = [html.unescape(v) for v in re.findall(r'value="([^"]*)"', usek) if v.strip()]
        odkazy = [f"{prosty_text(t)} ({html.unescape(u)})" for u, t in re.findall(r'<a href="([^"]+)">(.*?)</a>', usek, re.S)]
        hodnota = ", ".join(hodnoty) or "; ".join(odkazy) or prosty_text(usek)
        if popisek and hodnota:
            vysledek[popisek] = hodnota
    return vysledek


def prosty_text(h):
    return re.sub(r"\s*\n\s*", "\n", re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))).strip()


def hroby_obce(obec, orp=None):
    celkem, hroby = seznam("Graves/Select", FullText=obec)
    if celkem > len(hroby):
        print(f"Pozor: „{obec}“ má v evidenci {celkem} výsledků, projdu jen prvních {len(hroby)}.")
    hroby = [h for h in hroby if bez_diakritiky(h["Municipality"]) == bez_diakritiky(obec)]
    if not hroby:
        print(f"V obci „{obec}“ evidence nic nemá (hledá název obce, ne části obce – zkus obec z `mista.py ruian`).")
        return
    jine_orp = set()
    for h in hroby:
        d = pole(otevri(f"{B}/Graves/Detail/{h['Id']}"))
        if orp and bez_diakritiky(d.get("ORP", "")) != bez_diakritiky(orp):
            jine_orp.add(d.get("ORP", "?"))
            continue
        _, lide = seznam(f"People/Select/{h['Id']}")
        print(vypis_hrobu(h, d, lide))
    if jine_orp:
        print(f"\nVynechané hroby stejnojmenné obce v ORP: {', '.join(sorted(jine_orp))}")
    print(f"\nCitace: {CITACE}, <číslo hrobu>. Fotky jen odkazem.")


def vypis_hrobu(h, d, lide):
    radky = [f"\n{h['Identifier']} | {h['Character']} | {d.get('Obec/újezd', h['Municipality'])}, "
             f"{d.get('Ulice / č.p.', '')} | ORP {d.get('ORP', '?')} | {d.get('Zeměpisná poloha', '')}",
             f"  {B}/Graves/Detail/{h['Id']}"]
    for klic in ("Historické události", "Popis vzhledu", "Poznámka"):
        if d.get(klic):
            radky.append(f"  {klic}: " + d[klic].replace("\n", " / "))
    radky.append(f"  Jména ({len(lide)}):")
    for o in lide:
        narozen = " ".join(filter(None, [o.get("DateOfBirth"), o.get("BirthLocation")]))
        radky.append(f"    {o['FullName']}" + (f", * {narozen}" if narozen else "")
                     + (f", † {o['DeathLabel']}" if o.get("DeathLabel") else "")
                     + (f" – {o['CauseOfDeath']}" if o.get("CauseOfDeath") else ""))
    return "\n".join(radky)


def padli(prijmeni, jmeno=None, obec=None):
    filtr = {"Surname": prijmeni, **({"FirstName": jmeno} if jmeno else {})}
    celkem, lide = seznam("FallenPeople/Select", **filtr)
    limit = DETAILU_PADLYCH_OBEC if obec else DETAILU_PADLYCH
    print(f"Padlí „{' '.join(filter(None, [jmeno, prijmeni]))}“: {celkem}"
          + (f" (detail jen u prvních {limit} – zúži jménem)" if celkem > limit else ""))
    jinde = 0
    for o in lide[:limit]:
        d = pole(otevri(f"{B}/FallenPeople/Detail/{o['ICP']}"))
        if obec and not any(zminuje_obec(d.get(k, ""), obec) for k in ("Místo narození", "Obec (Rakousko-Uhersko)")):
            jinde += 1
            continue
        print(vypis_padleho(o, d))
    if jinde:
        print(f"\nVynecháno {jinde} s jinou nebo neznámou obcí než „{obec}“ (obec bývá německy: zkus i německý tvar).")
    print(f"\nCitace: {CITACE}, Evidence padlých, IČP <číslo>; pramen podle řádku „Prameny“.")


def vypis_padleho(o, d):
    def spoj(*klice):
        return ", ".join(d[k] for k in klice if d.get(k))
    radky = [f"\nIČP {o['ICP']} | {o['FirstName']} {o['Surname']} | * {d.get('Den narození', o['BirthYear'])}"
             f" {spoj('Místo narození')} | domovská obec: {spoj('Obec (Rakousko-Uhersko)', 'Okres (Rakousko-Uhersko)') or '?'}",
             f"  † {spoj('Den úmrtí', 'Místo úmrtí', 'Země (úmrtí)')}" + (f" – {d['Příčina úmrtí']}" if d.get("Příčina úmrtí") else ""),
             f"  {B}/FallenPeople/Detail/{o['ICP']}"]
    if spoj("Vojenská hodnost", "Vojenský útvar"):
        radky.append(f"  útvar: {spoj('Vojenská hodnost', 'Vojenský útvar', 'Jednotka')}")
    if spoj("Rodinný stav", "Místo (pohřbení)"):
        radky.append(f"  {spoj('Rodinný stav')}" + (f", pohřben: {d['Místo (pohřbení)']}" if d.get("Místo (pohřbení)") else ""))
    for klic in ("Zdrojová DB", "Kramerius dokument"):   # „Kramerius dokument“ = prameny s odkazem do Digitální studovny
        if d.get(klic):
            radky.append(f"  prameny: {d[klic]}")
    return "\n".join(radky)


def volba(a, nazev):
    if nazev not in a:
        return a, None
    i = a.index(nazev)
    return a[:i] + a[i + 2:], a[i + 1]


def main():
    a = sys.argv[1:]
    a, orp = volba(a, "--orp")
    a, obec = volba(a, "--obec")
    if len(a) == 2 and a[0] == "obec":
        hroby_obce(a[1], orp)
    elif len(a) in (2, 3) and a[0] == "padli":
        padli(a[1], a[2] if len(a) == 3 else None, obec)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
