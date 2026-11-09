"""Testy nazvy.py: obec v textu portálu bez diakritiky a v jiném pádě. Bez internetu."""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools"))
import nazvy  # noqa: E402


class ZminujeObecTest(unittest.TestCase):
    def test_obec_v_nazvu_i_v_jinem_pade(self):
        self.assertTrue(nazvy.zminuje_obec("Madona ze Lniště", "Lniště"))
        self.assertTrue(nazvy.zminuje_obec("Zámek Telč", "telc"))
        self.assertTrue(nazvy.zminuje_obec("Náměstí v Telči", "Telč"))
        self.assertTrue(nazvy.zminuje_obec("[Praha-Holešovice]", "Holešovice"))
        self.assertFalse(nazvy.zminuje_obec("Telčice", "Telč"))
        self.assertFalse(nazvy.zminuje_obec("Lhotka u Prahy", "Lhota"))   # zdrobnělina je jiná obec
        self.assertTrue(nazvy.zminuje_obec("Mlýn pod Lhotou", "Lhota"))
        self.assertFalse(nazvy.zminuje_obec("Sezemice", "Nežetice"))
        self.assertFalse(nazvy.zminuje_obec(None, "Telč"))

    def test_bez_diakritiky(self):
        self.assertEqual(nazvy.bez_diakritiky("Žďár NAD Sázavou"), "zdar nad sazavou")
        self.assertEqual(nazvy.bez_diakritiky(None), "")


if __name__ == "__main__":
    unittest.main()
