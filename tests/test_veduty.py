"""Testy veduty.py (veduty a mapy obce z České digitální knihovny): heslo obce, výpis, dotaz. Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import veduty  # noqa: E402

# zkrácené skutečné záznamy CDK (8. 11. 2026)
ZAMEK = {"pid": "uuid:1dd4cb48-2693-4276-8108-d2228024ec75", "model": "graphic", "date.str": "[mezi 1833 a 1835]",
         "title.search": "Ansicht des Schlosses Teltsch in Mähren", "cdk.collection": ["mzk"], "licenses": ["public"],
         "genres.search": ["graphic", "grafické listy"], "geographic_names.search": ["Telč (Česko)"]}
LIST = {"pid": "uuid:e3e7bce0", "model": "map", "date.str": "1975", "title.search": "Telč. 23-431",
        "cdk.collection": ["mzk"], "licenses": ["onsite"], "genres.search": ["topographic maps", "topografické mapy"],
        "geographic_names.search": ["Česko", "Telč (Česko : oblast)", "Telč Region (Czechia)"]}
PORTRET = {"pid": "uuid:x", "model": "graphic", "title.search": "[Ivan Petrovič Pavlov]", "geographic_names.search": None}
JINA_OBEC = {"pid": "uuid:y", "model": "graphic", "title.search": "Telčice", "geographic_names.search": ["Telčice (Česko)"]}


class VedutyTest(unittest.TestCase):

    def test_heslo_obce(self):
        self.assertEqual(veduty.heslo(ZAMEK, "telc"), "Telč (Česko)")
        self.assertEqual(veduty.heslo(LIST, "Telč"), "Telč (Česko : oblast)")
        self.assertIsNone(veduty.heslo(PORTRET, "Pavlov"))
        self.assertIsNone(veduty.heslo(JINA_OBEC, "Telč"))

    def test_vypis_po_druzich(self):
        radky = veduty.vypis([LIST, ZAMEK, PORTRET], "Telč")
        self.assertEqual(radky[0], "\nVeduty, pohlednice, fotografie: 1")
        self.assertEqual(radky[1], "  [mezi 1833 a 1835] | obraz | Ansicht des Schlosses Teltsch in Mähren | Telč (Česko) | "
                                   "grafické listy | mzk | public | "
                                   "https://www.ceskadigitalniknihovna.cz/uuid/1dd4cb48-2693-4276-8108-d2228024ec75")
        self.assertEqual(radky[2], "\nMapy a plány: 1")
        self.assertIn("| topografické mapy | mzk | onsite |", radky[3])

    def test_zanr_posledni_i_bez_diakritiky(self):
        self.assertEqual(veduty.zanr({"genres.search": ["graphic", "government publication", "grafické listy", "veduty"]}), "veduty")
        self.assertEqual(veduty.zanr({"genres.search": ["graphic"]}), "")

    def test_nic(self):
        self.assertEqual(veduty.vypis([PORTRET], "Pavlov"), [])

    def test_dotaz_s_roky(self):
        self.assertEqual(veduty.dotaz("Beroun", ("1800", "1900")),
                         'geographic_names.search:"Beroun" AND model:(graphic OR map) AND date_range_start.year:[1800 TO 1900]')

    def test_spatne_roky(self):
        with self.assertRaises(SystemExit):
            veduty.roky_z("1800")


if __name__ == "__main__":
    unittest.main()
