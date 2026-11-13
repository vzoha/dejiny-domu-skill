# Jak číst matriky – praktický návod

## Druhy knih
| Zkratka | Kniha | Co v ní je | Proč je cenná |
|---|---|---|---|
| **N** | narození (křty), *Liber natorum / baptisatorum*, *Geburtsbuch* | datum narození a křtu, dům (čp.), dítě, rodiče (od ~1784 i jejich rodiče a bydliště), kmotři, porodní bába | pohlaví, legitimita, rodiče matky → další generace |
| **O** | oddaní (sňatky), *Liber copulatorum*, *Trauungsbuch* | datum, dům, ženich a nevěsta (věk, stav, náboženství), jejich rodiče, svědci | **nejlepší první cíl** – otevírá dvě rodiny naráz |
| **Z** | zemřelí, *Liber defunctorum*, *Sterbebuch* | datum úmrtí a pohřbu, dům, jméno, věk, příčina | věk → odhad roku narození, stav (vdova po…) |
| **I** | index (rejstřík) k N/O/Z | jméno → datum / strana | rychlé hledání; **index bývá neúplný**, negativní výsledek v indexu nic nedokazuje |

Další prameny: sčítání lidu (1857–1921; domácnosti s daty narození), soupis poddaných 1651 (Čechy; rodiny s věkem,
děti ne všude všechny – chybějící dítě není důkaz úmrtí), berní rula 1654 (Čechy, jen hospodáři), gruntovní/pozemkové knihy (kdo vlastnil který dům – propojí generace přes dům),
vojenské záznamy, domovské listy, parte. Viz `portaly.md` a `metodika.md` (mrtvé body, prameny mimo ČR).

## Lhůty (zákon 301/2000 Sb.)
Dvě různé lhůty, nepleť je ([MV](https://mv.gov.cz/nahlizeni-do-matricnich-knih-a-sbirky-listin)):
- **Nahlížení do zápisu (§ 25b):** kdokoli, když od **toho zápisu** uplyne: narození **100 let**, sňatek **75**, úmrtí **30**.
  Dřív jen ten, koho se zápis týká, jeho rodina (manžel, rodiče, děti, sourozenci, prarodiče, vnuci, pravnuci)
  nebo kdo doloží, že výpis nezbytně potřebuje (§ 25).
- **Předání knihy archivu (§ 23):** celá kniha, až od jejího **posledního** zápisu uplyne: narození **100 let**,
  sňatky **75**, úmrtí **75**. Do té doby je na matričním úřadě (obec s rozšířenou působností / pověřený úřad).
- **Předání archivu ≠ online.** Archiv knihu naskenuje, až na ni dojde. Co je online, ukáže až portál archivu.

Příklad: úmrtí z roku 1980 smí vidět kdokoli, ale kniha vedená do 1990 je ještě na matričním úřadě – nahlížet se dá
jen tam, za přítomnosti matrikáře. Narození z roku 1890 v knize vedené do 1935 je na matrice přístupné už dnes,
do archivu kniha půjde až 2035. Dotaz na úřad zapiš do `archivni_dotazy.md`.

## Jak vypadá hledání v praxi
1. **Obec → farnost.** Malé vesnice patřily k faře v sousední obci; popis svazku vyjmenovává všechny obce farnosti.
   Hledej obec v popisu svazku (`aron_search.py "Obec"`), ne jen v názvu – a hledej i podle obce, ne jen podle fary
   z pozdějšího zápisu: obec mohla mít vlastní matriku (filiální kostel, lokálie), i když list vydala mateřská fara.
   Obec rozdělená mezi dvě fary má dvě řady knih, každou jen pro „svá“ čísla domů.
2. **Svazek podle roku a druhu.** Nejdřív `tools/sdileni.py najdi "Obec" rok N` (Mapa matrik a index matrik,
   `sdileni.md`): ukáže knihu, odhad snímku a co už někdo přečetl. Pozor na překryvy: jedna kniha pro více obcí, zvláštní knihy pro jednotlivé obce.
   **Druhopisy** (duplikáty pro děkanát nebo úřad, např. „T“ svazky v ZA Opava) mívají N, O a Z jednoho roku u sebe –
   hodí se, když originál chybí, je nečitelný nebo velký.
3. **Index, pak kniha.** Index řazený po písmenech a letech dá stránku/folio; snímek odhadni (snímek ≈ folio × 1 až 2) a dolaď.
   Starší rejstříky (18. stol.) občas ukazují o 1–4 strany vedle – když zápis na udané straně není, listuj kolem.
   Posun „snímek – strana“ se v knize mění (vložené listy, chybějící strany) – přečti číslo strany na náhledu a dopočítej.
   U starých far se vyplatí nejdřív najít **souhrnný index** přes víc desetiletí (např. N/O/Z 1636–1746) – dovede
   rychle až do 17. století. Rejstříky bývají podle **německého pravopisu**: česká jména na O a V hledej i pod W
   (Otava = Wotawa, Vávra = Wawra). Knihy pro více obcí bývají řazené po obcích, rejstřík na konci.
   Velké fary mají rejstříky i jako **samostatné svazky** (např. rejstřík oddaných přes 300 let) – hledej je nejdřív.
   **Když matrika chybí** (není online nebo se nedochovala), zkus rejstřík – bývá vedený zvlášť a přežil i tam, kde kniha
   ne. Zápis v rejstříku dokládá datum, místo a otce; zapiš ho jako `prob` (opis, ne originál) a matriku zkus později.
4. **Bez indexu: listuj chronologicky.** Odhadni pozici podle let na prvních a posledních snímcích svazku (půlení intervalu).
   Staré knihy svázané z **ročních výtahů** (Extractus, Consignatio, 18. stol.) nemusí jít po sobě a ročníky chybí;
   rok bývá jen v nadpisu výtahu. Než napíšeš „zápis tam není“, ověř hlavičky ročníků.
   **Nejisté datum** (číslice z pozdější poznámky): nejdřív projdi všechny možné roky v domovské farnosti, teprve pak
   okolní fary. (Skutečná chyba: „9?“ přečteno jako 97, prošlo se pět okolních far; sňatek byl doma o pět let dřív.)
5. **Přečti celý zápis**, pak se podívej i na okolí (dvojčata, další děti stejných rodičů).
6. **Sňatek se obvykle konal ve farnosti nevěsty** (v jejím bydlišti) – hledej ho nejdřív tam, pak ve faře ženicha.
   Nedaří se? Ve křtu dítěte bývá (Praha ~1880–1890) připsané datum a místo sňatku rodičů – ověř ho v oddaných.
7. **Rodina v katolické matrice chybí? Zkus evangelickou nebo židovskou.** Po toleranci (1781) vedly vlastní matriky
   evangelické sbory (a. v. i h. v.), jeden sbor pokrýval desítky obcí; v ARONu mají signatury „R …“ a `aron_search.py`
   je najde podle obce. Ve východních Čechách časté (Rychnovsko, Dobrušsko, Opočensko). Židovské matriky viz `portaly.md`.
   Ve 20. století (1920–1945) zkus i **civilní matriky** lidí bez vyznání u okresních úřadů (vyzkoušeno v SOA Třeboň, viz `portaly.md`).

## Čtení písma
- Kurentový rejstřík: stáhni plné rozlišení a rozřež stránku na čtvrtiny (sloupec jmen + data),
  `magick f.jpg -crop 1250x1650+X+Y +repage ctvrt.jpg`. **Dopisované řádky** se snadno přečtou špatně (Franziska × Heinrich,
  strana 131 × 151) – údaj z rejstříku vždy ověř v matrice.
- **Vybledlý inkoust, tužka, tmavý mikrofilm:** `python3 -I tools/zesil_snimek.py <snímek> [x0,y0,x1,y1] [--zvetsit 2]`
  → `<jméno>_porovnani.jpg` (nahoře šedý originál, dole odečtené pozadí a ztmavené písmo). Čti z obou: zesílení
  zvýrazní i skvrny a ztuční přeškrtnutí, sporné písmeno rozhodne originál. Ostrý snímek zesilovat netřeba.
- Do ~1780 latina nebo čeština, pak hodně němčina (kurent), od ~1860 často čeština, ve 20. století čeština.
- Česká jména v němčině/latině: Johann/Joannes = Jan, Wenzel/Wenceslaus = Václav, Joseph = Josef, Franz/Franciscus = František,
  Maria = Marie, Anna, Katharina = Kateřina, Barbara = Barbora, Magdalena = Majdalena/Magdaléna, Theresia = Terezie,
  Ludmilla = Lidmila, Dorothea = Dorota, Apollonia = Apolena, Georg/Georgius = Jiří, Matthias = Matěj, Adalbert = Vojtěch.
- Příjmení se píše foneticky a mění se (Šaršon/Scharschon/Šaršoun, Kroupa/Kraupa). Hledej všechny varianty.
- Ženská příjmení v němčině bez „-ová“ (Maria Novak = Marie Nováková).
- Názvy obcí mívají staré tvary, třeba s předsunutým „V“ („Volešnice“ = Olešnice); při hledání obce zkus i ty.
- Kurent: dlouhé „ſ“ vypadá jako „f“, „e“ jako „n“, „h“ s kličkou dolů. Při nejistotě porovnej se stejným písmenem
  jinde na stránce stejné ruky – i u „divného“ příjmení (koncové „k“ psané skoro jako „r“: „-ek“ vypadá jako „-er“).
  Slovo rozdělené přes konec řádku („Urlau-“ / „ber“) dočti na začátku dalšího řádku.
  Čárka nad „m“ / „n“ = písmeno dvakrát („kom̄en“ = kommen).
- Měsíce číslicí: 7ber = září, 8ber = říjen, 9ber = listopad, 10ber / Xber = prosinec (ne červenec–říjen).
  Číslice před „-ber“ se snadno spletou (7, 8, 9 i X). Měsíc ověř pořadím zápisů nebo jiným pramenem.
- Český pravopis do ~1850: g = j, j = í, w = v, au = ou („Gan“ = Jan, „Wáclaw“ = Václav, „kaupil“ = koupil).
  V německém zápisu č = tsch/cz, š = sch, v = w, ě = ie („Tschermak“ = Čermák, „Matieg“ = Matěj, ne Matyáš) – hledej i tyto varianty.
- Daty bývají svátky (*Dominica*, *festum S. Joannis*) – v nejasných případech dopočítej.

### Slovníček (lat. / něm. → česky)
| výraz | význam |
|---|---|
| *natus / geboren*, *baptisatus / getauft* | narozen, pokřtěn |
| *copulati / getraut*, *sponsus / Bräutigam*, *sponsa / Braut* | oddáni, ženich, nevěsta |
| *mortuus, sepultus / gestorben, begraben* | zemřel, pohřben |
| *legitimus / ehelich*, *illegitimus / unehelich* | manželský, nemanželský |
| *viduus, vidua / Witwer, Witwe* | vdovec, vdova |
| *filius, filia / Sohn, Tochter* | syn, dcera |
| *patrini / Pathen*, *testes / Zeugen*, *obstetrix / Hebamme* | kmotři, svědci, porodní bába |
| *agricola, rusticus / Bauer* | sedlák, rolník |
| *Häusler*, *casarius* | domkář |
| *Inwohner / inquilinus*, *podruh* | podruh (bydlel v cizím domě) |
| *Gärtner* (na vsi) | zahradník = malý usedlík, ne nutně pěstitel |
| *Inleute*, *Taglöhner* | podruzi, nádeníci |
| *Bürger*, *civis* | měšťan |
| *Schneider / sartor*, *Schuhmacher / sutor*, *Weber / textor*, *Schmied / faber*, *Müller / molitor* | krejčí, švec, tkadlec, kovář, mlynář |
| *N.* / *No.* / *Haus Nr.* | číslo domu (popisné) |
| *ex*, *aus*, *von* | z (obce) |
| *Lungensucht*, *Abzehrung* | souchotiny (TBC) |
| *Cholera*, *Blattern* | cholera, neštovice |
| *Fraisen* | křeče (časté u kojenců) |

## Odhad roků
- Věk při úmrtí/sňatku je často zaokrouhlený o ±2–5 let. Uváděj „asi 1756“ a hledej křest v širším okně.
  I přesné datum narození v oddacím zápisu mívá špatný měsíc: když křest v něm není, projdi celý rok ±1 a farnost
  matky (dítě se často narodilo u jejích rodičů).
- Nevěsta mívala 18–28, ženich 22–32; děti po 1,5–3 letech.
- „Vdovec“ u ženicha = hledej první manželství a děti z něj.

## Stavy údajů v datech
Stavy (`doc`, `lit`, `prob`, `fam`, `unk`) jsou v `data.md`. U matrik: `doc` jen tehdy, když zápis osobu i dům
jednoznačně určuje. Údaj z cizího stromu na internetu (MyHeritage, Geni) je nanejvýš `prob` s `note`, odkud je.

## Typické pasti (ze skutečného výzkumu)
- Písař spletl jméno dědečka (Josef místo Václava) – rozhodne více zápisů téže rodiny.
- Dítě zapsané pod jiným křestním jménem, než jakým ho volala rodina (Františka → v rodině Anna).
- Sňatek pár měsíců před porodem nebo po něm – není chyba, jen „svatba na poslední chvíli“; zajímavost pro web.
- Nemanželské dítě nese příjmení matky; otec chybí nebo je dopsán později (legitimace na okraji).
- Stejné jméno ve dvou domech nebo dvou generacích (otec a syn, bratranci) – rozliš je podle věku, manželky a domu,
  než je spojíš v jednu osobu.
- Index nenašel ≠ zápis neexistuje. Zapiš, co přesně jsi prošel.
- Pomocníci (subagenti) a OCR/AI čtou historické písmo chybně – vždy ověř sám.
- **Nenačtený snímek není „nenalezeno“.** Když konverzace narazí na limit obrázků, snímky se tiše zahodí („media removed“)
  a pomocník vrátí prázdný výsledek. Dej pomocníkovi nejvýš asi 10 snímků, ať je čte po jednom, průběžně si zapisuje
  poznámky do souboru a na konci vypíše snímky, které neviděl. Ty přečti znovu, jinak je nepočítej jako prošlé.
- **Stejné číslo domu v jiné obci.** Kniha farnosti má čísla domů všech obcí. Název obce bývá jen v nadpisu oddílu,
  třeba o pár stran dřív, a v jednom oddílu se objeví i cizí obce. U každého nálezu ověř obec. Pomocníkům napiš,
  ať u čísla vždy uvedou i obec. „Z Horní Lhoty č. 7“ u otce nebo matky je jejich původ, ne dům, kde se dítě narodilo.
- **Obec stejného jména.** Katalog (FamilySearch, ARON) může nabídnout jinou obec téhož jména. Než začneš číst,
  ověř na prvním snímku politický a soudní okres a rozsah čísel domů.

## Technické pasti (macOS, zsh) – napiš je i pomocníkům do zadání
- Shell je zsh: `for a in "x y z"; do set -- $a` slova nerozdělí (v zsh `${=a}`); `ls F*` bez shody = chyba
  „no matches found“; `echo ====` je chyba (`=` na začátku slova). Složitější smyčky pouštěj přes `bash -c '…'`.
- ImageMagick: seznam souborů předávej jako jednotlivé argumenty, ne jednou proměnnou s mezerami.
  `-annotate` potřebuje písmo: `-font /System/Library/Fonts/Supplemental/Arial.ttf` (bez něj spadne na „unable to read
  font“; totéž `montage` s popisky) – pořadí výřezů raději vypiš zvlášť.
- Ověření čtení: `python3 -I tools/overit.py <snímek> x0,y0,x1,y1 pracovni/over [v]` (zlomky 0–1, ne pixely) – zápis rozdělený na dvě poloviny
  zmenšené na 1900 px (dvoustrana je jinak nečitelná).
- Výřez pro web (`vyrez.py`) dělej jen na **čtený zápis** (případně s hlavičkou sloupců), ne na celou dvoustranu –
  na webu by byl nečitelně malý. Celá stránka je v `zdroje/` a na portálu přes odkaz.

## Technické pasti (Windows) – napiš je i pomocníkům do zadání
(Nahrazují první dva body macOS sekce; body o `overit.py` a výřezu platí i tady.)
- Python: `python -I -X utf8 tools/<nástroj>.py` (ne `python3` – bývá to nefunkční alias z Microsoft Store). Bez `-X utf8`
  je výstup do roury v cp1250: čeština se rozbije a skripty spadnou na „≈“ a „→“ (nástroje skillu si výstup přepnou
  do UTF-8 samy, vlastní jednorázové skripty ne – `-X utf8` proto používej vždy). Totéž platí při
  přesměrování do souboru (soubor z `… --osoby > x.py` by jinak vznikl v cp1250; ve Windows PowerShellu 5.1 `>` dokonce
  zapisuje UTF-16 – přesměrovávej v Git Bash). Proměnná `PYTHONUTF8` s `-I` nefunguje.
- ImageMagick je `magick`, nikdy `convert` (`convert` je ve Windows systémový nástroj na převod disku z FAT na NTFS).
  Po instalaci přes winget je `magick` v PATH až po restartu Claude Code. Písmo pro `-annotate`: `-font C:/Windows/Fonts/arial.ttf`.
- Limit délky příkazové řádky je 32 767 znaků – stovky souborů (dlaždic) v jednom příkazu `magick` neprojdou
  (WinError 206); skládej po řádcích.
- Skripty `.sh` přes Git Bash (`bash tools/…`). Markdown a JSON nikdy neupravuj `sed -i` (escapy v Git Bash rozbijí
  soubor) – data zapisuj podle pravidla „Zápis do dat“ v SKILL.md.
- Windows nerozlišuje velikost písmen v názvech (`o_29.jpg` = `O_29.jpg`) – náhled a plné rozlišení odliš předponou
  (`nahled_`, `plne_`), jinak se přepíšou.
- Datové soubory zapisuj v UTF-8 **bez BOM** (Windows PowerShell 5.1 s `-Encoding UTF8` přidá BOM a nástroje pak JSON nenačtou).

