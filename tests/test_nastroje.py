"""Testy nástrojů, které sahají na data uživatele: zapis.py, kontrola.py, export_web.py (a novy_projekt.py).

Spuštění z kořene repa:  python3 -m unittest discover tests
Bez sítě a bez závislostí (jen standardní knihovna). Každý test si založí projekt ze šablony skillu v dočasné
složce a pracuje se smyšlenými daty (Horní Lhota).
"""
import json, os, re, shutil, subprocess, sys, tempfile, time, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu")
# nejmenší platný JPEG (1×1 px) – export ho jen kopíruje, rozměry nezjišťuje
JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c"
    "20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100ffc4001f00000105010101010101000000"
    "00000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1"
    "082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a7374"
    "75767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1"
    "e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbd3ffd9")

DOMY = '''
OBEC = dict(nazev="Horní Lhota", jine_nazvy="Ober-Lhotta", obec="Horní Lhota, okres Pelhřimov",
            farnost="Dolní Lhota", panstvi="Kamenice", popis="Ves na kopci.", lat=49.4, lon=15.2)
OBEC_UDALOSTI = [
    dict(rok="1352", text="První zmínka o vsi.", st="lit", zdroj="vlastivěda, s. 12"),
]
D = {
    "12": dict(nazev="U Nováků", druh="chalupa", st="doc", popis="Chalupa u návsi.", lat=49.41, lon=15.21,
               udalosti=[dict(rok="1890", text="Sčítání lidu: 7 osob.", st="doc", r=["lhota_scitani_cp12_1890"])],
               drzitele=[dict(od="1820", do="1850", n="Josef Novák", st="doc", r=["lhota_scitani_cp12_1890"]),
                         dict(od="?", do="1820", n="Jan Novák", st="fam"),
                         dict(od="1786", do="1800", n="Matěj Dvořák", st="lit", zdroj="kronika, s. 3")],
               obyvatele=[dict(n="Josef Novák", y="1795–1860", role="hospodář", st="doc", r=["lhota_scitani_cp12_1890"])]),
}
ISSUES = [("Kdo byl držitel před 1786?", "Otevřené: gruntovní kniha není online.")]
'''

ZAZNAM = {"klic": "lhota_scitani_cp12_1890", "druh": "S", "datum": "1890", "nazev": "Sčítání lidu 1890, čp. 12",
          "shrnuti": "Domácnost Josefa Nováka, 7 osob.", "svazek": "trebon_4250", "snimek": "5",
          "odkaz": "https://digi.ceskearchivy.cz/4250/5"}
SVAZEK = {"archiv": "SOA Třeboň", "portal": "digi.ceskearchivy.cz", "svazek": "Sčítání lidu 1890",
          "popis": "Horní Lhota", "snimku": 40, "url": "https://digi.ceskearchivy.cz/4250"}


class Projekt(unittest.TestCase):
    """Nový projekt ze šablony v dočasné složce; pomocné funkce na spouštění nástrojů a čtení dat."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="dejiny_test_")
        self.root = os.path.join(self.tmp, "Horni-Lhota-12")
        p = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), self.root],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def path(self, *p):
        return os.path.join(self.root, *p)

    def nastroj(self, nazev, *args, vstup=None):
        return subprocess.run([sys.executable, "-I", "-X", "utf8", self.path("tools", nazev), *args], cwd=self.root,
                              input=vstup, capture_output=True, text=True, encoding="utf-8")

    def zapis(self, soubor, klic, obj, *volby):
        vstup = self.path("pracovni", "vstup.json")
        with open(vstup, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return self.nastroj("zapis.py", soubor, klic, vstup, *volby)

    def text(self, *p):
        with open(self.path(*p), encoding="utf-8", newline="") as f:
            return f.read()

    def data(self, soubor):
        return json.loads(self.text("data", soubor + ".json"))

    def napln(self):
        """Malý úplný projekt: jeden dům, jeden zápis se svazkem, výřezem, rámečkem a přepisem."""
        with open(self.path("data", "domy.py"), "w", encoding="utf-8") as f:
            f.write(DOMY)
        for args in (("zaznamy", ZAZNAM["klic"], ZAZNAM), ("svazky", "trebon_4250", SVAZEK),
                     ("prepisy", ZAZNAM["klic"], {"orig": "Novak Josef", "cs": "Novák Josef"}),
                     ("zvyrazneni", ZAZNAM["klic"], {"boxes": [[0.1, 0.1, 0.9, 0.5]]})):
            p = self.zapis(*args)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for d in ("vyrezy", "zdroje"):
            with open(self.path(d, ZAZNAM["klic"] + ".jpg"), "wb") as f:
                f.write(JPEG)


class TestZapis(Projekt):

    def test_pridani_do_prazdneho_seznamu(self):
        p = self.zapis("zaznamy", "a_1", {"druh": "N", "nazev": "Křest Jana Nováka"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("přidáno", p.stdout)
        self.assertEqual(self.data("zaznamy"), [{"druh": "N", "nazev": "Křest Jana Nováka", "klic": "a_1"}])

    def test_format_ceske_znaky_a_lf(self):
        self.zapis("zaznamy", "a_1", {"nazev": "Křest Jana Nováka"})
        t = self.text("data", "zaznamy.json")
        self.assertIn("Křest", t)            # ne Ř
        self.assertNotIn("\r\n", t)
        self.assertTrue(t.endswith("\n"))

    def test_nahrazeni_meni_jen_tu_polozku(self):
        self.zapis("zaznamy", "a_1", {"nazev": "první"})
        self.zapis("zaznamy", "a_2", {"nazev": "druhá"})
        pred = self.text("data", "zaznamy.json")
        p = self.zapis("zaznamy", "a_1", {"nazev": "první opravená"})
        self.assertIn("změněno", p.stdout)
        po = self.text("data", "zaznamy.json")
        self.assertEqual([z["nazev"] for z in self.data("zaznamy")], ["první opravená", "druhá"])
        zmenene = [(a, b) for a, b in zip(pred.splitlines(), po.splitlines()) if a != b]
        self.assertEqual(len(pred.splitlines()), len(po.splitlines()))
        self.assertEqual(len(zmenene), 1, zmenene)   # zbytek souboru doslova stejný

    def test_bez_sloucit_nahradi_celou_polozku(self):
        self.zapis("zaznamy", "a_1", {"nazev": "x", "datum": "1890"})
        self.zapis("zaznamy", "a_1", {"nazev": "y"})
        self.assertNotIn("datum", self.data("zaznamy")[0])

    def test_sloucit_doplni_pole(self):
        self.zapis("zaznamy", "a_1", {"nazev": "x", "datum": "1890"})
        self.zapis("zaznamy", "a_1", {"shrnuti": "doplněno"}, "--sloucit")
        self.assertEqual(self.data("zaznamy")[0], {"nazev": "x", "datum": "1890", "klic": "a_1", "shrnuti": "doplněno"})

    def test_slovnik_pridani_a_nahrazeni(self):
        self.zapis("svazky", "trebon_1", {"svazek": "A"})
        self.zapis("svazky", "trebon_2", {"svazek": "B"})
        self.zapis("svazky", "trebon_1", {"svazek": "A2"})
        self.assertEqual(self.data("svazky"), {"trebon_1": {"svazek": "A2"}, "trebon_2": {"svazek": "B"}})
        self.assertEqual(list(self.data("svazky")), ["trebon_1", "trebon_2"])   # pořadí zůstane

    def test_web_textova_hodnota_ze_vstupu(self):
        p = self.nastroj("zapis.py", "web", "nazev", "-", vstup='"Dějiny Horní Lhoty"')
        self.assertEqual(p.returncode, 0, p.stderr)
        web = self.data("web")
        self.assertEqual(web["nazev"], "Dějiny Horní Lhoty")
        self.assertIn("prihlaseni", web)   # ostatní nastavení zůstalo

    def test_jinde_nez_web_musi_byt_objekt(self):
        p = self.nastroj("zapis.py", "svazky", "x", "-", vstup='"text"')
        self.assertNotEqual(p.returncode, 0)

    def test_spatny_json_nezmeni_soubor(self):
        self.zapis("zaznamy", "a_1", {"nazev": "x"})
        pred = self.text("data", "zaznamy.json")
        p = self.nastroj("zapis.py", "zaznamy", "a_1", "-", vstup='{"nazev": ')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("není platný JSON", p.stdout + p.stderr)
        self.assertEqual(self.text("data", "zaznamy.json"), pred)

    def test_rozbity_soubor_dat_neprepise(self):
        with open(self.path("data", "zaznamy.json"), "w", encoding="utf-8") as f:
            f.write('[{"klic": "a_1",')
        p = self.zapis("zaznamy", "a_2", {"nazev": "y"})
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.text("data", "zaznamy.json"), '[{"klic": "a_1",')

    def test_klic_nesouhlasi_se_vstupem(self):
        p = self.zapis("zaznamy", "a_1", {"klic": "a_2"})
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.data("zaznamy"), [])

    def test_neznamy_soubor(self):
        p = self.zapis("domy", "12", {})
        self.assertNotEqual(p.returncode, 0)

    def test_odmitne_bezet_ze_slozky_skillu(self):
        p = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "zapis.py"), "svazky", "x", "-"],
                           input="{}", capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("není složka projektu", p.stdout + p.stderr)
        self.assertFalse(os.path.exists(os.path.join(SKILL, "data")))


class TestSoubeh(Projekt):
    """Souběžní pomocníci: zámek v zapis.py a nástroje, které do data/ zapisují přes něj."""

    def py(self, kod, cekat=True):
        cmd = [sys.executable, "-I", "-X", "utf8", "-c", "import sys; sys.path.insert(0, 'tools')\n" + kod]
        if not cekat:
            return subprocess.Popen(cmd, cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, encoding="utf-8")

    def test_zapis_pocka_na_zamek_a_cizi_zmenu_neprepise(self):
        drzi = self.py("import zapis, time\nwith zapis.zamek('svazky'):\n    print('mam', flush=True)\n    time.sleep(1)\n"
                       "    zapis.zamek = lambda n: __import__('contextlib').nullcontext()\n"
                       "    zapis.zapis('svazky', 'prvni', {'svazek': 'A'})", cekat=False)
        self.assertEqual(drzi.stdout.readline().strip(), "mam")
        druhy = subprocess.Popen([sys.executable, "-I", self.path("tools", "zapis.py"), "svazky", "druhy", "-"], cwd=self.root,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        druhy.stdin.write(b'{"svazek": "B"}')
        druhy.stdin.close()
        time.sleep(0.4)
        self.assertIsNone(druhy.poll(), "zapis.py nečekal na zámek")
        self.assertEqual(drzi.wait(), 0, drzi.stderr.read())
        self.assertEqual(druhy.wait(), 0, druhy.stderr.read())
        self.assertEqual(sorted(self.data("svazky")), ["druhy", "prvni"])

    def test_drzeny_zamek_skonci_hlaskou(self):
        drzi = self.py("import zapis, time\nwith zapis.zamek('svazky'):\n    print('mam', flush=True)\n    time.sleep(5)",
                       cekat=False)
        self.assertEqual(drzi.stdout.readline().strip(), "mam")
        p = self.py("import zapis; zapis.CEKANI_NA_ZAMEK = 0.3; zapis.zapis('svazky', 's1', {})")
        drzi.kill()
        drzi.communicate()
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("zapisuje jiný proces", p.stderr)

    def test_svazek_z_nastroje_necha_ostatni_svazky_doslova(self):
        with open(self.path("data", "svazky.json"), "w", encoding="utf-8") as f:
            f.write('{"rucni": {"svazek": "Gruntovní kniha", "popis": "zapsal uživatel"}}\n')
        p = self.py("import ebadatelna; ebadatelna.zapis_svazek('ebad_1', {'svazek': 'Matrika N 1800–1850'})")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(self.text("data", "svazky.json").startswith('{"rucni": {"svazek": "Gruntovní kniha", "popis": "zapsal uživatel"}'))
        self.assertEqual(self.data("svazky")["ebad_1"], {"svazek": "Matrika N 1800–1850"})

    def test_neplatny_unicode_odmitne_bez_zmeny_souboru(self):
        self.zapis("svazky", "a", {"svazek": "Gruntovní kniha"})
        pred = self.text("data", "svazky.json")
        vstup = self.path("pracovni", "vstup.json")
        with open(vstup, "w", encoding="utf-8") as f:
            f.write('{"svazek": "Grunt\\ud800"}')   # osamělá polovina páru UTF-16
        p = self.nastroj("zapis.py", "svazky", "a", vstup)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("neplatný znak", p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        self.assertEqual(self.text("data", "svazky.json"), pred)

    def test_mista_zapise_jen_zmenene_misto(self):
        self.zapis("mista", "Kaple", {"lat": 49.1, "lon": 15.1, "popis": "barokní"})
        p = self.py("import mista; mista.geocode = lambda q: (49.2, 15.2, 'osm/1')\n"
                    "sys.argv = ['mista.py', 'pridej', 'Mlýn']; mista.main()")
        self.assertEqual(p.returncode, 0, p.stderr)
        d = self.data("mista")
        self.assertEqual(d["Kaple"], {"lat": 49.1, "lon": 15.1, "popis": "barokní"})
        self.assertEqual((d["Mlýn"]["lat"], d["Mlýn"]["osm"]), (49.2, "osm/1"))


class TestKontrola(Projekt):

    def kontrola(self):
        p = self.nastroj("kontrola.py")
        return p.returncode, p.stdout + p.stderr

    def test_prazdna_sablona_bez_chyb(self):
        rc, out = self.kontrola()
        self.assertEqual(rc, 0, out)
        self.assertNotIn("CHYBA", out)

    def test_uplny_projekt_bez_chyb(self):
        self.napln()
        rc, out = self.kontrola()
        self.assertEqual(rc, 0, out)
        self.assertIn("1 domů", out)
        self.assertIn("1 zápisů", out)
        self.assertNotIn(f"zápis {ZAZNAM['klic']}:", out)   # zápis má všechno (výřez, rámeček, přepis, citaci)

    def test_citace_neexistujiciho_zapisu(self):
        self.napln()
        with open(self.path("data", "domy.py"), "a", encoding="utf-8") as f:
            f.write('D["12"]["udalosti"].append(dict(rok="1900", text="x", st="doc", r=["neni_takovy"]))\n')
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("cituje neexistující zápis 'neni_takovy'", out)

    def test_duplicitni_klic_zapisu(self):
        with open(self.path("data", "zaznamy.json"), "w", encoding="utf-8") as f:
            json.dump([{"klic": "a", "druh": "N", "datum": "1", "nazev": "x", "shrnuti": "y"}] * 2, f)
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("zápisy se stejným klíčem", out)

    def test_neznamy_stav_a_druh(self):
        self.napln()
        with open(self.path("data", "domy.py"), "a", encoding="utf-8") as f:
            f.write('D["12"]["drzitele"][0]["st"] = "jiste"\n')
        self.zapis("zaznamy", ZAZNAM["klic"], {"druh": "X"}, "--sloucit")
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("neznámý stav 'jiste'", out)
        self.assertIn("neznámý druh 'X'", out)

    def test_svazek_chybi_v_svazky(self):
        self.napln()
        self.zapis("zaznamy", ZAZNAM["klic"], {"svazek": "trebon_9999"}, "--sloucit")
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("svazek 'trebon_9999' není v data/svazky.json", out)

    def test_hlavni_dum_neexistuje(self):
        self.napln()
        self.nastroj("zapis.py", "web", "hlavni_dum", "-", vstup='"99"')
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("hlavni_dum '99' není v domy.py", out)

    def test_cislo_domu_jako_cislo(self):
        with open(self.path("data", "domy.py"), "w", encoding="utf-8") as f:
            f.write("D = {12: dict(st='doc')}\n")
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("číslo popisné piš jako text", out)

    def test_soukromi_zijici_lide(self):
        self.napln()
        with open(self.path("data", "domy.py"), "a", encoding="utf-8") as f:
            f.write('D["12"]["obyvatele"].append(dict(n="Eva Nová", y="1990", f=["* 1990 Horní Lhota 12"], st="fam"))\n')
        rc, out = self.kontrola()
        self.assertIn("SOUKROMÍ", out)

    def test_nebezpecny_odkaz_mista(self):
        with open(self.path("data", "mista.json"), "w", encoding="utf-8") as f:
            json.dump({"Kaple": {"lat": 49.4, "lon": 15.2, "odkaz": "javascript:void(0)"},
                       "Mlýn": {"lat": 49.4, "lon": 15.2, "odkaz": "https://cs.wikipedia.org/wiki/Ml%C3%BDn"}}, f)
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("místo Kaple: odkaz", out)
        self.assertNotIn("místo Mlýn", out)

    def test_poloha_bez_lon(self):
        self.napln()
        with open(self.path("data", "domy.py"), "a", encoding="utf-8") as f:
            f.write('del D["12"]["lon"]\nOBEC["lat"] = "49,4"\n')
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("dům 12: má jen lat", out)
        self.assertIn("OBEC: lat '49,4' není číslo", out)

    def test_kolize_adres_domu(self):
        with open(self.path("data", "domy.py"), "w", encoding="utf-8") as f:
            f.write("D = {'12a': dict(st='doc'), '12á': dict(st='doc')}\n")
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("stejná adresa stránky /dum/12a/", out)

    def test_nemozne_datum_a_obraceny_interval(self):
        self.napln()
        with open(self.path("data", "domy.py"), "a", encoding="utf-8") as f:
            f.write('D["12"]["drzitele"].append(dict(od="1900", do="1800", n="Petr Nový", st="fam"))\n'
                    'D["12"]["udalosti"].append(dict(rok="31. 2. 1900", text="Požár.", st="fam"))\n'
                    'D["12"]["drzitele"].append(dict(od="asi 1900", do="1800", n="Nejistý", st="fam"))\n'
                    'D["12"]["obyvatele"].append(dict(n="Anna Nová", y="1860–1795", st="fam"))\n')
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("držitel Petr Nový: 'od' 1900 je po 'do' 1800", out)
        self.assertIn("datum 31. 2. 1900 v kalendáři není", out)
        self.assertIn("obyvatel Anna Nová: roky 1860–1795 jsou pozpátku", out)
        self.assertNotIn("Nejistý: 'od'", out)   # nejistou mez nechá být

    def test_odpoved_jen_z_jinych_pisem(self):
        self.nastroj("zapis.py", "web", "prihlaseni", "-", vstup='{"otazka": "Heslo?", "odpoved": "漢字"}')
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("nemá žádné písmeno a–z ani číslici", out)

    def test_jistota_cteni_a_domu(self):
        self.napln()
        with open(self.path("data", "domy.py"), "a", encoding="utf-8") as f:
            f.write('D["12"]["drzitele"][0].update(cteni="nejiste", dum="nejiste")\n'
                    'D["12"]["obyvatele"][0]["cteni"] = "asi"\n')
        rc, out = self.kontrola()
        self.assertEqual(rc, 1)
        self.assertIn("obyvatel Josef Novák: pole 'cteni' smí být jen \"nejiste\"", out)
        self.assertIn("držitel Josef Novák: dum=\"nejiste\" bez 'note'", out)

    def test_rodinny_dokument_bez_odkazu(self):
        self.napln()
        self.zapis("svazky", "rodina", {"archiv": "u rodiny Novákových", "svazek": "Kupní smlouva 1923", "soukrome": True})
        self.zapis("zaznamy", "lhota_smlouva_cp12_1923", {"druh": "J", "datum": "1923", "nazev": "Kupní smlouva",
                                                          "shrnuti": "Prodej domu.", "svazek": "rodina"})
        rc, out = self.kontrola()
        self.assertNotIn("lhota_smlouva_cp12_1923: chybí odkaz", out)

    def test_rozbity_domy_py(self):
        with open(self.path("data", "domy.py"), "w", encoding="utf-8") as f:
            f.write("D = {\n")
        rc, out = self.kontrola()
        self.assertNotEqual(rc, 0)
        self.assertIn("domy.py nejde načíst", out)


class TestExport(Projekt):

    def export(self, *args):
        p = self.nastroj("export_web.py", *args)
        return p.returncode, p.stdout + p.stderr

    def site(self):
        return json.loads(self.text("web", "src", "data", "site.json"))

    def test_prazdna_sablona(self):
        rc, out = self.export()
        self.assertEqual(rc, 0, out)
        s = self.site()
        self.assertEqual(s["houses"], {})
        self.assertIsNone(s["mainHouse"])

    def test_klic_mimo_vyrezy_export_odmitne_a_nic_nezverejni(self):
        with open(self.path("soukromy.jpg"), "wb") as f:   # vedle vyrezy/: ../soukromy by vedl sem
            f.write(JPEG)
        with open(self.path("data", "zaznamy.json"), "w", encoding="utf-8") as f:
            json.dump([{"klic": "../soukromy", "nazev": "podvržený"}], f)
        rc, out = self.export()
        self.assertNotEqual(rc, 0)
        self.assertIn("data/zaznamy.json", out)
        verejne = [f for _, _, soubory in os.walk(self.path("web", "public")) for f in soubory]
        self.assertNotIn("soukromy.jpg", verejne)

    def test_obrazek_pribehu_mimo_vyrezy_export_odmitne(self):
        with open(self.path("data", "pribeh_mlyn.md"), "w", encoding="utf-8") as f:
            f.write("---\ntitle: Mlýn\nobrazek: ../../soukromy\n---\nText.\n")
        rc, out = self.export()
        self.assertNotEqual(rc, 0)
        self.assertIn("pribeh_*.md obrazek", out)

    def test_nebezpecny_odkaz_export_odmitne(self):
        with open(self.path("data", "mista.json"), "w", encoding="utf-8") as f:
            json.dump({"Kaple": {"lat": 49.4, "lon": 15.2, "odkaz": " JavaScript:alert(1)"}}, f)
        rc, out = self.export()
        self.assertNotEqual(rc, 0)
        self.assertIn("data/mista.json Kaple", out)

    def test_misto_bez_lon_export_odmitne_srozumitelne(self):
        with open(self.path("data", "mista.json"), "w", encoding="utf-8") as f:
            json.dump({"Kaple": {"lat": 49.4}}, f)
        rc, out = self.export()
        self.assertNotEqual(rc, 0)
        self.assertNotIn("KeyError", out)
        self.assertIn("Kaple: má jen lat", out)

    def test_kolize_adres_domu_export_odmitne(self):
        with open(self.path("data", "domy.py"), "w", encoding="utf-8") as f:
            f.write("D = {'12a': dict(st='doc'), '12á': dict(st='doc')}\n")
        rc, out = self.export()
        self.assertNotEqual(rc, 0)
        self.assertIn("/dum/12a/", out)

    def test_odpoved_jen_z_jinych_pisem_export_odmitne(self):
        self.nastroj("zapis.py", "web", "prihlaseni", "-", vstup='{"otazka": "Heslo?", "odpoved": "漢字"}')
        rc, out = self.export()
        self.assertNotEqual(rc, 0)
        self.assertIn("prihlaseni.odpoved", out)

    def test_vyhrady_jistoty_na_webu(self):
        self.napln()
        with open(self.path("data", "domy.py"), "a", encoding="utf-8") as f:
            f.write('D["12"]["drzitele"][0].update(cteni="nejiste", dum="nejiste", note="jen jméno a doba")\n')
        rc, out = self.export()
        self.assertEqual(rc, 0, out)
        majitele = {o["name"]: o["caveats"] for o in self.site()["houses"]["12"]["owners"]}
        self.assertEqual(majitele["Josef Novák"], ["nejisté čtení", "k domu přiřazeno nejistě"])
        self.assertEqual(majitele["Jan Novák"], [])

    def test_uplny_projekt(self):
        self.napln()
        rc, out = self.export()
        self.assertEqual(rc, 0, out)
        s = self.site()
        self.assertEqual(s["village"]["name"], "Horní Lhota")
        dum = s["houses"]["12"]
        self.assertEqual(dum["name"], "U Nováků")
        self.assertEqual(s["mainHouse"], "12")   # bez hlavni_dum první dům
        self.assertEqual([o["name"] for o in dum["owners"]], ["Matěj Dvořák", "Jan Novák", "Josef Novák"])
        self.assertEqual(dum["records"], [ZAZNAM["klic"]])
        r = s["records"][0]
        self.assertEqual((r["houses"], r["cs"], r["volume"], r["img"]), (["12"], "Novák Josef", "Sčítání lidu 1890", True))
        self.assertEqual(s["stats"]["oldest"], 1352)
        self.assertEqual(s["issues"][0]["title"], "Kdo byl držitel před 1786?")
        self.assertTrue(os.path.exists(self.path("web", "public", "img", ZAZNAM["klic"] + ".jpg")))
        self.assertTrue(os.path.exists(self.path("web", "public", "zdroje", ZAZNAM["klic"] + ".jpg")))

    def test_skryty_a_smazany_obrazek_zmizi_z_webu(self):
        self.napln()
        with open(self.path("vyrezy", "lhota_foto.jpg"), "wb") as f:
            f.write(JPEG)
        p = self.zapis("dokumenty", "lhota_foto", {"img": "lhota_foto", "popis": "Chalupa 1930", "domy": ["12"]})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        rc, out = self.export()
        self.assertEqual(rc, 0, out)
        foto = self.path("web", "public", "img", "lhota_foto.jpg")
        self.assertTrue(os.path.exists(foto))
        dok = self.data("dokumenty")
        dok[0]["skryt"] = True
        with open(self.path("data", "dokumenty.json"), "w", encoding="utf-8") as f:
            json.dump(dok, f, ensure_ascii=False)
        os.remove(self.path("zdroje", ZAZNAM["klic"] + ".jpg"))
        rc, out = self.export()
        self.assertEqual(rc, 0, out)
        self.assertIn("odebráno 2", out)
        self.assertFalse(os.path.exists(foto))
        self.assertFalse(os.path.exists(self.path("web", "public", "zdroje", ZAZNAM["klic"] + ".jpg")))
        self.assertTrue(os.path.exists(self.path("web", "public", "img", ZAZNAM["klic"] + ".jpg")))

    def test_odpoved_prihlaseni_neni_na_webu(self):
        self.nastroj("zapis.py", "web", "prihlaseni", "-",
                     vstup='{"uvod": "Jen pro známé.", "otazka": "Jak se říká chalupě?", "odpoved": "U Nováků"}')
        rc, out = self.export()
        self.assertEqual(rc, 0, out)
        self.assertIn("přihlášení zapnuté", out)
        self.assertNotIn("prihlaseni", self.site()["config"])
        for f in (("web", "src", "data", "site.json"), ("web", "public", "prihlaseni.html"), ("web", "nginx.conf"),
                  ("web", "netlify", "edge-functions", "brana.js")):
            self.assertNotIn("Nováků", self.text(*f), f)   # odpověď jen jako otisk
        self.assertIn("Jak se říká chalupě?", self.text("web", "public", "prihlaseni.html"))
        nginx = self.text("web", "nginx.conf")
        self.assertEqual(nginx.count("default 0;"), 1)
        self.assertIn("map_hash_bucket_size 128;", nginx)   # 64znakový otisk se do výchozí velikosti nevejde

    def test_bez_odpovedi_otevreny_web_a_nasazeni_odmitne(self):
        rc, out = self.export()
        self.assertIn("VYPNUTÉ", out)
        self.assertFalse(os.path.exists(self.path("web", "netlify", "edge-functions", "brana.js")))
        self.assertEqual(self.text("web", "nginx.conf").count("default"), 1)   # dvě default nginx nespustí
        rc, out = self.export("--nasazeni")
        self.assertNotEqual(rc, 0)
        self.assertIn("web by byl otevřený", out)

    def test_nefunkcni_odkaz(self):
        self.napln()
        with open(self.path("data", "zajimavosti.md"), "a", encoding="utf-8") as f:
            f.write("\nViz [dům 99](/dum/99/) a [sčítání](/zdroj/lhota_scitani_cp12_1890/).\n")
        rc, out = self.export()
        self.assertIn("nefunkční odkaz /dum/99/", out)
        self.assertNotIn("/zdroj/lhota_scitani_cp12_1890/", out)

    def test_pribehy_a_poznamky_pro_clauda(self):
        with open(self.path("data", "pribeh_mlyn.md"), "w", encoding="utf-8") as f:
            f.write("---\ntitle: Mlýn\nporadi: 2\n---\nText <!-- jen pro Clauda -->příběhu.\n")
        rc, out = self.export()
        self.assertEqual(rc, 0, out)
        s = self.site()
        self.assertTrue(s["config"]["maPribeh"])
        self.assertEqual(s["config"]["dalsiPribehy"][0]["title"], "Mlýn")
        pribeh = self.text("web", "src", "generated", "pribehy", "mlyn.md")
        self.assertNotIn("jen pro Clauda", pribeh)


class TestDnnt(Projekt):
    """dnnt.py bez sítě: Kramerius NK i Česká digitální knihovna (CDK) jsou nahrazené."""

    NK = [dict(PID="uuid:dnnt-shoda", root_title="Adresář Brna", datum_str="1932", details=["48 ##NormalPage"],
               dostupnost="private", dnnt=True),
          dict(PID="uuid:dnnt-jen-nk", root_title="Adresář Brna", datum_str="1933", details=["50 ##NormalPage"],
               dostupnost="private", dnnt=True)]
    CDK = [{"pid": "uuid:mzk-kopie", "root.title": "Adresář Brna", "date.str": "1932", "page.number": "48",
            "cdk.collection": ["mzk"]},
           {"pid": "uuid:vkol-navic", "root.title": "Svoboda", "date.str": "1936", "page.number": "7",
            "cdk.collection": ["vkol"]}]

    def py(self, kod):
        p = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", "import sys; sys.path.insert(0, 'tools'); import dnnt\n" + kod],
                           cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout

    def test_hledej_najde_verejnou_kopii_a_zbytek_da_do_cteciho_listu(self):
        out = self.py(f"""
def solr(params, api=dnnt.API):
    if api == dnnt.CDK:
        assert "accessibility:public" in params["q"] and "model:page" in params["q"], params["q"]
        return {{"response": {{"numFound": 2, "docs": {self.CDK!r}}}}}
    return {{"response": {{"numFound": 2, "docs": {self.NK!r}}},
            "highlighting": {{"uuid:dnnt-jen-nk": {{"text_ocr": ["<script>x</script> <em>Dlouhá</em> 14"]}}}}}}
dnnt.solr = solr
dnnt.hledej(['text_ocr:"Dlouhá 14"', "--ulozit", "dl14"])
""")
        self.assertIn("1 neveřejných stránek NK, 1 nálezů navíc", out)
        tsv = self.text("pracovni", "dnnt", "dl14.tsv")
        self.assertIn("uuid:dnnt-shoda\t1932\t48\tDNNT\tAdresář Brna\tuuid:mzk-kopie\tmzk", tsv)
        self.assertIn("uuid:vkol-navic\t1936\t7\tpublic\tSvoboda\tuuid:vkol-navic\tvkol", tsv)
        lst = self.text("pracovni", "dnnt", "dl14.html")
        self.assertIn('href="https://ndk.cz/uuid/uuid:dnnt-jen-nk"', lst)
        self.assertNotIn("dnnt-shoda", lst)   # veřejnou kopii přečte nástroj, uživatel ji číst nemusí
        self.assertIn("&lt;script&gt;", lst)

    def test_bez_neverejnych_stranek_smaze_stary_cteci_list(self):
        os.makedirs(self.path("pracovni", "dnnt"), exist_ok=True)
        with open(self.path("pracovni", "dnnt", "dl14.html"), "w", encoding="utf-8") as f:
            f.write("starý list")
        self.py('dnnt.uloz("dl14", [dict(pid="uuid:a", datum="1930", strana="1", pristup="public", titul="T", '
                'verejne="", knihovna="", uryvky=[])])')
        self.assertFalse(os.path.exists(self.path("pracovni", "dnnt", "dl14.html")))

    def test_ocr_cte_verejnou_kopii_z_cdk_a_po_chybe_nenecha_prazdny_soubor(self):
        os.makedirs(self.path("pracovni", "dnnt"), exist_ok=True)
        with open(self.path("pracovni", "dnnt", "s.tsv"), "w", encoding="utf-8") as f:
            f.write("pid\tdatum\tstrana\tpristup\ttitul\tverejne\tknihovna\n"
                    "uuid:dnnt-shoda\t1932\t48\tDNNT\tAdresář Brna\tuuid:mzk-kopie\tmzk\n"
                    "uuid:dnnt-jen-nk\t1933\t50\tDNNT\tAdresář Brna\t\t\n")
        kod = """
import urllib.error
def get(url):
    if "dnnt-jen-nk" in url:
        raise urllib.error.HTTPError(url, 403, "zakázáno", {}, None)
    print("URL", url)
    return b"text"
dnnt.get = get
dnnt.ocr(["pracovni/dnnt/s.tsv"])
"""
        out = self.py(kod)
        self.assertIn("URL " + "https://api.ceskadigitalniknihovna.cz/search/api/client/v7.0/items/uuid:mzk-kopie/ocr/text", out)
        self.assertIn("neveřejných 1", out)
        self.assertEqual(sorted(os.listdir(self.path("pracovni", "dnnt", "ocr"))), ["1932_48_dnnt_sho.txt"])

    def test_ocr_nezapise_mimo_slozku_ani_nepouzije_divny_pid(self):
        os.makedirs(self.path("pracovni", "dnnt"), exist_ok=True)
        with open(self.path("pracovni", "dnnt", "s.tsv"), "w", encoding="utf-8") as f:
            f.write("pid\tdatum\tstrana\tpristup\ttitul\tverejne\tknihovna\n"
                    "uuid:../../item/x\t1932\t48\tpublic\tAdresář\t\t\n"
                    "uuid:dobry\t1932\t49\tDNNT\tAdresář\tuuid:a/../b\tmzk\n")
        out = self.py("""
def get(url):
    print("URL", url)
    return b"text"
dnnt.get = get
dnnt.ocr(["pracovni/dnnt/s.tsv", "../../venku=uuid:abc"])
""")
        self.assertNotIn("..", "".join(r for r in out.splitlines() if r.startswith("URL")))
        self.assertEqual(os.listdir(self.path("pracovni", "dnnt", "ocr")), ["venku.txt"])
        self.assertFalse(os.path.exists(self.path("venku.txt")))


class TestMza(Projekt):
    """mza.py snimek bez sítě: curl i stránka knihy jsou nahrazené."""

    def snimek(self, data, kod=0):
        """Stáhne snímek do pracovni/x.jpg; podvržený curl zapíše `data` a vrátí `kod`."""
        p = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", f"""
import subprocess, sys; sys.path.insert(0, 'tools'); import mza
mza.scan = lambda mid, n: ({{"stavy": ["0"], "dzi": ["https://x/Deepzoom=a.dzi"], "jmena": ["a"]}}, 1)
def curl(args, **kw):
    open(args[args.index("-o") + 1], "wb").write({data!r})
    return subprocess.CompletedProcess(args, {kod}, "", "")
mza.slusne.curl = curl
mza.snimek(1, 1, "pracovni/x.jpg")
"""], cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        return p.returncode

    def setUp(self):
        super().setUp()
        os.makedirs(self.path("pracovni"), exist_ok=True)
        with open(self.path("pracovni", "x.jpg"), "wb") as f:
            f.write(b"stary snimek")

    def obsah(self):
        with open(self.path("pracovni", "x.jpg"), "rb") as f:
            return f.read()

    def test_chyba_curl_necha_stary_snimek(self):
        self.assertNotEqual(self.snimek(b"", 22), 0)
        self.assertEqual(self.obsah(), b"stary snimek")

    def test_html_misto_obrazku_necha_stary_snimek(self):
        self.assertNotEqual(self.snimek(b"<html>chyba</html>"), 0)
        self.assertEqual(self.obsah(), b"stary snimek")

    def test_uspech_prepise_snimek_a_neuklada_docasny_soubor(self):
        self.assertEqual(self.snimek(JPEG), 0)
        self.assertEqual(self.obsah(), JPEG)
        self.assertEqual(os.listdir(self.path("pracovni")), ["x.jpg"])


class TestTrebon(Projekt):
    """trebon.py snimek bez sítě: podvržený server dlaždic, ImageMagick nahrazený (jen se počítá)."""

    def snimek(self, dlazdice):
        """`dlazdice(t, x, y)` vrací tělo odpovědi; vrátí (návratový kód, počet dotazů na dlaždice, výstup)."""
        p = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", f"""
import subprocess, sys; sys.path.insert(0, 'tools'); import trebon
JPEG = {JPEG!r}
dotazy = []
def get(path, referer=None, binary=False):
    if "isrv8.cgi" not in path:
        return ('showImage("x","tok")', path)
    t, x, y = (int(v) for v in path.rsplit(".", 1)[1].split("-"))
    dotazy.append(1)
    return ({dlazdice}), path
trebon.get = get
trebon.magick = lambda: "magick"
trebon.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "", "")
try:
    trebon.snimek(1, 1, "pracovni/x.jpg")
finally:
    print("DOTAZU", len(dotazy))
"""], cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        return p.returncode, int(re.search(r"DOTAZU (\d+)", p.stdout).group(1)), p.stdout + p.stderr

    def test_snimek_slepi_existujici_dlazdice(self):
        rc, n, out = self.snimek("JPEG if t <= 3 and x < 2 and y < 2 else b''")
        self.assertEqual(rc, 0, out)
        self.assertEqual(n, 3 + 2 * 3 + 1)   # úrovně 2–4, dva řádky po 2 + konec řádku, prázdný třetí řádek

    def test_html_misto_dlazdice_zastavi_hned(self):
        rc, n, out = self.snimek("b'<html>chyba</html>' if t > 2 else JPEG")
        self.assertNotEqual(rc, 0)
        self.assertLess(n, 5)
        self.assertIn("něco jiného než obrázek", out)

    def test_nekonecne_urovne_maji_strop(self):
        rc, n, out = self.snimek("JPEG")
        self.assertNotEqual(rc, 0)
        self.assertLessEqual(n, 13)
        self.assertNotIn("Traceback", out)


@unittest.skipUnless(shutil.which("bash"), "chybí bash")
class TestMatricula(Projekt):
    """matricula_dl.sh a matricula_batch.sh bez sítě: curl v PATH je podvržený a vrací obsah souboru VRAT."""
    URL = "https://img.data.matricula-online.eu/x.jpg?csrf=abc&ctrl=1"

    def setUp(self):
        super().setUp()
        self.bin = self.path("bin")
        os.makedirs(self.bin)
        with open(os.path.join(self.bin, "curl"), "w") as f:
            f.write('#!/bin/bash\nwhile [ "$1" ]; do [ "$1" = -o ] && cp "$VRAT" "$2"; shift; done\nexit $KOD\n')
        os.chmod(os.path.join(self.bin, "curl"), 0o755)
        os.makedirs(self.path("pracovni"), exist_ok=True)

    def spust(self, data, kod, *args):
        with open(self.path("vrat"), "wb") as f:
            f.write(data)
        env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"], VRAT=self.path("vrat"), KOD=str(kod),
                   SLUSNE_DIR=self.path("slusne"))
        return subprocess.run(["bash", *args], cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8")

    def test_chyba_curl_vrati_chybu_a_necha_stary_snimek(self):
        with open(self.path("pracovni", "x.jpg"), "wb") as f:
            f.write(b"stary snimek")
        p = self.spust(b"", 22, "tools/matricula_dl.sh", self.URL, "pracovni/x.jpg")
        self.assertEqual(p.returncode, 1, p.stderr)
        with open(self.path("pracovni", "x.jpg"), "rb") as f:
            self.assertEqual(f.read(), b"stary snimek")
        self.assertEqual(os.listdir(self.path("pracovni")), ["x.jpg"])

    def test_html_misto_obrazku_se_neulozi(self):
        p = self.spust(b"<html>Forbidden</html>", 0, "tools/matricula_dl.sh", self.URL, "pracovni/x.jpg")
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertEqual(os.listdir(self.path("pracovni")), [])

    def test_obrazek_se_ulozi(self):
        p = self.spust(JPEG, 0, "tools/matricula_dl.sh", self.URL, "pracovni/x.jpg")
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(self.path("pracovni", "x.jpg"), "rb") as f:
            self.assertEqual(f.read(), JPEG)

    def test_davka_skonci_chybou_u_prvniho_nestazeneho_snimku(self):
        with open(self.path("urls.txt"), "w") as f:
            f.write(f"1 {self.URL}\n2 {self.URL}\n")
        p = self.spust(b"", 22, "tools/matricula_batch.sh", "urls.txt", "pracovni/kniha")
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertEqual(p.stderr.count("nevrátila obrázek"), 1, p.stderr)
        self.assertEqual(os.listdir(self.path("pracovni")), [])


class TestIpr(Projekt):
    """ipr_praha.py serie bez sítě: služba IPR, převod souřadnic i volání vyrez.py a zapis.py jsou nahrazené."""

    def serie(self, odpoved, *args, zapis_kod=0):
        """Pustí `serie` s podvrženou odpovědí služby; vrací (kód, výstup)."""
        p = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", f"""
import subprocess, sys; sys.path.insert(0, 'tools'); import ipr_praha
ipr_praha.get = lambda url, binary=False: {odpoved!r}
ipr_praha.sjtsk = lambda lat, lon: (-740000 - lat, -1040000 - lon)
ipr_praha.subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(cmd, {zapis_kod} if "zapis.py" in cmd[2] else 0, "", "chyba zápisu")
sys.argv = ["ipr_praha.py", "serie", *{list(args)!r}, "--jen", "herget_1791"]
ipr_praha.main()
"""], cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout + p.stderr

    def soubory(self):
        return sorted(os.listdir(self.path("pracovni", "ipr")))

    def test_ruzne_stredy_se_neprepisi(self):
        self.assertEqual(self.serie(JPEG, "1,1", "80", "1")[0], 0)
        self.assertEqual(self.serie(JPEG, "2,2", "80", "1")[0], 0)
        self.assertEqual(self.soubory(), ["herget_1791_r80_1px_740001_1040001.jpg", "herget_1791_r80_1px_740002_1040002.jpg"])

    def test_chybova_odpoved_neni_obrazek(self):
        kod, out = self.serie(b'{"error": {"code": 500, "message": "' + b"x" * 500 + b'"}}', "1,1", "80", "1")
        self.assertEqual(kod, 1, out)
        self.assertIn("CHYBA", out)
        self.assertEqual(self.soubory(), [])

    def test_obrazek_jine_velikosti_je_chyba(self):
        kod, out = self.serie(JPEG, "1,1", "80", "2")
        self.assertEqual(kod, 1, out)
        self.assertIn("1×1 px místo 2×2", out)
        self.assertEqual(self.soubory(), [])

    def test_selhany_zapis_do_map_vrati_chybu(self):
        kod, out = self.serie(JPEG, "1,1", "80", "1", "--zapsat", "dum", zapis_kod=1)
        self.assertEqual(kod, 1, out)
        self.assertIn("mapy.json selhal", out)


class TestMista(Projekt):
    """mista.py okoli/parcely bez sítě: odpovědi RÚIAN podstrčené místo urlopen."""

    def okoli(self, adresy, rucne):
        kod = (f"import mista, sys\nADR = {adresy!r}\n"
               "mista.adresni_mista = lambda d, p: [{'attributes': {'adresa': a}, 'geometry': {'y': y, 'x': x}}"
               " for a, y, x, _ in ADR[:2 if d == 'Dvojí 1' else 1]]\n"
               "mista.v_obdelniku = lambda *a: [{'attributes': {'adresa': a, 'stavebniobjekt': so}, 'geometry': {'y': y, 'x': x}} for a, y, x, so in ADR]\n"
               f"sys.argv = ['mista.py', 'okoli', {rucne!r}, '80']; mista.main()")
        return subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", "import sys; sys.path.insert(0, 'tools')\n" + kod],
                              cwd=self.root, capture_output=True, text=True, encoding="utf-8")

    ADRESY = [("Dlouhá 12/3, Lhota", 49.0, 15.0, 7), ("Krátká 12/1, Lhota", 49.0001, 15.0, 7),
              ("Polní 14, Lhota", 49.0002, 15.0, 8), ("Daleká 99, Lhota", 49.00096, 15.0, 9)]   # 107 m na sever

    def test_okoli_jen_do_polomeru_a_roh_podle_budovy(self):
        p = self.okoli(self.ADRESY, "Dlouhá 12/3")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Daleká", p.stdout)
        self.assertIn("3 adres do 80 m", p.stdout)
        self.assertRegex(p.stdout, r"Krátká 12/1 +11 m +← víc adres jedné budovy")
        self.assertRegex(p.stdout, r"Polní 14 +22 m\n")   # jiná budova: bez značky

    def test_vic_mist_se_stejnou_adresou_nevybere_nahodne(self):
        p = self.okoli(self.ADRESY, "Dvojí 1")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("RÚIAN má 2 míst", p.stderr)
        self.assertIn("49.00010,15.00000", p.stderr)


class TestNovyProjekt(Projekt):

    def test_aktualizace_neprepise_data(self):
        self.napln()
        pred = self.text("data", "domy.py"), self.text("data", "zaznamy.json")
        p = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), self.root],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual((self.text("data", "domy.py"), self.text("data", "zaznamy.json")), pred)

    def test_aktualizace_zazalohuje_upraveny_nastroj(self):
        with open(self.path("tools", "vyrez.py"), "a", encoding="utf-8") as f:
            f.write("# vlastní úprava\n")
        p = self.aktualizuj()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("Nástroje aktualizovány (1)", p.stdout)
        zalohy = [d for d in os.listdir(self.path("pracovni")) if d.startswith("zaloha_tools_")]
        self.assertEqual(len(zalohy), 1)
        self.assertTrue(self.text("pracovni", zalohy[0], "vyrez.py").endswith("# vlastní úprava\n"))
        self.assertNotIn("vlastní úprava", self.text("tools", "vyrez.py"))   # nástroj je zase ze skillu

    def test_aktualizace_beze_zmen_nezalohuje(self):
        p = self.aktualizuj()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("Nástroje aktualizovány", p.stdout)

    def aktualizuj(self, cil=None):
        return subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), cil or self.root],
                              capture_output=True, text=True, encoding="utf-8")

    def venku(self):
        """Složka mimo projekt, kam by zápis přes odkaz utekl."""
        d = os.path.join(self.tmp, "venku")
        os.makedirs(d, exist_ok=True)
        return d

    @unittest.skipIf(os.name == "nt", "symlinky na Windows chtějí práva správce")
    def test_slozka_data_jako_odkaz_projekt_nezmeni(self):
        novy = os.path.join(self.tmp, "Novy")
        os.makedirs(novy)
        os.symlink(self.venku(), os.path.join(novy, "data"))
        p = self.aktualizuj(novy)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("data → ", p.stderr)
        self.assertEqual(os.listdir(self.venku()), [])
        self.assertEqual(os.listdir(novy), ["data"])

    @unittest.skipIf(os.name == "nt", "symlinky na Windows chtějí práva správce")
    def test_skill_verze_jako_odkaz_se_nahradi_souborem(self):
        cizi = os.path.join(self.venku(), "cizi.txt")
        with open(cizi, "w") as f:
            f.write("nedotknutelné")
        os.remove(self.path(".skill_verze"))
        os.symlink(cizi, self.path(".skill_verze"))
        self.assertEqual(self.aktualizuj().returncode, 0)
        self.assertFalse(os.path.islink(self.path(".skill_verze")))
        with open(cizi) as f:
            self.assertEqual(f.read(), "nedotknutelné")

    @unittest.skipIf(os.name == "nt", "symlinky na Windows chtějí práva správce")
    def test_odkazy_v_pracovni_a_skills_jsou_v_poradku(self):
        os.symlink(self.venku(), self.path("pracovni", "dum_sousedu"))
        os.makedirs(self.path(".claude", "skills"), exist_ok=True)
        os.symlink(SKILL, self.path(".claude", "skills", "dejiny-domu"))
        p = self.aktualizuj()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(os.listdir(self.venku()), [])

    @unittest.skipIf(os.name == "nt", "symlinky na Windows chtějí práva správce")
    def test_settings_jako_odkaz_se_neprepise(self):
        cizi = os.path.join(self.venku(), "settings.json")
        with open(cizi, "w") as f:
            f.write("{}")
        os.remove(self.path(".claude", "settings.json"))
        os.symlink(cizi, self.path(".claude", "settings.json"))
        p = self.aktualizuj()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("hook hlidac.py nepřidán", p.stdout)
        self.assertEqual(open(cizi).read(), "{}")

    def test_nastroje_zkopirovane(self):
        for f in ("zapis.py", "kontrola.py", "export_web.py", "mza.py", "zdravi.py"):
            self.assertTrue(os.path.exists(self.path("tools", f)), f)


if __name__ == "__main__":
    unittest.main()
