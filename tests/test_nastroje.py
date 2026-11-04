"""Testy nástrojů, které sahají na data uživatele: zapis.py, kontrola.py, export_web.py (a novy_projekt.py).

Spuštění z kořene repa:  python3 -m unittest discover tests
Bez sítě a bez závislostí (jen standardní knihovna). Každý test si založí projekt ze šablony skillu v dočasné
složce a pracuje se smyšlenými daty (Horní Lhota).
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

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


class TestNovyProjekt(Projekt):

    def test_aktualizace_neprepise_data(self):
        self.napln()
        pred = self.text("data", "domy.py"), self.text("data", "zaznamy.json")
        p = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), self.root],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual((self.text("data", "domy.py"), self.text("data", "zaznamy.json")), pred)

    def test_nastroje_zkopirovane(self):
        for f in ("zapis.py", "kontrola.py", "export_web.py", "mza.py", "zdravi.py"):
            self.assertTrue(os.path.exists(self.path("tools", f)), f)


if __name__ == "__main__":
    unittest.main()
