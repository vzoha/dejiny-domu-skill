"""Společná pravidla platnosti dat pro kontrola.py a export_web.py (ať obě řeknou totéž).

Jen funkce, nic nespouští. Každá vrací text chyby, nebo None, když je hodnota v pořádku.
"""
import datetime, math, re, unicodedata

BEZPECNY_ODKAZ = re.compile(r"(?i)https?://\S+|/(?!/)\S*|#\S*")   # web, stránka vlastního webu, kotva


def slugify(text):
    """Adresa stránky domu: bez diakritiky a interpunkce („ev. 3“ → „ev-3“)."""
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def chyba_odkazu(url):
    """Odkaz na webu smí vést jen na http(s) nebo na stránku webu. javascript:, data: ap. by se po kliknutí spustily."""
    if url and not BEZPECNY_ODKAZ.fullmatch(str(url).strip()):
        return f"odkaz {str(url)[:60]!r} nevede na http(s):// ani na stránku webu (/…)"
    return None


def chyba_polohy(x):
    """lat a lon buď obě chybí, nebo jsou obě čísla v rozsahu. Jen jedna nebo text rozbije export a mapy."""
    lat, lon = x.get("lat"), x.get("lon")
    if lat is None and lon is None:
        return None
    if lat is None or lon is None:
        return f"má jen {'lat' if lon is None else 'lon'} – doplň i {'lon' if lon is None else 'lat'}, nebo smaž obě"
    for nazev, v, mez in (("lat", lat, 90), ("lon", lon, 180)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > mez:
            return f"{nazev} {v!r} není číslo v rozsahu ±{mez} (zapiš číslo bez uvozovek, např. 49.41)"
    return None


def chyby_adres_domu(klice):
    """Klíče domů, které dají stejnou adresu stránky („12a“ a „12á“, na webu by zůstal jen jeden) nebo žádnou („?“)."""
    podle = {}
    for k in klice:
        podle.setdefault(slugify(k), []).append(str(k))
    return [f"domy {', '.join(ks)}: stejná adresa stránky /dum/{s}/, na webu by zůstal jen jeden – přejmenuj klíč" if s
            else f"dům {', '.join(ks)}: klíč bez písmen a číslic nedá adresu stránky"
            for s, ks in podle.items() if len(ks) > 1 or not s]


DATUM = re.compile(r"\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\b")


def nemozna_data(text):
    """Přesně zapsaná data, která v kalendáři nejsou (31. 2. 1900). Přibližná („kolem 1900“, „1890?“) neřeší."""
    spatne = []
    for m in DATUM.finditer(str(text)):
        d, mes, r = map(int, m.groups())
        try:
            datetime.date(r, mes, d)
        except ValueError:
            spatne.append(m.group(0))
    return spatne


def obracene_rozpeti(text):
    """Rozpětí „1860–1795“ zapsané pozpátku."""
    m = re.fullmatch(r"\s*(\d{4})\s*[–-]\s*(\d{4})\s*", str(text or ""))
    return bool(m) and obraceny_interval(*m.groups())


def obraceny_interval(od, do):
    """Obě meze jsou holé letopočty a začátek je po konci (1900 → 1800). Nejisté meze („?“, „asi 1800“) nechá být."""
    od, do = str(od or "").strip(), str(do or "").strip()
    return bool(re.fullmatch(r"\d{4}", od) and re.fullmatch(r"\d{4}", do) and int(od) > int(do))
