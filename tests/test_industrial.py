"""Testy industrial.py (Industriální topografie VCPD FA ČVUT): výpis, detail a pojistka čtení. Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import industrial  # noqa: E402

# zkrácené skutečné výsledky structure/filter (8. 11. 2026)
PIVOVAR = {"id": 762, "nameOriginal": "Měšťanský (Nový) pivovar", "addressCity": "Beroun", "addressCityDistrict": "Město",
           "okecList": [{"name": "pivovar"}, {"name": "sladovna"}],
           "datings": [{"yearFrom": 1295, "yearTo": None}, {"yearFrom": 1870, "yearTo": 1871}]}
MLYN = {"id": 94, "nameOriginal": "Akciový parní mlýn", "addressCity": "Praha 7", "addressCityDistrict": "Holešovice",
        "okecList": [{"name": "mlýn, pekárna"}], "datings": []}
MOST = {"id": 12355, "nameOriginal": "Železniční most přes Berounku", "addressCity": "Černošice",
        "addressCityDistrict": None, "okecList": [{"name": "most, lávka"}], "datings": [{"yearFrom": 1862}]}


class IndustrialTest(unittest.TestCase):

    def setUp(self):   # detaily objektů bez internetu: okres a text zmínky
        industrial._detaily.clear()
        industrial._detaily.update({
            762: {"address": {"district": "Beroun"}},
            12355: {"nameOriginal": "Železniční most přes Berounku", "descriptionPublic": "Most u Berouna, okres Beroun."},
            16414: {"literature": '<a href="http://hrebecskedulnistezky.cz">hrebecskedulnistezky.cz</a>'}})

    def test_v_miste_s_okresem_a_jinde(self):
        radky = industrial.vypis([PIVOVAR, MOST], "Beroun")
        self.assertEqual(radky[0], "\nV místě „Beroun“ (obec, část obce): 1")
        self.assertEqual(radky[1], "  762 | Měšťanský (Nový) pivovar | Beroun – Město (okres Beroun) | pivovar, sladovna | 1295, 1870–1871")
        self.assertEqual(radky[2], "\nJinde, obec zmíněná v textu: 1")

    def test_cast_obce_bez_diakritiky(self):
        industrial._detaily[94] = {}
        self.assertEqual(industrial.vypis([MLYN], "holesovice")[0], "\nV místě „holesovice“ (obec, část obce): 1")

    def test_podobny_nazev_obce_zvlast(self):
        vlachovo = dict(PIVOVAR, id=3528, addressCity="Vlachovo Březí", addressCityDistrict=None)
        self.assertEqual(industrial.vypis([vlachovo], "Březí")[0], "\nObce a části s podobným názvem: 1")

    def test_zminka_uvnitr_slova_neplati(self):
        dul = dict(MOST, id=16414, nameOriginal="Důl Václav – Theodor", addressCity="Koclířov")
        self.assertEqual(industrial.vypis([dul], "Lniště"), [])

    def test_velkou_skupinu_jen_spocita(self):
        mosty = [dict(MOST, id=i) for i in range(industrial.SKUPINA_NEJVIC + 5)]
        radky = industrial.vypis(mosty, "Beroun")
        self.assertEqual(radky[0], f"\nJinde, neověřeno (fulltext hledá i uvnitř slov, zužuj výrazem): {industrial.SKUPINA_NEJVIC + 5}")
        self.assertIn("zúží je hledaný výraz", radky[1])
        self.assertEqual(len(radky), 2)

    def test_vyraz_v_nazvu_nebo_druhu(self):
        self.assertTrue(industrial.ma_vyraz(MLYN, "mlyn"))
        self.assertTrue(industrial.ma_vyraz(PIVOVAR, "sladovna"))
        self.assertFalse(industrial.ma_vyraz(MOST, "mlýn"))

    def test_odkaz(self):
        self.assertEqual(industrial.odkaz(762, "Měšťanský (Nový) pivovar"),
                         "https://www.industrialnitopografie.cz/cs/structures/mestansky-novy-pivovar-762")

    def test_post_jen_na_filter(self):
        # holá cesta kolekce záznam založí (structureMap, 8. 11. 2026) – na síť se nesmí dostat
        with self.assertRaises(ValueError):
            industrial.cti("structureMap", {"filterColumns": []})

    def test_filtr_jako_web(self):
        f = industrial.filtr({"city": "Beroun"}, 1)
        self.assertEqual(f["page"], 1)
        self.assertEqual(f["filterColumns"], [{"name": "city", "filters": [{"combination": 0, "value": "Beroun", "operation": 1}]}])

    def test_detail(self):
        d = {"id": 762, "internalNumber": "V21259", "nameOriginal": "Měšťanský (Nový) pivovar",
             "address": {"streetAndNumber": "V Zahradách", "city": "Beroun", "cityDistrict": "Město", "district": "Beroun"},
             "okecList": [{"name": "pivovar"}], "conditionList": [{"name": "zbořeno"}], "lat": 49.96732, "lng": 14.0718972,
             "structureDatation": [{"yearFrom": 1295, "description": "založen"}],
             "descriptionPublic": 'Vařil od 1872. Zapsán na <a href="https://www.pamatkovykatalog.cz/x-1 " target="_blank">seznam</a>.',
             "literature": "Pavel Jákl, <em>Encyklopedie pivovarů</em>, Praha 2004, s. 18.",
             "topPartyRelationships": [{"name": "Josef Zobel", "partyRelationshipType": "stavitel"}],
             "photos": [{}, {}], "recordAuthors": [{"firstname": "Jan", "surname": "Pechánek"}] * 2}
        radky = industrial.popis(d)
        self.assertEqual(radky[0], "Měšťanský (Nový) pivovar (pivovar)")
        self.assertIn("adresa: V Zahradách, Město, Beroun, okres Beroun", radky)
        self.assertIn("datace: 1295 založen", radky)
        self.assertIn("stav: zbořeno", radky)
        self.assertIn("dějiny (shrň vlastními slovy, necituj celé): Vařil od 1872. Zapsán na seznam "
                      "(https://www.pamatkovykatalog.cz/x-1).", radky)
        self.assertIn("literatura: Pavel Jákl, Encyklopedie pivovarů, Praha 2004, s. 18.", radky)
        self.assertIn("osoba / firma: Josef Zobel (stavitel)", radky)
        self.assertIn("fotky: 2 na webu (jen odkazem, nepřebírat)", radky)
        self.assertEqual(radky[-1], "citace: Jan Pechánek, Měšťanský (Nový) pivovar, Industriální topografie VCPD FA ČVUT "
                                    "(www.industrialnitopografie.cz), [datum přístupu], V21259")


if __name__ == "__main__":
    unittest.main()
