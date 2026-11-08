"""Testy pamatky.py (Památkový katalog NPÚ): výpis a detail z uložených odpovědí API. Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import pamatky  # noqa: E402

KP = {"protectionType": {"name": "kulturní památka"}, "indexNumber": "22583/3-254"}
# zkrácené skutečné výsledky /api/search/fulltext (8. 11. 2026)
KAPLE = {"id": "25529919", "name": "návesní kaple sv. Jana Nepomuckého", "address": "Slavče, Lniště",
         "streetHouseNumber": "", "municipality": "Slavče", "district": "Lniště", "legalStates": [],
         "description": "Lidově barokní\nštítová kaple."}
MUKA = {"id": "680990", "name": "boží muka", "address": "Slavče, Lniště", "municipality": "Slavče",
        "district": "Lniště", "legalStates": [KP, KP], "description": "Kamenná boží muka."}
DOM = {"id": "13760842", "name": "dům Domovina", "address": "Praha, Holešovice, Na Maninách č.p. 1149/32",
       "streetHouseNumber": "Na Maninách č.p. 1149/32", "municipality": "Praha", "district": "Holešovice",
       "legalStates": [KP], "description": "Nájemní dům."}
JINDE = {"id": "18870837", "name": "návesní kaple sv. Víta", "address": "Jankov, Jankov", "municipality": "Jankov",
         "district": "Jankov", "legalStates": [], "description": "Kaple, zmínka o Lništi."}


class PamatkyTest(unittest.TestCase):

    def test_v_miste_a_jinde(self):
        radky = pamatky.vypis([KAPLE, JINDE, MUKA], "Lniště")
        self.assertEqual(radky[0], "\nV místě „Lniště“ (obec, část obce, ulice): 2")
        self.assertIn("  25529919 | návesní kaple sv. Jana Nepomuckého | Slavče, Lniště | evidováno, bez ochrany | "
                      "Lidově barokní štítová kaple.", radky)
        self.assertIn("  680990 | boží muka | Slavče, Lniště | kulturní památka 22583/3-254 | Kamenná boží muka.", radky)
        self.assertEqual(radky[3], "\nJinde (hledané slovo jen v textu): 1")

    def test_ulice_bez_zdvojene_adresy(self):
        radky = pamatky.vypis([DOM], "Na Maninách")
        self.assertTrue(radky[0].startswith("\nV místě"))
        self.assertIn("| Praha, Holešovice, Na Maninách č.p. 1149/32 |", radky[1])

    def test_cislo_domu(self):
        self.assertTrue(pamatky.ma_cislo(DOM, "1149"))
        self.assertTrue(pamatky.ma_cislo(DOM, "32"))
        self.assertFalse(pamatky.ma_cislo(DOM, "114"))
        self.assertEqual(pamatky.vypis([DOM], "Na Maninách", "27"), [])

    def test_odkaz_bez_diakritiky(self):
        self.assertEqual(pamatky.odkaz(KAPLE), "https://www.pamatkovykatalog.cz/navesni-kaple-sv-jana-nepomuckeho-25529919")

    def test_detail(self):
        d = {"id": "680990", "name": "boží muka", "elementKind": {"name": "drobný objekt"}, "municipality": "Slavče",
             "district": "Lniště", "cadastralArea": "Mohuřice", "catalogNumber": "1000133534", "legalStates": [KP],
             "origin": "1887", "events": [{"type": "vznik", "dating": "1887", "description": None}],
             "literatureSources": [{"quote": "Hájek: Návesní kaple, 2021"}],
             "misMedia": [{"description": "pohled od J", "url": "https://iispp.npu.cz/mis_public/documentDetail.htm?id=1"}],
             "permanentUrl": "https://www.pamatkovykatalog.cz/bozi-muka-680990"}
        radky = pamatky.popis(d)
        self.assertEqual(radky[0], "boží muka (drobný objekt)")
        self.assertIn("místo: Slavče, Lniště, k. ú. Mohuřice", radky)
        self.assertIn("vznik: 1887", radky)
        self.assertIn("událost: vznik 1887", radky)
        self.assertIn("literatura: Hájek: Návesní kaple, 2021", radky)
        self.assertIn("foto MIS: pohled od J – https://iispp.npu.cz/mis_public/documentDetail.htm?id=1", radky)
        self.assertEqual(radky[-2], "odkaz: https://www.pamatkovykatalog.cz/bozi-muka-680990")
        self.assertIn("1000133534 (CC BY 4.0)", radky[-1])


if __name__ == "__main__":
    unittest.main()
