"""Testy mis.py (MIS NPÚ): rozbor stránky výsledků a detailu podle zkrácených skutečných stránek. Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import mis  # noqa: E402

VYSLEDKY = """<span>, zobrazených 1 - 7 z 7 nalezených</span>
<div  class="searchResultInfo"  ><sub class="score">(score 28.8)</sub>
 <div class="searchResultNotes"><b>Popis&nbsp;dokumentu: </b><str:substring start="0" end="350">
  Lniště, CB, boží muka, pohled od J</str:substring></div>
 <table><tr><td class="localityLabelLocName">Název lokality:</td><td colspan="3">Lniště</td></tr>
 <tr><td>Kat. území:</td><td>Mohuřice</td><td>Obec:</td><td>Slavče</td></tr></table>
 <table><tr><td>Typ dokumentu:</td><td>fotografická dokumentace</td></tr></table>
 <table><tr><td>Datum vzniku:</td><td>
   05.10.2023   </td><td>Autor originálu:</td><td> Štorková Jana &nbsp;</td></tr></table></div>
<div class="searchResultButtons"><a href="documentDetail.htm?id=1755176">Detail</a></div>"""

DETAIL = """<b>Typ dokumentu:</b> fotografická dokumentace <b>Popis&nbsp;dokumentu:</b> Lniště, boží muka.
<b>Datum vzniku:</b> 06.1997 <b>Licence:</b> <b>Typ:</b> neurčena
<td>Část obce:</td><td>Lniště</td><td>Č. dom.:</td><td></td><td>Ulice:</td><td></td><td>Obec:</td><td>Slavče</td>
<span>boží muka (prvek 680990)</span><td>Obec:</td><td>Slavče</td><span>boží muka (prvek 680990)</span>"""


class MisTest(unittest.TestCase):

    def test_vysledky_hledani(self):
        z = mis.vysledky(VYSLEDKY)
        self.assertEqual(len(z), 1)
        self.assertEqual(z[0]["id"], "1755176")
        self.assertEqual(z[0]["popis"], "Lniště, CB, boží muka, pohled od J")
        self.assertEqual(z[0]["Datum vzniku"], "05.10.2023")
        self.assertEqual(z[0]["Název lokality"], "Lniště")
        self.assertEqual(z[0]["Autor originálu"], "Štorková Jana")
        self.assertEqual(mis.pocet(VYSLEDKY), 7)

    def test_detail(self):
        radky = mis.popis_detailu(DETAIL, "93811")
        self.assertIn("Popis dokumentu: Lniště, boží muka.", radky)   # popisek s &nbsp;
        self.assertIn("licence: neurčena", radky)
        self.assertIn("Část obce: Lniště", radky)
        self.assertFalse(any(r.startswith("Č. dom.") for r in radky))   # prázdná hodnota se nevypíše
        self.assertEqual(radky.count("Obec: Slavče"), 1)
        self.assertEqual(radky.count("památka: prvek 680990"), 1)
        self.assertEqual(radky[-1], "odkaz: https://iispp.npu.cz/mis_public/documentDetail.htm?id=93811")


if __name__ == "__main__":
    unittest.main()
