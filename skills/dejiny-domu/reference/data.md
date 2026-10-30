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
- `zdroj` povinně (autorská práva). Je vidět na webu – žádné TODO ani pracovní poznámky; ty patří do `poznamka`
  (na web nejde). `rok` musí obsahovat čtyřčíslí („1827“, „asi 1840“), jinak se mapa řadí na konec.

## `mista.json` – další body na mapě
```json
{"Kaple na návsi": {"dotaz": "…", "lat": 49.432, "lon": 15.219, "popis": "Barokní socha sv. Jana.",
  "druh": "vira", "odkaz": "/zajimavosti/#kaple-na-návsi", "odkaz_text": "Zajímavosti", "priblizne": false}}
```
Bod přidá `mista.py pridej` (poloha z OSM), další pole `zapis.py mista "<název>" <vstup.json> --sloucit`.
- `druh` – barva a skupina v legendě a v seznamu pod mapou: `vira` (kaple, kostely), `pamatka` (kříže, pomníky), `remeslo`
  (mlýny, hamry, kovárny), `verejne` (škola, hospoda, obecní místa), `ves` (sousední vsi), jinak `jine`. Názvy a barvy:
  `web/src/lib/places.js`.
- `odkaz` + `odkaz_text` – kam vede odkaz z bubliny: zajímavost `/zajimavosti/#<id nadpisu>` (id = nadpis malými písmeny,
  mezery → `-`, interpunkce pryč, diakritika zůstává; ověř v `web/dist/zajimavosti/index.html`), zápis `/zdroj/<klíč>/`,
  `/obec/`, `/mapy/`, příběh `/pribehy/<slug>/`. Krátký text, dlouhý se v kartě zalomí pod „Na mapě“: „Celý příběh“
  jen pro `/pribehy/`, na zajímavosti „Zajímavosti“, na zápis např. „Zpráva z novin 1889“.
- `priblizne: true` – poloha jen odvozená (např. „před čp. 24“ z kroniky → dnešní čp. 24 z RÚIAN). Bod je čárkovaný a má štítek
  „poloha přibližná“; v `popis` napiš, odkud poloha je, ne „bod je přibližný“ (to už říká štítek).
- `popis` 1–3 věty pro hosta: co to je a proč to patří k dějinám obce. Nejistotu přiznej („Jestli kříž ještě stojí, nevíme.“).
- Okolní místa (sousední vsi, farní kostel) jen do ~5 km; dál ležící body roztáhnou přepínač „Okolí“ tak, že ves zmizí.
- Přejmenovat bod `zapis.py` neumí: klíč změň nástrojem pro úpravu souborů (jen ten řádek).

## `dokumenty.json` – fotky a dokumenty
`[{"img": "foto_cp12_1935", "popis": "Čp. 12 kolem 1935 (fotka od paní X).", "domy": ["12"]}]`
Obrázek přes `vyrez.py dokumenty/<sken>.jpg foto_cp12_1935 0,0,1,1`.
Volitelně (galerie na stránce příběhů):
- `skupina` – id skupiny z `web.json` → `galerie.skupiny` (např. `tehdy`, `dnes`, `rekonstrukce`); `poradi` – číslo v rámci galerie.
- `par` – `img` druhé fotky do dvojice „tehdy – dnes“ (stará kresba/fotka + dnešní foto ze stejného místa); ukáží se
  vedle sebe. `"format": "sirka"` u dvojice na šířku (jinak na výšku).
- `skryt: true` – na web nedávat (fotka zůstane v datech).

## `web.json`
Viz `web.md`. `hlavni_dum` = čp. domu, o kterém projekt hlavně je (úvodní stránka).

## Markdown
- `research_log.md` – tabulka `| # | datum | zdroj | rozsah | hledáno | výsledek | citace |`, i negativní výsledky.
- `zajimavosti.md` – `## Nadpis` + text, odkazy `[čp. 12](/dum/12/)`, `[zápis](/zdroj/<klic>/)`. Od ~10 položek
  seskup: `## Skupina` (dům, ves, rodina) + jedna věta úvodu, položky `###`, ve skupině podle času. Odkaz hned pod
  `## Skupinou` na samostatném řádku (`[Celý příběh domu →](/pribehy/cp12/)`) web ukáže jako tlačítko na konci skupiny.
- `pribeh.md` – „Příběh domu“: frontmatter `title`, `lead` + kapitoly `##` (`pribehy.md`).
- `pribeh_<slug>.md` – další příběhy → `/pribehy/<slug>/`; frontmatter navíc `poradi`, `obdobi`, `obrazek` (`pribehy.md`).
- `pametnici.md`, `archivni_dotazy.md` – volný text. Poznámky pro Clauda `<!-- … -->` na web nejdou.
