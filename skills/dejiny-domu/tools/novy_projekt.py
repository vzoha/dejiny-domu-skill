#!/usr/bin/env python3
"""Založí nový projekt dějin domu / obce ze šablony skillu.

Použití: python3 <skill>/tools/novy_projekt.py <cílová složka>

Vytvoří: data/ (prázdné kostry nebo ukázka), web/ (Astro web), tools/ (kopie nástrojů),
vyrezy/, zdroje/, dokumenty/, pracovni/, CLAUDE.md, .gitignore, .gitattributes (konce řádků LF i na Windows)
a .claude/launch.json (náhled v Claude desktop), v .claude/settings.json hook tools/hlidac.py
(síť k archivům jen přes slusne.py – existující nastavení zůstane).
Existující data nepřepisuje.
Aktualizace staršího projektu (znovu spustit na stejnou složku): tools/ se přepíše vždy a soubory webu,
které se liší od nové šablony, taky – jejich staré verze se nejdřív uloží do pracovni/zaloha_web_<datum>/.
"""
import filecmp, json, os, shutil, sys, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def copy(src, out):
    if os.path.islink(out):   # nepsat přes symlink mimo projekt
        os.remove(out)
    shutil.copy2(src, out)


def copy_tree(src, dst, backup=None):
    """Zkopíruje chybějící soubory. S backup= přepíše i ty, které se liší, a starou verzi uloží do backup/."""
    changed = []
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".astro", "__pycache__")]
        rel = os.path.relpath(base, src)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            new, out = os.path.join(base, f), os.path.join(dst, rel, f)
            if not os.path.lexists(out):
                copy(new, out)
            elif backup and (os.path.islink(out) or not filecmp.cmp(new, out, shallow=False)):
                keep = os.path.join(backup, os.path.normpath(os.path.join(rel, f)))
                os.makedirs(os.path.dirname(keep), exist_ok=True)
                if not os.path.islink(out):
                    shutil.copy2(out, keep)
                copy(new, out)
                changed.append(os.path.normpath(os.path.join(rel, f)))
    return changed


HOOK = ('python3 -I "$CLAUDE_PROJECT_DIR/tools/hlidac.py" 2>/dev/null || '
        'python -I -X utf8 "$CLAUDE_PROJECT_DIR/tools/hlidac.py"')   # Windows: python3 bývá nefunkční alias


def pridej_hook(dst):
    """Hook tools/hlidac.py do .claude/settings.json projektu (síť k archivům jen přes slusne.py).
    Existující nastavení zůstane, hook se přidá jen jednou."""
    path = os.path.join(dst, ".claude", "settings.json")
    try:
        cfg = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    except ValueError:
        print(f"POZOR: {path} není platný JSON – hook hlidac.py nepřidán (oprav soubor a spusť znovu)")
        return
    pre = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if any("hlidac.py" in h.get("command", "") for m in pre for h in m.get("hooks", [])):
        return
    pre.append({"matcher": "Bash|WebFetch", "hooks": [{"type": "command", "command": HOOK, "timeout": 60}]})
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dst = os.path.abspath(os.path.expanduser(sys.argv[1]))
    os.makedirs(dst, exist_ok=True)
    copy_tree(os.path.join(SKILL, "template", "data"), os.path.join(dst, "data"))
    web = os.path.join(dst, "web")
    backup = os.path.join(dst, "pracovni", "zaloha_web_" + time.strftime("%Y%m%d-%H%M%S"))
    changed = copy_tree(os.path.join(SKILL, "template", "web"), web, backup if os.path.isdir(web) else None)
    tools = os.path.join(dst, "tools")
    os.makedirs(tools, exist_ok=True)
    for f in os.listdir(os.path.join(SKILL, "tools")):
        if f.endswith((".py", ".sh")) and f != "novy_projekt.py":
            copy(os.path.join(SKILL, "tools", f), os.path.join(tools, f))   # nástroje vždy aktualizovat
            if f.endswith(".sh"):   # skill naklonovaný na Windows (core.autocrlf) má CRLF – Git Bash by skript nespustil
                p = os.path.join(tools, f)
                data = open(p, "rb").read()
                if b"\r\n" in data:
                    open(p, "wb").write(data.replace(b"\r\n", b"\n"))
    for d in ("vyrezy", "zdroje", "dokumenty", "pracovni"):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    os.makedirs(os.path.join(dst, ".claude"), exist_ok=True)
    for name in ("CLAUDE.md", ".gitignore", ".gitattributes", "poznamky_pro_skill.md", os.path.join(".claude", "launch.json")):
        out = os.path.join(dst, name)
        if not os.path.lexists(out):
            copy(os.path.join(SKILL, "template", name), out)
    pridej_hook(dst)
    with open(os.path.join(dst, ".skill_verze"), "w", encoding="utf-8") as f:   # SKILL.md podle něj nabídne aktualizaci
        f.write(open(os.path.join(SKILL, "VERZE"), encoding="utf-8").read())
    print("Projekt připraven:", dst)
    if changed:
        print(f"Web aktualizován na novou šablonu ({len(changed)} souborů). Původní verze jsou v {backup}:")
        for f in changed:
            print("  web/" + f)
        print("Pokud jste vzhled webu upravovali, převezměte úpravy ze zálohy. Pak `npm install` a `npm run data` ve web/.")


if __name__ == "__main__":
    main()
