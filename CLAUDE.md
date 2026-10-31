# dejiny-domu-skill

## Commity

Conventional Commits, popis česky:

```
<typ>(<scope>): <popis>
```

- **typ:** `feat`, `fix`, `docs`, `refactor`, `style`, `chore`, `release`
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
