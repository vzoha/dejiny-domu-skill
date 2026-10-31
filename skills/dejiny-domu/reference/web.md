# Web – stavba, nastavení, zveřejnění

Web je statický (Astro + vyhledávání Pagefind), data bere z `data/` přes `tools/export_web.py`.
Stránky: úvod (lákadlo, hlavní dům s časovou osou, zajímavosti, mapa), příběhy (jeden, nebo rozcestník s kartami
+ galerie fotek po skupinách), zajímavosti, obec (údaje a časová
osa), domy (seznam), stránka domu (čísla v čase, časová osa, držitelé, obyvatelé, mapa, fotky, prameny), staré mapy
(galerie + prolínání map stejné `skupiny`), mapa (OpenStreetMap, letecký snímek a katastr ČÚZK), prameny (s výřezem,
rámečkem, přepisem a překladem), „Co hledáme“, výzkumný deník, hledání.

## Příkazy (ve složce `web/`)
| příkaz | co dělá |
|---|---|
| `npm install` | jednou na začátku (stáhne knihovny, ~1 minuta) |
| `npm run data` | převede data do webu (vždy po změně dat; funkční Python 3 vyhledá `scripts/data.mjs`) |
| `npm run build` | sestaví web do `dist/` |
| `npm run nahled` | data + build + náhled na http://localhost:4321 (Ctrl+C ukončí) |
| `npm run dev` | vývojový režim při úpravách vzhledu |
| `npm run nasadit` | data + build + nahrání na Netlify |

Náhled spouštěj na pozadí a uživateli pošli odkaz. **Port:** když je 4321 obsazený (jiný projekt), Astro tiše přejde na další (4322…) –
skutečnou adresu vyčti z výstupu (`Preview server running at …`) a před odesláním odkazu ověř, že na ní je tento projekt
(titulek stránky). Vzhled si ověř sám (snímek obrazovky přes prohlížeč, je-li k dispozici).

## `data/web.json`
```json
{
 "nazev": "Horní Lhota čp. 12",
 "popis": "Popis pro sdílení (web je noindex).",
 "zapati": "Dohledáno v digitalizovaných pramenech SOA Třeboň a ČÚZK",
 "kontakt": {"jmeno": "Novákovým", "email": "…"},
 "prihlaseni": {"uvod": "Tenhle web je zatím jen pro známé.", "otazka": "…", "odpoved": "…"},
 "uvod": {"nadpis": "Lákavý nadpis", "odstavce": ["2–3 věty, které chytí"], "foto": "klic_obrazku_ve_vyrezech", "foto_popis": "…"},
 "hlavni_dum": "12",
 "pribeh": {"menu": "Příběh domu", "tlacitko": "Přečíst příběh čp. 12", "hlavni": "cp12"},
 "galerie": {"skupiny": [{"id": "tehdy", "nazev": "Tehdy a dnes", "uvod": "Stará fotka a dnešní ze stejného místa."}]},
 "zajimavosti_na_uvodu": [{"nadpis": "Nejstarší zmínka", "text": "1351 – …"}],
 "verejny": false
}
```
- `kontakt.jmeno` je ve 3. pádě („Napište Petrovi na …“).
- `verejny`: `true` až u webu, který je otevřený všem (`prihlaseni.otevreny`) – pak zápatí nepíše „neveřejný web“.
- **Když uživatel nechce vymýšlet otázku** („jen pro rodinu“, „vygeneruj heslo“): otázka „Heslo k rodinnému webu
  (pošle vám ho <jméno>)“ a odpověď jako náhodná heslová fráze ze 3 slov z dějin domu + číslo (`secrets`), např.
  `mlyn-kaple-hamr-42`. Uživateli řekni, ať ji rodině pošle zvlášť od odkazu.
- **Přihlášení:** otázka, na kterou znají odpověď jen ti, komu je web určený – rodina, sousedé, spolek
  (ne snadno dohledatelná na sociálních sítích).
  Odpověď se porovnává bez diakritiky a velkých písmen. Na serveru i v cookie prohlížeče je jen její otisk (SHA-256),
  samotná odpověď se nikam neukládá. Krátkou nebo běžnou odpověď (jméno, obec) ale jde z otisku uhádnout zkoušením,
  proto ať ji uživatel nepoužívá jako heslo jinde. Bez odpovědi nasazení (`npm run nasadit`, `deploy-caprover`)
  skončí chybou; otevřený web jen výslovně přes `"otevreny": true` v `prihlaseni`.
  Je to lehká ochrana proti náhodným návštěvníkům, ne bankovní zabezpečení – citlivé věci na web nepatří.
- `uvod.foto` = klíč obrázku ve `vyrezy/` (ulož přes `vyrez.py`).
- `hlavni_dum`: čp. hlavního domu (úvodní stránka ho ukáže s časovou osou). `pribeh` viz `pribehy.md`
  (`pribeh.hlavni` = slug příběhu, kam vede tlačítko na úvodu; bez něj vede na rozcestník `/pribehy/`).
- `galerie.skupiny`: názvy, úvodní věta a pořadí skupin fotek na stránce příběhů (`skupina` v `dokumenty.json`).
  Fotky bez skupiny jdou na konec („Další fotografie“).
- Šablona `web.json` je prázdná – název nastav hned na začátku.
## Zveřejnění na Netlify (výchozí, zdarma)
1. Uživatel si založí účet na netlify.com (stačí přihlášení přes Google/GitHub) – udělá sám.
2. Přihlášení CLI (otevře prohlížeč) – dej uživateli: `! cd web && npx -y netlify-cli@latest login`.
   První stažení netlify-cli je velké a na pomalé síti padá (`ETIMEDOUT`) – předem ho stáhni sám:
   `cd web && npx -y --fetch-retries=5 --fetch-retry-maxtimeout=120000 netlify-cli@latest --version`.
   Když `!` nejde (cloudové prostředí): `npx -y netlify-cli@latest login --request "Dejiny domu"` vypíše odkaz a číslo
   lístku – uživatel odkaz otevře a schválí, pak `npx -y netlify-cli@latest login --check <lístek>`.
3. Založení webu a propojení složky (interaktivní, jednou) – dej uživateli:
   `! cd web && npx -y netlify-cli@latest sites:create` (zvolí tým a název → adresa `https://<název>.netlify.app`),
   případně `npx netlify-cli link`, pokud web už existuje. Je-li uživatel už přihlášený, jde web založit i bez dotazů
   (můžeš spustit sám): `cd web && npx -y netlify-cli@latest sites:create --name <název> --account-slug <tým>`.
   **Windows:** když `!` běží ve Windows PowerShellu 5.1 (`&&` tam nefunguje a `npx` blokuje Execution Policy), ať uživatel
   otevře PowerShell 7 nebo Příkazový řádek, přejde do složky `web` a spustí `npx -y netlify-cli@latest login` (a `sites:create`).
4. Nasazení: `cd web && npm run nasadit` (můžeš spustit sám; vypíše adresu webu).
5. Ověř: otevři adresu **v anonymním okně** → musí se ukázat přihlašovací otázka; po správné odpovědi web.
   Ukáže-li se místo ní přihlášení k Netlify (401, „Login Redirect“), zdědil web ochranu týmu („Team protection“).
   Uživatel ji vypne v administraci webu: Project configuration → Access & security → Visitor access. (V novém rozhraní: Project configuration → General → Visitor access → „Customize this project’s visibility“ → **Public** → Save; „Public“ znamená jen bez přihlášení k Netlify, web dál chrání přihlašovací otázka.) Web pak chrání
   přihlašovací otázka – proto znovu ověř v anonymním okně, že se ukáže.
   Přihlášení zajišťuje Netlify Edge Function `web/netlify/edge-functions/brana.js` (generuje ji export).
Další aktualizace = jen `npm run nasadit`. Vlastní doménu lze nastavit v administraci Netlify.

**Pozor:** „Netlify Drop“ (přetažení složky v prohlížeči) neumí Edge Functions → web by byl bez přihlášení. Nepoužívat.

## Náhled v Claude desktop
Projekt má `.claude/launch.json` – náhled webu v Claude desktop spustí `npm --prefix web run dev` (port 4321). Data se
předtím musí vyexportovat (`cd web && npm run data`). Když náhled nenaběhne (třeba na Windows, kde je `npm` jako `npm.cmd`),
zkus v `launch.json` `"runtimeExecutable": "node"` a `"runtimeArgs": ["web/node_modules/astro/bin/astro.mjs", "dev", "--root", "web"]`
(Astro 7 má spouštěč `astro.mjs`, ne `astro.js`). Server běží jen na tomto počítači – nepřidávej `--host`.

## Vlastní server (pokročilé)
- Docker: `web/Dockerfile` (build Astro → nginx s `nginx.conf` z `nginx.sablona.conf`). Před buildem image vždy `npm run data`.
- CapRover: `npm run deploy-caprover` (vyžaduje nainstalovaný a přihlášený `caprover` CLI).

## Úpravy vzhledu
Styly: `web/src/styles/global.css` (základ) a nad ním `modern.css` (barvy v `:root`, karty, časová osa, formuláře) –
vzhled měň v `modern.css`. Písma (Fraunces na nadpisy, Source Sans 3 na text) jsou v projektu z balíčků `@fontsource-variable`
a načítá je Astro (`astro.config.mjs` → `fonts`, `<Font>` v `Base.astro`) s přednačtením a dorovnaným záložním písmem,
takže text při načtení neposkočí; nic se nestahuje z Google Fonts. Rozložení `web/src/layouts/Base.astro`, stránky
`web/src/pages/`. Šířka stránky: `<Base>` bez parametru = 1120 px, `wide` = 1600 px, `narrow` = čtecí sloupec (příběh).
Upravuj jen na přání uživatele a po úpravě zkontroluj web na mobilu i počítači.

## Mapa
Mapa (`components/HouseMap.astro`) má OpenStreetMap, ortofoto ČÚZK (WMS `ags.cuzk.cz/arcgis1/services/ORTOFOTO`) a dnešní
katastr (WMS `services.cuzk.cz/wms/wms.asp`, vrstva `KN`). Staré mapy jsou obrázky v `mapy.json` (ne georeferencované).
- Body: domy z `domy.py` (s `lat`/`lon`) a místa z `mista.json` (pole viz `data.md`), barva podle `druh` (`lib/places.js`).
- Úvodní výřez = domy a místa do 700 m od obce (`OBEC` lat/lon); přepínač **Ves / Okolí** vlevo nahoře (pod +/−) ukáže i vzdálená místa.
  Na stránce domu se mapa přiblíží na dům a přepínač nemá.
- **Vysvětlivky** vlevo dole (jen stránka Mapa) – jen barvy a „přibližná poloha“, nic dalšího; na mobilu sbalené.
- **Bublina** = malá karta: druh, název, vzdálenost od středu obce (`STRED` v `places.js`, výchozí „návsi“), štítek přibližné
  polohy, popis, odkaz. Vybraný bod se zvětší a dostane klidný prstenec (bez animace).
- Stránka Mapa má pod mapou **seznam míst** po skupinách jako karty; „Na mapě“ přiblíží bod a otevře bublinu
  (`el.fmap.select(i)`, pořadí bodů = domy s polohou, pak `mista.json`).

## Aktualizace staršího projektu
Znovu spusť `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu>`. Data (`data/`, výřezy) zůstanou, `tools/` se přepíše
a soubory ve `web/`, které se liší od nové šablony, taky – staré verze uloží do `pracovni/zaloha_web_<datum>/` a vypíše jejich seznam.
Upravoval-li jsi s uživatelem vzhled (styly, stránky), převezmi úpravy ze zálohy (porovnej soubory) a ověř web. Pak ve `web/`
`npm install` a `npm run data`. Starou šablonu přihlášení `export_web.py` odmítne s výzvou k aktualizaci.
