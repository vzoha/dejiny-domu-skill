#!/usr/bin/env python3
"""Translokační plány židovských obydlí 1727–1728 (Národní archiv, MZA a VÚGTK, www.vugtk.cz/plany).

Plány ~200 měst a vsí v Čechách a na Moravě, kde žili Židé: zakreslují domy, synagogy, kostel a vzdálenost
od něj, často celé náměstí nebo ves sto let před stabilním katastrem. Vznikly kvůli nařízení odstěhovat
Židy od kostelů – plán je návrh, ne doklad, že se přestěhování stalo.

Použití:
  translokace.py "<obec>"      – číslo plánu | lokalita (obec, okres) | rok | název | archiv a signatura | odkaz
  translokace.py detail <č.>   – vše o plánu: autor, měřítko, legenda, zakreslené domy a stavby, citace
Plán i indikační skicu si uživatel prohlédne odkazem. Do výstupu zjištění s citací, obrázek se souhlasem archivu."""
import html, os, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

WEB = "https://www.vugtk.cz/plany/cs"
# sloupce seznamu v pořadí webu (třídy <th>), stav 8. 11. 2026
SLOUPCE = ["id", "lokalita", "nazev", "archiv", "fond", "ev_jednotka", "ev_pocet", "inv_c", "signatura",
           "datace", "obec", "obec_nem", "okres", "kraj"]


def cti(adresa):
    with urllib.request.urlopen(adresa, timeout=60) as r:
        return r.read().decode("utf-8")


def text(kus):
    """HTML buňky → text; položky seznamu <li> oddělí čárkou."""
    kus = re.sub(r"</li>\s*<li[^>]*>", ", ", kus)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", kus))).strip()


def bez_diakritiky(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()


def plany(stranka):
    """Řádky tabulky seznamu → [{id, lokalita, nazev, …}]."""
    vysledek = []
    for radek in re.findall(r"<tr>(.*?)</tr>", stranka, re.S):
        bunky = [text(b) for b in re.findall(r"<td[^>]*>(.*?)</td>", radek, re.S)]
        if len(bunky) >= len(SLOUPCE):
            vysledek.append(dict(zip(SLOUPCE, bunky)))
    return vysledek


def najdi(seznam, obec):
    """Plány, kde obec, německý název nebo lokalita je hledaná obec (bez ohledu na diakritiku a velikost)."""
    hledam = bez_diakritiky(obec)
    return [p for p in seznam if hledam in {bez_diakritiky(p[k]) for k in ("obec", "obec_nem", "lokalita")}]


def odkaz(cislo):
    return f"{WEB}/mapa/{urllib.parse.quote(cislo)}"


def citace(archiv, fond, inv_c, signatura, datace):
    return ", ".join(x for x in (archiv, fond, inv_c and "inv. č. " + inv_c, signatura and "sign. " + signatura, datace) if x)


def radek(p):
    return (f"  {p['id']} | {p['lokalita']}, {p['obec_nem']}, okr. {p['okres']} | {p['datace']} | {p['nazev']} | "
            f"{citace(p['archiv'], p['fond'], p['inv_c'], p['signatura'], p['datace'])} | {odkaz(p['id'])}")


def vlastnosti(stranka):
    """Detail plánu: tabulka popisek → hodnota (základní i rozšířené údaje)."""
    return [(text(k), text(v)) for k, v in re.findall(
        r'<td class="label">(.*?)</td>\s*<td class="value">(.*?)</td>', stranka, re.S) if text(v)]


def detail(cislo, nacti=cti):
    try:
        stranka = nacti(odkaz(cislo))
    except urllib.error.HTTPError as e:
        if e.code in (404, 500):   # neexistující číslo web hlásí jako 500
            sys.exit(f"Plán {cislo} se nenačetl: číslo mezi plány není (čísla z výpisu, např. 1 nebo „4 a“), "
                     f"nebo má web výpadek (hlásí obojí stejně) – když je číslo z výpisu, zkus to později.")
        raise
    udaje = vlastnosti(stranka)
    if not udaje:
        sys.exit(f"Plán {cislo}: stránka nemá údaje, web se asi změnil ({odkaz(cislo)}).")
    udaj = dict(udaje)
    radky = [f"{k}: {v}" for k, v in udaje]
    radky += [f"Odkaz (plán, indikační skica, letecký snímek): {odkaz(cislo)}",
              "Citace: " + citace(udaj.get("archiv"), udaj.get("archivní soubor"), udaj.get("inventární číslo"),
                                  udaj.get("signatura"), udaj.get("datace - vznik")),
              "Pozor: plán je návrh přestěhování Židů od kostela, ne doklad, že se stalo. "
              "Domy porovnej s indikační skicou (odkaz) a s pozdějšími prameny."]
    return radky


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    if argv[1] == "detail":
        if len(argv) < 3:
            sys.exit("Použití: translokace.py detail <číslo plánu> (z výpisu, např. 1 nebo „4 a“)")
        print("\n".join(detail(" ".join(argv[2:]))))
        return
    obec = argv[1]
    seznam = plany(cti(f"{WEB}/seznam/"))
    if not seznam:
        sys.exit(f"Seznam plánů je prázdný, web se asi změnil ({WEB}/seznam/).")
    nalez = najdi(seznam, obec)
    if not nalez:
        print(f"Translokační plán pro „{obec}“ není (prošlo {len(seznam)} plánů). Plány jsou jen z obcí, "
              "kde v letech 1727–1728 žili Židé; zkus i německý název nebo obec, ke které ves patří.")
        return
    print(f"Translokační plány 1727–1728 pro „{obec}“: {len(nalez)}")
    print("\n".join(radek(p) for p in nalez))
    print("\nDetail: translokace.py detail <číslo> (zakreslené domy, synagoga, kostel, autor, měřítko).\n"
          "Plán je návrh přestěhování, ne skutečnost. Do výstupu zjištění s citací, obrázek se souhlasem archivu.")


if __name__ == "__main__":
    main(sys.argv)
