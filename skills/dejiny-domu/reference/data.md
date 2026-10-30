# Formát dat projektu

Všechna data jsou v `data/`. Web se z nich generuje (`npm run data`), nikdy needituj `web/src/data/site.json` ručně.
Po změnách spusť `python3 -I tools/kontrola.py`.
Položky do JSON souborů přidávej a měň přes `python3 -I tools/zapis.py` (zachová formát souboru, viz SKILL.md).
`domy.py` a markdown uprav nástrojem pro úpravu souborů.

## Stavy doložení (`st`)
| stav | význam |
|---|---|
| `doc` | přečteno přímo na snímku pramene (matrika, gruntovní kniha, sčítání, katastr, mapa). Vždy s `r` |
| `lit` | z literatury (kniha, článek, vlastivěda), vždy se `zdroj` („Vlastivěda okresu, 1899, s. 389“) |
| `prob` | pravděpodobné (shoda jména, doby a čísla, ale ne přímý doklad, třeba před ztotožněním přečíslování), v `note` proč |
| `fam` | od majitele, pamětníka nebo z domovního dokumentu |
| `unk` | neznámé |

## `domy.py`
```python
OBEC = dict(nazev="Horní Lhota", jine_nazvy="Ober-Lhotta", obec="Dolní Lhota, okres Pelhřimov",
            farnost="Dolní Lhota", panstvi="Kamenice (8 domů) a Pacov (10 domů)",
            popis="…", lat=…, lon=…)
OBEC_UDALOSTI = [
 dict(rok="22. 7. 1352", text="Ves poprvé zmíněna v listině…", st="lit",
      zdroj="Vlastivěda okresu (1899), s. 389"),
]
D = {
 "12": dict(nazev="", druh="chalupa", st="doc", popis="…", lat=…, lon=…,
     cisla=[("1771–1827", "čp. 21 (?)"), ("od 1827", "čp. 12")],
     udalosti=[dict(rok="1890", text="Sčítání lidu: 7 osob, hospodář …", st="doc", r=["lhota_scitani_cp12_1890"])],
     drzitele=[dict(od="1786", do="1820", n="Jan Novák", jak="koupě od otce za 300 zl.", st="doc", r=[…], note="")],
     obyvatele=[dict(n="Anna Nováková", y="1857–?", role="dcera hospodáře", f=["* 1857 Horní Lhota 12"], st="doc", r=[…])],
     note=""),
}
ISSUES = [("Kdy dům dostal číslo 12?", "Otevřené: v matrice 1786 je Novák na čp. 4…")]
```
- Klíč domu = číslo popisné **jako text** („12“, „12a“, „ev. 3“). Adresa stránky `/dum/12/`.
- `rok` / `od` / `do` jako text: „1352“, „22. 7. 1352“, „asi 1600“, „před 1654“. Web řadí podle prvního čtyřčíslí.
- `udalosti`: stavba, požár, přestavba, dělení gruntu, prodej, sčítání (shrnutí domácnosti), válka, elektrifikace…
- `drzitele`: jeden řádek = jeden držitel (u manželů „Jan a Marie Novákovi“), `jak` = koupě / dědictví / přiženění / dražba / přídělem.
- `obyvatele`: lidé, kteří v domě žili (i výměnkáři, čeleď, nájemníci). `f` krátká fakta
  (`* narození`, `× sňatek`, `† úmrtí`). **Žijící jen jméno** (soukromí).
- `cisla`: všechna čísla domu v čase, dvojice (období, číslo). Ztotožnění doložit v `udalosti` nebo `note`.

## `zaznamy.json` – zápisy z pramenů
```json
[{"klic": "lhota_scitani_cp12_1890", "svazek": "trebon_123456", "snimek": 65, "druh": "S",
  "datum": "1890", "nazev": "Sčítání lidu 1890, Horní Lhota čp. 12",
  "shrnuti": "Hospodář Jan Novák (* 1830), manželka Marie, 4 děti, čeledín…",
  "odkaz": "https://digi.ceskearchivy.cz/DA?…&id=123456&page=65"}]
```
- `klic`: malá písmena bez diakritiky, `obec_druh_cp_kdo_rok` (druh: krest, snatek, umrti, scitani, grunt, katastr,
  mapa, kronika, kniha…). Je to i název obrázku.
- `druh`: N křest, O sňatek, Z úmrtí, I rejstřík, S sčítání, G gruntovní / pozemková kniha, K katastr, M mapa,
  C kronika, L literatura, J jiný.
- U literatury (`L`) je `snimek` strana a `odkaz` odkaz do Krameria / Google Books, výřez = sken strany.

## `svazky.json`
`{"trebon_123456": {"archiv": "SOA Třeboň – SOkA Pelhřimov", "portal": "digi.ceskearchivy.cz",
"svazek": "Sčítání lidu 1890, Horní Lhota", "popis": "Horní Lhota", "url": "…"}}`. Matriky přes `trebon.py svazek` apod.
Gruntovní knihy: „Velkostatek Kamenice, gruntovní kniha Horní Lhota 1650–1780, inv. č. …“.

## `prepisy.json`, `zvyrazneni.json`
`{"<klic>": {"orig": "[Číslo domu] 30\n[Jméno] …", "cs": "Překlad celou větou…"}}`,
`orig` po sloupcích s `[Názvem sloupce]`, nejisté „(?)“, nečitelné „[…]“. U gruntovních knih vysvětli staré pojmy
(kopa, vejrunk, výminek, závdavek) v `cs`. Rámečky zapisuje `ramecek.py`.

## `mapy.json` – staré mapy a letecké snímky
```json
[{"img": "mapa_lhota_1827_cisarsky_otisk", "rok": "1827", "nazev": "Stabilní katastr – císařský otisk",
  "zdroj": "ČÚZK, Archiv ČÚZK, císařský otisk B2/a/6C 570, list 4", "url": "https://ags.cuzk.gov.cz/archiv/", "popis": "Čp. 12 je dřevěný dům (žlutě) u cesty…",
  "skupina": "ves"}]
```
- Obrázek přes `vyrez.py dokumenty/<soubor> <img> 0,0,1,1` (celý) nebo s výřezem (vznikne `vyrezy/` i `zdroje/`).
- `skupina`: mapy se **stejným výřezem krajiny** (stejná oblast, sever nahoře, stejné měřítko) mají stejnou
  skupinu. Web je umí prolínat posuvníkem. Mapy s jiným výřezem skupinu nemají a jsou jen v galerii.
  **Snímky obrazovky od uživatele (geoportál, Mapy.cz) skupinu nedostávají**: nemají stejný výřez ani měřítko
  a prolínání nesedí (automatické zarovnání přes OpenCV selhává – jiná sezóna, rozlišení). Pro porovnání stáhni
  sérii se stejným bbox (WMS/ArcGIS export, např. ortofota ČÚZK po letech, `cuzk_archiv.py mapa` se stejným poloměrem).
- `zdroj` povinně (autorská práva).

## `mista.json` – další body na mapě
`{"Kaple na návsi": {"dotaz": "…", "lat": 49.432, "lon": 15.219, "popis": "Barokní socha sv. Jana"}}`, spravuje `mista.py`.

## `dokumenty.json` – fotky a dokumenty
`[{"img": "foto_cp12_1935", "popis": "Čp. 12 kolem 1935 (fotka od paní X).", "domy": ["12"]}]`
Obrázek přes `vyrez.py dokumenty/<sken>.jpg foto_cp12_1935 0,0,1,1`.

## `web.json`
Viz `web.md`. `hlavni_dum` = čp. domu, o kterém projekt hlavně je (úvodní stránka).

## Markdown
- `research_log.md` – tabulka `| # | datum | zdroj | rozsah | hledáno | výsledek | citace |`, i negativní výsledky.
- `zajimavosti.md` – `## Nadpis` + text, odkazy `[čp. 12](/dum/12/)`, `[zápis](/zdroj/<klic>/)`.
- `pribeh.md` – „Příběh domu“: frontmatter `title`, `lead` + kapitoly `##` (`pribehy.md`).
- `pametnici.md`, `archivni_dotazy.md` – volný text. Poznámky pro Clauda `<!-- … -->` na web nejdou.
