#!/usr/bin/env python3
"""Souhlas uživatele s podmínkami portálů s citlivými údaji o obětech (obeti.py).

Databáze obětí žádá při vstupu o potvrzení podmínek (osobní odpovědnost za nakládání s údaji). Nástroj prohlížeč nemá,
takže by potvrzení přeskočil. Proto bez zapsaného souhlasu nic nestahuje a skončí s kódem 4. Souhlas zapíše jen
uživatel sám: příkaz `souhlas` nástroje ukáže znění a chce odpověď „ano“ napsanou ručně v terminálu. Claude ho
nespouští a nepotvrzuje za uživatele (v běžném terminálu; `!` v Claude Code nemá vstup z klávesnice, tam nejde). Jde o pojistku proti
nedopatření, ne o technickou ochranu: že Claude souhlas nepotvrzuje, drží pravidlo, ne kód.

Souhlas platí 30 dní na tomto počítači a jen pro dané znění podmínek (změní-li se, zeptá se znovu).
Stav ve ~/.cache/dejiny-domu/souhlas/<portál>.json (jinde: proměnná SOUHLAS_STAV).
  python3 -I tools/souhlas.py stav   -> které souhlasy platí a do kdy

Převzato a upraveno z rodokmen-plus (licence MIT, © srameko):
  https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/souhlas.py
"""
import hashlib, json, os, sys, time
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

PLATNOST = 30 * 24 * 3600
KOD = 4


def slozka():
    return os.environ.get("SOUHLAS_STAV") or os.path.join(os.path.expanduser("~"), ".cache", "dejiny-domu", "souhlas")


def otisk(zneni):
    return hashlib.sha256(zneni.encode("utf-8")).hexdigest()[:16]


def ma_souhlas(klic, zneni):
    try:
        with open(os.path.join(slozka(), klic + ".json"), encoding="utf-8") as fh:
            d = json.load(fh)
        return d.get("otisk") == otisk(zneni) and -300 < time.time() - float(d.get("cas", 0)) < PLATNOST
    except (OSError, ValueError, TypeError):
        return False


def vyzaduj(klic, nazev, zneni, prikaz):
    """Skončí (kód 4), pokud uživatel souhlas nezapsal. `prikaz` = jak ho zapsat (např. „tools/obeti.py souhlas“)."""
    if ma_souhlas(klic, zneni):
        return
    sys.stderr.write(
        f"{nazev} žádá při vstupu o souhlas s podmínkami (citlivé údaje o obětech). Nástroj bez něj nic nestahuje.\n"
        f"Souhlas potvrdí uživatel sám: v běžném terminálu v kořeni projektu `python3 -I {prikaz}` (ne přes `!` v Claude Code),\n"
        "přečte znění a ručně odpoví „ano“. Claude souhlas nikdy nepotvrzuje za uživatele.\n")
    sys.exit(KOD)


def potvrd(klic, nazev, zneni, url, prikaz):
    """Ukáže znění a zapíše souhlas, jen když uživatel v terminálu ručně odpoví „ano“."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        sys.stderr.write("Souhlas jde zapsat jen v terminálu, kam píše uživatel. Spusť příkaz sám "
                         f"v běžném terminálu (`!` v Claude Code nemá vstup z klávesnice); Claude ho nesmí potvrdit za tebe.\n")
        sys.exit(KOD)
    print(f"{nazev} – podmínky vstupu:\n\n{zneni}\n\nPodmínky a pravidla: {url}\n")
    if input("Souhlasíš a přebíráš odpovědnost za nakládání s těmito údaji? Napiš „ano“: ").strip().lower() != "ano":
        print("Souhlas nezapsán.")
        sys.exit(KOD)
    os.makedirs(slozka(), exist_ok=True)
    cil = os.path.join(slozka(), klic + ".json")
    with open(cil + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"portal": nazev, "cas": time.time(), "datum": time.strftime("%Y-%m-%d"), "otisk": otisk(zneni)}, fh)
    os.replace(cil + ".tmp", cil)
    print(f"Souhlas zapsán (platí 30 dní na tomto počítači): {cil}")


def main(a):
    if a != ["stav"]:
        sys.exit("Použití: souhlas.py stav   (zapsat souhlas: python3 -I tools/<nástroj>.py souhlas – jen uživatel sám)")
    try:
        soubory = sorted(f for f in os.listdir(slozka()) if f.endswith(".json"))
    except OSError:
        soubory = []
    if not soubory:
        print("Žádný souhlas není zapsaný.")
    for f in soubory:
        try:
            with open(os.path.join(slozka(), f), encoding="utf-8") as fh:
                d = json.load(fh)
            do = time.strftime("%Y-%m-%d", time.localtime(float(d["cas"]) + PLATNOST))
            print(f"{f[:-5]}: {d.get('portal', '?')} – potvrzeno {d.get('datum', '?')}, platí do {do}")
        except (OSError, ValueError, KeyError, TypeError):
            print(f"{f[:-5]}: nečitelný záznam")


if __name__ == "__main__":
    main(sys.argv[1:])
