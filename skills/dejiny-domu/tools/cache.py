#!/usr/bin/env python3
"""Sdílená mezipaměť obrázků z archivů – každý snímek nebo dlaždice se z archivu stáhne jen jednou.

Ukládá ji brzda tools/slusne.py: obrázek stažený přes brzdu (nástroje, vlastní skripty, pomocníci) se uloží podle
adresy a příště se vezme z disku bez dotazu na archiv. Z adresy se před uložením odstraní jen části, které obsah
nemění (;jsessionid=, PHPSESSID, pojistky proti mezipaměti typu _=1793…, utm_…); neznámé parametry zůstávají –
raději stáhnout znovu, než vrátit cizí snímek. Ukládá se jen úspěšná odpověď, která je opravdu celý obrázek
(sedí délka ze serveru a soubor má značku konce); zkrácený uložený snímek se smaže a stáhne znovu.

Mezipaměť je společná pro všechny projekty (domy) na počítači: ~/.cache/dejiny-domu/snimky/
(Windows %LOCALAPPDATA%\\dejiny-domu\\snimky), jinou složku nastaví proměnná DEJINY_SNIMKY. Nejvýš 5 GB
(DEJINY_SNIMKY_GB), nejdéle nepoužité soubory se mažou samy. Složku lze kdykoli smazat, nástroje si snímky
stáhnou znovu.

Použití:
  cache.py stav     -> kolik místa zabírá a kolik stažení z archivu ušetřila
"""
import glob, hashlib, json, os, re, shutil, subprocess, sys, time
from urllib.parse import parse_qsl, urlencode, urlsplit

KOREN = os.environ.get("DEJINY_SNIMKY") or os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache"), "dejiny-domu", "snimky")
LIMIT = float(os.environ.get("DEJINY_SNIMKY_GB") or 5) * 1024 ** 3
PRIPONY = ((b"\xff\xd8\xff", ".jpg"), (b"\x89PNG\r\n\x1a\n", ".png"), (b"GIF8", ".gif"), (b"II*\x00", ".tif"),
           (b"MM\x00*", ".tif"), (b"\x00\x00\x00\x0cjP  ", ".jp2"), (b"\xffO\xffQ", ".j2k"))
STAT = os.path.join(KOREN, "stav.json")


def pripona(data):
    """Přípona podle prvních bajtů; None = není obrázek (chybová stránka, „zablokováno“ …)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return next((p for z, p in PRIPONY if data.startswith(z)), None)


def _cely(hlava, konec, velikost):
    """Má obrázek konec? Přerušené stažení má hlavičku taky, jen mu chybí spodek snímku."""
    p = pripona(hlava)
    if p in (".jpg", ".jp2", ".j2k"):   # značka konce FF D9 (za ní bývá výplň)
        return b"\xff\xd9" in konec
    if p == ".png":
        return b"IEND" in konec[-64:]
    if p == ".gif":
        return konec.rstrip(b"\x00")[-1:] == b";"
    if p == ".webp":
        return int.from_bytes(hlava[4:8], "little") + 8 <= velikost
    return p is not None   # TIFF konec nemá – ohlídá ho jen délka ze serveru


def cely(data, delka=None):
    """Úplný obrázek: sedí délka ze serveru (Content-Length), je-li, a má značku konce."""
    if delka is not None and len(data) != delka:
        return False
    return _cely(data[:16], data[-1024:], len(data))


def _cely_soubor(path):
    try:
        n = os.path.getsize(path)
        with open(path, "rb") as f:
            hlava = f.read(16)
            f.seek(max(0, n - 1024))
            return _cely(hlava, f.read(), n)
    except OSError:
        return False


def klic_url(url):
    """Cesta v mezipaměti (bez přípony) podle adresy bez částí, které obsah nemění."""
    u = urlsplit(url)
    path = re.sub(r";jsessionid=[^/?#;]*", "", u.path, flags=re.I)
    q = []
    for k, v in parse_qsl(u.query, keep_blank_values=True):
        kl = k.lower()
        if kl in ("jsessionid", "phpsessid") or kl.startswith("utm_"):
            continue
        if (kl == "_" and v.isdigit()) or (not v and re.fullmatch(r"\d{10,}", k)):   # pojistka proti mezipaměti
            continue
        q.append((k, v))
    host = (u.hostname or "").lower()
    port = f":{u.port}" if u.port and u.port not in (80, 443) else ""   # http i https = týž obrázek
    h = hashlib.sha1(f"{host}{port}{path}?{urlencode(sorted(q))}".encode()).hexdigest()
    return os.path.join(KOREN, "web", host, h[:2], h)


def najdi_url(url):
    """Uložený celý obrázek pro adresu, nebo None (zkrácený smaže)."""
    k = klic_url(url)
    for p in dict.fromkeys(p for _, p in PRIPONY + ((None, ".webp"),)):
        if os.path.exists(k + p):
            if not _cely_soubor(k + p):
                try:
                    os.remove(k + p)
                except OSError:
                    pass
                return None
            try:
                os.utime(k + p)   # naposledy použito – úklid maže nejdéle nepoužité
            except OSError:
                pass
            return k + p
    return None


_ulozeno = [0]


def uloz_url(url, data, delka=None):
    """Uloží obrázek stažený z adresy (jen opravdový a úplný). Vrací cestu nebo None."""
    p = pripona(data)
    if not p or not cely(data, delka):
        return None
    cil = klic_url(url) + p
    try:
        os.makedirs(os.path.dirname(cil), exist_ok=True)
        tmp = f"{cil}.{os.getpid()}.{id(data)}.tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, cil)   # atomicky: souběžné stažení téhož snímku si nepřekáží
    except OSError:   # plný disk, sandbox bez zápisu – mezipaměť je jen úspora, práci nezastaví
        return None
    _ulozeno[0] += 1
    if _ulozeno[0] % 200 == 1:   # úklid jen občas (prochází celou složku)
        uklid()
    return cil


def uklid():
    """Nad limitem smaže nejdéle nepoužité soubory (na 90 % limitu)."""
    soubory = []
    for d, _, fs in os.walk(os.path.join(KOREN, "web")):
        for f in fs:
            if ".tmp" not in f:
                p = os.path.join(d, f)
                try:
                    st = os.stat(p)
                    soubory.append((st.st_mtime, st.st_size, p))
                except OSError:
                    pass
    celkem = sum(s for _, s, _ in soubory)
    for _, s, p in sorted(soubory):
        if celkem <= LIMIT * 0.9:
            break
        try:
            os.remove(p)
            celkem -= s
        except OSError:
            pass


def zapocti(velikost, z_disku):
    """Statistika pro „cache.py stav“: vzato z disku místo z archivu, nebo staženo a uloženo. Bez zámku – jen přibližná."""
    try:
        st = json.load(open(STAT, encoding="utf-8"))
    except (OSError, ValueError):
        st = {"od": time.strftime("%Y-%m-%d")}
    k = "z_disku" if z_disku else "stazeno"
    st[k] = st.get(k, 0) + 1
    st[k + "_mb"] = round(st.get(k + "_mb", 0) + velikost / 1024 ** 2, 2)
    try:
        os.makedirs(KOREN, exist_ok=True)
        tmp = f"{STAT}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f)
        os.replace(tmp, STAT)
    except OSError:
        pass


def odvod(src, out, crop=None, zmenseni=1):
    """Výřez (zlomky 0–1) a zmenšení (1, 2, 4 …) z uloženého snímku bez sítě. True = povedlo se."""
    M = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))
    if not M:
        return False
    args = [M, src + "[0]"]
    if crop:
        r = subprocess.run([M, src + "[0]", "-format", "%w %h", "info:"], capture_output=True, text=True)
        try:
            W, H = map(int, r.stdout.split())
        except ValueError:
            return False
        x0, y0, x1, y1 = crop
        args += ["-crop", f"{round((x1 - x0) * W)}x{round((y1 - y0) * H)}+{round(x0 * W)}+{round(y0 * H)}", "+repage"]
    if zmenseni > 1:
        args += ["-resize", f"{100 / zmenseni:g}%"]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    return subprocess.run(args + ["-quality", "90", out], capture_output=True).returncode == 0


def main(a):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    if a[:1] != ["stav"]:
        sys.exit(__doc__)
    n = s = 0
    for d, _, fs in os.walk(os.path.join(KOREN, "web")):
        for f in fs:
            n += 1
            s += os.path.getsize(os.path.join(d, f))
    print(f"{KOREN}: {n} souborů, {s / 1024 ** 2:.0f} MB z {LIMIT / 1024 ** 3:g} GB "
          "(nejdéle nepoužité se nad limitem mažou samy)")
    try:
        st = json.load(open(STAT, encoding="utf-8"))
        print(f"od {st.get('od')}: z archivu staženo {st.get('stazeno', 0)} obrázků ({st.get('stazeno_mb', 0):.0f} MB), "
              f"z disku místo archivu {st.get('z_disku', 0)} ({st.get('z_disku_mb', 0):.0f} MB)")
    except (OSError, ValueError):
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
