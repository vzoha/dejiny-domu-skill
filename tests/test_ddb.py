"""Testy ddb.py (Deutsche Digitale Bibliothek): dotaz, datace, licence, výpis. Bez internetu."""
import os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import ddb  # noqa: E402

# zkrácený skutečný záznam indexu (9. 11. 2026)
DIA = {"id": "ZLJKVSSWKTP44BZSPPAVUK42UFYVNFRV", "label": ["Rumburg, Marktplatz, Rumburg, Mariensäule"],
       "place": ["Rumburg", "Berlin"], "objecttype": ["Dia"], "begin_time": [720106],
       "dataprovider_fct": ["Mediathek des Instituts für Kunst- und Bildgeschichte der Humboldt-Universität zu Berlin"],
       "license": ["http://creativecommons.org/licenses/by-sa/4.0/"]}


class DdbTest(unittest.TestCase):

    def test_dotaz(self):
        q = ddb.dotaz(["Rumburk", "Rumburg"])
        self.assertTrue(q.startswith('(place:"Rumburk" OR label:"Rumburk" OR place:"Rumburg" OR label:"Rumburg") '
                                     'AND digitalisat:true AND type_fct:mediatype_002 AND -objecttype_fct:("Urkunden" OR '), q)
        self.assertTrue(ddb.dotaz(["Telč"], (1900, 1910)).endswith(
            f"AND begin_time:[{ddb.den(1900, 1, 1)} TO {ddb.den(1910, 12, 31)}]"))

    def test_rok(self):
        self.assertEqual(ddb.rok(DIA), 1972)
        self.assertEqual(ddb.rok({"begin_time": [ddb.den(1905, 6, 1)]}), 1905)
        self.assertIsNone(ddb.rok({}))

    def test_licence(self):
        self.assertTrue(ddb.smi_obrazek("http://creativecommons.org/licenses/by-sa/4.0/").startswith("ano"))
        self.assertTrue(ddb.smi_obrazek("http://creativecommons.org/publicdomain/mark/1.0/").startswith("ano, volné dílo"))
        self.assertTrue(ddb.smi_obrazek("http://creativecommons.org/licenses/by-nc-sa/4.0/").startswith("jen nevýdělečně"))
        self.assertTrue(ddb.smi_obrazek("http://rightsstatements.org/vocab/InC/1.0/").startswith("jen se souhlasem"))
        self.assertTrue(ddb.smi_obrazek("").startswith("jen se souhlasem"))
        self.assertEqual(ddb.zkratka_licence("http://creativecommons.org/publicdomain/zero/1.0/"), "CC0")
        self.assertEqual(ddb.zkratka_licence("http://rightsstatements.org/vocab/InC/1.0/"), "práva vyhrazena")

    def test_radek(self):
        self.assertEqual(ddb.radek(DIA, ["Rumburk", "Rumburg"]), "  ZLJKVSSWKTP44BZSPPAVUK42UFYVNFRV | 1972 | Rumburg, Marktplatz, Rumburg, Mariensäule | Rumburg | Dia | "
                         "Mediathek des Instituts für Kunst- und Bildgeschichte der Humboldt-Universität zu Berlin | CC BY-SA | "
                         "https://www.deutsche-digitale-bibliothek.de/item/ZLJKVSSWKTP44BZSPPAVUK42UFYVNFRV")

    def test_misto(self):
        p = {"place": ["Berlin", "Schweinitz (Kreis Jessen <Elster>)"]}
        self.assertEqual(ddb.misto(p, ["Trhové Sviny", "Schweinitz"]), "Schweinitz (Kreis Jessen <Elster>)")
        self.assertEqual(ddb.misto({"place": ["Berlin"]}, ["Rumburg"]), "Berlin")
        self.assertEqual(ddb.misto({}, ["Rumburg"]), "")

    def test_detail(self):
        with mock.patch.object(ddb, "api", return_value={"response": {"docs": [DIA]}}):
            radky = ddb.detail(DIA["id"])
        self.assertIn("Místo: Rumburg, Berlin", radky)
        self.assertIn("Obrázek do výstupu: ano, s autorem, institucí a licencí (http://creativecommons.org/licenses/by-sa/4.0/)", radky)


if __name__ == "__main__":
    unittest.main()
