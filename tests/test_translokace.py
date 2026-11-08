"""Testy translokace.py (translokační plány židovských obydlí 1727–1728, VÚGTK): seznam, hledání obce, detail. Bez internetu."""
import os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import translokace  # noqa: E402


def bunky(*hodnoty):
    return "".join(f"<td>\n  {h}\n</td>" for h in hodnoty)


# zkrácené řádky seznamu www.vugtk.cz/plany/cs/seznam/ (8. 11. 2026); za krajem web má dalších 16 sloupců
BECOV = bunky("1", '<a href="/plany/cs/mapa/1" target="_blank">Bečov nad Teplou</a>', "Mappa uber das Juden Stadt zu Petschau",
              "Národní archiv", "Sbírka map a plánů", "plán", "1", "1133", "F/XI/30", "1727", "Bečov nad Teplou", "Petschau",
              "Karlovy Vary", "Karlovarský kraj", "numerická legenda")
BOSKOVICE = bunky("98", '<a href="/plany/cs/mapa/98">Boskovice</a>', "Boskovicium.", "Moravský zemský archiv v Brně",
                  "Sbírka map a plánů", "plán", "1", "", "1316", "1727", "Boskovice", "Boskowitz", "Blansko", "Jihomoravský kraj")
RADOSOV = bunky("67 b", '<a href="/plany/cs/mapa/67%20b">Radošov</a>', "Dorff Reschwitz.", "Národní archiv", "Sbírka map a plánů",
                "plán", "1", "1145", "A/XI/12", "1727", "Radošov 2", "Reschwitz", "Karlovy Vary", "Karlovarský kraj")
SEZNAM = f"<table><thead><tr><th>id</th></tr></thead><tbody><tr>{BECOV}</tr><tr>{BOSKOVICE}</tr><tr>{RADOSOV}</tr></tbody></table>"

DETAIL = """<table><tbody>
<tr><td class="label">archiv</td><td class="value">Národní archiv</td></tr>
<tr><td class="label">archivní soubor</td><td class="value">Sbírka map a plánů</td></tr>
<tr><td class="label">inventární číslo</td><td class="value">1133</td></tr>
<tr><td class="label">signatura</td><td class="value">F/XI/30</td></tr>
<tr><td class="label">datace - vznik</td><td class="value">1727</td></tr>
<tr><td class="label">měřítko převedené</td><td class="value"></td></tr>
<tr><td class="label">židovské objekty a objekty pronajaté Židům</td><td class="value"><ul>
  <li>15 domů</li>
  <li>synagoga</li>
</ul></td></tr>
</tbody></table>"""


class TranslokaceTest(unittest.TestCase):

    def test_plany_ze_seznamu(self):
        plany = translokace.plany(SEZNAM)
        self.assertEqual([p["id"] for p in plany], ["1", "98", "67 b"])   # hlavička bez <td> vypadne
        self.assertEqual(plany[0]["obec_nem"], "Petschau")

    def test_najdi_cesky_nemecky_bez_diakritiky(self):
        plany = translokace.plany(SEZNAM)
        self.assertEqual([p["id"] for p in translokace.najdi(plany, "becov nad teplou")], ["1"])
        self.assertEqual([p["id"] for p in translokace.najdi(plany, "Boskowitz")], ["98"])
        self.assertEqual([p["id"] for p in translokace.najdi(plany, "Radošov")], ["67 b"])   # obec „Radošov 2“, lokalita sedí
        self.assertEqual(translokace.najdi(plany, "Bečov"), [])   # celé jméno, ne kus

    def test_radek_bez_prazdneho_inventarniho_cisla(self):
        p = translokace.plany(SEZNAM)[1]
        self.assertEqual(translokace.radek(p), "  98 | Boskovice, Boskowitz, okr. Blansko | 1727 | Boskovicium. | "
                         "Moravský zemský archiv v Brně, Sbírka map a plánů, sign. 1316, 1727 | "
                         "https://www.vugtk.cz/plany/cs/mapa/98")

    def test_odkaz_s_mezerou_v_cisle(self):
        self.assertTrue(translokace.radek(translokace.plany(SEZNAM)[2]).endswith("/mapa/67%20b"))

    def test_detail(self):
        radky = translokace.detail("1", nacti=lambda adresa: DETAIL)
        self.assertIn("židovské objekty a objekty pronajaté Židům: 15 domů, synagoga", radky)
        self.assertNotIn("měřítko převedené: ", radky)   # prázdné údaje vynechá
        self.assertIn("Citace: Národní archiv, Sbírka map a plánů, inv. č. 1133, sign. F/XI/30, 1727", radky)
        self.assertTrue(any(r.startswith("Pozor: plán je návrh") for r in radky))

    def test_detail_neni(self):
        chyba = translokace.urllib.error.HTTPError("u", 500, "Internal Server Error", {}, None)
        with self.assertRaises(SystemExit):
            translokace.detail("999", nacti=mock.Mock(side_effect=chyba))

    def test_detail_bez_udaju(self):
        with self.assertRaises(SystemExit):
            translokace.detail("1", nacti=lambda adresa: "<html></html>")


if __name__ == "__main__":
    unittest.main()
