# dejiny-domu

Skill pro Claude Code: dějiny domu a vesnice z českých archivů (sčítání lidu, matriky podle čísla domu, stabilní
katastr, gruntovní knihy, staré mapy, literatura) a web s časovou osou, držiteli, obyvateli a porovnáním starých map.

Odvozeno ze skillu **rodokmen** 0.5.0 od Jindřicha Šaršona – https://github.com/sarsonj/rodokmen-skill
(první commit je nezměněná kopie jeho `skills/rodokmen`). Nástroje na archivy jsou společné. Licence MIT, viz `LICENSE`.

Použití: `python3 -I tools/novy_projekt.py ~/Obec-cp` založí projekt. Do projektu skill připoj jako
`.claude/skills/dejiny-domu` (kopie nebo symlink na tento repozitář). Návod pro Clauda je v `SKILL.md`.
