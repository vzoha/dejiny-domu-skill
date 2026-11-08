"""Testy seidel.py (Fotobanka Musea Fotoateliér Seidel): obec v adrese a popisu, třídění, detail. Bez internetu."""
import os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import seidel  # noqa: E402

# zkrácené skutečné záznamy API (8. 11. 2026); ve výpisu hledání chybí jmeno, adresa a text_desk
PORTRET = {"id_foto": "302040401060021020001", "popis": "Portrét ženy, Porträt Frau", "jmeno": "Klimová Theresie",
           "adresa": "Slavče 23, Post Č. Křemže", "rok": "1925-1930", "datum_vznik": "6.6.1926",
           "text_desk": "56175 Klinová Theresie 3 Vis.", "negativ": "56175", "keywords": ["portrét", "klinová theresie"]}
POHLED = {"id_foto": "302070503040130720001", "popis": "Trhové Sviny, Schweinitz", "jmeno": "Klárová Augustine",
          "adresa": "Český Krumlov Plešivec312", "rok": "1952", "text_desk": "3920, Schweinitz, Trhové Sviny",
          "keywords": ["dům", "trhové sviny"]}
MORIC = {"id_foto": "301070201040979920001", "popis": "Muž v ateliéru", "jmeno": "", "adresa": "",
         "text_desk": "167 Jos. Jodlischka 3, 166 Moric 6", "keywords": ["moric"]}


def vypis_hledani(d):
    return {k: d[k] for k in ("id_foto", "popis", "keywords")}


class SeidelTest(unittest.TestCase):

    def test_zminka(self):
        self.assertEqual(seidel.zminka(PORTRET, "Slavče"), "zakaznik")
        self.assertEqual(seidel.zminka(POHLED, "Trhové Sviny"), "misto")   # objednala paní z Krumlova
        self.assertIsNone(seidel.zminka(MORIC, "Mohuřice"))                # volné hledání webu
        self.assertIsNone(seidel.zminka(PORTRET, "Slavčice"))

    def test_roztrid_nacte_detail(self):
        detaily = {d["id_foto"]: d for d in (PORTRET, MORIC)}
        skupiny = seidel.roztrid([vypis_hledani(PORTRET), vypis_hledani(MORIC)], "Slavče", nacti=detaily.get)
        self.assertEqual([s["jmeno"] for s in skupiny["zakaznik"]], ["Klimová Theresie"])
        self.assertEqual(skupiny["misto"], [])

    def test_roztrid_za_limitem_jen_popis(self):
        nacti = mock.Mock(return_value=None)
        with mock.patch.object(seidel, "NEJVIC_DETAILU", 0):
            skupiny = seidel.roztrid([vypis_hledani(POHLED), vypis_hledani(PORTRET)], "Trhové Sviny", nacti=nacti)
        nacti.assert_not_called()
        self.assertEqual([s["id_foto"] for s in skupiny["misto"]], ["302070503040130720001"])

    def test_radek(self):
        self.assertEqual(seidel.radek(PORTRET), "  302040401060021020001 | 1925-1930 | Portrét ženy, Porträt Frau | "
                         "Klimová Theresie, Slavče 23, Post Č. Křemže | "
                         "https://fotobanka.seidel.cz/fotobanka/detail/302040401060021020001")

    def test_detail(self):
        with mock.patch.object(seidel, "detail_snimku", return_value=PORTRET):
            radky = seidel.detail("302040401060021020001")
        self.assertIn("Adresa: Slavče 23, Post Č. Křemže", radky)
        self.assertIn("Citace: Museum Fotoateliér Seidel, Český Krumlov, negativ č. 56175, 6.6.1926, "
                      "https://fotobanka.seidel.cz/fotobanka/detail/302040401060021020001", radky)

    def test_detail_neni(self):
        with mock.patch.object(seidel, "detail_snimku", return_value=None), self.assertRaises(SystemExit):
            seidel.detail("999")


if __name__ == "__main__":
    unittest.main()
