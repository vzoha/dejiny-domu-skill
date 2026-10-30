# Stav projektu a pravidla práce

Tento soubor je vstupní bod. Po každém restartu (nová konverzace, zkrácený kontext) ho Claude čte jako první,
pak konec `research_log.md` a sekci „Rozpracováno“.

## O čem to je
- Obec a hlavní dům: (doplnit – obec, číslo popisné, dnešní adresa)
- Kdo s Claudem pracuje, jaký má k domu vztah a jak chce komunikovat: (doplnit)
- Farnost (matriky), panství před 1848, archiv: (doplnit)

## Kde co je
| Soubor | Obsah |
|---|---|
| `data/domy.py` | Obec (`OBEC`, `OBEC_UDALOSTI`), domy podle čp. (`D`: události, držitelé, obyvatelé), otevřené otázky. |
| `data/zaznamy.json` | Každý použitý zápis z pramene (klíč = název obrázku). |
| `data/svazky.json` | Svazky a fondy (matriky, gruntovní knihy, sčítání, katastry) – archiv, signatura, odkaz. |
| `data/prepisy.json` | Přepis originálu a český překlad každého zápisu. |
| `data/zvyrazneni.json` | Rámečky – které místo výřezu čteme. |
| `data/mapy.json` | Historické mapy a letecké snímky (rok, zdroj) – stránka „Staré mapy“ s porovnáním. |
| `data/research_log.md` | Deník VŠECH hledání, i neúspěšných. |
| `data/pametnici.md` | Co řekli majitelé a pamětníci, domovní dokumenty. |
| `data/zajimavosti.md`, `data/pribeh.md` | Texty na web. |
| `data/archivni_dotazy.md` | Co by šlo zjistit jen v archivu / na katastru. |
| `data/mista.json`, `data/dokumenty.json`, `data/web.json` | Okolní místa na mapě, fotky a dokumenty, nastavení webu. |
| `vyrezy/`, `zdroje/` | Výřezy zápisů a map pro web (1800 px) a v plném rozlišení. |
| `dokumenty/` | Materiály od uživatele (originály). |
| `pracovni/` | Pracovní soubory (stažené stránky, kontrolní obrázky) – nejdou na web. |
| `web/` | Web. `cd web && npm run data && npm run build`, náhled `npm run preview`. |

## Pravidla
1. Než něco ohlásím jako nové, prohledám `domy.py`, `zaznamy.json` a `research_log.md` (číslo domu, jméno, rok).
2. Údaj je „doloženo“ (doc) jen tehdy, když jsem ho přečetl přímo na snímku. Literatura je `lit`, ne `doc`.
3. Každé hledání (i neúspěšné) zapíšu do `research_log.md`.
4. Nejistá čtení označím (?) – nic nedomýšlím. Číslo domu ověřuji proti přečíslování.
5. Ke každému novému zápisu: výřez (`tools/vyrez.py`), rámeček (`tools/ramecek.py`) a přepis s překladem.
6. Po změně dat spustím `python3 -I tools/kontrola.py`.

## Rozpracováno (aktualizovat průběžně)
- (zatím nic)
