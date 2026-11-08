"""Testy esbirky.py (předměty obce ve sbírkách muzeí na eSbírkách): data stránky, obec v názvu, licence, detail. Bez internetu."""
import json, os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import esbirky  # noqa: E402

# zkrácené skutečné záznamy eSbírek (8. 11. 2026)
JATKY = {"id": 21678531, "name": "Holešovice", "slug": "holesovice-21678531", "inventoryNumber": "PS 1395",
         "license": {"name": "CC_BY"}, "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
         "currentCollection": {"name": "Praha"}, "datingNote": "1903", "datingFrom": 1901, "datingTo": 2000,
         "description": "Jatky", "locationDetails": None, "location": {"name": "Česko"},
         "institution": {"name": "Národní muzeum"}, "collectionPath": [{"name": "Sbírka NM-HM"}, {"name": "Praha"}]}
MADONA = {"id": 63291100, "name": "Madona ze Lniště", "mediaType": "Skleněná deska", "license": {"name": "CC_BY_NC_SA"},
          "currentCollection": {"name": "Trojrozměrné"}, "datingNote": "není upřesněna"}
SEZEMICE = {"id": 18115842, "name": "Sezemice", "license": {"name": "CC_BY"}}


def stranka_next(data):
    """HTML jako ze serveru: data v self.__next_f.push([1,"…"]), rozdělená na dva kusy."""
    text = json.dumps(data, ensure_ascii=False)
    pul = len(text) // 2
    return "".join(f'<script>self.__next_f.push([1,{json.dumps(kus, ensure_ascii=False)}])</script>'
                   for kus in (text[:pul], text[pul:]))


class EsbirkyTest(unittest.TestCase):

    def test_obec_v_nazvu_i_v_jinem_pade(self):
        self.assertTrue(esbirky.v_nazvu("Madona ze Lniště", "Lniště"))
        self.assertTrue(esbirky.v_nazvu("Zámek Telč", "telc"))
        self.assertTrue(esbirky.v_nazvu("Náměstí v Telči", "Telč"))
        self.assertTrue(esbirky.v_nazvu("[Praha-Holešovice]", "Holešovice"))
        self.assertFalse(esbirky.v_nazvu("Telčice", "Telč"))
        self.assertFalse(esbirky.v_nazvu("Sezemice", "Nežetice"))
        self.assertFalse(esbirky.v_nazvu(None, "Telč"))

    def test_vypis_jen_obec(self):
        self.assertEqual(esbirky.vypis([SEZEMICE, MADONA], "Lniště"),
                         ["  63291100 | není upřesněna | Madona ze Lniště | Skleněná deska | Trojrozměrné | CC_BY_NC_SA"])

    def test_licence_a_obrazek(self):
        self.assertTrue(esbirky.smi_obrazek(JATKY).startswith("ano"))
        self.assertTrue(esbirky.smi_obrazek(MADONA).startswith("jen nevýdělečně"))
        self.assertEqual(esbirky.smi_obrazek({"license": None}), "jen se souhlasem instituce")

    def test_datace_bez_poznamky(self):
        self.assertEqual(esbirky.datace({"datingFrom": 1901, "datingTo": 2000}), "1901–2000")
        self.assertEqual(esbirky.datace({}), "?")

    def test_data_stranky(self):
        html = stranka_next({"x": 1, "items": [JATKY], "totalCount": 65, "pagination": {"numberOfPages": 4}})
        data = esbirky.data_stranky(html)
        self.assertEqual(esbirky.json_za(data, "items")[0]["name"], "Holešovice")
        self.assertEqual(esbirky.json_za(data, "totalCount"), 65)
        self.assertIsNone(esbirky.json_za(data, "chybi"))

    def test_hledej_skonci_na_posledni_strane(self):
        html = stranka_next({"items": [JATKY], "totalCount": 1, "pagination": {"numberOfPages": 1}})
        with mock.patch.object(esbirky, "stranka", return_value=html) as st:
            predmety, celkem = esbirky.hledej("Holešovice", ("1900", "1910"))
        self.assertEqual((len(predmety), celkem, st.call_count), (1, 1, 1))
        self.assertIn("datingFrom=1900", st.call_args[0][0])

    def test_detail(self):
        with mock.patch.object(esbirky, "stranka", return_value=stranka_next({"subject": JATKY})):
            radky = esbirky.detail("21678531")
        self.assertIn("Popis: Jatky", radky)
        self.assertIn("Sbírka: Sbírka NM-HM › Praha", radky)
        self.assertIn("Citace: Holešovice, 1903, Národní muzeum, inv. č. PS 1395, eSbírky, "
                      "https://www.esbirky.cz/predmet/holesovice-21678531", radky)

    def test_spatne_roky(self):
        with self.assertRaises(SystemExit):
            esbirky.roky_z("1900")


if __name__ == "__main__":
    unittest.main()
