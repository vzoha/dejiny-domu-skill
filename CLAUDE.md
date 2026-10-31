# dejiny-domu-skill

## Commity

Conventional Commits, popis česky:

```
<typ>(<scope>): <popis>
```

- **typ:** `feat`, `fix`, `docs`, `refactor`, `style`, `test`, `chore`, `release`
- **scope** (volitelný): `skill` (SKILL.md), `playbook` (reference/), `nastroje` (tools/), `web` (template/), `readme`, `plugin` (.claude-plugin/)
- popis malým písmenem, bez tečky na konci, max ~72 znaků; detaily do těla commitu
- jeden commit = jedna logická změna; nemíchat víc funkcí do jednoho
- verze zvlášť: `release: 0.3.7` (bump `.claude-plugin/plugin.json` + `skills/dejiny-domu/VERZE`)

Příklady:

```
feat(web): odkazy /zdroj/ v příbězích jako kartičky
fix(nastroje): ipr_praha prázdný obrázek podle velikosti
docs(playbook): městský dům 20. století
release: 0.3.6
```

Kontrolu formátu dělá hook `.githooks/commit-msg`; po naklonování ho zapni přes `git config core.hooksPath .githooks`.

## Před vydáním verze

`python3 -m unittest discover tests` – testy `zapis.py`, `kontrola.py`, `export_web.py` a `novy_projekt.py` (bez sítě, pár sekund). Spouštěj i po každé změně těch nástrojů.

`python3 -I skills/dejiny-domu/tools/zdravi.py` – všechny portály musí projít (výpadek zkus znovu za chvíli).

## Vydání verze

1. Verze v `.claude-plugin/plugin.json`, `skills/dejiny-domu/VERZE` a README („Aktuální verze“) → commit `release: X.Y.Z`.
2. Tag `vX.Y.Z` a push (větev i tag).
3. GitHub release se shrnutím pro uživatele (novinky, opravy, jak aktualizovat projekt), česky, bez interních
   detailů: `gh release create vX.Y.Z --title "X.Y.Z – …" --notes "$(cat poznamky.md)"`
   (`gh` ze snapu nečte soubory v `/tmp` ani stdin – poznámky předej přes `--notes`).
