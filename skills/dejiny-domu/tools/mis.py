#!/usr/bin/env python3
"""Fotky, plány a mapy NPÚ v Metainformačním systému (MIS, iispp.npu.cz/mis_public) – jen popis a odkaz, ne soubory.

Použití:
  mis.py hledej "<text>"   – dokumenty: id | datum vzniku | typ | popis | lokalita | autor (nejvýš 50, MIS ukáže
                             jen prvních 200 nalezených – zpřesni: „Lniště kaple“, „Trhové Sviny čp. 12“)
  mis.py detail <id>       – popis, datum, autor, pracoviště, licence, místo (část obce, čp., ulice), vazba na památku
Fotky z Památkového katalogu vypíše i `pamatky.py detail <id>`. Hromadný export MIS chrání reCAPTCHA – nepoužívat.
Fotky a plány jsou dílo NPÚ: do PDF ani na web jen odkaz, kopii lze objednat (reference/podminky.md)."""
import html, os, re, sys, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

MIS = "https://iispp.npu.cz/mis_public/"
NA_STRANKU = 50   # víc MIS na stránku nedá
POLE_DETAILU = ("Popis dokumentu", "Typ dokumentu", "Datum vzniku", "Autor originálu", "Název pracoviště",
                "Rozměry obrazového dokumentu", "Typ", "Název objektu", "Část obce", "Č. dom.", "Ulice", "Č. or.",
                "Kat. území", "Obec", "Okres")


def stahni(cesta):
    with urllib.request.urlopen(MIS + cesta, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def text_html(kus):
    kus = re.sub(r"(?s)<(script|style).*?</\1>", "", kus)
    return [r.strip() for r in html.unescape(re.sub(r"<[^>]+>", "\n", kus)).splitlines() if r.strip()]


def dvojice(radky):
    """[„Obec:“, „Slavče“, „Č. dom.:“, „Ulice:“] → [(Obec, Slavče), (Č. dom., "")] – prázdná hodnota je další popisek."""
    out = []
    for i, r in enumerate(radky):
        if r.endswith(":") and len(r) < 40:
            dalsi = radky[i + 1] if i + 1 < len(radky) else ""
            out.append((" ".join(r[:-1].split()), "" if dalsi.endswith(":") else dalsi))   # &nbsp; v popisku
    return out


def vysledky(stranka):
    """Bloky výsledků hledání → [{id, popis, pole…}]. Id je v odkazu na detail za blokem."""
    out = []
    for blok in stranka.split('class="searchResultInfo"')[1:]:
        m = re.search(r"documentDetail\.htm\?id=(\d+)", blok)
        if not m:
            continue
        poznamka = re.search(r'(?s)class="searchResultNotes">(.*?)</div>', blok)
        zaznam = {"id": m.group(1), "popis": " ".join(text_html(poznamka.group(1))[1:]) if poznamka else ""}
        for k, v in dvojice(text_html(blok.split('class="searchResultButtons"')[0])):
            zaznam.setdefault(k, " ".join(v.split()))
        out.append(zaznam)
    return out


def radek_vysledku(z):
    return [z["id"], z.get("Datum vzniku", ""), z.get("Typ dokumentu", ""), z["popis"], z.get("Název lokality", ""),
            z.get("Obec", ""), z.get("Autor originálu", "")]


def pocet(stranka):
    m = re.search(r"zobrazených\s*([\d\s–-]+?)\s*z\s*(prvních\s*)?(\d+)\s*nalezených", " ".join(text_html(stranka)))
    return int(m.group(3)) if m else None


def hledej(text):
    stranka = stahni("searchDocument.htm?" + urllib.parse.urlencode({"search": text, "itemsPerPage": NA_STRANKU}))
    return vysledky(stranka), pocet(stranka)


def popis_detailu(stranka, id_):
    pary = dvojice(text_html(stranka))
    radky = [f"{'licence' if k == 'Typ' else k}: {v}" for k, v in pary if k in POLE_DETAILU and v]   # „Typ“ v oddílu Licence
    radky = list(dict.fromkeys(radky))   # místo bývá v definičním i přírůstkovém bodu a v lokalitách
    radky += [f"památka: prvek {m}" for m in dict.fromkeys(re.findall(r"\(prvek (\d+)\)", " ".join(text_html(stranka))))]
    radky.append(f"odkaz: {MIS}documentDetail.htm?id={id_}")
    return radky


def main(argv):
    if len(argv) > 2 and argv[1] == "detail":
        print("\n".join(popis_detailu(stahni(f"documentDetail.htm?id={argv[2]}"), argv[2])))
        return
    if len(argv) < 3 or argv[1] != "hledej":
        sys.exit(__doc__)
    zaznamy, celkem = hledej(argv[2])
    if not zaznamy:
        print(f"MIS pro „{argv[2]}“ nic nenašel.")
        return
    print(f"dokumentů: {len(zaznamy)}" + (f" z {celkem} nalezených – zpřesni hledání" if celkem and celkem > len(zaznamy) else ""))
    for z in zaznamy:
        print(" | ".join(radek_vysledku(z)))
    print(f"\nPodrobnosti: mis.py detail <id>. Odkaz: {MIS}documentDetail.htm?id=<id>. Soubory jen odkazem.")


if __name__ == "__main__":
    main(sys.argv)
