#!/usr/bin/env python3
"""Zaniklá místa u obce z portálu Zaniklé obce a objekty (zanikleobce.cz): vsi, samoty, mlýny, dvory, cihelny, kaple.

Hlavně pohraničí zaniklé po roce 1945, ale i mlýny a dvory ve vnitrozemí. U místa bývají dobové fotky a pohlednice,
články přispěvatelů (často s čísly domů a jmény majitelů), počty obyvatel a domů a komentáře pamětníků.

Použití:
  zanikleobce.py "<obec>" [--km 3]   – id | název | druh | vzdálenost | fotky | odkaz (+ začátek popisu)
  zanikleobce.py <šířka,délka> [--km 3]
  zanikleobce.py detail <id>         – údaje o místě, popisky fotek, články, počty obyvatel, komentáře
Seznam všech míst je na mapě webu: stáhne ho jednou za 30 dní do ~/.cache/dejiny-domu/zanikleobce/ (2,6 MB).
Hledání a filtry webu (adresy s ?) robots.txt zakazuje kvůli přetížení, nástroj je nepoužívá.
Fotky a texty patří přispěvatelům a web brání jejich kopírování: do výstupu zjištění s citací a odkaz,
fotku jen se souhlasem autora (přes správce webu)."""
import argparse, html, json, os, re, sys, time, urllib.error, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)
from nazvy import zminuje_obec   # porovnání názvů obcí (nazvy.py)
from vzdalenost import km

WEB = "https://www.zanikleobce.cz"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "dejiny-domu", "zanikleobce")
PLATNOST = 30 * 24 * 3600
VYCHOZI_KM = 3
DRUHY = {"sidlo": "sídlo", "prumysl": "průmysl, mlýn", "hospodarstvi": "dvůr, samota", "verejna": "veřejná stavba",
         "cirkevni": "církevní stavba", "jiny": "jiné", "hrad": "hrad, tvrz"}
NEJVIC_POPISKU = 15


def stahni(adresa):
    with urllib.request.urlopen(adresa, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def vsechna_mista():
    """Všechna místa z mapy webu (pole n, lat, lon, kat, url, img, popis…); mezipaměť PLATNOST."""
    cesta = os.path.join(CACHE, "mista.json")
    if not os.path.exists(cesta) or time.time() - os.path.getmtime(cesta) > PLATNOST:
        print("Stahuji seznam míst z mapy zanikleobce.cz (2,6 MB, jednou za měsíc)…", file=sys.stderr)
        m = re.search(r"var MISTA = (\[.*?\]);\n", stahni(f"{WEB}/mapa/"))
        if not m:
            sys.exit("Na mapě zanikleobce.cz chybí seznam míst (web se změnil) – hledej ručně na webu.")
        os.makedirs(CACHE, exist_ok=True)
        with open(cesta + ".tmp", "w", encoding="utf-8") as f:
            f.write(m.group(1))
        os.replace(cesta + ".tmp", cesta)
    with open(cesta, encoding="utf-8") as f:
        return json.load(f)


def najdi(vsechna, lat=None, lon=None, obec=None, polomer=VYCHOZI_KM):
    """[(vzdálenost km nebo None, místo)] v okruhu od středu nebo s obcí v názvu, seřazené podle vzdálenosti."""
    nalez = []
    for m in vsechna:
        vzdalenost = km(lat, lon, m["lat"], m["lon"]) if lat is not None else None
        if (vzdalenost is not None and vzdalenost <= polomer) or (obec and zminuje_obec(m.get("n"), obec)):
            nalez.append((vzdalenost, m))
    return sorted(nalez, key=lambda x: (x[0] if x[0] is not None else 1e9, x[1]["n"]))


def odkaz(cesta):
    return WEB + cesta


def radek(vzdalenost, m):
    casti = [str(m["id"]), m["n"].strip(), DRUHY.get(m.get("kat"), m.get("kat") or ""),
             f"{vzdalenost:.1f} km" if vzdalenost is not None else "", "fotky" if m.get("img") else "", odkaz(m["url"])]
    text = "  " + " | ".join(c for c in casti if c)
    if m.get("popis"):
        text += f"\n      {' '.join(m['popis'].split())[:160]}"
    return text


def text(kus):
    t = html.unescape(re.sub(r"<[^>]+>", " ", kus))
    t = re.sub(r"\s+([,.])\s*", r"\1 ", t)   # „usedlost ,stavení“ → „usedlost, stavení“
    return re.sub(r"\s+", " ", t).strip()


def sekce(stranka):
    """{název sekce: HTML} podle nadpisů section-title na stránce místa."""
    stranka = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", stranka)
    casti = re.split(r'<div class="section-title"[^>]*>', stranka)
    return {c[:c.find("<")].strip(): c[c.find("<"):] for c in casti[1:]}


def hlavicka(stranka):
    """Název, německý název, alternativní názvy, kdo místo vložil a údaje (okres, typ, důvod, období, stav)."""
    karta = re.search(r'(?s)<h1 class="misto-nazev">(.*?)</div>', stranka)
    if not karta:
        return []
    k = karta.group(1)
    radky = [("Název", text(k[:k.find("</h1>")]))]
    alt = re.search(r'misto-altnazvy">(.*?)</p>', k, re.S)
    if alt:
        radky.append(("Jiné názvy", text(alt.group(1)).removeprefix("Alternativní názvy:").strip(" ,")))
    vlozil = re.search(r'\[místo vložil (.*?)\]', text(k))
    if vlozil:
        radky.append(("Vložil", vlozil.group(1)))
    radky += [(text(n).rstrip(":"), text(v)) for n, v in re.findall(r"<b>(.*?)</b>(.*?)<br>", k, re.S)]
    return radky


def fotky(kus):
    """[(popisek, odkaz)] fotek v sekci."""
    return [(text(p) or "bez popisku", odkaz(a)) for a, p in
            re.findall(r'(?s)<figure>\s*<a href="([^"]+)">.*?<figcaption>(.*?)</figcaption>', kus)]


def clanky(kus):
    """[(název, autor a datum, začátek textu, odkaz)] z karty článků."""
    vysledek = []
    for a, nazev, zbytek in re.findall(r'(?s)<a href="(/clanek/[^"]+)"><b>(.*?)</b></a>(.*?)</p>', kus):
        podpis = re.search(r'\[(.*?)\]', text(zbytek))
        obsah = text(re.sub(r'(?s)<span class="datum">.*?</span>', "", zbytek)).replace("Celý článek →", "").strip()
        vysledek.append((text(nazev), podpis.group(1).strip() if podpis else "", obsah, odkaz(a)))
    return vysledek


def detail(id_mista):
    if not str(id_mista).isdigit():
        sys.exit("Použití: zanikleobce.py detail <id> (číslo z výpisu)")
    try:
        stranka = stahni(f"{WEB}/misto/{id_mista}/")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Místo {id_mista} na zanikleobce.cz není.")
        raise
    udaje = hlavicka(stranka)
    radky = [f"{n}: {v}" for n, v in udaje if v]
    for nazev, kus in sekce(stranka).items():
        if nazev.startswith("Vývoj počtu"):
            radky.append(f"\n{nazev}: {text(kus)[:400]}")
        elif "fotografie" in nazev.lower():
            f = fotky(kus)
            radky.append(f"\n{nazev}: {len(f)}")
            radky += [f"  {p} | {o}" for p, o in f[:NEJVIC_POPISKU]]
            if len(f) > NEJVIC_POPISKU:
                radky.append(f"  … a dalších {len(f) - NEJVIC_POPISKU}, viz stránka místa")
        elif nazev.startswith("Historie"):
            c = clanky(kus)
            radky.append(f"\n{nazev}: {len(c)}")
            for titul, podpis, obsah, o in c:
                radky.append(f"  {titul} [{podpis}] {o}\n    {obsah[:400]}")
        elif nazev == "Komentáře":
            pocet = len(re.findall(r"\[vložil ", text(kus)))
            if pocet:
                radky.append(f"\nKomentáře: {pocet} (pamětníci, potomci; čti na stránce místa)")
    adresa = odkaz(f"/misto/{id_mista}/")
    radky += [f"\nOdkaz: {adresa}",
              f"Citace: {dict(udaje).get('Název', '')}, Zaniklé obce a objekty (zanikleobce.cz), "
              f"místo vložil {dict(udaje).get('Vložil') or '?'}, {adresa}",
              "Do výstupu: zjištění s citací a odkaz; fotky a delší texty jen se souhlasem autora (správce beran@seznam.cz)."]
    return radky


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        print("\n".join(detail(argv[2] if len(argv) > 2 else "")))
        return
    p = argparse.ArgumentParser(prog="zanikleobce.py", usage=__doc__)
    p.add_argument("misto")
    p.add_argument("--km", type=float, default=VYCHOZI_KM)
    a = p.parse_args(argv[1:])
    import mista   # střed obce z RÚIAN; jen v projektu (mista.py jinde skončí)
    lat, lon, popis = mista.obec_nebo_poloha(a.misto)
    obec = None if mista.POLOHA.fullmatch(a.misto) else a.misto
    nalez = najdi(vsechna_mista(), lat, lon, obec, a.km)
    print(f"Střed: {popis} ({lat:.5f},{lon:.5f}), okruh {a.km:g} km." if popis else
          f"RÚIAN „{a.misto}“ nezná, hledám jen podle názvu.")
    if not nalez:
        print("Na zanikleobce.cz u obce nic. Zkus větší --km nebo německý název.")
        return
    print(f"Zaniklá místa: {len(nalez)}")
    print("\n".join(radek(v, m) for v, m in nalez))
    print("\nDetail s fotkami, články a počty obyvatel: zanikleobce.py detail <id>.")


if __name__ == "__main__":
    main(sys.argv)
