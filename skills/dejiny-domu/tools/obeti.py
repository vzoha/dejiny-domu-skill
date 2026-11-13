#!/usr/bin/env python3
"""Oběti nacistické perzekuce podle ulice a čísla domu (Databáze obětí, holocaust.cz, Institut Terezínské iniciativy).

Databáze má Židy deportované z českých zemí (a Romy z tábora v Letech) se jménem, narozením, transporty, osudem
a u mnoha i s adresou registrace v protektorátu („Praha I, Dlouhá 18“). Přesné adresy jsou hlavně u Prahy,
jinde často jen obec. U městského domu tak zjistíš, kdo z domu a z ulice byl deportován.

Před prvním použitím potvrdí podmínky vstupu do databáze UŽIVATEL sám (citlivé údaje, důstojné vzpomínání):
  python3 -I tools/obeti.py souhlas     v běžném terminálu v kořeni projektu (`!` v Claude Code nemá vstup, nejde); Claude ho nespouští
Použití (z kořene projektu):
  obeti.py ulice "<Ulice>" [--cislo N]… [--obec <text>] [--max 100]
      oběti s adresou v ulici seskupené podle adresy. Hledá podle názvu ulice (celá slova, bez čísla), pak čte detail
      každé oběti (1 dotaz na osobu, nejvýš --max). --cislo nechá jen adresy s tím číslem (orientační i popisné, lze
      víckrát: dnešní i staré číslo), --obec jen adresy s tím textem („Praha I“). Zkus i staré názvy ulice.
  obeti.py hledat [--prijmeni P] [--jmeno J] [--bydliste B] [--rok R] [--stran N]
      jméno | narození | osud | odkaz, N stran po 20 (výchozí 3); příjmení i v ženském tvaru („Nováková“).
  obeti.py detail <odkaz|číslo-jméno>
      bydliště, adresa v protektorátu, transporty, osud, dokumenty.
Do výstupu jen fakta s citací (CITACE níže) a odkaz na oběť; dokumenty a fotky ne (patří Národnímu archivu nebo
dárcům, publikace jen s jejich souhlasem). Prázdný výsledek neznamená, že v domě nikdo nežil: databáze má jen
oběti a adresa u nich často chybí.

Převzato a upraveno z rodokmen-plus (licence MIT, © srameko):
  https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/obeti.py
"""
import html, http.cookiejar, os, re, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
from nazvy import bez_diakritiky  # noqa: E402
import slusne; slusne.instaluj()   # noqa: E402 – společný limit rychlosti k webům archivů (slusne.py)
import souhlas  # noqa: E402 – souhlas uživatele s podmínkami vstupu do databáze

BASE = "https://www.holocaust.cz/databaze-obeti/"
CITACE = "Databáze obětí, Institut Terezínské iniciativy (holocaust.cz)"
SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_PRIKAZ = "holocaust_cz", "Databáze obětí (holocaust.cz)", "tools/obeti.py souhlas"
SOUHLAS_URL = BASE + "help/"
SOUHLAS_ZNENI = ("Databáze obětí nacistického pronásledování obsahuje jména a osudy Židů deportovaných z českých zemí a vězňů "
                 "terezínského ghetta z dalších evropských zemí a dále základní informace o Romech, Sintech a dalších osobách, "
                 "které zemřely jako vězni v takzvaném „Cikánském táboře I“ v Letech u Písku. Upozorňujeme, že databáze obsahuje "
                 "citlivé osobní údaje a jejím účelem je důstojné vzpomínání s respektem vůči pozůstalým. Vstupem do databáze "
                 "uživatel potvrzuje, že se seznámil s informacemi o jejím obsahu a je si plně vědom své osobní odpovědnosti "
                 "za nakládání s materiály a informacemi, které v ní nalezne.")
ADRESA = "Adresa/místo registrace v Protektorátu:"
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))   # stránkování drží relaci
_op.addheaders = [("User-Agent", slusne.UA)]


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    with _op.open(urllib.request.Request(url, data=body), timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def vysledky(page):
    """Výsledky hledání: [{jmeno, info, url}]."""
    out = []
    for blok in re.findall(r'<div class="victims-wrapper">(.*?)</div>', page, re.S):
        m = re.search(r'<p>\s*<a href="([^"]+)">(.*?)</a>(.*?)</p>', blok, re.S)
        if m:
            info = " | ".join(t for t in (text(x) for x in re.split(r"<br\s*/?>", m.group(3))) if t)
            out.append(dict(jmeno=text(m.group(2)), info=info, url=m.group(1)))
    return out


def celkem(page):
    m = re.search(r"Celkem nalezeno: ([\d\s\xa0]+)", page)
    return int(re.sub(r"\D", "", m.group(1)) or 0) if m else None


def dalsi(page):
    m = re.search(r'<a href="(https://www\.holocaust\.cz/databaze-obeti/strana/\d+/)">další</a>', page)
    return m.group(1) if m else None


def detail_z(page):
    """Detail oběti: {jmeno, radky, adresa, dokumenty}, nebo None."""
    jm = re.search(r"<h1>(.*?)</h1>", page, re.S)
    w = re.search(r'<div class="wrapper">.*?<p>(.*?)</p>', page, re.S)
    if not jm or not w:
        return None
    radky = [t for t in (text(r) for r in re.split(r"<br\s*/?>", w.group(1))) if t]
    adresa = next((r[len(ADRESA):].strip() for r in radky if r.startswith(ADRESA)), "")
    dok = [(text(n), h) for h, n in re.findall(r'<div class="victim-documents">\s*<a href="([^"]+)">.*?<span>(.*?)</span>',
                                               page, re.S)]
    return dict(jmeno=text(jm.group(1)), radky=radky, adresa=adresa, dokumenty=dok)


def _norm(s):
    return bez_diakritiky(s).lower()


def cisla_adresy(adresa, ulice):
    """Čísla za názvem ulice: „Praha I, Dlouhá 13/745“ → {"13", "745"}."""
    a, u = _norm(adresa), _norm(ulice)
    i = a.find(u)
    return set(re.findall(r"\d+", a[i + len(u):])) if i >= 0 else set()


def v_ulici(adresa, ulice, cisla=(), obec=""):
    a = _norm(adresa)
    if _norm(ulice) not in a or _norm(obec) not in a:
        return False
    return not cisla or bool(cisla_adresy(adresa, ulice) & set(cisla))


def hledej(pole):
    """První stránka hledání (POST jako formulář portálu)."""
    return get(BASE, {"searchFirstname": pole.get("jmeno", ""), "searchSurname": pole.get("prijmeni", ""),
                      "searchPlaceLast": pole.get("bydliste", ""), "searchPlaceBirth": "",
                      "searchDateBirthDay": "0", "searchDateBirthMonth": "0", "searchDateBirthYear": pole.get("rok", ""),
                      "searchTransport": "", "searchSubmit": "Vyhledat v databázi"})


def vsechny(pole, stran):
    """Výsledky z nejvýš `stran` stran a celkový počet."""
    page = hledej(pole)
    n, out = celkem(page), []
    for p in range(stran):
        out += vysledky(page)
        url = dalsi(page)
        if not url or p == stran - 1:
            break
        page = get(url)
    return out, n


def cmd_hledat(pole, stran):
    out, n = vsechny(pole, stran)
    for r in out:
        print(f"{r['jmeno']} | {r['info']} | {r['url']}")
    if n is None:
        sys.exit("Portál nevrátil výsledky (změnil se formulář?). Hledej v prohlížeči.")
    if not out:
        print("Nic nenalezeno (zkus příjmení v ženském tvaru nebo méně údajů).", file=sys.stderr)
    elif len(out) < n:
        print(f"… nalezeno {n}, zobrazeno {len(out)}; zúžit jménem nebo rokem, víc stran --stran", file=sys.stderr)


def url_obeti(arg):
    if not arg.startswith("http") and not re.fullmatch(r"[0-9a-z-]+", arg):
        sys.exit("Zadej odkaz na oběť (z výpisu) nebo její číslo s jménem, např. 12345-jana-novakova.")
    url = arg if arg.startswith("http") else f"{BASE}obet/{arg}/"
    if not url.startswith(BASE):
        sys.exit("Odkaz musí být z databáze obětí na holocaust.cz.")
    return url


def cmd_detail(arg):
    d = detail_z(get(url_obeti(arg)))
    if not d:
        sys.exit("Oběť nenalezena (zkontroluj odkaz).")
    print(d["jmeno"])
    for r in d["radky"]:
        print("  " + r)
    for nazev, href in d["dokumenty"]:
        print(f"  dokument (jen odkaz): {nazev} | {href}")


def cmd_ulice(ulice, cisla, obec, nejvic):
    nazev = re.sub(r"\s*\d+(/\d+)?\s*$", "", ulice).strip()   # portál s číslem nenajde nic
    out, n = vsechny({"bydliste": nazev}, (nejvic + 19) // 20)
    if n is None:
        sys.exit("Portál nevrátil výsledky (změnil se formulář?). Hledej v prohlížeči.")
    out = out[:nejvic]
    adresy = {}
    for r in out:
        d = detail_z(get(r["url"]))
        if d and v_ulici(d["adresa"], nazev, cisla, obec):
            osud = " | ".join(x for x in d["radky"] if not x.startswith(("Poslední bydliště", ADRESA)))
            adresy.setdefault(d["adresa"], []).append(f"{d['jmeno']} | {osud} | {r['url']}")
    for a in sorted(adresy, key=lambda a: [int(c) for c in re.findall(r"\d+", a)] or [0]):
        print(a)
        for o in adresy[a]:
            print("  " + o)
    print(f"\n{sum(map(len, adresy.values()))} obětí na {len(adresy)} adresách z {len(out)} prověřených "
          f"(portál našel {n} pro „{nazev}“). Citace: {CITACE}.", file=sys.stderr)
    if len(out) < n:
        print(f"Prověřeno jen {len(out)} z {n}: zvyš --max, nebo zužuj --obec až po načtení.", file=sys.stderr)
    if not adresy:
        print("V databázi nikdo s touto adresou. Zkus starý název ulice a stará čísla; databáze má jen oběti "
              "a adresu jen u části z nich.", file=sys.stderr)


def volby(a, s_hodnotou, opakovane=()):
    """Jednoduché --volba hodnota; opakované volby jako seznam."""
    out, i = {k: [] for k in opakovane}, 0
    while i < len(a):
        k = a[i]
        if k not in s_hodnotou or i + 1 >= len(a):
            sys.exit(__doc__)
        if k in opakovane:
            out[k].append(a[i + 1])
        else:
            out[k] = a[i + 1]
        i += 2
    return out


def main(a):
    if not a:
        sys.exit(__doc__)
    if a == ["souhlas"]:
        souhlas.potvrd(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_URL, SOUHLAS_PRIKAZ)
        return
    if a[0] not in ("ulice", "hledat", "detail"):
        sys.exit(__doc__)
    souhlas.vyzaduj(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_PRIKAZ)
    if a[0] == "detail" and len(a) == 2:
        cmd_detail(a[1])
    elif a[0] == "ulice" and len(a) >= 2:
        v = volby(a[2:], ("--cislo", "--obec", "--max"), opakovane=("--cislo",))
        if not v.get("--max", "100").isdigit():
            sys.exit("--max chce číslo.")
        cmd_ulice(a[1], v["--cislo"], v.get("--obec", ""), int(v.get("--max", "100")))
    elif a[0] == "hledat":
        v = volby(a[1:], ("--prijmeni", "--jmeno", "--bydliste", "--rok", "--stran"))
        pole = {k[2:]: x for k, x in v.items() if k != "--stran"}
        if not pole:
            sys.exit("Zadej aspoň --prijmeni, --jmeno nebo --bydliste.")
        if "rok" in pole and not re.fullmatch(r"\d{4}", pole["rok"]):
            sys.exit("--rok chce čtyřmístný rok narození.")
        if not v.get("--stran", "3").isdigit():
            sys.exit("--stran chce číslo.")
        cmd_hledat(pole, max(1, int(v.get("--stran", "3"))))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
