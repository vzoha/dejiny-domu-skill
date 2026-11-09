"""Testy europeana.py: dotaz s polohou, filtry, licence, výpis, detail s překladem URI, klíč. Bez internetu."""
import os, sys, tempfile, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import europeana  # noqa: E402

# zkrácené skutečné odpovědi API (9. 11. 2026)
MAPA = {"id": "/2024014/1592942", "title": ["Rumburg"], "year": ["1925"], "dataProvider": ["Map Collection UK"],
        "rights": ["http://creativecommons.org/licenses/by-nc/4.0/"]}
ZAZNAM = {"object": {
    "proxies": [{"dcIdentifier": {"def": ["HA904465"]}},
                {"dcDescription": {"cs": ["Lniště, boží muka.\nEvidenční list"]}, "dctermsSpatial": {"def": ["HA904465#place"]}}],
    "places": [{"about": "HA904465#place", "prefLabel": {"cs": ["Lniště"]}, "isPartOf": {"cs": ["Česká republika", "Slavče"]}}],
    "organizations": [{"about": "http://data.europeana.eu/organization/2757",
                       "prefLabel": {"cs": ["Národní památkový ústav"], "en": ["The National Heritage Institute"]}}],
    "aggregations": [{"edmDataProvider": {"def": ["http://data.europeana.eu/organization/2757"]},
                      "edmRights": {"def": ["http://rightsstatements.org/vocab/InC/1.0/"]},
                      "edmIsShownAt": "http://iispp.npu.cz/mis_public/publicDocumentDetail.htm?id=904465"}]}}


class EuropeanaTest(unittest.TestCase):

    def test_dotaz_s_polohou(self):
        q = europeana.dotaz(["Rumburk", "Rumburg"], 50.0, 14.0, 2)
        self.assertTrue(q.startswith('"Rumburk" OR "Rumburg" OR (pl_wgs84_pos_lat:[49.9820 TO 50.0180] AND '
                                     'pl_wgs84_pos_long:[13.97'), q)
        self.assertEqual(europeana.dotaz(["Telč"]), '"Telč"')
        # souřadnice místo názvu se nehledají jako text (Praha 7: vracelo jen herbáře)
        self.assertTrue(europeana.dotaz(["50.1049,14.4521"], 50.1049, 14.4521, 1).startswith("(pl_wgs84_pos_lat:"))

    def test_filtry(self):
        zaklad = [("qf", "TYPE:IMAGE"), ("qf", europeana.PRIRODOVEDNE)]
        self.assertEqual(europeana.filtry(), zaklad + [("qf", '-DATA_PROVIDER:"The National Heritage Institute"')])
        self.assertEqual(europeana.filtry((1900, 1910), True, True),
                         zaklad + [("qf", "YEAR:[1900 TO 1910]"), ("reusability", "open")])

    def test_licence(self):
        self.assertEqual(europeana.zkratka_licence("http://creativecommons.org/licenses/by-nc/4.0/"), "CC BY-NC")
        self.assertEqual(europeana.zkratka_licence("http://rightsstatements.org/vocab/InC-EDU/1.0/"), "jen vzdělávání")
        self.assertTrue(europeana.smi_obrazek("http://creativecommons.org/publicdomain/mark/1.0/").startswith("ano, volné dílo"))
        self.assertTrue(europeana.smi_obrazek("http://creativecommons.org/licenses/by-sa/4.0/").startswith("ano, s autorem"))
        self.assertTrue(europeana.smi_obrazek("http://creativecommons.org/licenses/by-nc/4.0/").startswith("jen nevýdělečně"))
        self.assertTrue(europeana.smi_obrazek("http://rightsstatements.org/vocab/InC/1.0/").startswith("jen se souhlasem"))

    def test_radek(self):
        self.assertEqual(europeana.radek(MAPA), "  /2024014/1592942 | 1925 | Rumburg | Map Collection UK | CC BY-NC | "
                         "https://www.europeana.eu/item/2024014/1592942")

    def test_detail_preklada_uri(self):
        with mock.patch.object(europeana, "api", return_value=ZAZNAM):
            radky = europeana.detail("/2020706/HA904465")
        self.assertIn("Název: Lniště, boží muka. Evidenční list", radky)
        self.assertIn("Místo: Lniště (Česká republika)", radky)
        self.assertIn("Instituce: Národní památkový ústav", radky)
        self.assertIn("Obrázek do výstupu: jen se souhlasem instituce (práva vyhrazena)", radky)

    def test_detail_spatne_id(self):
        with self.assertRaises(SystemExit):
            europeana.detail("Lniště")

    def test_bez_klice_poradi(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"EUROPEANA_API_KEY": ""}), \
                mock.patch.object(europeana, "KLIC", os.path.join(d, "api-key")), self.assertRaises(SystemExit) as e:
            europeana.klic()
        self.assertIn("get-api", str(e.exception))


if __name__ == "__main__":
    unittest.main()
