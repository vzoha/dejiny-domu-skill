# Zajímavosti a příběh domu

Tabulku držitelů nikdo číst nebude. „Dům třikrát vyhořel a pokaždé ho postavili znovu na stejném místě“ nebo
„chalupu koupil čeledín, který na ní dvacet let sloužil“ si přečte každý. Zajímavosti sbírej průběžně, ne až na konci.

## Zajímavosti – sbírej průběžně
Co najdeš při čtení, hned zapiš do `data/zajimavosti.md` (nadpis `##` + 2–5 vět) a řekni to uživateli jako příběh.
| Typ | Příklad |
|---|---|
| Nejstarší zmínka | první písemná zmínka o vsi / o gruntu, co v ní stojí doslova |
| Jedna rodina, sto let | stejné příjmení na gruntu přes generace, a kdy a proč se to zlomilo |
| Přiženění | vdova se znovu vdala a grunt přešel na nové příjmení |
| Ceny | za kolik se grunt prodával (kopy, zlaté), co to znamenalo (kolik krav, kolik let práce čeledína) |
| Pohromy | požár, povodeň, mor, cholera (úmrtí v matrice za pár týdnů), válka, rekvizice |
| Dělení a slučování | grunt rozdělený mezi syny, nový domek na dílu pole |
| Řemesla | kovárna, hospoda, mlýn, hamr v domě |
| Dvě vrchnosti | ves rozdělená mezi dvě panství, roboty jinam |
| Přečíslování | „dům měl tři různá čísla“ |
| 20. století | odsun Němců, kolektivizace, chalupáři. Jen fakta, citlivé věci se souhlasem (`soukromi.md`) |
| Mapy | co ukazuje stabilní katastr 1827 a co zmizelo (stodola, rybník, cesta) |
| Ústní podání vs. prameny | co vypráví sousedé a co potvrdil (nebo vyvrátil) archiv |

Nejlepší 2–4 dej na úvod webu (`web.json` → `zajimavosti_na_uvodu`).

## Příběh domu
**Kdy:** když má hlavní dům zhruba 4 doložené držitele nebo pokrytí ~150 let (`kontrola.py` připomene).
**Postup:**
1. Sesbírej: události a držitele domu, obyvatele, zajímavosti, mapy, `pametnici.md`, dějiny obce.
2. Napiš **koncept do chatu**. Pod něj připiš, co je z pramenů a co z literatury nebo od pamětníků. Uložíš ho až po schválení.
3. `data/pribeh.md`:
   ```markdown
   ---
   title: Příběh čp. 12
   lead: Jedna věta, která chytí.
   ---
   ## Ves pod hradem (1352–1650)
   …
   ## Novákovi (1786–1870)
   …
   ```
4. `web.json` → `"pribeh": {"menu": "Příběh domu", "tlacitko": "Přečíst příběh čp. 12"}` a `uvod`.

**Víc příběhů** (dům, výměnek, ves, rodina): každý do `data/pribeh_<slug>.md` → stránka `/pribehy/<slug>/`.
Jakmile je aspoň jeden, `/pribehy/` je rozcestník s kartami (obrázek, období, název, lead) a pod nimi galerie fotek
(`dokumenty.json` → `skupina`, `par`; `web.md` → `galerie`). Frontmatter:
```markdown
---
title: Statek čp. 12
lead: Jedna věta, která chytí.
poradi: 1
obdobi: 1654–dnes
obrazek: foto_cp12_1935
---
```
`obrazek` = klíč ve `vyrezy/`. Slug `cp<čp>` přidá tlačítko „Přečíst příběh domu“ na stránku domu, slug `obec`
tlačítko „Přečíst příběh obce“ na stránku obce. Tlačítko na úvodu vede na `web.json` → `pribeh.hlavni` (slug).
Starý `pribeh.md` pak už nepoužívej (s rozcestníkem se neukáže) – přejmenuj ho na `pribeh_<slug>.md`.

**Tvar** (800–1500 slov): kapitoly po obdobích nebo po rodinách držitelů. Nadpis = rodina nebo období a roky.
Začni krajinou a vsí (kdy vznikla, komu patřila), pak jednotliví držitelé a obyvatelé: kdo, odkud přišel, za kolik
koupil, kolik měl dětí, co je potkalo. Konkrétně: roky, ceny, citace z pramenů v uvozovkách, odkazy `[zápis](/zdroj/<klic>/)`.
Velké dějiny jen tam, kde se dotkly domu (robota, 1848, války, 1945, kolektivizace). Co nevíme, napiš jako otázku.
Poslední kapitola „Dnes“: jen to, co majitel na web pustí.
