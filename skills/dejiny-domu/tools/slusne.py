#!/usr/bin/env python3
"""Slušný přístup k webům archivů: společný limit rychlosti a zastavení, když server dá najevo, že ho zatěžujeme.

Archivy (MZA Brno, SOA Litoměřice, ZA Opava…) banují IP adresu po sérii rychlých dotazů. Ban dopadne na uživatele
a archivy pak přitvrzují vůči všem. Proto:
- limit platí pro každý web zvlášť a je SPOLEČNÝ všem procesům (pomocníci/subagenti, dva nástroje najednou),
- dotazy (hledání, API, HTML) přísně – výchozí 1 za 2 s; obrázky a dlaždice volněji – 20 za s
  (ban způsobují rychlé dotazy, ne dlaždice jednoho snímku); pauza se počítá od odpovědi, ne od odeslání –
  pomalý server by jinak dostal další dotaz hned po dokončení předchozího,
- po HTTP 429 nebo 503 (a po 403 na dotaz uprostřed práce, po stránce „zablokováno“) se web zablokuje pro všechny
  procesy a nástroj hned skončí – na 30 minut, při druhém bloku během 24 h na 2 hodiny, při dalším na 8 hodin –
  žádné další pokusy.

Nástroje v tools/ to mají zapnuté samy (`slusne.instaluj()` na začátku). Vlastní skript nebo curl spouštěj takhle:
  python3 -I tools/slusne.py pracovni/muj_skript.py [argumenty]   -> skript běží se stejným limitem (urllib, requests)
  python3 -I tools/slusne.py curl [argumenty curl]                -> curl se stejným limitem
  python3 -I tools/slusne.py stav                                 -> které weby jsou teď zablokované a do kdy
  python3 -I tools/slusne.py zablokuj <web> [důvod]               -> zablokovat web (429/503/403 v prohlížeči), délka jako výše
  python3 -I tools/slusne.py odblokuj <web>                       -> zrušit blokaci (jen když víš, že šlo o omyl)
Před každým požadavkem se navíc kontrolují podmínky portálu (tools/podminky.json, reference/podminky.md):
portál, který nástrojům stahování nedovoluje, skončí hláškou „PODMÍNKY: …“ s návodem, jak dál.
Nástroje se představují jako Claude-User (stahování na dotaz uživatele, ne plošný robot) a dodržují robots.txt
skupiny, která jmenuje Claude-User. Zákaz pro ClaudeBota (trénink), Claude-SearchBota nebo GPTBota se jich netýká,
obecné `User-agent: *` taky ne (reference/podminky.md). robots.txt se stahuje 1× za den do stejné složky.
Stav je ve ~/.cache/dejiny-domu/slusne/ (jinde: proměnná SLUSNE_DIR).
"""
import email.utils, http.client, io, json, os, re, subprocess, sys, threading, time, urllib.parse, urllib.robotparser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import podminky   # co smí nástroje stahovat (tools/podminky.json)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

# (s mezi dotazy, s mezi obrázky). Weby, které banují, přísně; velké státní služby volněji.
VYCHOZI = (2.0, 0.05)
LIMITY = {
    "ags.cuzk.gov.cz": (0.5, 0.05), "ags.cuzk.cz": (0.5, 0.05),   # ArcGIS ČÚZK – mapy jsou dotazy na export
    "kramerius5.nkp.cz": (1.0, 0.05), "anno.onb.ac.at": (1.0, 0.05),
    "nominatim.openstreetmap.org": (1.1, 1.1),                       # pravidla OSM: nejvýš 1 dotaz za s
    "gs-pub.praha.eu": (0.5, 0.05), "geoportal.cuzk.gov.cz": (0.5, 0.05),
    "commons.wikimedia.org": (0.5, 0.05), "www.wikidata.org": (0.5, 0.05),   # API pro roboty, sériové dotazy povoleny
    "images.archives.cz": (2.0, 0.25),   # ZA Opava: 10. 11. 2026 HTTP 429/503 i po pár náhledech, když už jednou blokoval
    "digi.archives.cz": (4.0, 0.25),     # ZA Opava, badatelna: po desítkách rychlých dotazů blok 30 min, denní limit
    "kramerius.vkol.cz": (5.0, 0.5),     # Kramerius VKOL: 10. 11. 2026 HTTP 403 po 4 rychlých dotazech na OCR (nástroje jdou přes ČDK)
}
BLOKACE = 30 * 60
STOPKY = (BLOKACE, 2 * 3600, 8 * 3600)   # blok po 1., 2. a 3. (i každém dalším) odmítnutí webu během OKNO
OKNO = 24 * 3600
BAN_TEXT = {"digi.archives.cz": re.compile(rb"zablokov[a\xc3\xa1]n|byl[a ]+zablokov|blocked|nestandardn", re.I)}   # 200 s textem bloku
ROBOT = "Claude-User"
UA = f"Mozilla/5.0 (compatible; {ROBOT}; dejiny-domu skill, on user request; +https://github.com/vzoha/dejiny-domu-skill)"
ROBOTS_PLATNOST = 24 * 3600
PRIPONA = re.compile(r"\.(jpe?g|png|gif|webp|tiff?|jp2|dzi)$", re.I)   # jen v cestě: MZA má stránku knihy na …?image=…jp2
OBRAZEK = re.compile(r"_files/|iipsrv|IIIF=|Deepzoom=|ximage|zoomify|"
                     r"TileGroup|ImageProperties\.xml|isrv\d*\.cgi|/full/|default\.jpg|/image/|mrimage|/tiles?/", re.I)


MAX_DLAZDIC = 3000   # jeden snímek v plném rozlišení má nejvýš stovky dlaždic; víc = chybná odpověď serveru


def strop_dlazdic(pocet, kde):
    """Skončí dřív, než nástroj začne stahovat nesmyslně velký snímek (server poslal špatné rozměry)."""
    if pocet > MAX_DLAZDIC:
        sys.exit(f"{kde}: snímek by měl {pocet} dlaždic (strop {MAX_DLAZDIC}) – server poslal nečekané rozměry, nic nestahuji.")


class Zablokovano(SystemExit):   # SystemExit: nástroje chytají OSError/Exception – tohle jim neproklouzne do opakování
    pass


def adresar():
    d = os.environ.get("SLUSNE_DIR") or os.path.join(os.path.expanduser("~"), ".cache", "dejiny-domu", "slusne")
    os.makedirs(d, exist_ok=True)
    return d


def _soubor(host, co):
    return os.path.join(adresar(), re.sub(r"[^a-z0-9.-]", "_", host.lower()) + "." + co)


def _zamkni(f):
    if os.name == "nt":
        import msvcrt
        f.seek(0)
        while True:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError:   # LK_LOCK to zkouší jen 10 s
                pass
    else:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_EX)


def _odemkni(f):
    if os.name == "nt":
        import msvcrt
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)


def host_z(arg):
    """„https://www.mza.cz/x“ i „www.mza.cz“ → „www.mza.cz“."""
    return (urllib.parse.urlsplit(arg).hostname if "://" in arg else arg).lower()


def druh(url):
    return "obr" if PRIPONA.search(url.split("?", 1)[0]) or OBRAZEK.search(url) else "dotaz"


def blokace(host):
    """(do kdy, proč) nebo None."""
    try:
        with open(_soubor(host, "blok"), encoding="utf-8") as f:
            b = json.load(f)
    except (OSError, ValueError):
        return None
    if b.get("do", 0) <= time.time():
        return None
    return b["do"], b.get("proc", "")


def zablokuj(host, proc, sekund=0):
    """Zablokuje web podle počtu bloků za posledních 24 h (STOPKY), nejméně na `sekund` (Retry-After). Vrací do kdy.
    Opakovaný blok = server si nás pamatuje; další pokus po 30 min by ho jen prodloužil (ZA Opava 10. 11. 2026).
    Zápis přes dočasný soubor a os.replace: souběžný proces nikdy nepřečte napůl zapsanou blokaci."""
    cil, ted = _soubor(host, "blok"), time.time()
    try:
        with open(cil, encoding="utf-8") as f:
            historie = [t for t in json.load(f).get("historie", []) if t > ted - OKNO]
    except (OSError, ValueError):
        historie = []
    historie.append(ted)
    do = ted + max(sekund, STOPKY[min(len(historie), len(STOPKY)) - 1])
    tmp = f"{cil}.{os.getpid()}.{threading.get_ident()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"do": do, "proc": proc, "historie": historie}, f, ensure_ascii=False)
    os.replace(tmp, cil)
    return do


def sekund_z_retry_after(hodnota):
    """Retry-After je počet sekund, nebo datum (RFC 9110 § 10.2.3). Neznámý tvar → None."""
    hodnota = str(hodnota or "").strip()
    if hodnota.isdigit():
        return int(hodnota)
    try:
        return max(0, round(email.utils.parsedate_to_datetime(hodnota).timestamp() - time.time()))
    except (TypeError, ValueError):
        return None


def _hlaska(host, do, proc):
    zbyva = max(1, round((do - time.time()) / 60))
    return (f"STOP: web {host} je zablokovaný ještě {zbyva} min ({proc}). Server dal najevo, že ho zatěžujeme – "
            f"NEZKOUŠEJ to znovu ani jinou cestou (jiný nástroj, curl, prohlížeč). Pokračuj jiným pramenem "
            f"a k tomuhle se vrať po {time.strftime('%H:%M', time.localtime(do))}. Řekni to uživateli.")


class Fronta(SystemExit):
    pass


class RobotsZakazuje(SystemExit):
    pass


def _stahni_robots(host, https, port):
    """Text robots.txt, nebo "" (chybí, chyba, HTML místo textu). Mimo limit a hlídání kódů: 1 požadavek za den."""
    _lokalni.robots = True
    try:
        c = (http.client.HTTPSConnection if https else http.client.HTTPConnection)(host, port, timeout=15)
        c.request("GET", "/robots.txt", headers={"User-Agent": UA})
        r = c.getresponse()
        text = r.read(500_000).decode("utf-8", "replace")
        return text if r.status == 200 and "html" not in (r.getheader("Content-Type") or "") else ""
    except (OSError, http.client.HTTPException):
        return ""
    finally:
        _lokalni.robots = False


def robots_povoli(host, cesta, https=True, port=None):
    """Povolí robots.txt webu Claude-User tuhle cestu? Rozhoduje jen skupina, která Claude-User jmenuje."""
    soubor = _soubor(host, "robots")
    try:
        cerstvy = time.time() - os.path.getmtime(soubor) < ROBOTS_PLATNOST
    except OSError:
        cerstvy = False
    if cerstvy:
        with open(soubor, encoding="utf-8") as f:
            text = f.read()
    else:
        text = _stahni_robots(host, https, port)
        with open(soubor, "w", encoding="utf-8") as f:
            f.write(text)
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    skupina = next((e for e in rp.entries if e.applies_to(ROBOT)), None)   # `*` je v rp.default_entry, sem nepatří
    return skupina is None or skupina.allowance(cesta or "/")


def zkontroluj_robots(host, cesta, https=True, port=None):
    if not robots_povoli(host, cesta, https, port):
        raise RobotsZakazuje(f"ROBOTS: {host} v robots.txt zakazuje {ROBOT} cestu {cesta} – web si nepřeje AI ani na dotaz "
                             "uživatele. Nic nestahuj, ani jinou cestou. Stránku si otevře uživatel v prohlížeči sám.")


def _zkontroluj_blokaci(host):
    b = blokace(host)
    if b:
        raise Zablokovano(_hlaska(host, *b))


OCHRANA = re.compile(r"/(challenge|captcha|altcha)\b|[?&](challenge|captcha)=", re.I)


class Ochrana(SystemExit):
    pass


def zkontroluj_ochranu(adresa):
    """Adresa ověření proti robotům (i jako cíl přesměrování) → konec. Ochrana se nikdy neobchází."""
    if OCHRANA.search(adresa or ""):
        raise Ochrana(f"OCHRANA: {host_z(adresa)} chce ověření proti robotům ({adresa}). NEOBCHÁZEJ ho – nástroj ani "
                      "prohlížeč řízený skriptem. Stránku otevře uživatel v prohlížeči sám a ty čteš, co ti pošle.")


def pockej(host, co, nejdele=None, adresa=None):
    """Počká, až je na webu volno (společně pro všechny procesy). Zablokovaný web → Zablokovano.
    nejdele: kolik s nejvýš čekat (hook má časový limit) – jinak Fronta a termín se nezabere.
    adresa: celá adresa požadavku – podmínky portálu mají i výjimky podle cesty (podminky.json, „vyjimky“)."""
    host = (host or "").lower()
    zkontroluj_ochranu(adresa)
    podminky.zkontroluj_stahovani(adresa or host, co)
    _zkontroluj_blokaci(host)
    rozestup = LIMITY.get(host, VYCHOZI)[0 if co == "dotaz" else 1]
    with open(_soubor(host, co), "a+", encoding="utf-8") as f:
        _zamkni(f)
        try:
            f.seek(0)
            try:
                posledni = float(f.read().strip() or 0)
            except ValueError:
                posledni = 0.0
            ted = time.time()
            slot = max(ted, posledni + rozestup)   # rezervace termínu – další proces dostane až ten po něm
            if nejdele is not None and slot - ted > nejdele:
                raise Fronta(f"{host}: na web čeká fronta dotazů ({slot - ted:.0f} s) – zkus to za chvíli")
            f.seek(0)
            f.truncate()
            f.write(repr(slot))
            f.flush()
        finally:
            _odemkni(f)
    if slot > ted:
        time.sleep(slot - ted)
        _zkontroluj_blokaci(host)   # mezitím mohl jiný proces dostat 429


def odpovedel(host, co):
    """Server začal odpovídat (u curl dokončil přenos): další dotaz počká celý rozestup až od teď.
    Termín už zarezervovaný jiným procesem se nezkrátí."""
    host = (host or "").lower()
    with open(_soubor(host, co), "a+", encoding="utf-8") as f:
        _zamkni(f)
        try:
            f.seek(0)
            try:
                posledni = float(f.read().strip() or 0)
            except ValueError:
                posledni = 0.0
            f.seek(0)
            f.truncate()
            f.write(repr(max(posledni, time.time())))
            f.flush()
        finally:
            _odemkni(f)


def _byl_uspech(host):
    """Odpověděl web v posledních 30 min v pořádku (kterémukoli procesu)? Pak 403 není špatný User-Agent, ale zátěž."""
    try:
        return time.time() - os.path.getmtime(_soubor(host, "ok")) < BLOKACE
    except OSError:
        return False


def posoudit(host, co, kod, retry_after=None):
    """Po odpovědi: 429/503 (a 403 na dotaz) → zablokovat web a skončit.
    403 hned na první dotaz bývá špatný User-Agent nebo neveřejná stránka, ne zátěž – skončí bez blokace."""
    host = host.lower()
    if kod < 400:
        with open(_soubor(host, "ok"), "w"):
            pass
        return
    if kod == 403 and co == "dotaz" and not _byl_uspech(host):
        raise SystemExit(f"{host} odmítl dotaz (HTTP 403) – buď chybí prohlížečový User-Agent / stránka není veřejná, "
                         "nebo web zablokoval IP adresu (v prohlížeči „Sorry, you have been blocked“ → vypni VPN nebo "
                         "zkus jinou síť). Neopakuj dotaz ve smyčce.")
    if kod in (429, 503) or (kod == 403 and co == "dotaz"):
        proc = f"HTTP {kod}"
        raise Zablokovano(_hlaska(host, zablokuj(host, proc, sekund_z_retry_after(retry_after) or 0), proc))


def posoudit_text(host, telo):
    """Stránka s kódem 200, která hlásí zablokování (ZA Opava) → zablokovat web jako po 429."""
    vzor = BAN_TEXT.get(host.lower())
    if vzor and telo and vzor.search(telo):
        proc = "stránka hlásí zablokování"
        raise Zablokovano(_hlaska(host, zablokuj(host.lower(), proc), proc))


_lokalni = threading.local()
_instalovano = False


def _napoveda():
    """Bez toho by nástroj „--help“ hledal jako název obce. Jen u nástroje vedle slusne.py: cizí program,
    který nástroj importuje (unittest -h), si nápovědu vypíše sám."""
    hlavni = sys.modules.get("__main__")
    soubor = getattr(hlavni, "__file__", None)
    if (sys.argv[1:2] in (["-h"], ["--help"]) and hlavni is not sys.modules[__name__] and getattr(hlavni, "__doc__", None)
            and soubor and os.path.dirname(os.path.abspath(soubor)) == os.path.dirname(os.path.abspath(__file__))):
        print(hlavni.__doc__)
        sys.exit(0)


def instaluj():
    """Zapne limit pro všechno, co v procesu jde přes http.client (urllib, requests, http.client).
    Nástroj spuštěný s -h/--help tu rovnou vypíše svůj popis a skončí."""
    global _instalovano
    if _instalovano:
        return
    _instalovano = True
    _napoveda()
    put, get = http.client.HTTPConnection.putrequest, http.client.HTTPConnection.getresponse
    hlavicka = http.client.HTTPConnection.putheader

    def putrequest(self, method, url, *a, **k):
        if getattr(_lokalni, "robots", False):
            return put(self, method, url, *a, **k)
        co = druh(url)
        https = isinstance(self, http.client.HTTPSConnection)
        pockej(self.host, co, adresa=url if "://" in url else f"{'https' if https else 'http'}://{self.host}{url}")
        zkontroluj_robots(self.host, urllib.parse.urlsplit(url).path if "://" in url else url.split("?", 1)[0],
                          https, self.port)
        _lokalni.posledni = (self.host, co)
        return put(self, method, url, *a, **k)

    def putheader(self, header, *values):
        if header.lower() == "user-agent" and not getattr(_lokalni, "robots", False):
            values = (UA,)   # i nástroje s vlastní hlavičkou se představí stejně
        return hlavicka(self, header, *values)

    def getresponse(self, *a, **k):
        r = get(self, *a, **k)
        if getattr(_lokalni, "robots", False):
            return r
        host, co = getattr(_lokalni, "posledni", (self.host, "dotaz"))
        odpovedel(host, co)
        posoudit(host, co, r.status, r.getheader("Retry-After"))
        if host.lower() in BAN_TEXT and r.status == 200 and "html" in (r.getheader("Content-Type") or ""):
            telo = r.read()   # přečíst a vrátit zpět, aby volající dostal celé tělo
            r.fp, r.length, r.chunked, r.will_close = io.BytesIO(telo), len(telo), False, True
            posoudit_text(host, telo)
        return r

    http.client.HTTPConnection.putrequest = putrequest
    http.client.HTTPConnection.putheader = putheader
    http.client.HTTPConnection.getresponse = getresponse


HODNOTOVE = {"-e", "--referer", "-x", "--proxy", "-H", "--header", "-b", "--cookie", "-A", "--user-agent",
             "-u", "--user", "-d", "--data", "--data-urlencode", "-F", "--form"}   # volby curl, jejichž hodnota může být adresa


def _bez_user_agentu(args):
    """Volby curl bez vlastního User-Agentu (-A, --user-agent, -H "User-Agent: …") – představí se UA ze slusne.py."""
    volby = ("-A", "--user-agent")
    ua_hlavicka = lambda x: re.match(r"\s*user-agent\s*:", x, re.I)
    out, preskoc = [], False
    for i, a in enumerate(args):
        if preskoc:
            preskoc = False
        elif a in volby or (a in ("-H", "--header") and i + 1 < len(args) and ua_hlavicka(args[i + 1])):
            preskoc = True
        elif not a.startswith("--user-agent="):
            out.append(a)
    return out


def curl(args, **kw):
    """Spustí curl s limitem: počká podle adresy, po odpovědi posoudí kód webu, kde curl skončil (i po přesměrování).
    Jedna adresa na volání – víc adres by curl stáhl hned po sobě mimo limit. Vrací CompletedProcess (stderr jako text)."""
    urls = [a for i, a in enumerate(args) if re.match(r"https?://", a) and (i == 0 or args[i - 1] not in HODNOTOVE)]
    if len(urls) > 1:
        sys.exit("slusne.py curl: jedna adresa na jedno volání (víc adres by šlo mimo limit rychlosti) – spusť curl pro každou zvlášť.")
    cil = urllib.parse.urlsplit(urls[0]) if urls else None
    host = cil.hostname if cil else ""
    co = druh(urls[0]) if urls else "dotaz"
    if host:
        pockej(host, co, adresa=urls[0])
        zkontroluj_robots(host, cil.path, cil.scheme == "https", cil.port)
    args = ["-A", UA, *_bez_user_agentu(args)]
    kw.setdefault("stderr", subprocess.PIPE)
    kw.setdefault("text", True)
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    args, znacka = list(args), "%{stderr}\nSLUSNE %{http_code} %{url_effective}\n"
    for i, x in enumerate(args[:-1]):
        if x in ("-w", "--write-out"):   # vlastní -w nechat, značku připojit za něj (curl bere jen poslední -w)
            args[i + 1] += znacka
            break
    else:
        args += ["-w", znacka]
    p = subprocess.run(["curl", *args], **kw)
    if host:
        odpovedel(host, co)
    vysledky = re.findall(r"SLUSNE (\d+) (\S*)", p.stderr or "")
    p.stderr = re.sub(r"\n?SLUSNE \d+ \S*\n", "", p.stderr or "")
    if host and vysledky:
        kod, kde = vysledky[-1]
        zkontroluj_ochranu(kde)
        posoudit(urllib.parse.urlsplit(kde).hostname or host, co, int(kod))
    return p


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "stav":
        nic = True
        for fn in sorted(os.listdir(adresar())):
            if fn.endswith(".blok"):
                b = blokace(fn[:-5])
                if b:
                    nic = False
                    print(f"{fn[:-5]}: zablokováno do {time.strftime('%H:%M', time.localtime(b[0]))} ({b[1]})")
        if nic:
            print("Žádný web není zablokovaný.")
    elif a[0] == "zablokuj" and len(a) > 1:
        host = host_z(a[1])
        do = zablokuj(host, " ".join(a[2:]) or "ručně")
        print(f"{host}: zablokováno do {time.strftime('%H:%M', time.localtime(do))}")
    elif a[0] == "odblokuj" and len(a) > 1:
        host = host_z(a[1])
        p = _soubor(host, "blok")
        if os.path.exists(p):
            os.remove(p)
        print(f"{host}: odblokováno")
    elif a[0] == "curl":
        try:
            p = curl(a[1:])
        except (Zablokovano, RobotsZakazuje, Ochrana, podminky.Zakazano) as e:
            print(e, file=sys.stderr)
            sys.exit(22)
        sys.stderr.write(p.stderr)
        sys.exit(p.returncode)
    else:
        import runpy
        sys.modules.setdefault("slusne", sys.modules[__name__])   # `import slusne` ve skriptu = tenhle modul, ne druhá kopie
        instaluj()
        sys.argv = a
        sys.path.insert(0, os.path.dirname(os.path.abspath(a[0])))
        runpy.run_path(a[0], run_name="__main__")


if __name__ == "__main__":
    main(sys.argv[1:])
