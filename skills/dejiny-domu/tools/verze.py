#!/usr/bin/env python3
"""Kontrola verze na začátku konverzace: nainstalovaný skill × projekt × nejnovější vydání na GitHubu.
Použití: python3 -I <skill>/tools/verze.py [<složka projektu>]

GitHubu se ptá nejvýš jednou za 24 hodin (mezipaměť ~/.cache/dejiny-domu/verze.json, Windows %LOCALAPPDATA%),
bez sítě nebo při chybě se ho prostě nezeptá. Výsledek je řádek začínající „→“ a klíčovým slovem pro Clauda:
  NOVA_VERZE_SKILLU   na GitHubu je novější verze než nainstalovaný skill – ať uživatel aktualizuje skill
                      (projekt se pak aktualizuje z nového skillu, ne z GitHubu)
  AKTUALIZUJ_PROJEKT  nainstalovaný skill je novější než projekt – nabídni novy_projekt.py
  PROJEKT_NOVEJSI     projekt vznikl novějším skillem než ten nainstalovaný (stará kopie skillu) – projekt neměnit
  SKILL_NEZJISTEN     spuštěno z kopie v projektu a nainstalovaný skill se nenašel – verze skillu neověřena
  AKTUALNI            vše sedí
Kopie v tools/ projektu najde nainstalovaný skill sama (registr pluginů Claude Code, ~/.claude/skills/dejiny-domu).
Kód je vždy 0 (kontrola nesmí zastavit práci).
Podle tools/verze.py ze skillu rodokmen (Jindřich Šaršon, MIT).
"""
import json, os, re, sys, time, urllib.request

REPO = "vzoha/dejiny-domu-skill"
PLUGIN = "dejiny-domu@dejiny-domu-skill"
URL = os.environ.get("DEJINY_VERZE_URL", f"https://api.github.com/repos/{REPO}/releases/latest")
CACHE = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache"),
                     "dejiny-domu", "verze.json")
DEN = 24 * 3600


def cislo(v):
    """„v0.10.0“ → (0, 10, 0); nesrozumitelná verze → None."""
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def cti(cesta):
    try:
        with open(cesta, encoding="utf-8-sig") as f:
            return f.read().strip()
    except OSError:
        return None


def github():
    """Nejnovější vydání na GitHubu (text verze) nebo None; nejvýš jeden dotaz za 24 hodin."""
    try:
        with open(CACHE, encoding="utf-8") as f:
            c = json.load(f)
        if time.time() - c.get("cas", 0) < DEN and cislo(c.get("verze")):
            return c["verze"]
    except (OSError, ValueError, AttributeError):
        pass
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "dejiny-domu-skill", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            verze = json.load(r).get("tag_name", "").lstrip("v")
    except Exception:   # noqa: BLE001 – bez sítě, limit API, jiná odpověď: kontrola jen vynechá GitHub
        return None
    if not cislo(verze):
        return None
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump({"cas": time.time(), "verze": verze}, f)
    except OSError:
        pass
    return verze


def nainstalovany(projekt_dir):
    """Nainstalovaný skill pro kopii v tools/ projektu (ta nemá vedle sebe VERZE): plugin z registru Claude Code
    (instalace pro tento projekt má přednost před uživatelskou), jinak ručně nakopírovaný ~/.claude/skills/dejiny-domu.
    Vrátí (verze, cesta) nebo (None, None)."""
    cfg = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    projekt = os.path.realpath(projekt_dir) if projekt_dir else None
    try:
        with open(os.path.join(cfg, "plugins", "installed_plugins.json"), encoding="utf-8") as f:
            zaznamy = json.load(f).get("plugins", {}).get(PLUGIN, [])
    except (OSError, ValueError, AttributeError):
        zaznamy = []
    poradi = []
    for z in zaznamy if isinstance(zaznamy, list) else []:
        pp = z.get("projectPath")
        if pp and projekt and os.path.realpath(pp) == projekt:
            poradi.insert(0, z)
        elif z.get("scope") == "user":
            poradi.append(z)
    for z in poradi:
        cesta = os.path.join(z.get("installPath", ""), "skills", "dejiny-domu")
        verze = cti(os.path.join(cesta, "VERZE")) or z.get("version")
        if cislo(verze):
            return verze, cesta
    rucne = os.path.join(cfg, "skills", "dejiny-domu")
    verze = cti(os.path.join(rucne, "VERZE"))
    return (verze, rucne) if cislo(verze) else (None, None)


def jak_aktualizovat(skill_dir):
    if os.sep + "plugins" + os.sep in skill_dir:
        return ("jako plugin: v Claude Code `/plugin marketplace update dejiny-domu-skill`, pak restart Claude Code "
                "(natrvalo: v /plugin zapnout automatické aktualizace)")
    return (f"ručně nakopírovaný skill ({skill_dir}): stáhnout novou verzi z https://github.com/{REPO} "
            "(Code → Download ZIP), složkou skills/dejiny-domu nahradit tu stávající a restartovat Claude Code")


def main(argv):
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__.strip())
        return
    if argv and (argv[0].startswith("-") or not os.path.isdir(argv[0])):
        print(f"verze.py: „{argv[0]}“ není složka projektu – zadej cestu ke složce projektu (nebo nic).")
        return
    projekt_dir = argv[0] if argv else None
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skill = cti(os.path.join(skill_dir, "VERZE"))
    if skill is None:   # spuštěno z kopie v tools/ projektu
        skill, nalezeny = nainstalovany(projekt_dir or skill_dir)
        skill_dir = nalezeny or skill_dir
    projekt = cti(os.path.join(projekt_dir, ".skill_verze")) if projekt_dir else None
    gh = github()

    print(f"Skill (nainstalovaný): {skill}")
    if projekt_dir:
        print(f"Projekt: {projekt or 'bez .skill_verze'}")
    print(f"GitHub (nejnovější vydání): {gh or 'nezjištěno (bez sítě nebo GitHub neodpověděl)'}")

    s, p, g = cislo(skill), cislo(projekt), cislo(gh)
    novy_projekt = os.path.join(skill_dir, "tools", "novy_projekt.py")
    if g and s and g > s:
        print(f"→ NOVA_VERZE_SKILLU: vyšla verze {gh}, nainstalovaný skill je {skill}. Řekni to uživateli jednou větou\n"
              f"  a poraď, jak skill aktualizovat – {jak_aktualizovat(skill_dir)}. Projekt aktualizuj až z nového skillu.")
    elif projekt_dir and p and s and p > s:
        print(f"→ PROJEKT_NOVEJSI: projekt je z verze {projekt}, nainstalovaný skill je starší ({skill}). Projekt\n"
              "  neaktualizuj (vrátil bys ho ke starší verzi); ať uživatel aktualizuje skill (README, část Instalace).")
    elif projekt_dir and s and (not p or s > p):
        print(f"→ AKTUALIZUJ_PROJEKT: skill {skill} je novější než projekt. Nabídni aktualizaci projektu (data zůstanou):\n"
              f"  python3 -I {novy_projekt} <složka projektu>   (projekt bez web/ s --bez-webu), pak ve web/ npm ci")
    elif not s:
        print("→ SKILL_NEZJISTEN: nainstalovaný skill jsem nenašel, verzi skillu neporovnávám. Spusť kontrolu ze složky\n"
              "  skillu: python3 -I SKILL_DIR/tools/verze.py <složka projektu>")
    else:
        print("→ AKTUALNI")


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
