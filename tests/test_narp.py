"""Testy narp.py (Národní archivní portál): výpis fondů a detail z uložené odpovědi API. Bez internetu."""
import json, os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import narp  # noqa: E402

# zkrácená skutečná odpověď /apu/<id> (8. 11. 2026); data jsou JSON v řetězci, jak je API posílá
FOND = {"id": "f9b99c8f", "name": "Státní okresní archiv České Budějovice: Archiv obce Slavče (u Trhových Svinů) 1887 — 1945",
        "parts": [{"type": "PT~FUND~INFO", "items": [
            {"type": "CISLO~NAD", "value": "1478"},
            {"type": "FUND~MARK", "value": "B1921"},
            {"type": "UNIT~DATE", "value": '{\n  "from" : "1887",\n  "to" : "1945",\n  "format" : "Y-Y"\n}'},
            {"type": "ACCESSIBILITY", "value": "Částečně přístupný"},
            {"type": "FUND~TOPIC", "value": "Matrika příslušníků obce"},
            {"type": "EVIDENCE~UNIT", "value": json.dumps({"type": "table", "data": {"rows": [
                ["Úřední knihy a rukopisy", "2", "9", "9", "0", "1889 — 1945"],
                ["* úřední knihy", "2", "9", "9", "0", "1889 — 1945"]]}})},
            {"type": "FINDINGAID~REF", "value": "b648f034"}]},
            {"type": "PT~TITLE", "items": [{"type": "TITLE", "value": "Archiv obce Slavče (u Trhových Svinů)"}]}]}


class NarpTest(unittest.TestCase):

    def test_fondy_podle_archivu(self):
        items = [{"id": "b", "name": "Státní okresní archiv České Budějovice: Národní škola Slavče 1880-1952"},
                 {"id": "c", "name": "Státní oblastní archiv v Třeboni: Statek Slavče s.p. 1991-1994"},
                 {"id": "a", "name": "Státní okresní archiv České Budějovice: Archiv obce Slavče 1887 — 1945"},
                 {"id": "d", "name": "Fond bez archivu"}]
        self.assertEqual(narp.vypis_fondy(items), [
            "\n(archiv neuveden)", "  d | Fond bez archivu",
            "\nStátní oblastní archiv v Třeboni", "  c | Statek Slavče s.p. 1991-1994",
            "\nStátní okresní archiv České Budějovice", "  a | Archiv obce Slavče 1887 — 1945",
            "  b | Národní škola Slavče 1880-1952"])

    def test_stejny_nazev_dvou_fondu(self):
        items = [{"id": "x", "name": "A: Fond"}, {"id": "y", "name": "A: Fond"}]
        self.assertEqual(len(narp.vypis_fondy(items)), 3)

    def test_detail_fondu(self):
        radky = narp.popis_fondu(FOND, ["Archiv obce Slavče. Inventář, 1993"])
        self.assertEqual(radky[0], "Archiv obce Slavče (u Trhových Svinů) (1887–1945)")
        self.assertIn("archiv: Státní okresní archiv České Budějovice", radky)
        self.assertIn("číslo NAD: 1478 · značka: B1921 · Částečně přístupný", radky)
        self.assertIn("  Úřední knihy a rukopisy: 11 (1889 — 1945)", radky)
        self.assertFalse(any("* úřední" in r for r in radky))   # rozpad téže jednotky nezdvojí počet
        self.assertIn("pomůcka: Archiv obce Slavče. Inventář, 1993", radky)
        self.assertEqual(radky[-1], "odkaz: https://portal.nacr.cz/aron/apu/f9b99c8f")

    def test_fond_bez_pomucky(self):
        radky = narp.popis_fondu({"id": "x", "name": "Archiv: Fond", "parts": []})
        self.assertTrue(any(r.startswith("pomůcka: žádná") for r in radky))


if __name__ == "__main__":
    unittest.main()
