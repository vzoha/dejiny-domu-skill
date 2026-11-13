"""Testy podmínek portálů (podminky.py, podminky.json): zákaz stahování v slusne.py a posouzení obrázků. Bez internetu."""
import json, os, shutil, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import podminky, slusne  # noqa: E402


class PodminkyTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["SLUSNE_DIR"] = os.path.join(self.tmp, "slusne")
        os.makedirs(os.path.join(self.tmp, "data"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def data(self, name, obsah):
        with open(os.path.join(self.tmp, "data", name), "w", encoding="utf-8") as f:
            json.dump(obsah, f, ensure_ascii=False)

    def test_json_je_platny(self):
        p = podminky.portaly()
        self.assertIn("digi.ceskearchivy.cz", p)
        for host, x in p.items():
            self.assertIn(x["vyrez"], ("ano", "neresi", "nekomercne", "souhlas", "ne"), host)
            self.assertIsInstance(x["dotazy"], bool, host)
            self.assertIsInstance(x["obrazky"], bool, host)

    def test_zakazany_portal_zastavi_slusne(self):
        with self.assertRaises(podminky.Zakazano) as e:
            slusne.pockej("digi.ceskearchivy.cz", "dotaz")
        self.assertIn("PODMÍNKY", str(e.exception))

    def test_za_opava_skriptum_nic(self):   # od 11/2026 obrázkový server skriptům 503, prohlížeči ne
        for host in ("digi.archives.cz", "images.archives.cz"):
            for co in ("dotaz", "obr"):
                with self.assertRaises(podminky.Zakazano):
                    slusne.pockej(host, co)

    def test_soa_praha_hledani_ano_snimky_ne(self):   # 11/2026 archiv omezil nástroje, stránka snímku /d/ ani /a/ ne
        slusne.pockej("https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/1", "dotaz")   # neskončí
        for url, co in (("https://ebadatelna.soapraha.cz/d/1/2", "dotaz"), ("https://ebadatelna.soapraha.cz/a/1/2", "dotaz"),
                        ("https://ebadatelna.soapraha.cz/scan/1.jpg", "obr")):
            with self.assertRaises(podminky.Zakazano):
                slusne.pockej(url, co)

    def test_mza_dotazy_ano_snimky_ne(self):
        slusne.pockej("www.mza.cz", "dotaz")   # neskončí
        with self.assertRaises(podminky.Zakazano):
            slusne.pockej("www.mza.cz", "obr")

    def test_stranka_knihy_mza_neni_snimek(self):
        self.assertEqual(slusne.druh("/actapublica/matrika/detail/3090?image=2160-00010.jp2"), "dotaz")
        self.assertEqual(slusne.druh("/x/snimek.jpg"), "obr")
        self.assertEqual(slusne.druh("/fcgi-bin/iipsrv.fcgi?IIIF=a.jp2/full/full/0/default.jpg"), "obr")

    def test_neznamy_portal_projde(self):
        slusne.pockej("example.org", "dotaz")

    def test_vyjimka_podle_textu(self):
        self.assertEqual(podminky.pravidlo("https://ags.cuzk.gov.cz/archiv/")["vyrez"], "ano")
        self.assertEqual(podminky.pravidlo("https://ags.cuzk.gov.cz/archiv/", "Indikační skica")["vyrez"], "souhlas")

    def test_posouzeni_obrazku(self):
        self.data("svazky.json", {})
        self.data("zaznamy.json", [
            {"klic": "a", "svazek": "s", "odkaz": "https://www.mza.cz/actapublica/matrika/detail/1"},
            {"klic": "b", "svazek": "s", "odkaz": "https://www.mza.cz/actapublica/matrika/detail/1", "souhlas": "MZA, 1. 1. 2027"},
            {"klic": "c", "svazek": "s", "odkaz": "https://aron.vychodoceskearchivy.cz/apu/1"}])
        self.data("dokumenty.json", [{"img": "foto"}])
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "a")[0], "souhlas")
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "b")[0], "ok")
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "c")[0], "ok")
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "foto")[0], "ok")   # vlastní fotka bez odkazu
        self.assertEqual(podminky.posoud_obrazek(self.tmp, "nic")[0], "pozor")


if __name__ == "__main__":
    unittest.main()
