# dejiny-domu-skill

## Commity

Conventional Commits, popis česky:

```
<typ>(<scope>): <popis>
```

- **typ:** `feat`, `fix`, `docs`, `refactor`, `style`, `test`, `chore`, `release`
- **scope** (volitelný): `skill` (SKILL.md), `reference` (reference/), `nastroje` (tools/), `web` (template/), `readme`, `plugin` (.claude-plugin/)
- popis malým písmenem, bez tečky na konci, max ~72 znaků; detaily do těla commitu
- jeden commit = jedna logická změna; nemíchat víc funkcí do jednoho
- verze zvlášť: `release: 0.3.7` (bump `.claude-plugin/plugin.json` + `skills/dejiny-domu/VERZE`)

Příklady:

```
feat(web): odkazy /zdroj/ v příbězích jako kartičky
fix(nastroje): ipr_praha prázdný obrázek podle velikosti
docs(reference): městský dům 20. století
release: 0.3.6
```

Kontrolu formátu dělá `tests/commit_msg.py`; po naklonování ho zapni obalem:
`printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/tests/commit_msg.py" "$1"\n' > .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg`

## Plugin
Plugin je celé repo (`.claude-plugin/plugin.json`). Adresář pluginů Anthropicu ho 15. 11. odmítl: od neověřených
organizací nebere skripty vůbec (ani ve `skills/`), o ověření zatím nejde požádat. Z pokusů zůstalo: nástroje bez `#!`
(spouštějí se přes `python3`/`bash`) a v šabloně webu `*.sablona` místo `package.json` a `.npmrc`. Nic z toho nevracet.

## Knihovny webu (template/web)
V šabloně jsou `package.sablona.json` a `npmrc.sablona` (adresář pluginů nepřijme `package.json` s polem `scripts`
ani `.npmrc` od neověřených autorů); `novy_projekt.py` je v projektu přejmenuje na `package.json` a `.npmrc`.
Lock proto generuj v projektu založeném ze šablony a `package-lock.json` (a změněný `package.json` jako
`package.sablona.json`) zkopíruj zpět do šablony.
`package-lock.json` generuj **npm 10** (`npx -y npm@10 install`): npm 11 vynechá volitelné `@emnapi/*` a `npm ci`
v npm 10 pak skončí chybou (audit D03). Ověř `npm ci` v npm 10 i 11, `npm audit` a `npm run build` na skutečném projektu.
Nejnižší Node = nejvyšší `engines.node` v locku (teď undici ≥ 22.19): oprav `package.sablona.json` (`engines`) i `SKILL.md`.

## Před vydáním verze

`python3 -m unittest discover tests` – testy `zapis.py`, `kontrola.py`, `export_web.py` a `novy_projekt.py` (bez sítě, pár sekund). Spouštěj i po každé změně těch nástrojů.

`python3 -I skills/dejiny-domu/tools/zdravi.py` – všechny portály musí projít (výpadek zkus znovu za chvíli).

## Vydání verze

1. Verze v `.claude-plugin/plugin.json`, `skills/dejiny-domu/VERZE` a README („Aktuální verze“) → commit `release: X.Y.Z`.
2. Tag `vX.Y.Z` a push (větev i tag).
3. GitHub release se shrnutím pro uživatele (novinky, opravy, jak aktualizovat projekt), česky, bez interních
   detailů: `gh release create vX.Y.Z --title "X.Y.Z – …" --notes-file poznamky.md`.
   Sekce Poděkování: přispěvatelé od minulé verze jménem a GitHub účtem, s tím, co udělali (`git log --format=%an`,
   autoři issues). **Proč:** v PR a issues jim to slibujeme („zmíním v poznámkách k vydání“), u 0.15.0 se na to zapomnělo.
