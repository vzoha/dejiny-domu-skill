"""Testy akon.py (otevřená data AKON, ÖNB Labs): datace, hledání podle polohy a názvu, detail, geohash. Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import akon  # noqa: E402

# zkrácené skutečné řádky CSV (9. 11. 2026)
KOMOTAU = {"akon_id": "AK111_293", "city": "Komotau", "name": "Komotau", "comment": "1905 gel", "year": "",
           "date": "vor 1905", "latitude": "50.46048", "longitude": "13.41779", "publisher": "", "color": "True",
           "download_link": "https://iiif.onb.ac.at/images/AKON/AK111_293/293/full/full/0/native.jpg"}
GRUND = {"akon_id": "AK118_401", "city": "Grundthale", "name": "Komotau", "comment": "1900 gel", "year": "",
         "date": "gelaufen 1900", "latitude": "50.46048", "longitude": "13.41779", "publisher": "Grund"}
KRUMMAU = {"akon_id": "AK014_250", "city": "Krummau ", "name": "Český Krumlov", "comment": "", "year": "1908.0",
           "date": "1908", "latitude": "48.81091", "longitude": "14.31521", "publisher": "Seidel"}
KARTY = [KOMOTAU, GRUND, KRUMMAU]


class AkonTest(unittest.TestCase):

    def test_rok_a_datace(self):
        self.assertEqual(akon.rok(KOMOTAU), 1905)
        self.assertEqual(akon.rok(KRUMMAU), 1908)
        self.assertEqual(akon.datace(KOMOTAU), "před 1905")
        self.assertEqual(akon.datace(GRUND), "odesláno 1900")

    def test_najdi_podle_polohy(self):
        nalez = akon.najdi(KARTY, 48.81094, 14.31598, polomer=3)
        self.assertEqual([k["akon_id"] for _, k in nalez], ["AK014_250"])
        self.assertLess(nalez[0][0], 0.2)

    def test_najdi_podle_nazvu_i_geonames(self):
        nalez = akon.najdi(KARTY, obec="Komotau")
        self.assertEqual([k["akon_id"] for _, k in nalez], ["AK118_401", "AK111_293"])   # bez polohy podle roku
        self.assertEqual(akon.najdi(KARTY, obec="Kom"), [])

    def test_najdi_roky(self):
        self.assertEqual([k["akon_id"] for _, k in akon.najdi(KARTY, obec="Komotau", roky=(1901, 1910))], ["AK111_293"])

    def test_radek_a_detail(self):
        self.assertEqual(akon.radek(0.04, KRUMMAU),
                         "  AK014_250 | 1908 | Krummau | 0.0 km | Seidel | http://data.onb.ac.at/AKON/AK014_250")
        radky = akon.detail(KARTY, "ak111_293")
        self.assertIn("Citace: Österreichische Nationalbibliothek, AKON, AK111_293, Komotau, před 1905, "
                      "http://data.onb.ac.at/AKON/AK111_293", radky)
        self.assertIn("Obrázek do výstupu: ano, volné dílo (Public Domain Mark), s citací", radky)

    def test_detail_neni(self):
        with self.assertRaises(SystemExit):
            akon.detail(KARTY, "AK999_999")

    def test_geohash(self):
        self.assertEqual(akon.geohash(57.64911, 10.40744, 11), "u4pruydqqvj")   # vzor z Wikipedie


if __name__ == "__main__":
    unittest.main()
