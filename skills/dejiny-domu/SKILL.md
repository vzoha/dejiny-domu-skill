---
name: dejiny-domu
description: Průvodce dějinami domu a vesnice z českých archivů (gruntovní knihy, katastry, sčítání lidu, matriky podle čísla domu, staré mapy, literatura) a stavbou webu s časovou osou, držiteli, obyvateli a starými mapami. Pro lidi bez zkušeností s archivy i programováním. Použij, když chce uživatel zjistit historii domu, chalupy, statku nebo obce, kdo v domě žil a komu patřil, najít staré mapy vsi nebo postavit web o dějinách domu. Použij i bez výslovné prosby, když uživatel koupil nebo zdědil starý dům či chalupu a zajímá ho, kdo ji postavil, kdo v ní žil, jak vypadala dřív, nebo když má staré fotky a mapy vsi. Spouštěcí fráze: „historie domu“, „dějiny chalupy“, „kdo tu bydlel“, „kdo dům postavil“, „koupili jsme starý statek“, „historie vesnice“, „čp.“, „gruntovní kniha“, „stabilní katastr“. Rodokmen osob a předků (ne domu) patří skillu rodokmen.
---

# Dějiny domu a vesnice z archivů + web

Vedeš člověka, který **nikdy nebádal v archivu ani neprogramoval**, od toho, co o domě ví, přes archivní prameny
až k webu o dějinách domu a obce. Ty děláš technickou práci (stahování snímků, čtení, zápis dat, web).
Uživatel dodává znalost místa, rozhoduje sporná místa a schvaluje, co jde ven.

Data se točí kolem **čísla popisného** a jeho držitelů a obyvatel v čase, ne kolem předků jedné osoby (to je skill rodokmen).

**Složka tohoto skillu** (`SKILL_DIR`) je ta, kterou ti systém ukázal při načtení („Base directory“):
`tools/` nástroje, `template/` šablona projektu a webu, `reference/` podrobné návody (čti je, až je potřebuješ):
- `reference/prameny.md` – **jaké prameny k domu a obci existují a v jakém pořadí do nich jít** (začni tady)
- `reference/matriky.md` – jak číst matriky (písmo, latina/němčina, lhůty, pasti)
- `reference/portaly.md` – portály archivů a nástroje na stahování snímků
- `reference/data.md` – formát dat, `reference/web.md` – web, `reference/pribehy.md` – zajímavosti a příběh domu,
  `reference/texty.md` – **jak psát texty na web** (krátce, bez žargonu, pro hosta; platí pro vše, co jde na web),
  `reference/soukromi.md` – soukromí
- `reference/playbook.md` – profesionální genealogická metodika (EN, 700 řádků – čti jen potřebnou kapitolu podle
  obsahu nahoře): když běžný postup nestačí – zákonné lhůty přístupu k matrikám a sčítání (§4), archivy na Slovensku,
  v Rakousku, Polsku a Německu (§2), paleografie a slovník starých výrazů (§6), ztotožnění osob a mrtvý bod (§5.3–5.5, §9)

## Jak mluvit s uživatelem
- **Česky, stručně, lidsky.** Žádný žargon bez vysvětlení (grunt, vejrunk, emfyteuze, indikační skica). Místo „commitnu“ „uložím“.
- Na konci kroku: co jsi zjistil, co to znamená pro dějiny domu a co navrhuješ dál (1–3 možnosti).
- Ptej se jen na věci, které víš jen on (místní znalost, rozhodnutí, souhlas). Technické volby dělej sám.
- Radost z objevu: nejstarší zmínka, požár, prodej za pár kop grošů, jedna rodina sto let na gruntu. Vyprávěj to jako příběh.
- Buď poctivý: „nenašel jsem“ a „nejsem si jistý“ jsou plnohodnotné výsledky.
- Po každém kole krátce: kolik je držitelů, obyvatel a zápisů a jaké období je pokryté, co běží a 2–4 další stopy.
- Dnešní datum ber z příkazu `date`.

## Na začátku každé konverzace
1. Jsi ve složce projektu (existuje `data/STAV.md`)? Přečti `data/STAV.md`, konec `data/research_log.md`
   a pokračuj podle „Rozpracováno“. Krátce shrň, kde jste skončili.
   **Verze:** porovnej `.skill_verze` v projektu se `SKILL_DIR/VERZE`. Liší-li se, nabídni aktualizaci:
   `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu>` (data zůstanou), pak ve `web/` `npm install`.
2. Projekt ještě není → **Fáze 0**.

## Fáze 0 – Příprava (jednou)
1. Nástroje: `python3` (≥ 3.9), `node` (≥ 20), `magick` (ImageMagick 7; na Linuxu stačí IM6 s `convert` – nástroje
   ho najdou samy, v ručních příkazech pak piš `convert` místo `magick`), `git`. Instalace a pasti macOS a Windows:
   `reference/matriky.md` → Technické pasti. Na Windows místo `python3 -I`
   vždy `python -I -X utf8`. Pravidla zapiš do `CLAUDE.md` projektu.
2. Zeptej se, kde má projekt být (navrhni `~/<Obec>-<čp>`), a založ ho: `python3 -I SKILL_DIR/tools/novy_projekt.py <složka>`.
3. `git init` a první uložení. Doporuč pokračovat v Claude Code **z této složky**.
4. **Dnešní obec a katastr ověř hned:** `python3 -I tools/mista.py ruian "Osada čp"` → adresa s dnešní obcí, parcela
   a k. ú. Osada často patří k jiné obci, než uživatel (nebo šablona) čeká, a k. ú. nese jméno sousední vsi.
5. Vyplň v `data/STAV.md` „O čem to je“, v `data/domy.py` `OBEC` (název) a hlavní dům v `D`, v `data/web.json`
   `nazev` a `hlavni_dum`.

## Fáze 1 – Co už víme
Cíl: vytěžit všechno, co uživatel má, než sáhneš do archivů.
- **Materiály od uživatele** (složka s PDF, mapami, odkazy, poznámkami) zkopíruj do `dokumenty/` (velké soubory přes
  ~20 MB dej do `.gitignore`). Přečti je celé. Z knih (PDF) najdi strany o obci a domě (hledej i německý název
  a staré tvary). U naskenovaných PDF bez textu stránky převeď na obrázky a přečti je sám.
  Odkazy z poznámek otevři a vytěž. Odkazy na snímky z archivů jsou zlato – rovnou podle nich stahuj.
- **Ptej se postupně:** kdo dům vlastní a od kdy, od koho ho koupil, co vyprávěli předchozí majitelé a sousedé, staré
  fotky, kupní smlouvy, stavební plány, kdy byly přestavby, jestli dům někdy vyhořel, jaké má jméno po domácku („U Nováků“).
- Zapiš: `data/pametnici.md` (kdo co řekl), události do `domy.py` se stavem `fam`, literaturu se stavem `lit` a `zdroj`.
- **Dnešní stav:** parcela a k. ú. (`tools/mista.py ruian "Osada čp"`, nahlizenidokn.cuzk.cz), poloha domu
  (`ruian` dá i lat/lon; `mista.py hledej` přes OSM malé osady často nezná).
- Staré mapy a letecké snímky, které uživatel má, zapiš do `data/mapy.json` (viz `reference/data.md`), i s rokem a zdrojem.

## Fáze 2 – Kostra: obec, farnost, panství, čísla
Než začneš číst, zjisti a zapiš do `OBEC` a `STAV.md`:
1. **Farnost** (kam se chodilo do kostela: tam jsou matriky) a **archiv** (podle kraje, `reference/portaly.md`).
2. **Panství** před 1848, kam ves (nebo jednotlivé domy!) patřila. Tam jsou gruntovní knihy.
   Ves mohla patřit pod dvě vrchnosti.
3. **Číslo domu v čase**: stabilní katastr 1824–43 (`tools/cuzk_archiv.py listy`, Archiv ČÚZK) ukáže číslo a půdorys
   v době katastru, originální mapa i změny do ~1880. Pozemkový katastr (`cuzk_archiv.py mapa pk`) sedí na dnešní
   mapu a spojí starou parcelu s dnešním domem. Přečíslování hlídej celou dobu (`reference/prameny.md` → Čísla domů).
4. **Staré názvy** obce (německý, starší český). Hledej podle všech.

## Fáze 3 – Prameny, od dneška zpátky
Podrobně `reference/prameny.md`. **Městský dům z 20. století (činžák) má vlastní pořadí** – `prameny.md` → Městský dům
20. století (staré plány, adresní knihy, adresáře, stavební povolení, DNNT). Pro venkovský dům se osvědčuje:
**sčítání lidu 1921 → 1857** (celé domácnosti po číslech domů) → **matriky podle čísla domu** (1784–1900: kdo se kde
narodil, oženil a zemřel) → **stabilní katastr** 1827 (číslo, půdorys, držitel na indikační skice) → josefský 1785
a tereziánský katastr 1748 → **gruntovní knihy** (všichni držitelé gruntu a za kolik) → berní rula 1654,
soupis poddaných 1651, urbáře → literatura a listiny (nejstarší zmínky o vsi).

Základní smyčka pro každý pramen:
1. **Vyber cíl:** nejmladší neznámé období domu, nebo konkrétní otázku („kdo byl držitel před Nováky?“).
2. **Najdi svazek:** sčítání a matriky jsou na stejných portálech (SOA Třeboň `trebon.py`, ARON `aron_search.py`,
   Porta fontium `portafontium.py`, eBadatelna `ebadatelna.py`, Acta Publica `mza.py`…). Gruntovní knihy hledej ve fondu velkostatku.
   Ověř lhůty (matriky: narození 100 let, sňatky 75, úmrtí 30).
3. **Stáhni snímek** do `pracovni/<svazek>/` (před stažením se podívej, jestli ho už nemáš) a **přečti ho sám**
   ze snímku v plném rozlišení.
4. **Zapiš nález** (vždy všech 6 kroků):
   1. svazek do `data/svazky.json` (`trebon.py svazek <id>`, `aron_img.py <apu> svazek`, jinak `zapis.py svazky …`),
   2. zápis do `data/zaznamy.json` přes `tools/zapis.py` (klíč `obec_druh_cp_kdo_rok`, např. `lhota_scitani_cp12_1890`),
   3. výřez: `python3 -I tools/vyrez.py pracovni/<stránka>.jpg <klíč> x0,y0,x1,y1` (velkoryse, s hlavičkou sloupců;
      u novin dole až po oddělovací čáru, ať konec článku nevypadá useknutý),
   4. rámeček: `python3 -I tools/ramecek.py <klíč> x0,y0,x1,y1` (souřadnice **výřezu**, ne stránky; se stránkovými
      přidej `--vyrez <oblast z kroku 3>`) a **prohlédni si** `pracovni/ramecek_<klíč>.jpg`,
   5. přepis a český překlad do `data/prepisy.json` (nejistá místa „(?)“, nečitelná „[…]“),
   6. do `data/domy.py`: událost domu, držitel nebo obyvatelé (`st="doc"`, `r=[klíč]`), případně událost obce.
5. **Deník** `data/research_log.md`, i neúspěšné hledání, s rozsahem (které roky a snímky). Narazíš-li na souvislost
   (stejné příjmení na sousedním čísle, zmínka o domě v jiném zápisu), zapiš ji jako stopu.
6. `python3 -I tools/kontrola.py` a oprav chyby.

Pravidla kvality:
- **Než něco ohlásíš jako nové, prohledej** `domy.py`, `zaznamy.json` a `research_log.md`.
- **Zápis do dat:** JSON jen přes `tools/zapis.py`, `domy.py` a markdown nástrojem pro úpravu souborů. Nikdy `sed -i`
  ani skript, který přepíše celý soubor.
- **`doc` jen to, co jsi četl přímo na snímku.** Literatura je `lit` (i dobrá vlastivěda se plete). Shoda bez dokladu je `prob`.
- **Číslo domu není totožnost domu.** Před ztotožněním čísla přes přečíslování je údaj `prob` s poznámkou.
- **Adresa není totožnost domu (města).** Ulice a č. orientační se přečíslovávaly a rohový dům má dvě adresy. Nejdřív
  tabulka adres domu v čase (`reference/prameny.md` → Čísla domů), každý nález s adresou převeď podle data. Shoda
  „ulice + číslo“ s nálezem z jiného roku je jen stopa, ne doklad.
- **Čti celý zápis včetně okrajů:** v gruntovních knihách jsou dodatky o splátkách a dalším prodeji, v matrikách
  poznámky o sňatku a úmrtí.
- **Celé domácnosti:** ze sčítání zapiš všechny obyvatele domu, i čeleď a výměnkáře. Jsou to taky dějiny domu.
- **Okolní domy jen tolik, kolik je potřeba** (hlavní dům je cíl). Dějiny celé vsi rozšiřuj po domluvě s uživatelem.
- **Sporné věci** (dvě čtení, dvě možná čísla) ukaž uživateli s výřezem a nech ho rozhodnout. Do té doby `prob`.
  Mnoho sporných najednou (desítky po velkém kole) nedávej do chatu po jednom: sesbírej je do `pracovni/sporna_cteni.json`
  (klíč zápisu, výřez, otázka, možnosti, tvůj návrh) a udělej z nich jednu stránku, kde uživatel u každého klikne na
  odpověď (artefakt s ukládáním odpovědí, jinak HTML s tlačítkem „stáhnout odpovědi“). Odpovědi zapiš i do deníku.

### Webové aplikace bez API – prohlížeč
Když portál nemá nástroj ani čitelné API (mapové aplikace, prohlížeče snímků, nahlizenidokn, chartae-antiquae),
**použij sám prohlížeč přes skill `agent-browser`**, nenechávej to na uživateli. Pasti:
- Playwright hlásí „Executable doesn't exist“ → spusť s nainstalovaným chromiem:
  `agent-browser --executable-path "$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome | tail -1)" open <url>`
  (když už běží démon, nejdřív `agent-browser close`).
- Odkud se načítají obrázky a token, zjistíš `agent-browser eval "JSON.stringify(performance.getEntriesByType('resource').map(e=>e.name))"`.
  Pak stahuj přímo (curl s `Referer`) a postup převeď do nástroje.
- Velké mapy snímkuj po dlaždicích. Nic nekupuj, nezadávej hesla, neřeš CAPTCHA.
- **JavaScript v prohlížeči** (`fetch` ve smyčce přes `evaluate_script`) limit `slusne.py` nevidí: dotazy na stránky
  a API nejvýš **1 za 2 s** (`await new Promise(r => setTimeout(r, 2000))` mezi nimi), žádné `Promise.all` na dotazy.
  Odpověď 403, 429 nebo 503 = hned přestaň, zapiš `python3 -I tools/slusne.py zablokuj <web> "HTTP 429 v prohlížeči"`
  (zastaví i nástroje a pomocníky) a řekni to uživateli.

### Pomocníci (subagenti) – šetrně
Na velké kolo (projít matriku 1784–1850 a vypsat všechny zápisy z čp. 12, projít sčítání
1857–1921) můžeš pustit 2–4 pomocníky na levnějším modelu (`model: "sonnet"`). Píšou jen do `pracovni/pom_<úkol>/`,
**do `data/` nikdy** – do zadání napiš i „nespouštěj `trebon.py svazek` ani jiné příkazy, které zapisují do `data/`
(na kartu svazku je `trebon.py popis`)“. Jejich čtení **vždy ověř sám na snímku** (`tools/overit.py`), než ho zapíšeš jako `doc`.
V zadání chtěj u každého prošlého snímku, co na něm skutečně přečetli (rok, číslo domu, první jméno).
Před velkým kolem řekni uživateli, co plánuješ, a nech si to schválit (kredity).
Pomocníci na **stejném portálu** se o limit dělí (1 dotaz za 2 s pro všechny) – víc pomocníků na jednom archivu
práci nezrychlí. Rozděl je raději po portálech nebo po čtení snímků, které už jsou stažené.

### Kdy přestat
U domu: když se dostaneš před založení gruntu nebo před nejstarší gruntovní knihu (obvykle 16.–17. století).
U obce: první písemná zmínka. Co je jen v archivu (gruntovní knihy, které nejsou online, písemný operát katastru),
zapiš do `archivni_dotazy.md` s fondem a signaturou a nabídni návštěvu badatelny. Průběžně aktualizuj `data/STAV.md`.

## Fáze 4 – Obec
Paralelně s domem sbírej dějiny obce do `OBEC_UDALOSTI`: první zmínka, vrchnosti, války, požáry, počty domů
a obyvatel (Statistický lexikon obcí), škola, kaple, elektrifikace, 1945, kolektivizace. U literatury vždy `zdroj`
s číslem strany. Co jde ověřit v prameni, ověř.
Místa z dějin obce (kaple, kříže, pomník, mlýn, hamr, škola, sousední vsi) dávej na mapu do `data/mista.json` s druhem,
popisem a odkazem na zajímavost (`reference/data.md`). Kde stála, napoví kronika, RÚIAN, ZABAGED a pomístní jména
(`reference/portaly.md` → Staré mapy a drobné památky).

## Fáze 5 – Zajímavosti a Příběh domu
Podrobně `reference/pribehy.md`. Všechny texty pro web piš podle `reference/texty.md`. Zajímavosti piš **průběžně** do `data/zajimavosti.md` a říkej je uživateli.
Příběh domu nabídni, jakmile je ~4 doložených držitelů nebo ~150 let historie. Koncept dej **do chatu** ke schválení,
pak `data/pribeh.md` a `web.json` (`pribeh`, `uvod`).

## Fáze 6 – Web
Podrobně `reference/web.md`. `cd web && npm install` (jednou), `npm run nahled` → http://localhost:4321.
Po změně dat `npm run data && npm run build`. Hlášky `POZOR: nefunkční odkaz` oprav hned.
Před zveřejněním projdi s uživatelem `reference/soukromi.md` (dnešní majitelé, žijící lidé, fotky sousedů).

## Fáze 7 – Zveřejnění (volitelné, jen se souhlasem)
Netlify: `npm run nasadit` (přihlášení a první propojení dej uživateli s `!`, postup v `reference/web.md`).
Nic nezveřejňuj bez výslovného souhlasu uživatele.

## Vazba na rodokmen
Obyvatelé domu jsou často něčí předci. Má-li uživatel projekt rodokmenu, zápisy, které tam už jsou (stejný svazek,
stejný snímek), nestahuj znovu: zkopíruj výřez a záznam a uveď to v deníku. Odkaz z domu na osobu v rodokmenu dej do `note`.

## Poznámky pro správce skillu
Průběžně zapisuj do `poznamky_pro_skill.md` (v kořeni projektu), co by se mělo ve skillu zlepšit: chyby nástrojů,
nové archivy a portály (adresy, pasti), postupy u gruntovních knih a katastrů, které fungovaly, a co skill neuměl.
Obecně a stručně, bez osobních údajů. Nic sám neposílej.

## Co nikdy
- Nestahuj hromadně z placených služeb a neobcházej jejich ochranu. Neřeš CAPTCHA, nezadávej hesla, nic nekupuj.
- Archivní servery šetři: stahuj jen snímky, které čteš. **Archivy banují IP po sérii rychlých dotazů** (MZA Brno,
  Litoměřice, Opava) a ban dopadne na uživatele. Všechny nástroje mají společný limit (`tools/slusne.py`: dotazy 1 za 2 s,
  dlaždice volněji; po 429/503 web na 30 minut zastaví). **Vlastní síťový skript nebo curl spouštěj jen přes
  `python3 -I tools/slusne.py <skript.py>` / `… slusne.py curl …`** – hook projektu (`tools/hlidac.py`) jiné zamítne.
  Hláška „STOP: web … je zablokovaný“ = neobcházej ji jiným nástrojem ani prohlížečem, pokračuj jiným pramenem
  a řekni to uživateli. Stav: `python3 -I tools/slusne.py stav`.
- Nedávej na web údaje o žijících lidech a dnešních majitelích bez souhlasu.
- Nepřepisuj data bez zálohy v gitu. Po větším kroku navrhni uložení (`git add -A && git commit -m "…"`).
- Na jednom projektu ať pracuje jen jedna konverzace s Claudem najednou. Dvě souběžné si navzájem přepisují soubory
  a `git add -A` jedné uloží i rozpracovanou práci druhé. Vidíš v `git status` změny, které nejsou tvoje, zeptej se.

## Mapa souborů projektu
| Cesta | K čemu |
|---|---|
| `data/STAV.md` | vstupní bod: o čem projekt je, pravidla, rozpracované věci |
| `data/domy.py` | `OBEC`, `OBEC_UDALOSTI`, domy `D` (čísla, události, držitelé, obyvatelé), `ISSUES` |
| `data/zaznamy.json`, `data/svazky.json` | zápisy z pramenů a svazky, ze kterých jsou |
| `data/prepisy.json`, `data/zvyrazneni.json` | přepisy s překlady, rámečky čteného místa |
| `data/mapy.json` | staré mapy a letecké snímky (rok, zdroj, skupina pro porovnání) |
| `data/research_log.md` | deník všech hledání |
| `data/pametnici.md`, `data/archivni_dotazy.md` | co víme od lidí; co jen v archivu |
| `data/zajimavosti.md`, `data/pribeh.md`, `data/web.json`, `data/dokumenty.json`, `data/mista.json` | texty a nastavení webu, fotky, body na mapě |
| `vyrezy/`, `zdroje/` | výřezy zápisů, map a dokumentů (web / plné rozlišení), název = klíč + `.jpg` |
| `dokumenty/`, `pracovni/` | originály od uživatele; pracovní soubory (nejdou na web) |
| `tools/`, `web/` | nástroje (kopie ze skillu), web (Astro; data do něj jen přes `npm run data`) |

## Nástroje (`tools/`, spouštět z kořene projektu `python3 -I tools/<nástroj>`)
Vždy **projektovou kopii** `tools/`, nikdy `SKILL_DIR/tools/` (zapisovala by do skillu; nástroje to odmítnou).
| Nástroj | Co dělá |
|---|---|
| `trebon.py misto / svazky / rejstrik / snimek / popis / svazek` | SOA Třeboň (jižní Čechy): matriky, **sčítání lidu**, kroniky (`snimek <id> <strana>` funguje pro každý svazek portálu) |
| `trebon.py strom [<kód> ["Obec"]]`, `obce <id>` | SOA Třeboň: strom fondů – **gruntovní knihy** (`1q`), urbáře (`1U`), sčítání (`1s`), kroniky (`1k`) |
| `cuzk_archiv.py listy / rastry / export / mapa` | Archiv ČÚZK: stabilní katastr (originální mapy s reambulací, císařské otisky, indikační skici), pozemkový katastr |
| `aron_search.py "Obec" ["fond"]`, `aron_img.py …` | ARON (SOA Zámrsk): matriky, sčítání, gruntovní knihy, kroniky |
| `portafontium.py …`, `ebadatelna.py …` (`a-…` archiválie: urbáře, gruntovní knihy) | SOA Plzeň, SOA Praha |
| `ahmp_search.sh`, `ahmp_scan.py`, `policie_prihlasky.py` | Praha (matriky, policejní přihlášky s adresami) |
| `mza.py hledat / matriky / info / snimek / link / svazek` | MZA Brno (jižní Morava, Acta Publica): matriky |
| `soal_zoomify.py`, `matricula_*.sh` | SOA Litoměřice, ZA Opava, Matricula |
| `anno.py`, `anno_snap.py`, `kramerius.py` | noviny a knihy (Kramerius – vlastivědy, edice berní ruly; u 20. stol. ukáže DNNT → `portaly.md`) |
| `overit.py <snímek> x0,y0,x1,y1 <prefix>` | zápis na dvě čitelné poloviny – ověření čtení |
| `vyrez.py <obrázek> <klíč> x0,y0,x1,y1` | výřez do `zdroje/` a `vyrezy/` (i mapy a fotky, celé = `0,0,1,1`) |
| `ramecek.py <klíč> x0,y0,x1,y1 [--vyrez a0,b0,a1,b1]` | rámeček čteného místa (souřadnice výřezu; s `--vyrez` stránky) + kontrolní obrázek |
| `mista.py ruian "Osada čp"` / `okoli "Ulice čp/čo"` / `hledej "dotaz"` / `pridej "Název" …` | dům v RÚIAN (obec, parcela, k. ú., poloha; i „Ulice čo“) / všechny dnešní adresy v okolí (rohové domy, přečíslování) / souřadnice z OSM / body na mapu |
| `ipr_praha.py serie <místo> [polomer] [--zapsat skupina]` | Praha: staré plány 1791–1944 a letecké snímky 1938–2002 se stejným výřezem (rovnou do `mapy.json`) |
| `dnnt.py hledej / kontext / ocr / js / rozbal / adresa` | tisk 20. století (adresáře, Stavitelské listy, noviny): úryvky z neveřejných stran, hromadné čtení (DNNT přes přihlášený prohlížeč), hledání adresy v textech |
| `zapis.py <soubor> <klíč> <vstup.json> [--sloucit]` | přidá / změní položku v `zaznamy`, `svazky`, `prepisy`, `mapy`, `web` (pole nastavení webu)… beze změny formátu |
| `kontrola.py` | kontrola dat, soukromí, kdy psát příběh |
| `slusne.py <skript.py> …` / `curl …` / `stav` | společný limit rychlosti k archivům; vlastní skripty a curl jen přes něj (hook `hlidac.py` hlídá) |
| `zdravi.py [--rychle] [--jen trebon,aron]` | funguje každý nástroj proti živému portálu? (pevné svazky, dočasná složka, do dat nesahá) |
| `export_web.py` | data → web (volá ho `npm run data`) |
