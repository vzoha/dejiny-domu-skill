#!/usr/bin/env python3
"""Tisk 20. století z Krameria NK (ndk.cz): hledání, úryvky z neveřejných stran, OCR veřejných stran a hledání adres.

Většina tisku 1900–2000 je „private“, ale s DNNT – čitelná po přihlášení na ndk.cz (reference/portaly.md → DNNT).
Vyhledávání a úryvky fungují bez přihlášení; celý text a sken neveřejné strany čte uživatel po přihlášení sám
(podmínky NDK: jen osobní čtení, stahovat a ukládat zakázáno).

Použití (z kořene projektu):
  dnnt.py hledej '<solr dotaz>' [--od 1925 --do 1940] [--titul 'Adresář*'] [--max 200] [--ulozit nazev]
      stránky s nálezem: rok | titul | strana | přístup (public / DNNT / jen knihovna) | pid | úryvky.
      Neveřejné stránky NK hledá i v Krameriích ostatních knihoven (Česká digitální knihovna): kde jsou veřejné,
      přečte je ocr; přidá i veřejné nálezy, které NK nemá.
      Dotaz jako v kramerius.py, např. 'text_ocr:"Dlouhá 14"'. --ulozit uloží seznam do pracovni/dnnt/<nazev>.tsv
      a čtecí list <nazev>.html: neveřejné stránky s odkazem na ndk.cz, úryvkem a políčkem na poznámku uživatele.
      Pozor: --od/--do vyřadí čísla periodik bez data – při malém počtu nálezů zkus i bez nich.
  dnnt.py kontext <pid> '<slova>'
      úryvky ze zadané stránky (i neveřejné) kolem slov – kontext bez přihlášení; 0 úryvků = slova na stránce nejsou.
      Úryvek z OCR je „lit“, ne „doc“ (doc = přečteno na skenu).
  dnnt.py ocr <seznam.tsv | klic=pid | pid ...> [--slozka pracovni/dnnt/ocr]
      stáhne OCR text veřejných stránek (<klic>.txt), i těch veřejných jen v jiné knihovně; neveřejné čte uživatel sám.
  dnnt.py js / rozbal – VYPNUTO: podmínky NDK zakazují DNNT stahovat a ukládat (reference/podminky.md).
  dnnt.py adresa <slozka> "<Ulice>" <číslo> [číslo ...]
      projde *.txt a najde adresu i rozdělenou na konci řádku („Dlou-\\nhá 14“), s variantami „č.“, „čp.“, „čís.“;
      vypíše soubor, hlavičku stránky (obor adresáře) a okolí nálezu.
"""
import glob, html, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: data projektu tam nejsou, zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
API = "https://kramerius5.nkp.cz/search/api/v5.0/"
CDK = "https://api.ceskadigitalniknihovna.cz/search/api/client/v7.0/"   # Česká digitální knihovna: Krameria všech knihoven
CDK_POLE = {"fedora.model": "model", "root_title": "root.title", "datum_begin": "date_range_start.year",
            "datum_str": "date.str", "dostupnost": "accessibility", "PID": "pid"}
DIR = os.path.join(ROOT, "pracovni", "dnnt")
PID = re.compile(r"uuid:[\w-]+")   # pid jde do adresy API: žádná lomítka ani tečky
UA = {"User-Agent": "Mozilla/5.0 (dejiny-domu skill)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def solr(params, api=API):
    return json.loads(get(api + "search?" + urllib.parse.urlencode({"wt": "json", **params})))


def po_strankach(params, mx, api=API):
    """Odpovědi Solru po 100 výsledcích, dokud není mx výsledků nebo konec."""
    rows, start = min(mx, 100), 0
    while start < mx:
        d = solr({**params, "rows": rows, "start": start}, api)
        yield d
        start += rows
        if start >= d["response"]["numFound"]:
            break
        time.sleep(0.5)


def cdk_dotaz(q):
    """Dotaz pro Kramerius NK přeložený na pole CDK (Kramerius 7)."""
    return re.sub(r"\b(" + "|".join(map(re.escape, CDK_POLE)) + r"):", lambda m: CDK_POLE[m.group(1)] + ":", q)


def verejne_jinde(q, mx):
    """Veřejné stránky odpovídající dotazu v jiných knihovnách (CDK): {(titul, rok, strana): (pid, knihovny, titul)}."""
    out = {}
    try:
        for d in po_strankach({"q": cdk_dotaz(q) + " AND accessibility:public",
                               "fl": "pid,root.title,date.str,page.number,cdk.collection"}, mx, CDK):
            for x in d["response"]["docs"]:
                out.setdefault(stranka_id(x.get("root.title"), x.get("date.str"), x.get("page.number")),
                               (x["pid"], ",".join(x.get("cdk.collection") or []), str(x.get("root.title"))[:80]))
    except urllib.error.HTTPError as e:   # dotaz, který NK zvládne, CDK někdy odmítne – výsledky NK nezahazovat
        print(f"POZOR: ostatní knihovny (CDK) dotaz odmítly (HTTP {e.code}), veřejné kopie jinde neověřeny", file=sys.stderr)
    return out


def stranka_id(titul, datum, strana):
    return (bez_diakritiky(str(titul or "")).strip(), str(datum or "").strip(), str(strana or "").strip())


def pristup(x):
    d = x.get("dostupnost") or "?"
    dn = x.get("dnnt") or "dnnto" in (x.get("dnnt-labels") or [])   # „dnnto“ = online po přihlášení
    return "DNNT" if d == "private" and dn else ("jen knihovna" if d == "private" else d)


def strana(x):
    return str(x["details"][0]).split()[0] if x.get("details") else ""


def cisty(h):
    return re.sub(r"\s+", " ", h).replace("<em>", "[").replace("</em>", "]")


def opt(a, name, default=None):
    if name in a:
        i = a.index(name)
        v = a[i + 1]
        del a[i:i + 2]
        return v
    return default


def hledej(a):
    od, do, titul = opt(a, "--od"), opt(a, "--do"), opt(a, "--titul")
    mx, ulozit = int(opt(a, "--max", "200")), opt(a, "--ulozit")
    q = f"({a[0]}) AND fedora.model:page"
    if od or do:
        q += f" AND datum_begin:[{od or '*'} TO {do or '*'}]"
    if titul:   # víc slov = fráze v uvozovkách (bez nich Solr vrátí HTTP 500); hvězdička ve frázi nefunguje
        holy = titul.strip('"').rstrip("*")
        q += f' AND root_title:"{holy}"' if " " in holy else f" AND root_title:{titul}"
    docs, hl, total = [], {}, 0
    for d in po_strankach({"q": q, "fl": "PID,root_title,datum_str,details,dostupnost,dnnt,dnnt-labels",
                           "hl": "true", "hl.fl": "text_ocr", "hl.fragsize": "200", "hl.snippets": "3"}, mx):
        total = d["response"]["numFound"]
        docs += d["response"]["docs"]
        hl.update(d.get("highlighting", {}))
    jinde = verejne_jinde(q, mx)
    print(f"nalezeno {total} stránek, vypisuji {len(docs)}")
    stranky = []
    for x in sorted(docs, key=lambda x: (x.get("datum_str") or "")[-4:]):
        st = dict(pid=x["PID"], datum=x.get("datum_str", ""), strana=strana(x), pristup=pristup(x),
                  titul=str(x.get("root_title"))[:80], verejne="", knihovna="",
                  uryvky=[cisty(h) for h in hl.get(x["PID"], {}).get("text_ocr", [])])
        if st["pristup"] != "public":
            st["verejne"], st["knihovna"], _ = jinde.pop(stranka_id(st["titul"], st["datum"], st["strana"]), ("", "", ""))
        stranky.append(st)
    v_nk = {st["pid"] for st in stranky}
    navic = [dict(pid=pid, datum=k[1], strana=k[2], pristup="public", titul=titul, verejne=pid, knihovna=kn, uryvky=[])
             for k, (pid, kn, titul) in jinde.items() if pid not in v_nk]
    vypis(stranky + navic)
    prenos = sum(1 for st in stranky if st["verejne"])
    if prenos or navic:
        print(f"Veřejně v jiných knihovnách (Česká digitální knihovna): {prenos} neveřejných stránek NK, {len(navic)} nálezů navíc "
              "– přečte je dnnt.py ocr.")
    if ulozit:
        uloz(ulozit, stranky + navic)


def vypis(stranky):
    for st in sorted(stranky, key=lambda st: st["datum"][-4:]):
        if st["verejne"] and st["verejne"] != st["pid"]:
            kde = f" → veřejně v {st['knihovna']}: {st['verejne']}"
        elif st["knihovna"]:
            kde = f" (jiná knihovna: {st['knihovna']})"
        else:
            kde = ""
        print(f"{st['datum']} | {st['titul'][:45]} | s. {st['strana']} | {st['pristup']}{kde} | {st['pid']}\n    "
              + " || ".join(st["uryvky"])[:300])


def uloz(nazev, stranky):
    """Seznam stránek do pracovni/dnnt/<nazev>.tsv a neveřejné bez veřejné kopie do čtecího listu <nazev>.html."""
    os.makedirs(DIR, exist_ok=True)
    tsv = os.path.join(DIR, nazev + ".tsv")
    pole = ("pid", "datum", "strana", "pristup", "titul", "verejne", "knihovna")
    open(tsv, "w", encoding="utf-8").write(
        "\t".join(pole) + "\n" + "".join("\t".join(st[k] for k in pole) + "\n" for st in stranky))
    print("uloženo:", os.path.relpath(tsv, ROOT))
    cist = [st for st in stranky if st["pristup"] != "public" and not st["verejne"]]
    listek = os.path.join(DIR, nazev + ".html")
    if not cist:
        if os.path.exists(listek):   # starý list z dřívějšího hledání by sliboval stránky, které už v seznamu nejsou
            os.remove(listek)
        return
    open(listek, "w", encoding="utf-8").write(cteci_list(nazev, cist))
    print(f"čtecí list: {os.path.relpath(listek, ROOT)} – {len(cist)} stránek přečte uživatel po přihlášení na ndk.cz; "
          f"poznámky stáhne tlačítkem jako {nazev}_poznamky.tsv (ulož do pracovni/dnnt/)")


def kontext(pid, slova):
    d = solr({"q": f'PID:"{pid}" AND text_ocr:({slova})', "rows": 1, "fl": "PID,root_title,datum_str,details,dostupnost,dnnt,dnnt-labels",
              "hl": "true", "hl.fl": "text_ocr", "hl.fragsize": "400", "hl.snippets": "20", "hl.mergeContiguous": "true"})
    if not d["response"]["docs"]:
        print("0 úryvků – slova na stránce nejsou (nebo je OCR přečetlo jinak).")
        return
    x = d["response"]["docs"][0]
    print(f"{x.get('datum_str', '')} | {x.get('root_title')} | s. {strana(x)} | {pristup(x)}")
    for h in d.get("highlighting", {}).get(pid, {}).get("text_ocr", []):
        print("  …", cisty(h))


def jmeno_souboru(s):
    """Jen písmena, číslice a _ – klíč z dat nesmí vést mimo složku (../, /)."""
    return re.sub(r"\W+", "_", s).strip("_")


def seznam(args):
    """[(klic, pid, adresa OCR)] ze souboru .tsv, z „klic=pid“ nebo z holých pid. Stránka veřejná jinde se čte z CDK."""
    out = []

    def pridej(klic, pid, verejne=""):
        if not PID.fullmatch(pid) or (verejne and not PID.fullmatch(verejne)) or not jmeno_souboru(klic):
            print(f"přeskočeno – divný pid nebo klíč: {klic}={pid} {verejne}".rstrip(), file=sys.stderr)
            return
        out.append((jmeno_souboru(klic), pid, ocr_adresa(verejne or pid, bool(verejne))))

    for a in args:
        if a.endswith(".tsv") and os.path.exists(a):
            radky = open(a, encoding="utf-8").read().splitlines()
            hlava = radky[0].split("\t")
            for r in radky[1:]:
                st = dict(zip(hlava, r.split("\t")))
                if st.get("pid", "").startswith("uuid:"):
                    pridej(f"{st['datum'][-4:]}_{st['strana']}_{st['pid'][5:13]}", st["pid"], st.get("verejne", ""))
        elif "=" in a:
            pridej(*a.split("=", 1))
        elif a.startswith("uuid:"):
            pridej(a[5:13], a)
    return out


def ocr_adresa(pid, cdk=False):
    return f"{CDK}items/{pid}/ocr/text" if cdk else f"{API}item/{pid}/streams/TEXT_OCR"


def ocr(args):
    slozka = opt(args, "--slozka", os.path.join(DIR, "ocr"))
    polozky = seznam(args)
    os.makedirs(slozka, exist_ok=True)
    nejde, chybi = [], []
    for k, pid, url in polozky:
        out = os.path.join(slozka, k + ".txt")
        if os.path.exists(out):
            continue
        try:
            text = get(url)   # nejdřív stáhnout: při chybě nesmí zůstat prázdný soubor, další běh by ho přeskočil
        except urllib.error.HTTPError as e:
            if e.code == 403:
                nejde.append(f"{k}={pid}")
                continue
            if e.code == 404:   # stránka v jiné knihovně zmizela – pokračovat dalšími
                chybi.append(f"{k}={pid}")
                continue
            raise
        open(out, "wb").write(text)
        time.sleep(0.3)
    print(f"staženo do {os.path.relpath(slozka, ROOT)}; neveřejných {len(nejde)}, nenalezených {len(chybi)}"
          + (f" ({' '.join(chybi)})" if chybi else ""))
    if nejde:
        print("Neveřejné stránky (DNNT) čte uživatel po přihlášení na ndk.cz sám – stahovat a ukládat je podmínky zakazují. "
              "Čtecí list s odkazy a poznámkami dá dnnt.py hledej … --ulozit. Stránky: " + " ".join(nejde[:40]) + (" …" if len(nejde) > 40 else ""))


CTECI_LIST = r"""<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><title>Čtecí list: {nazev}</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:900px;margin:2em auto;padding:0 1em;color:#222}}
.st{{border:1px solid #ccc;border-radius:8px;padding:.8em 1em;margin:1em 0}}
.st.hotovo{{border-color:#4a4;background:#f4fbf4}}
.uryvek{{color:#555;font-size:.9em}} textarea{{width:100%;min-height:3em;font:inherit}}
.lista{{position:sticky;top:0;background:#fff;padding:.5em 0;border-bottom:1px solid #ddd}}
</style></head><body>
<h1>Čtecí list: {nazev}</h1>
<p>Stránky jsou díla nedostupná na trhu: číst je smíte po přihlášení na <b>ndk.cz</b>, ale nesmíte je kopírovat, fotit
ani stahovat. U každé stránky klikněte na odkaz, najděte místo z úryvku a <b>vlastními slovy</b> zapište fakta
(jména, povolání, čísla domů, rok). Nic nenašli? Napište „nic“. Poznámky se ukládají v tomto prohlížeči.</p>
<div class="lista"><button onclick="stahni()">Stáhnout poznámky</button> <span id="pocet"></span></div>
{stranky}
<script>
const KLIC = "dnnt-poznamky-{nazev}";
const ulozene = JSON.parse(localStorage.getItem(KLIC) || "{{}}");
const pole = [...document.querySelectorAll("textarea")];
function obnov() {{
  pole.forEach(t => t.closest(".st").classList.toggle("hotovo", t.value.trim() !== ""));
  document.getElementById("pocet").textContent = pole.filter(t => t.value.trim()).length + " z " + pole.length + " hotovo";
}}
pole.forEach(t => {{
  t.value = ulozene[t.dataset.pid] || "";
  t.addEventListener("input", () => {{ ulozene[t.dataset.pid] = t.value; localStorage.setItem(KLIC, JSON.stringify(ulozene)); obnov(); }});
}});
obnov();
function stahni() {{
  const radky = ["pid\tdatum\tstrana\ttitul\tpoznamka"].concat(pole.filter(t => t.value.trim()).map(t =>
    [t.dataset.pid, t.dataset.datum, t.dataset.strana, t.dataset.titul, t.value.trim().replace(/\s+/g, " ")].join("\t")));
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([radky.join("\n") + "\n"], {{type: "text/tab-separated-values"}}));
  a.download = "{nazev}_poznamky.tsv";
  a.click();
}}
</script></body></html>
"""


def cteci_list(nazev, stranky):
    """HTML se stránkami, které uživatel přečte po přihlášení sám: odkaz, úryvek a políčko na vlastní poznámku."""
    e = html.escape
    karty = "".join(
        f'<div class="st"><b>{e(st["datum"])} · {e(st["titul"])} · s. {e(st["strana"])}</b> ({e(st["pristup"])})<br>'
        f'<a href="https://ndk.cz/uuid/{e(st["pid"])}" target="_blank" rel="noopener">Otevřít stránku na ndk.cz</a>'
        + "".join(f'<div class="uryvek">… {e(u)} …</div>' for u in st["uryvky"])
        + f'<textarea data-pid="{e(st["pid"])}" data-datum="{e(st["datum"])}" data-strana="{e(st["strana"])}" '
          f'data-titul="{e(st["titul"])}" placeholder="Co tam je (vlastními slovy)"></textarea></div>\n'
        for st in stranky)
    return CTECI_LIST.format(nazev=e(nazev), stranky=karty)


def bez_diakritiky(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def adresa(slozka, ulice, cisla):
    # spojit dělená slova („Dlou-\nhá“) a sjednotit mezery; porovnávat bez diakritiky (OCR „Dlouha“, „Dlóuhá“)
    vzor_ul = r"\W*".join(re.escape(c) for c in bez_diakritiky(ulice).replace(" ", ""))
    vzor = re.compile(rf"{vzor_ul}\W{{0,3}}(?:c\.?\s*p\.?|cis\.?|c\.)?\s*({'|'.join(map(re.escape, cisla))})(?!\d)")
    n = 0
    for f in sorted(glob.glob(os.path.join(slozka, "*.txt"))):
        t = open(f, encoding="utf-8-sig", errors="replace").read()
        spoj = re.sub(r"[-¬]\s*\n\s*", "", t)
        jednoradek = re.sub(r"\s+", " ", spoj)
        nd = bez_diakritiky(jednoradek)
        hlava = " / ".join(r.strip() for r in t.splitlines()[:3] if r.strip())[:90]
        for m in vzor.finditer(nd):
            n += 1
            print(f"{os.path.basename(f)} | {hlava}\n    …{jednoradek[max(0, m.start() - 160):m.end() + 40]}")
    print(f"{n} nálezů. Ověř na skenu (doc) a převeď adresu podle data na číslo popisné (prameny.md → Čísla domů).")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    c, a = a[0], a[1:]
    if c == "hledej" and a:
        hledej(a)
    elif c == "kontext" and len(a) == 2:
        kontext(*a)
    elif c == "ocr" and a:
        ocr(a)
    elif c in ("js", "rozbal"):
        sys.exit("PODMÍNKY: díla nedostupná na trhu (DNNT) jsou jen pro osobní čtení registrovaných čtenářů – "
                 "stahovat, ukládat a hromadně vytěžovat je podmínky NDK zakazují (reference/podminky.md). "
                 "Uživatel čte po přihlášení na ndk.cz sám a ty radíš; úryvky kolem slov dá dnnt.py kontext.")
    elif c == "adresa" and len(a) >= 3:
        adresa(a[0], a[1], a[2:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
