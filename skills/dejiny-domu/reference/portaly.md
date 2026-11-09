# Portály archivů a jak z nich dostat snímky

Matriky jsou online u osmi státních archivů – podle toho, **kde dům stojí** (u lidí odjinud: kde žili; dnešní kraje zhruba odpovídají).
**Co se kde smí** (nástrojem, za peníze, zveřejnit obrázky) je v `podminky.md` – nástroje se tím řídí samy:

| Archiv | Oblast | Portál s matrikami | Vyzkoušeno se skillem |
|---|---|---|---|
| SOA Zámrsk | východní Čechy (Hradecký a Pardubický kraj) | ARON – aron.vychodoceskearchivy.cz | **ano – hotové nástroje** |
| SOA Praha | střední Čechy | eBadatelna – ebadatelna.soapraha.cz | **ano** – `ebadatelna.py` (celá kniha i jako ZIP po registraci) |
| SOA Plzeň | západní Čechy | Porta fontium – portafontium.eu | **ručně** – snímek uloží uživatel (firewall proti skriptům, jen nevýdělečně) |
| SOA Třeboň | jižní Čechy | digi.ceskearchivy.cz | **jen číst** – snímky jen k prohlížení online, čte uživatel |
| SOA Litoměřice | severní Čechy | Digitální badatelna – digi.soalitomerice.cz | **částečně – `soal_zoomify.py`** (knihu najdi v prohlížeči) |
| AHMP | hl. m. Praha | katalog.ahmp.cz (Pragapublica) | **ano – `ahmp_search.sh`, `ahmp_scan.py`** |
| MZA Brno | jižní Morava, Vysočina z části | Acta Publica – www.mza.cz/actapublica | **částečně – `mza.py`** hledá knihy, snímek uloží uživatel (ALTCHA) |
| MZA Brno – gruntovní a pozemkové knihy | totéž | ARON MZA – www.mza.cz/aron | **prohlížeč** – katalog v `agent-browser --headed` tempem člověka nebo uživatel ručně; skriptu API vrací 403 |
| ZA Opava | severní Morava a Slezsko, Olomoucko a Litovelsko | Digitální badatelna – digi.archives.cz/da/ | **částečně – `soal_zoomify.py`** (jen s prohlížečem, CAPTCHU řeší uživatel) |
| Národní archiv | židovské matriky (HBMa), soupisy; pražské policejní přihlášky 1850–1914 | digitalnibadatelna.nacr.cz; digi.nacr.cz/prihlasky2 | badatelna **ručně** (ověření „jste člověk“); přihlášky `policie_prihlasky.py` |

Pro **20. století** (městské domy, adresáře, stavební povolení) jsou hlavní **IPR Praha** (staré plány a letecké snímky
Prahy) a **DNNT na ndk.cz** (neveřejný tisk čitelný po přihlášení) – sekce níže.

**Nástroj selže nebo vrátí nesmysl?** Nejdřív `python3 -I tools/zdravi.py --jen <portál>`: zkusí pevný známý svazek. Selže-li i ten, změnil se portál (nebo má výpadek) – nehledej chybu v datech, zapiš to do `poznamky_pro_skill.md`.
Adresy u nevyzkoušených portálů ověř při prvním použití (portály se mění). Pro pohraničí a mimo ČR viz `playbook.md` §2
(Matricula pro Rakousko/Německo, Geneteka pro Polsko, FamilySearch pro Slovensko) a níže.

## Památkový katalog NPÚ (pamatkovykatalog.cz) – `tools/pamatky.py`
Kulturní památky a objekty, které památkáři jen evidují (návesní kaple, boží muka, mlýny, domy bez ochrany).
- `python3 -I tools/pamatky.py "Lniště"` → objekty v obci, části obce nebo ulici: id | název | adresa | ochrana | anotace.
  Druhý argument zúží na číslo v adrese (`pamatky.py "Na Maninách" 27`). Hledá se fulltextem, objekty jen se zmínkou
  jinde vypíše zvlášť. Víc než 250 výsledků katalog nevrátí – zúžit na část obce nebo ulici.
- `python3 -I tools/pamatky.py detail <id>` → vznik, autor, stavební vývoj, popis, **literatura o objektu**, fotky v MIS
  (popis + odkaz), odkaz do Carmen (plány, průzkumy), trvalý odkaz a citace.
- **Chybějící dům v katalogu neznamená, že nemá historickou hodnotu.** Údaje NPÚ (datace, popis) jsou `lit`, ne doklad.
- Fotky a plány (MIS, Carmen na iispp.npu.cz) jsou dílo NPÚ: do výstupu jen odkaz (`podminky.md`).
- **MIS** (`tools/mis.py`): fotky, plány a mapy i u objektů, které v katalogu nejsou. `mis.py hledej "Lniště"` →
  id | datum vzniku | typ | popis | lokalita | autor (nejvýš 50, MIS ukáže jen prvních 200 – zpřesni slovem: „kaple“,
  „čp. 12“). `mis.py detail <id>` → pracoviště, licence, místo s čp., vazba na památku. Hromadný export chrání
  reCAPTCHA – nepoužívat. Staré evidenční listy a fotky (60.–90. léta) ukážou dřívější podobu.
- **Carmen** (plány, stavebněhistorické průzkumy, restaurátorské zprávy; sbírka plánů NPÚ v Praze): web přesměruje
  na ověření proti robotům, hledá uživatel v prohlížeči. Odkaz na všechno k objektu dá `pamatky.py detail`
  („veškerá literatura a dokumentace“). Průzkum (SHP) domu je nejlepší popis, co je z které doby – kopii objedná
  uživatel u NPÚ (gnr.sbirkaplanu@npu.cz, k neveřejnému užití; badatelna byla 8. 11. 2026 dočasně zavřená).

## Veduty a mapy v digitálních knihovnách (MZK, UK…) – `tools/veduty.py`
Grafické sbírky (veduty, grafické listy, pohlednice, diapozitivy) a mapy knihoven: MZK (Mollova sbírka, mapy.mzk.cz,
grafiky.mzk.cz), Univerzita Karlova (plány Prahy, diapozitivy staveb), VKOL a další. Nástroj hledá přes Českou
digitální knihovnu (CDK), přímo na weby MZK nechodí (podmínky Krameria MZK: ručně).
- `python3 -I tools/veduty.py "Telč"` → veduty a mapy s geografickým heslem obce: rok | druh | název | heslo | žánr |
  knihovna | přístup | odkaz. Druhý argument zúží roky (`veduty.py "Beroun" 1800-1900`). Heslo ukáže, která ze
  stejnojmenných obcí to je („Pavlov (Břeclav, Česko)“ × „Pavlov (Žďár nad Sázavou, Česko)“). Část obce má heslo
  s městem („Smíchov (Praha, Česko)“), hledej jen „Smíchov“.
- Hledá jen podle hesla, ne v názvu („Pavlov“ v názvu = portréty I. P. Pavlova). Malá ves heslo často nemá (Lniště nic).
- `python3 -I tools/veduty.py mapy 48.830 14.615 [od-do]` → mapy, jejichž rozsah v katalogu místo obsahuje, od listů
  1 : 25 000 po mapy panství a okresních hejtmanství (celá mapa do ±0,45° šířky a ±0,7° délky, ne Čechy ani Evropa).
  Souřadnice z RÚIAN. Najde i to, co heslo nemá (Lniště: mapa panství Nové Hrady 1847, okres Kaplice 1887, listy
  1 : 25 000 z let 1917–1941). Místo bývá u okraje listu. Veduty a pohlednice podle polohy nenajde: ručně
  grafiky.mzk.cz a muzea (`esbirky.py`).
- `public` = volně online, `onsite` = jen v knihovně. Mapové listy 1 : 25 000 a 1 : 75 000 z 20. stol. bývají onsite.
- **Veduta není plán:** perspektiva, zkratka a idealizace. Dům podle veduty jen „podobný“, ověř mapou (stabilní katastr).
  Datace grafik bývá odhad („[1840?]“).
- Obrázek do výstupu jen volné dílo a podle podmínek knihovny (`podminky.md`, Kramerius MZK = souhlas), jinak popis,
  citace (knihovna, název, rok, signatura) a odkaz.

## Veduty v archivech do roku 1850 (www.veduty.cz) – prohlížeč
Soupis vedut vzniklých do roku 1850 (MV ČR, archivy ČR a SR, mapová sbírka PřF UK): ~14 000 záznamů, většinou se skenem.
Města, zámky, kláštery, kostely, poutní místa, požáry a povodně; ves jen výjimečně. Nástroj není (aplikace se session),
hledej sám v prohlížeči (`agent-browser`, ochranu nemá, robots.txt Claude-User nejmenuje), jen pár dotazů.
- Pole vpravo nahoře = fulltext celého záznamu: „Telč“ najde i soubory vedut jiných měst, kde je Telč jen zmínka. Zpřesni
  **Rozšířené vyhledávání → Popis veduty** (jen co je na obrázku) a přepínač **Celé slovo**; německý název zkus zvlášť.
- Detail: popis, přepis legendy, autor, nakladatel, datace, technika, **archiv uložení a fond**, číslo soupisu (II/5-1296)
  a „Přímý odkaz na záznam“ (permalink) – ten dej do citace. Rejstřík „Místo“ (Telč (okr. Jihlava)) ukáže všechny
  veduty místa.
- Veduta není plán: perspektiva, zkratky, idealizace, kopie starších předloh (datace vydání ≠ stav místa). Dům podle ní
  jen „podobný“, ověř stabilním katastrem.
- Sken patří archivu uložení: do výstupu jen popis, citace a odkaz, obrázek podle podmínek toho archivu (`podminky.md`).
- Po roce 1850 a malé obce: `veduty.py` (grafiky a pohlednice knihoven), městské archivy mají vlastní digitální archivy
  s mapami a vedutami (např. Archiv města Plzně, digiarchiv.plzen.eu), kroniky a muzea.

## Translokační plány židovských obydlí 1727–1728 (www.vugtk.cz/plany) – `tools/translokace.py`
Plány z let 1727–1728 k nařízení odstěhovat Židy od kostelů a křesťanských domů: ~200 měst a vsí v Čechách
(Národní archiv, Sbírka map a plánů) a na Moravě (MZA). Aplikaci udělal VÚGTK s Národním archivem, u plánu ukáže
i indikační skicu a dnešní letecký snímek.
- `python3 -I tools/translokace.py "Boskovice"` → číslo plánu | lokalita, německý název, okres | rok | název plánu |
  archiv, sbírka, inv. č., signatura | odkaz. Hledá celé jméno obce česky nebo německy (Boskowitz), ne kus.
- `python3 -I tools/translokace.py detail 98` → autor (měřič), verifikace (hejtman), měřítko, legenda a co je
  zakresleno: počet židovských domů, synagoga, škola, kostel, fara, radnice, dvůr, hospoda; odkaz na židovskou matriku.
- **Plán je návrh, ne skutečnost**: kreslí, kde Židé bydlí a kam se mají přestěhovat. Zda se to stalo, ukážou až
  pozdější prameny (indikační skica, katastry, matriky). Dům přiřaď podle polohy na skice.
- Plán si uživatel prohlédne odkazem (obrázek se načítá po dlaždicích z chartae-antiquae.cz, nástroj ho nestahuje).
  Do výstupu zjištění s citací (archiv, Sbírka map a plánů, inv. č., signatura), obrázek se souhlasem archivu.

## Veřejný rejstřík a ARES (ares.gov.cz, or.justice.cz) – `tools/rejstrik.py`
ARES (Ministerstvo financí) má veřejné API: najde subjekty se sídlem na adrese. Veřejný rejstřík (or.justice.cz)
hledá jen podle názvu, IČO nebo spisové značky, proto nástroj jde přes ARES a na or.justice.cz jen odkáže.
- `python3 -I tools/rejstrik.py "Holešovice" 1425` → všechny adresy domu (rohový dům má dvě) a subjekty se sídlem
  v kterékoli z nich: IČO | název | právní forma | zápis | adresa | odkaz na výpis a sbírku listin. Část obce
  jako v adrese (Holešovice, ne Praha 7), číslo popisné, ne orientační. Stejnojmenné části obce vypíše zvlášť,
  rozliší je PSČ. Evidenční čísla (č. ev., chaty) vynechá.
- **Podnikající fyzické osoby jen spočítá**, jména nevypíše: jsou to žijící lidé, často jen bydliště.
- `python3 -I tools/rejstrik.py detail 26480808` → názvy a sídla s daty, předmět činnosti, ostatní skutečnosti
  (u SVJ „Datum vzniku společenství: 1.7.2000.“), spisová značka. Členy statutárního orgánu nevypíše.
- ARES podle adresy najde **jen dnes zapsané** subjekty. Zaniklé (družstvo, firma z 90. let) hledej na or.justice.cz
  ručně: název (ulice, obec, „SVJ <ulice>“) a „Platné i neplatné“. Sbírka listin (stanovy, prohlášení vlastníka,
  smlouvy) je u výpisu, otevře ji uživatel.
- Limit ARES: nejvýš 500 dotazů za minutu, neposílat opakovaně stejné dotazy. Nástroj na dům pošle 3–10 dotazů.

## Fotoateliér Seidel, Český Krumlov (fotobanka.seidel.cz) – `tools/seidel.py`
Negativy Josefa (do 1935) a Františka Seidela (do 1970) a sbírka pohlednic R. Finka: Krumlovsko, Šumava, Pošumaví,
českorakouské pomezí. Fotobanka se 8. 11. 2026 teprve plní („testovací provoz“), co dnes chybí, může přibýt.
- `python3 -I tools/seidel.py "Slavče"` → dvě skupiny: **obec na snímku** (pohled, dům, kostel, pohlednice) a
  **zákazníci ateliéru z obce**: portrét s jménem a adresou z knihy zakázek („Klimová Theresie, Slavče 23, Post Č.
  Křemže“, 1926). Adresa s čp. = kdo v domě bydlel a jak vypadal. Zákazník je jen v detailu, nástroj ho načte
  u prvních 30 snímků (pomalé, ~1 s na snímek).
- Hledání webu je volné (Mohuřice → „Moric“), nástroj nechá jen snímky s obcí v adrese, popisu nebo popisku na desce.
  U pohledů z 50. let je „zákazník“ ten, kdo si fotku objednal, ne obyvatel.
- **Stejnojmenné obce** rozliší pošta v adrese: Slavče u Křemže („P. Křemže“) × Slavče u Trhových Svinů. Německé názvy
  zkus zvlášť (Schweinitz), přepisy jmen bývají zkomolené (Klimová × „Klinová“ na desce).
- `python3 -I tools/seidel.py detail <id>` → datum, zákazník, adresa, popisek na desce, číslo negativu, technika,
  odkaz a citace. Fotku otevře uživatel odkazem; do výstupu jen se souhlasem muzea.

## Sbírky muzeí a galerií (eSbírky, www.esbirky.cz) – `tools/esbirky.py`
Portál Národního muzea se sbírkami desítek muzeí a galerií: fotografie a skleněné negativy (Etnografický archiv NM,
krajská muzea), pohlednice, kresby, obrazy, mapy, předměty. Ochranu ani podmínky užití nemá, licence je u předmětu.
- `python3 -I tools/esbirky.py "Holešovice"` → předměty s obcí v názvu: id | datace | název | nosič | sbírka | licence.
  Druhý argument zúží roky (`esbirky.py "Telč" 1850-1950`). Jen název obce, bez dalších slov.
- Hledání webu je volné („Nežetice“ najde Sezemice, „Telč“ i střelecké terče), řadí podle shody. Nástroj projde prvních
  5 stran (90 předmětů) a nechá jen ty s obcí v názvu (i v jiném pádě: „ze Lniště“, „v Telči“). Zmínku jen v popisu
  nenajde – pak web s filtrem Typ předmětu.
- `python3 -I tools/esbirky.py detail <id>` → popis, místo, instituce, sbírka, inv. č., licence, co smí do výstupu,
  odkaz a citace. Místo bývá jen „Česko“, stejnojmenné obce rozliší popis a sbírka (městské muzeum).
- Datace bývá jen století („1901–2000“) – podobu domu k roku z ní neurčíš, ověř mapou nebo ortofotem.
- Obrázek: PDM, CC0, CC BY = smí i do placeného výstupu s autorem, institucí a licencí; CC BY-NC… (většina NM) jen
  nevýdělečně, jinak popis, citace a odkaz. Obrázek otevře uživatel odkazem.

## Industriální topografie VCPD FA ČVUT (industrialnitopografie.cz) – `tools/industrial.py`
Průmyslové a technické stavby celé ČR (~4 800): mlýny, pivovary, cihelny, sklárny, továrny, doly, mosty, nádraží,
vodárny. Hodí se, když byl dům mlýnem, hospodou s pivovarem, továrnou nebo stál u nich.
- `python3 -I tools/industrial.py "Beroun"` → objekty v obci: id | název | obec – část (okres) | druh | datace. Část obce
  (Holešovice) najde fulltext. Zvlášť vypíše obce s podobným názvem (Moravský Beroun) a objekty, kde je obec jen
  v textu (most přes Berounku); zmínky ověří jako celé slovo, protože API hledá i uvnitř slov. Skupinu nad 20 objektů
  jen spočítá.
  Druhý argument zúží: `industrial.py "Beroun" mlýn`.
- `python3 -I tools/industrial.py detail <id>` → adresa, poloha, datace s událostmi (založen, přestavěn, zbořen), stav,
  památková ochrana, dějiny objektu, **literatura**, osoby a firmy, odkaz a citace podle vzoru VCPD.
- Údaje jsou `lit` (zpracování z literatury a terénu), ne doklad z pramene. Obsah „všechna práva vyhrazena“: do výstupu
  jen zjištění vlastními slovy s citací a odkaz, texty a fotky nepřebírat (`podminky.md`).
- API webu (`api.databaze.fa.cvut.cz`) jen čte přes `…/filter` a `…/detail`. Holá cesta kolekce (`POST structureMap`)
  bez přihlášení záznam založí – nezkoušet (8. 11. 2026). Chybu nebo chybějící objekt hlásí VCPD: jan.zikmund@fa.cvut.cz.

## NTM – Archiv architektury a stavitelství (Praha), badatelna
Pozůstalosti architektů a stavitelů (asi 200 000 plánů), výkresy, skici, fotky, korespondence.
- Fond najdi v NARP: `narp.py "<příjmení architekta>"` (archiv „Národní technické muzea – Archiv architektury
  a stavitelství“), `narp.py detail <id>` dá číslo NAD a inventář. Seznam fondů je i jako PDF na ntm.cz.
- Online nic není: studium jen v badatelně po objednání (badatelna@ntm.cz), materiál z depozitáře mimo Prahu trvá
  déle. Navrhni to uživateli jako dotaz archivu (`archivni_dotazy.md`) s fondem a stavbou (adresa, rok).
- Kopie jen pro studium badatele, zveřejnění se smlouvou (`podminky.md`). Návrh nemusí být postavený.

## Archeologická mapa ČR (AMČR) – digiarchiv.aiscr.cz, ručně
Archeologické akce (výzkumy při stavbách), lokality a nálezy po katastrech, u části dokumentace zprávy a plány.
- Hledá uživatel v Digitálním archivu AMČR podle katastrálního území nebo obce, ty radíš: akce na návsi nebo
  u domu ukáže starší zástavbu a dataci, chybějící záznam neznamená, že tu nic nebylo (výzkum se dělá jen při stavbách).
- Licence CC BY-NC 4.0: jen nekomerčně a s uvedením autora. API (api.aiscr.cz, OAI-PMH na hromadné stahování)
  komerčně jen s písemnou smlouvou – nástroj skill nemá. Citace: „AIS CR: Archeologická mapa České republiky [cit. datum]“.

## Národní archivní portál (portal.nacr.cz) – `tools/narp.py`, seznam fondů všech archivů
Ústřední evidence Národního archivního dědictví: každý fond v každém archivu ČR (i muzea a knihovny), bez snímků.
Řekne, **co se k obci dochovalo a kde to leží** – než napíšeš archivu, víš název fondu, číslo NAD a jestli je přístupný.
- `python3 -I tools/narp.py "Slavče"` → fondy se slovem v názvu, seřazené podle archivu. Hledá se v názvu fondu,
  takže zkus i tehdejší obec, panství („Velkostatek Trhové Sviny“) nebo cech.
- `python3 -I tools/narp.py detail <id>` → NAD, značka, přístupnost, téma, počty knih a kartonů, název inventáře, odkaz.
- **Stejnojmenné obce** rozliší závorka („Slavče (u Trhových Svinů)“ × „(u Českých Budějovic)“). Vyber podle okresu.
- Obsah inventářů tu většinou není („strojopisná pomůcka“ = jen v archivu). Fond bez pomůcky je nezpracovaný.
- „Nepřístupný“ fond: zeptej se archivu, často jde o nezpracovaný fond nebo ochranu osobních údajů.
- Stejný software ARON jako SOA Zámrsk (níže), API `https://portal.nacr.cz/aron/api/aron`.

## ARON (SOA Zámrsk) – hotové nástroje
- **Hledání svazků:** `python3 -I tools/aron_search.py "Holice"` → řádky `apu_id | signatura, roky | druh, obce`.
  Popis obsahuje druh knihy (NAROZENÝCH / ODDANÝCH / ZEMŘELÝCH, index) a všechny obce farnosti.
- **Informace o svazku:** `python3 -I tools/aron_img.py <apu_id> info` → název a počet snímků.
- **Stažení snímku:** `python3 -I tools/aron_img.py <apu_id> <snímek> 1 pracovni/holice_n_57.jpg`
  (úroveň 1 = poloviční rozlišení – stačí na orientaci; 0 = plné rozlišení – na čtení a výřez).
  Jen část stránky v plném rozlišení: `… <snímek> 0 pracovni/detail.jpg 0.0,0.4,1.0,0.7`.
- **Odkaz na snímek** (pole `odkaz` v `zaznamy.json`): `python3 -I tools/aron_img.py <apu_id> link <snímek>`.
- **Svazek do dat:** `python3 -I tools/aron_img.py <apu_id> svazek` (klíč = prvních 8 znaků apu_id → pole `svazek` v zápisu).
- **Sčítání lidu:** `aron_search.py scitani "Obec"` – operáty 1857–1921 jsou ve fondech „Okresní úřad …“ (Sčítací operáty › rok
  › soudní okres › obec) a obec má v popisu jen svůj název, takže je hledání slovem „sčítání“ ani filtrem fondu nenajde.
  Osada bývá pod tehdejší obcí (Švihov u Nasavrk pod Krupínem). Ověřeno: okres Chrudim 1900, 1910, 1921 se snímky.
- V ARON jsou i další fondy (některé gruntovní knihy, kroniky) – `aron_search.py "Obec" "název fondu"`.
- Stejnojmenných obcí bývá víc (Vinice u Hořic × Vinice u Velké Jesenice). Výsledky jsou seřazené podle farnosti;
  zúžit jde víc slovy oddělenými čárkou, která musí být v popisu všechna: `aron_search.py "Vinice,Hořice"`
  (nebo hledej sousední obec či farní obec).
- U starých far hledej nejdřív **souhrnné indexy** (popis „index NAROZENÝCH…“ přes mnoho let), často sahají do 17. století.
- Obec nenalezena? Zkus název **bez přívlastku** („Lhota“ místo „Horní Lhota“) a starý název. Starší matriky
  (před ~1784) bývají ve faře sousedního města; indexy fary mají oddíly po vesnicích
  („Copulati Gross Lhota“).
- Ber ohled na server: stahuj jen to, co čteš; žádné hromadné stahování celých svazků. Limit rychlosti hlídá
  `tools/slusne.py` (SKILL.md → Co nikdy).

## SOA Třeboň (digi.ceskearchivy.cz) – jen číst
- **Podmínky:** snímky „pouze za účelem on-line prohlížení“, kopírování zakázáno; robots.txt zakazuje robotům stránky
  aplikace a archiv `trebon.py` blokuje. Nástroj proto stojí (`podminky.md`). Snímky čte uživatel v prohlížeči, ty radíš:
  která kniha, který snímek, jak číst písmo. Snímek pro výstup objednat u archivu (25 Kč) nebo požádat o souhlas.
- Níže je popis nástroje pro případ, že archiv souhlas dá:
- `trebon.py misto "Obec"` → id místa. Diakritiku a mezery nástroj odstraní sám (portál zná jen „RatiborskeHory“).
  Portál vrátí vždy jen jedno místo – **zkontroluj vypsaný název a okres**: u stejnojmenných obcí jinou (Buk → Bukovka),
  u měst i okres nebo synagogu (Jindřichův Hradec → okres 1949–1960). Správné id pak najdi na portálu a pracuj s ním.
  Malé osady portál jako místo nezná vůbec (Malá Chyška) – hledej farní nebo sousední obec (Chyšky) a osadu v popisu knih.
  Občasná chyba 500 bývá výpadek portálu – nástroj zkouší znovu; když trvá, zkus to později.
- `trebon.py svazky <id|"Obec">` → knihy místa (id knihy, druh, roky, obce).
- `trebon.py rejstrik <id_knihy> <písmeno>` → **dobrovolnický jmenný rejstřík** knihy se snímkem, obrovská úspora.
  Ne každá kniha ho má; prázdný výsledek = rejstřík chybí, ne „osoba tam není“.
- `trebon.py snimek <id_knihy> <snímek> pracovni/x.jpg [nahled]`, `trebon.py svazek <id_knihy>` (do `svazky.json`).
- Trvalý odkaz: `https://digi.ceskearchivy.cz/<id_knihy>/<snímek>`.
- Některé fary mají knihy po vesnicích, které nejsou v seznamu svazků místa (Vacov → Žár) – hledej podle titulků knih fary.
- **Civilní matriky (1920–1945) lidí bez vyznání** jsou v knihách okresních úřadů (např. Tábor, kniha 12304) a mají
  dobrovolnický rejstřík (`trebon.py rejstrik 12304 N`). Dobrá cesta, když farní matrika mlčí. V `svazky "Obec"`
  se neukážou (patří okresu, ne obci) – id knihy najdi na portálu.

## SOA Plzeň (Porta fontium, portafontium.eu) – ručně
- **Podmínky:** prohlížení i popisy archiválií jen „vyjma výdělečných účelů“, web blokuje skripty firewallem. `portafontium.py`
  proto stojí (`podminky.md`). Pro soukromé bádání snímek uloží uživatel v prohlížeči do `pracovni/` a ty ho přečteš.
- Níže je popis nástroje pro případ, že archiv souhlas dá:
- `portafontium.py fara <fara>` → knihy fary: kniha | obce | roky a druhy (`*` N, `oo` O, `+` Z, `i` index) | popis.
  `<fara>` je název římskokatolické fary („Dolní Bělá“, „Mýto“ – diakritiku nástroj odstraní) nebo přímo část
  její adresy (`dolni-bela` =
  `…/contents/register/soap-pn/cirkev-rimskokatolicka/dolni-bela`). Obec → faru nástroj nehledá: faru zjisti ve vyhledávání
  matrik na portálu (pole Místo, v prohlížeči) nebo v popisech knih okolních far. Bez prohlížeče: stránka
  `https://www.portafontium.eu/searching/register?search_api_views_fulltext_1=<obec>` vypíše odkazy
  `/register/soap-pn/<kniha>` – `<kniha>` (např. `kdyne-29`) rovnou použij v `portafontium.py info`.
- `portafontium.py info <kniha>` (`dolni-bela-17`) → signatura, druh, text desky a **obsah** – u knih psaných po vesnicích
  vypíše, na kterých foliích je která obec („Ves X z let 1862–1901 = fol. 121–200“).
- `portafontium.py snimek <kniha> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]` → celá stránka v plném rozlišení jedním
  požadavkem (IIIF), `nahled` = 1/4. Číslo snímku = pořadí náhledu v prohlížeči; soubory nesou číslo folia
  (`dolni-bela-17_0951` = fol. 95), takže u knih se souvislou foliací je **snímek ≈ folio**.
- `link <kniha> <snímek>` → trvalý odkaz, `svazek <kniha>` → `svazky.json` (klíč `pf_<kniha>`).
- Bez prohlížečového User-Agentu portál vrací 403 (nástroj ho posílá). Jmenné hledání portál nemá – indexy jsou jen uvnitř knih
  (`*i`, `ooi`, `+i` v seznamu knih fary).

## SOA Praha (eBadatelna, ebadatelna.soapraha.cz) – `tools/ebadatelna.py`
- **Podmínky:** robots.txt zakazuje ClaudeBota (trénink modelů), GPTBota a robota „rodokmen“, Claude-User ne (8. 11. 2026).
  Ostatním robotům zakazuje digitalizáty (`/d/`, `/a/`) – nástroj stahuje jen snímky, které čteš, nic dvakrát.
- **Celá kniha:** uživatel se zaregistruje (zdarma), otevře knihu, na záložce „Popis knihy“ vlevo dole klikne
  „Stáhnout knihu jako ZIP“ a rozbalí ho do `pracovni/<kniha>/`. U knihy, kterou čteš celou, šetrnější než snímek po snímku.
- `ebadatelna.py hledat "Obec"` → celé názvy lokalit („Lhota - obec X - okres Y“); `matriky "Obec"` (nebo celý název)
  → matrikaId | kniha | druh | roky | fara | počet snímků. U stejnojmenných obcí vypíše možnosti.
- `ebadatelna.py info <matrikaId>` → obsah knihy včetně **rozvržení stran po vesnicích** (např. „1–48 Ves A, 49–82 Ves B,
  1–30 Ves C …“ – každá ves může mít vlastní stránkování) – u takových knih neodhaduj snímek podle roku, ale podle stran
  dané vsi (číslo strany je nahoře na snímku). Takové knihy bývají řazené po vsích, ne chronologicky – je-li rejstřík,
  začni jím.
- `ebadatelna.py snimek <matrikaId> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]`; `link`, `svazek` (klíč `ebad_<id>`).
- **Archiválie** (urbáře, gruntovní a pozemkové knihy velkostatků – most přes 17. století): `a-info <archivalieId>`,
  `a-snimek`, `a-link`, `a-svazek` (klíč `ebad_a_<id>`). Archiválii nástroj nehledá – najdi ji na portálu v prohlížeči;
  id je v adrese `…/pages/ArchivaliePage/archivalieId/<id>`.
- Starší snímky bývají z mikrofilmu nebo silně vybledlé – čti ze zesílené verze:
  `python3 -I tools/zesil_snimek.py x.jpg [x0,y0,x1,y1]` (výřez pro web pak dělej z originálu).
- Portál dává vždy celý snímek (nedlaždicuje); náhled a výřez dělá nástroj po stažení přes ImageMagick (`magick`).
  Denní údržba kolem 4:44 (asi 2 minuty).

## AHMP Praha – `tools/ahmp_search.sh`, `tools/ahmp_scan.py`
- `bash tools/ahmp_search.sh "Smíchov"` → svazky Sbírky matrik: popis | farnost | (XID, id, počet snímků).
- `python3 -I tools/ahmp_scan.py <XID> <snímek> pracovni/x.jpg [1] [x0,y0,x1,y1]` → snímek (1 = poloviční rozlišení).
- Trvalý odkaz `https://katalog.ahmp.cz/pragapublica/permalink?xid=<XID>&scan=<N>`.
- Nový portál digi.ahmp.cz má ochranu proti robotům – nepoužívat. Pražské matriky 1890–1940 většinou **nemají rejstříky**
  a farností je mnoho – bez přesného data a farnosti (z úmrtí/sňatku nebo od rodiny) je hledání velmi drahé.

## SOA Litoměřice (severní Čechy) – `tools/soal_zoomify.py`
- Digitální badatelna digi.soalitomerice.cz má na vstupu automatické ověření (asi 15 s „počítání“) → knihu a snímek
  najdi v prohlížeči. V síťovém provozu pak najdi adresu `…/zoomify/cz/archives/CZ-214000010/matriky/<cesta>/ImageProperties.xml`.
- Snímky stahuj nástrojem: `python3 -I tools/soal_zoomify.py <cesta> 0 pracovni/x.jpg` (0 = plné rozlišení, 1 = poloviční).
  Obrázkový server neomezuje a cookies nepotřebuje.
- **POZOR: po zhruba 100 rychlých požadavcích na stránky aplikace (prohlížení snímků, detail výsledku) archiv zablokuje
  přístup na 30 minut.** V prohlížeči proto jen najdi knihu a cestu k obrázkům, pak už jen nástroj. Pomocníkům to napiš do zadání.

## ZA Opava (severní Morava, Slezsko, Olomoucko, Litovelsko) – `tools/soal_zoomify.py`
- Pozor na hranici: obce na Litovelsku a Olomoucku patří pod **ZA Opava**, ne pod MZA Brno.
- **Bez prohlížeče to nejde.** Badatelna `https://digi.archives.cz/da/` (stará adresa matriky.archives.cz jen přesměruje)
  má ochranu proti robotům – curl ani WebFetch se nedostanou ani na hledání. Potřebuješ připojený prohlížeč (Claude in
  Chrome – uživatel ho připojí příkazem `/chrome` – nebo Playwright); jinak ať knihu najde a snímky uloží uživatel.
  Úvodní ověření projde samo, ale hledání často skončí **CAPTCHou: tu vyřeší uživatel** v okně prohlížeče, ty nikdy.
- Hledej obec a vyfiltruj Matriky (ikona, potom znovu lupa). Hledání vrací i civilní matriky (u obce stovky svazků) –
  filtr „Datum od – do“ (podle začátku svazku, např. 1680–1873) nechá jen církevní. Knihy bývají řazené po obcích
  a na konci mají rejstřík. Vedle farních knih bývají i **druhopisy** („T“ v signatuře, viz `matriky.md`).
- **Seznam svazků a ID snímků si hned ulož** do `pracovni/<svazek>/` – relace po pár hodinách vyprší a výsledky
  hledání platí jen v ní. Na detailu svazku: entita `document.querySelector('[entityuuid]').getAttribute('entityuuid')`
  (u svazků uložených v jiném archivu nemá tvar UUID – nehledej ji regexem), ID snímků jsou hodnoty
  `select.getScanSelect option` (tvar „N%20uuid“). Snímek pak otevřeš kdykoli bez hledání:
  `/da/showZoomifySeparate?imageNumberSeparate=N&myEntityUuid=<entita>&myImageUuid=<uuid>`.
- Adresa obrázku: `fetch('/da/showZoomify/<id svazku z URL>/<část option.value za „%20“>')` vrátí HTML s cestou
  `…/images/<složka>/<uuid>.jpg`. Cesta se u svazků liší (`…/CZ-217000010/NAD-165/dao/images/…`, `…/zao/matriky/dao/images/…`)
  a přípona bývá i `.JPG` – nástroji dej vždy **celou adresu z HTML**:
  `python3 -I tools/soal_zoomify.py "<adresa>" 2 pracovni/x.jpg` (2 = čtvrtinové rozlišení na orientaci podle záhlaví
  stránek, 0 = plné jen u nalezeného zápisu). Obrázkový server images.archives.cz neomezuje a cookies nepotřebuje.
- **POZOR na blokování** (jen stránky aplikace, obrázky ne): rychlé dotazy → CAPTCHA, „operace vyhodnoceny jako
  nestandardní“ nebo „Access blocked“ na 30 minut; po desítkách dotazů za den vrací showZoomify „Server Exception“
  (denní limit – pokračuj až další den). Pauza 3–6 s mezi stránkami, dávky do ~80 stránek, žádné rychlé `fetch` hned
  po hledání a stránky výsledků neprocházej za sebou. Delší smyčku pusť v prohlížeči na pozadí, výsledky ukládej do
  `window` nebo `localStorage` a vyzvedávej po částech (nástroj pro JavaScript má limit asi 45 s). Pomocníkům to napiš do zadání.

## MZA Brno (jižní Morava, Acta Publica) – `tools/mza.py`, bez prohlížeče
- `mza.py hledat "Obec"` → obec_id | název s německým názvem a okresem (bez diakritiky i podle začátku názvu).
  Stejnojmenných obcí bývá víc (Pohořelice u Brna × u Zlína) – vyber podle okresu.
- **Sčítání lidu (MZA):** `mza.py scitani "Obec"` → roky, rozsah čísel popisných, fond a odkaz na portál sčítacích
  operátů (www.mza.cz/scitacioperaty, bez ALTCHA). Obec, kterou našeptávač portálu nezná, tam není (Telč ne).
- `mza.py matriky <obec_id>` → knihy obce: id | číslo knihy | původce (fara, typ) | roky N | O | Z (`i` = index) | obce | snímků.
  Jsou tam i knihy, které obec jen zmiňují (německé stavovské úřady 1938–45, sousední fary) – podívej se na původce.
- **Stránku knihy a snímky chrání ověření ALTCHA** (od listopadu 2026), nástroj ho neobchází a podmínky chtějí
  souhlas k dalšímu využití (`podminky.md`). Uživatel otevře `…/actapublica/matrika/detail/<id>` v prohlížeči,
  ověření vyřeší sám a pošle snímek obrazovky nebo snímek uloží do `pracovni/`. Části knihy („oddaní (1673–1716)
  201–250“) jsou v levém panelu stránky – podle nich skoč na správný snímek, neodhaduj podle roku. Trvalý odkaz
  (`…detail/<id>?image=…`) opiš z adresního řádku.
- `info`, `link`, `svazek` a `snimek` čtou stránku knihy, proto teď skončí hláškou PODMÍNKY; fungují jen bez ALTCHA
  a se souhlasem archivu. `svazky.json` (klíč `mza_<id>`) zapiš ručně přes `zapis.py`.
- `<id>` je číslo z adresy `…/actapublica/matrika/detail/<id>`, ne číslo knihy (to je ve druhém sloupci).
- Obrázkový server bere jen HTTP/2 – snímky stahuje nástroj přes `curl` (Python sám dostane HTTP 426). Starý curl
  bez HTTP/2 → nainstaluj novější.
- Adresa actapublica.eu bývá za Cloudflare zablokovaná („Sorry, you have been blocked“ – podle IP); nástroj jde na
  www.mza.cz. Když blokuje i ta, ať uživatel vypne VPN nebo zkusí jinou síť.

## MZA Brno – gruntovní a pozemkové knihy (ARON MZA) – ručně
- Gruntovní knihy, knihy listin (smluv) statků, pozemkové knihy obcí, josefinský katastr, vceňovací operáty stabilního
  katastru a fondy velkostatků jsou na **www.mza.cz/aron**, ne v Acta Publica. Stejný software jako ARON SOA Zámrsk.
- Skriptu (`aron_search.py` s adresou MZA) vrátilo API HTTP 403 (11/2026), skripty a API proto ne. Katalog jde
  procházet v prohlížeči: `agent-browser --headed`, tempem člověka (pauzy mezi kroky), jen hledání a knihy k domu,
  nic hromadně. Nebo hledá uživatel sám a posílá snímky obrazovky. Objeví-li se ALTCHA nebo blok, přestaň.
- Přímá adresa hledání s filtrem jen digitalizáty: `https://www.mza.cz/aron/arch-desc?p=1&s=50&q=<obec>&f=%5B%7B%22source%22%3A%22DIGITAL%22%2C%22value%22%3A%5B%22Ano%22%5D%7D%5D`.
  Hledá se celými slovy v popisu: „Staré Město Telč“ najde gruntovní knihy předměstí, „gruntovní Telč“ nic.
  Výpis přečteš přes `agent-browser get text body`.
- Postup: záložka **Archiválie** → hledat název obce → vlevo filtr **Digitální podoba: Ano** → **Druh archiválie:
  pozemková kniha** (příp. úřední kniha, mapa). Typický výsledek: pozemková kniha obce (fond Pozemkové knihy,
  „Jednotlivé obce“, ~1818–1885) a **Kniha listin** celého statku (fond Pozemkové knihy, „Celý statek“, od pol. 18. stol.).
  Města a obce mají knihy i ve fondech SOkA („Archiv města Telč“: kniha trhová 1606–1753, gruntovní 1758–1887;
  „Archiv obce …“: knihy pozemkové držby 1787–1879).
  Celé hledání bez filtru ukáže i nedigitalizované archiválie (karton jen v badatelně) a panství obce v popisu map.
- Podmínky jako u Acta Publica: snímky dál využít jen se souhlasem MZA (`podminky.md`), do výstupu přepis a odkaz.
- **Lánové rejstříky 1656–1679** (fond D 1, 372 svazků, digitalizované 2013–14): svazek = panství nebo statek, ne obec.
  Hledej obec s filtrem digitalizátů, ve výsledcích „Lánový rejstřík panství …“ (Hlína → Kounice a Vlasatice, sign. 181).
  Uvnitř svazku obec po obci, německy (kurent), na konci obce „Extract Dorff …“ se souhrnem (starousedlí, nově
  osazení, pustky). Čísla domů ještě nejsou: k domu vede až pořadí hospodářů a návaznost jmen na gruntovní knihu.
  Starší odkazy z webu (aplikace v Silverlightu, inventář v PDF) nehledej, stačí ARON.

## Pražské policejní přihlášky 1850–1914 (Národní archiv) – `tools/policie_prihlasky.py`
- **Podmínky:** jen zákaz v robots.txt, podmínky užití ani ochrana nenalezeny (8. 11. 2026, `podminky.md`). Hledej jen
  konkrétní osoby a stahuj jen karty, které opravdu potřebuješ.
- Karty pražských rodin: hlava rodiny, manželka s rokem a místem narození, děti s roky, adresy, někdy místo sňatku.
  Výborné, když rodina žila v Praze a nevíš farnost (pražské matriky nemají rejstříky).
- `python3 -I tools/policie_prihlasky.py Kolar [Jan] [1850] [1870]` – příjmení bez diakritiky (začátek jména), jméno a roky
  narození volitelně. Bez prohlížeče vrátí jen prvních 20 výsledků, proto hledej co nejúžeji.
  Kartu stáhni `policie_prihlasky.py karta <pořadí> pracovni/karta.jpg Kolar [Jan] [1850] [1870]` (stejné hledání; jde i pořadí
  nad 20) – vypíše citaci a trvalý odkaz (`index.php?action=link&ref=czarch:CZ-100000010:874&karton=K&folium=F`).
- **Nepokrývá Smíchov, Vinohrady, Žižkov, Karlín a další předměstí před 1922** (byla to samostatná města). Náboženství karty neuvádějí.

## Matricula (Rakousko, Bavorsko, Polsko…; data.matricula-online.eu) – `tools/matricula_*.sh`
- Bez přihlášení. Seznam knih: `…/de/oesterreich/<diecéze>/<farnost>/?page=N`; snímek knihy `…/<id>/?pg=<snímek>`
  (zároveň trvalý odkaz).
- URL obrázku obsahuje `csrf` a `ctrl` počítané JavaScriptem → je potřeba prohlížeč (Playwright / Claude in Chrome):
  otevři knihu, klikni na stránku (`.docview-pagelink`), URL obrázku vezmi z `performance.getEntriesByType('resource')`
  a stáhni `bash tools/matricula_dl.sh "<url>" pracovni/x.jpg`. Víc stránek: soubor řádků „<snímek> <url>“ → `matricula_batch.sh`.
- Rejstřík najdeš bez prohlížeče: HTML stránky knihy má seznam `labels` s popisky snímků („04-Index Taufe_0001“).
- Vojenské matriky (např. Štýrský Hradec) tam nejsou – jsou v Kriegsarchivu ve Vídni (offline).

## Polsko – Geneteka (geneteka.genealodzy.pl)
- Zdarma dobrovolnické indexy křtů, sňatků a úmrtí po farnostech; hledej ve webovém rozhraní (vojvodství → farnost →
  příjmení). Index je vodítko – skeny často online nejsou (farní nebo diecézní archiv), pak zápis žádej tam.
- **Farní příslušnost se měnila**: obec mohla patřit k sousední faře (Lipowa → Radziechowy do 1896) – hledej i tam.
- Nestahuj hromadně: PTG uvádí „linkujemy, nie pobieramy danych“ (odkazujeme, nestahujeme) a po desítkách rychlých dotazů
  server vrací nefiltrovaná data. Dotazy dávkuj, s pauzami, a výsledky si ověř.
- Jednotlivý dotaz jde i bez prohlížeče: `https://geneteka.genealodzy.pl/api/getAct.php?draw=1&start=0&length=10&bdm=B&rid=B&w=12sl&search_lastname=<příjmení>&search_name=&search_lastname2=&search_name2=&from_date=1850&to_date=1900&exac=1`
  (`bdm`/`rid` B křty, S sňatky, D úmrtí; `w` vojvodství, např. 12sl slezské, 08op opolské) → JSON. Past: `recordsTotal` > 0
  a prázdné `data` – zkus jen jedno příjmení bez křestního jména a užší roky. Stránkování opakuje řádky.
- Skeny některých polských far jsou i na Matricule (výše) nebo FamilySearch (níže).

## FamilySearch (jen ručně, přes uživatele)
- **Podmínky:** zakazují roboty, hromadné stahování a „scraping“; stahovat smí uživatel ručně pro osobní nekomerční
  potřebu. Žádné volání API ani stahování snímků z tvé strany.
- Přihlášení je potřeba i na hledání v indexech. České matriky tam skoro zindexované nejsou (Slovensko ano, hlavně křty).
- Užitečné na indexy matrik a hroby (BillionGraves, Find a Grave). Výsledek je vodítko – ověř v matrice.
- Postup: řekni uživateli, co hledat (příjmení, jméno otce, místo, roky). Výsledek nebo snímek pošle jako snímek
  obrazovky nebo uložený soubor do `pracovni/`, ty ho přečteš.

## Hroby a hřbitovy
- Kde jsou předci pohřbeni, víš z rozhovoru s rodinou (Fáze 1). Fotky náhrobků (jména, data, rodná příjmení) jsou
  cenný pramen hlavně pro 20. století, kde matriky ještě nejsou přístupné.
- Evidence hrobových míst: správa hřbitova (kdo je v hrobě uložen, kdo platí nájem – často žijící potomek);
  řada měst má online vyhledávání hrobů. Mezinárodně BillionGraves a Find a Grave.
- **Hřbitovní pasporty obcí (GisOnline.cz)** – `tools/hroby.py`: hroby a zemřelí se jménem, narozením, úmrtím a pohřbem,
  hlavně 1920–2020. `najdi "<obec>"` zkusí adresy app.gisonline.cz/<obec> a vypíše obec a okres podle RÚIAN (obce stejného
  jména!), `stahni <projekt>` uloží `data/hroby.json`, `hledej <příjmení>` vypíše zemřelé. Číslo popisné u hrobů není:
  shoda jména s obyvatelem je vodítko, ověř ji. Fotky náhrobků jen odkazem, jména zemřelých za posledních ~50 let
  na veřejný web jen se souhlasem rodiny. Jiné mapové portály obcí hledej na webu obce („mapa hřbitova“).

## IPR Praha – staré plány a letecké snímky Prahy (gs-pub.praha.eu) – `tools/ipr_praha.py`, bez tokenu
Pro Prahu výrazně lepší než Archiv ČÚZK (jeho spojené vrstvy stabilního katastru Prahu nepokrývají). Vše georeferencované
v S-JTSK (EPSG 5514) → stejný výřez pro celou sérii = prolínání map na webu (`mapy.json`, stejná `skupina`).
- `python3 -I tools/ipr_praha.py serie "Ulice čp/čo" 300 --zapsat okoli` (okolí) a `… 90 --zapsat dum` (detail domu) → celá
  série do `pracovni/ipr/`, výřezy a `mapy.json` se skupinou; pak doplň popisy. `ipr_praha.py vrstvy` = seznam.
Ruční dotazy, když nástroj nestačí:
- Plány: `https://gs-pub.praha.eu/imgs/rest/services/arch/<služba>/ImageServer/exportImage?bbox=x0,y0,x1,y1&bboxSR=5514&imageSR=5514&size=1200,1200&format=jpg&f=image`.
  Služby: `stabilni_katastr_cisarske_otisky_2880`, `stabilni_katastr_originaly_1440`, `plan_pav_1889`, `plan_orient_1909`,
  `plan_vysko_1920`, **`plan_orient_1938` (s čísly popisnými a orientačními)**, `plan_prahy_1944`, `byvaly_pozemkovy_katastr`.
  Herget 1791, Jüttner 1816, Mayr 1869, polohopisné 1884 a 1891 pokrývají jen centrum (mimo něj vrátí prázdný obrázek ~23 kB).
- Letecké snímky: `https://gs-pub.praha.eu/arcgis/rest/services/ort/ortofotomapa_archiv/MapServer/export?bbox=…&bboxSR=5514&imageSR=5514&size=…&format=jpg&f=image&layers=show:<id>`
  – id 0 = 1938, 4 = 1945, 8 = 1953, 150 = 1966, 12 = 1975, 16 = 1989, 20 = 1996, 36 = zaplavené území 2002 (seznam: `…/MapServer?f=json`).
- Střed výřezu = parcela domu v S-JTSK: `https://ags.cuzk.gov.cz/arcgis/rest/services/RUIAN/MapServer/5/query?where=KATASTRALNIUZEMI%3D<kód k. ú.>+AND+KMENOVECISLO%3D<parcela>&returnGeometry=true&outSR=5514&f=json`.
- **Všechny adresy domu a sousedů** (rohové domy, přečíslování): `mista.py okoli "Ulice čp/čo" 80`, ručně adresní místa v obálce
  `…/RUIAN/MapServer/1/query?geometry=x0,y0,x1,y1&geometryType=esriGeometryEnvelope&inSR=5514&outFields=*&f=json`.
- Zdroj do `mapy.json`: „IPR Praha, Geoportál hl. m. Prahy (geoportalpraha.cz), <služba>“.

## DNNT – díla nedostupná na trhu (ndk.cz): tisk 20. století z domova – `tools/dnnt.py`
Adresáře, ročenky, odborné časopisy a noviny zhruba 1900–2000 jsou v Krameriu NK „private“. Většina z nich má ale
`dnnt: true` – kdokoli je přečte z domova po přihlášení na **ndk.cz**. Pro dějiny městských domů je to hlavní zdroj.
- **Podmínky NDK:** díla nedostupná na trhu jsou jen pro osobní čtení registrovaného čtenáře; stahovat, ukládat
  a robotizovaně vytěžovat je zakázáno (`podminky.md`). Nástroj proto jen hledá a dává úryvky.
- **Postup s nástrojem:** `dnnt.py hledej 'text_ocr:"Dlouhá 14"' --ulozit dl14` → `dnnt.py kontext <pid> 'slova'`
  (úryvky bez přihlášení) → `dnnt.py ocr pracovni/dnnt/dl14.tsv` (veřejné stránky) → `dnnt.py adresa pracovni/dnnt/ocr
  "Dlouhá" 14 16` (najde i „Dlou-há“). Celý adresář nebo obor nejdřív `hledej` s `--titul`.
- **Veřejně jinde:** `hledej` zkusí neveřejné stránky NK najít v České digitální knihovně (Krameria ostatních knihoven).
  Kde je stejný titul, rok a strana veřejně (třeba v MZK nebo VKOL), přečte ji `ocr` sám; přidá i veřejné nálezy, které NK nemá.
- **Čtecí list:** zbylé neveřejné stránky dá `hledej --ulozit dl14` do `pracovni/dnnt/dl14.html`. Pošli ho uživateli:
  u každé stránky odkaz na ndk.cz, úryvek a políčko, kam vlastními slovy zapíše fakta. Tlačítkem stáhne `dl14_poznamky.tsv`,
  uloží ho do `pracovni/dnnt/` a ty ho přečteš. Poznámka uživatele je `lit` s citací stránky, ne `doc`. Snímky obrazovky
  ani zkopírovaný text z DNNT nechtěj, podmínky kopírování zakazují.
- **Bez přihlášení** je vyhledávání veřejné i pro DNNT stránky (úryvky, test výskytu slova na stránce). OCR text
  neveřejných stran bez přihlášení vrátí 403. Úryvek z vyhledávání je `lit` (čteno z OCR), ne `doc`.
- **Přístup:** uživatel musí být čtenářem zapojené knihovny. Seznam knihoven a kdo umí registraci na dálku:
  `https://ndk.cz/knihinst.json` (sloupce: knihovna, eduID / identity NDK, odkaz na vzdálenou registraci, kraj).
  Ověřeno (2026): Městská knihovna v Praze – levná registrace online přes Bank iD, pak přihlášení eduID. Na dálku
  dále např. NK ČR (bankovní identita), MZK Brno (Bank iD / MojeID, i krátkodobě) a několik krajských knihoven;
  ostatní chtějí jednu návštěvu. Ceny a možnosti ověř na webu knihovny.
- Metadata a nadřazené číslo: `/search/api/v5.0/item/<pid>`.
- Trvalý odkaz do `zaznamy.json`: `https://ndk.cz/uuid/<pid>`. Přepis ze skenu = `doc`; jen z OCR textu = `lit`.
- Užitečné tituly: Adresář Republiky československé pro průmysl, živnosti… (1927–1938, podle oborů), Adresář hl. m. Prahy
  1936, Orientační kniha Velké Prahy 1936/1937 (čp. → adresy), Stavitelské listy (stavební povolení), Právo lidu,
  Národní listy, Lidové noviny, ročenky spolků, Dílo družstevní svépomoci (1933).

## Noviny a ročenky – `tools/anno.py`, `tools/anno_snap.py`, `tools/kramerius.py`
**Kdy se vyplatí:** státní a vrchnostenští úředníci, soudci, učitelé, faráři, důstojníci, vojenští lékaři, notáři,
poštmistři, starostové, podnikatelé – noviny otiskovaly jmenování, přeložení, vyznamenání, penze, konkurzy, oznámení
sňatků a parte (zhruba od 1860). Z toho plyne, **kde člověk kdy žil** → kde hledat křty dětí, sňatek, úmrtí.
A když osoba „chybí“ v očekávaných matrikách (stěhovala se se službou). **Spíš ne:** sedláci a řemeslníci na vsi.
- ANNO (rakouské noviny 1700–1950, i Prager Zeitung, Wiener Zeitung): `python3 -I tools/anno.py '"Johann Nowak"' 1860 1915 [stran] [--snip]`
  – jména **německy** („Johann Nowak“, „Wenzel Dworschak“). Výřez místa: `tools/anno_snap.py <docId> "<dotaz>" pracovni/x.jpg`.
  ALEX a annoshow jsou za Cloudflare – neobcházet.
- Kramerius NK ČR (české noviny, ročenky, adresáře): `python3 -I tools/kramerius.py 'text_ocr:"Jan Novák" AND datum_begin:[1900 TO 1910]'`.
  Pozor: filtr `datum_begin` vyřadí část čísel periodik (u některých chybí) – při malém počtu nálezů hledej i bez něj.
  Neveřejné stránky 20. století čti přes DNNT (výše).
- Vojenské schematismy: fulltext na archive.org (např. `militrschematis13kriegoog` = 1850).
- **Rizika:** jména se opakují a fulltext šumí („Winter“ = i zima, „Novák“ = nový obyvatel). Ztotožni jen při shodě víc údajů (bydliště,
  funkce navazující na matriku, časová posloupnost). Zdroj je „J“ (jiný pramen) – vodítko a příběh, ne náhrada matriky.
- Výstřižky jsou skvělé na web: ulož do `dokumenty/noviny/`, přes `vyrez.py` a do `dokumenty.json`.
- Pořadí: nejdřív matriky; noviny, když chybí stopa kvůli stěhování, nebo když jde o úředníka/vojáka a chceme příběh.

## Dějiny obce v Krameriovi (staré knihy volně) – `tools/kramerius.py`
`python3 -I tools/kramerius.py 'text_ocr:Obec AND dostupnost:public' 50` – jen volně čitelná díla. Pro ves vypadnou:
- **edice listin a urbářů** (Archiv český aj.) – nejstarší zmínky, vrchnosti, poddaní;
- **topografie**: Sommer, *Das Königreich Böhmen* (1833–49, po krajích; počet domů a obyvatel, fara, škola, mlýn,
  vrchnost), Palacký, *Popis království českého* (1848); **Seznamy míst** (1878–1913: obec, fara, pošta, škola);
- okresní vlastivědy a čítanky.

Hledej **všechny podoby názvu**: česky i německy, staré pravopisy, a přes sousední nebo katastrální obec – prameny
se liší (Lniště: mapa 1827 „Ellnischen“, Sommer „Elnischt“; našel se až přes sousední Březí, „Pürchen“). V jedné knize:
`AND root_title:"Das Königreich Böhmen"`. Šum: obecná slova („lniště“ = lněné pole) a stejnojmenné vsi jinde –
kontroluj okres a sousední obce v úryvku. **OCR v edicích plete římské číslice** (roky, výměry, peníze): čísla ověř
na obrázku stránky. Zápis do `OBEC_UDALOSTI` se `zdroj` a stranou.

## Ostatní portály – obecný postup
Nástroje pro ně hotové nejsou. Postupuj takto a výsledek zapiš do `STAV.md`, ať to příště víš:
1. Otevři portál v prohlížeči sám (skill `agent-browser`, pasti v `SKILL.md` → Webové aplikace bez API; Claude in Chrome).
   Uživatele žádej až ve chvíli, kdy je potřeba přihlášení nebo souhlas.
   Najdi fond „Sbírka matrik“ / „Matriky“ a svazek podle obce a let.
2. **Snímek:** většina prohlížečů má tlačítko ke stažení obrázku – ulož do `pracovni/`. Když ne, podívej se v síťovém
   provozu, odkud se načítají dlaždice/obrázky (IIIF, DeepZoom, Zoomify), a stáhni celý obrázek touto cestou – jednotlivě,
   jen snímky, které čteš. Krajní možnost: požádej uživatele, ať snímek uloží a dá do `pracovni/`.
3. **Trvalý odkaz** na snímek (tlačítko „trvalý odkaz“/permalink, jinak URL svazku + číslo snímku) dej do `odkaz` v zápisu.
4. Svazek zapiš přes `zapis.py svazky <klic> pracovni/svazek.json` (ne ručně, souběžní pomocníci by si ho přepsali),
   v souboru `{"archiv": "SOA Třeboň", "portal": "digi.ceskearchivy.cz", "svazek": "N Volary 1784–1820, sign. …",
   "popis": "obce…", "url": "<odkaz na svazek>"}`.
5. Dál stejně jako u ARON: `vyrez.py`, `ramecek.py`, přepis, osoby, deník.
6. Když se postup osvědčí, napiš pro portál vlastní malý nástroj podle `trebon.py` (bez prohlížeče, pokud to jde)
   a postup zapiš do `STAV.md`. Poznatek zapiš i do `poznamky_pro_skill.md` (pro správce skillu).

## Starší prameny (17.–18. století)
- **Soupis poddaných podle víry 1651** – celé rodiny s věkem, po krajích; edice Národního archivu jako PDF
  (nacr.cz, hledej „Soupis poddaných podle víry“ + kraj). Fulltext v PDF, příjmení často bez diakritiky / s jinou ortografií
  (Šaršoun → „Šaroun“, dlouhé ſ jako f). Ves je v rámci panství; poznamenej si stránku edice.
- **Berní rula 1654** – jen hospodáři s půdou; edice a rejstříky v knihovnách (Kramerius/DNNT).
- **Gruntovní (pozemkové) knihy** – převody domů z otce na syna; online jen část (SOA Plzeň téměř vše, SOA Praha část,
  ostatní spíš badatelna). Fond „Velkostatek <panství>“.
- **Mapy stabilního katastru (1824–43)** – kde stál dům s číslem popisným: Archiv ČÚZK (ags.cuzk.gov.cz/archiv,
  nástroj `cuzk_archiv.py`, postup v `prameny.md`).
  Na **císařských otiscích** chybí u části listů barvy a čísla domů. Lepší jsou **indikační skici**: mají čísla domů
  a u pozemků jméno majitele („N. 13“ = patří k domu čp. 13). Dům bez pozemků mimo ves = domkář bez polí.
  Jméno majitele samotného domu bývá jen v písemném operátu (archiv, ne online). Výřezy map patří na web k domu (`mapy.json`).
- **Dnešní adresa domu** podle čísla popisného: RÚIAN (`mista.py ruian "Osada čp"`: adresa, parcela, k. ú.). Pozor, staré centrum mívá od 19. století
  stejná čp., ale předměstí a vesnice čísla přečíslovávaly. Hodí se na procházku po místech, kde lidé z domu žili a pracovali.
  Stavbu podle obce a čísla popisného najde i nahlizenidokn.cuzk.gov.cz (ověření adresy z dokladu); vlastník je za
  CAPTCHou a je to údaj o žijícím člověku – nezjišťuj ho.

## Staré mapy a drobné památky (pro mapu na webu)
- **Ortofoto z 50. let** (CENIA): `cuzk_archiv.py mapa cenia50 …` (WMS `https://gis.cenia.cz/mapcache/ortofotomapa_historicka/wms`,
  vrstva `orto`, EPSG:5514; rok snímku `…/geoserver/ortofotomapa_historicka_roky/wms` GetFeatureInfo). Stará
  kontaminace.cenia.cz je vypnutá.
- **2. vojenské mapování (1836–52)**: WMS `https://gis.cenia.cz/mapcache/II_vojenske_mapovani/wms` (WMS 1.1.1, vrstva
  `II_vojenske_mapovani`, jen EPSG:5514). Výřez: střed převeď z lat/lon na S-JTSK přes
  `https://ags.cuzk.gov.cz/arcgis/rest/services/Utilities/Geometry/GeometryServer/project` (`inSR=4326`, `outSR=5514`, `transformation=1623`, `transformForward=false` – bez ní ujede o ~10 m,
  `geometries={"geometryType":"esriGeometryPoint","geometries":[{"x":lon,"y":lat}]}`, `f=json`), pak `GetMap` s `BBOX` ±1300 m,
  `WIDTH=1800&HEIGHT=1200`, a `vyrez.py <obrázek> mapa_<obec>_1845_2_vojenske_mapovani 0,0,1,1`. Na jednotlivé domy podrobnost
  nestačí, ale ukáže ves, cesty a mlýny. Starší adresa `geoportal.gov.cz/ArcGIS/services/CENIA/…` hlásí údržbu a oldmaps.geolab.cz
  místo stránek vrací zdrojový kód – nepoužívat.
- **Kříže, boží muka, pomníky dnes**: ZABAGED (`https://ags.cuzk.gov.cz/arcgis/rest/services/ZABAGED_POLOHOPIS/MapServer`,
  vrstva 24 „Kříž, sloup kulturního významu“, 25 „Mohyla, pomník, náhrobek“; `query` s `geometry` = obálka kolem obce,
  `inSR=outSR=4326`). Názvy nemají, jen polohu. OpenStreetMap (Overpass, `historic=wayside_cross|wayside_shrine|memorial`)
  bývá podobné; přetížený server zkus znovu za chvíli.
- **Pomístní jména** (tratě, lesy, rybníky – „U hamru“, „Na tvrzi“, „Hradiště“): GEONAMES
  `https://ags.cuzk.gov.cz/arcgis/rest/services/GEONAMES/Vyhledavaci_sluzba_nad_daty_GEONAMES/MapServer/0/query` (obálka kolem obce).
- **Co kde stálo a proč**: obecní kronika (kronikář obvykle vyjmenuje kříže a kaple i s místem a důvodem), opisy kronik na webech
  obce a místních. Spojení: kronika řekne „kříž před čp. 24“ → RÚIAN dá polohu dnešního čp. 24 → bod `priblizne` s popisem,
  ze kterého pramene je. Shoda s křížem v ZABAGED/OSM je `prob`, ne jistota.
- **Tvrze a hrady**: Sedláček, *Hrady, zámky a tvrze království Českého* – původní vydání (1882–1927) je v Krameriovi veřejně
  (`kramerius.py '(text_ocr:Obec*) AND root_title:"Hrady, zámky a tvrze" AND dostupnost:public'`, text stránky přes
  `…/item/<uuid>/streams/TEXT_OCR`, kódování UTF-16). Novější regionální soupisy tvrzí bývají jen v knihovně.

## Oběti 2. světové války
- **Arolsen Archives** (collections.arolsen-archives.org): dokumenty o vězních, nuceně nasazených a vysídlených. Vyhledávání
  v prohlížeči, vstupní prohlášení musí odsouhlasit uživatel.
- **Mauthausen – Raum der Namen** (raumdernamen.mauthausen-memorial.org): vězni zemřelí v Mauthausenu, s datem a místem
  narození i úmrtí. Takové údaje jsou citlivé – na web jen se souhlasem rodiny (`soukromi.md`).

## Příjmení dnes a DNA
- **Rozšíření příjmení dnes**: kdejsme.cz (počty nositelů po okresech). Rychle ukáže, jestli je příjmení vzácné a kde
  jsou jeho „hnízda“. Při hledání vzdálených příbuzných vyškrtni vlastní rodinu.
- **DNA** (jen když o to uživatel stojí, a jeho rozhodnutí): autosomální test (MyHeritage, Ancestry) najde bratrance
  do ~5. kolene. **Y-DNA** (FamilyTreeDNA, Y-37 až Big Y) se dědí po meči beze změny. Ověří, jestli dvě linie stejného
  příjmení mají společného předka, a u nemanželského dítěte může shoda s jiným příjmením ukázat otce. Kontakt se žijícími
  příbuznými vždy jen přes uživatele.
Všechno, co jde jen v badatelně, zapisuj do `data/archivni_dotazy.md` (archiv, fond, inventární číslo, co hledat).
