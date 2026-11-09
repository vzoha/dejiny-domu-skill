"""Testy brno_scitani.py (sčítání lidu Brna 1850–1921, Digitální archiv AMB). Bez internetu."""
import contextlib, io, os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import brno_scitani  # noqa: E402

# zkrácené skutečné odpovědi (9. 11. 2026)
OPERATY = [{"year": 1880, "streetName": "Kröna", "houseNumber": "75", "numberOfPeople": 32, "existOperatImage": True,
            "idAipv": "0b84a8e7"},
           {"year": 1870, "streetName": "Kröna", "houseNumber": "75", "numberOfPeople": 205, "existOperatImage": False,
            "idAipv": None}]
LIDE_1880 = [{"surname": "Chafranek", "firstName": "Josefa", "regVolume": "A-E", "regPage": "143b", "regLine": 12},
             {"surname": "Jeřabek", "firstName": "Mathias", "regVolume": "J-K", "regPage": "31a", "regLine": 18},
             {"surname": "Beranek", "firstName": "Stefan", "regVolume": "A-E", "regPage": "62a", "regLine": 3},
             {"surname": " \n ", "firstName": " ", "regVolume": "A-E", "regPage": "1", "regLine": 1}]
for _clovek in LIDE_1880:
    _clovek.update(year=1880, streetName="Kröna", houseNumber="75")


def odpoved(vysledky, stran=1, strana=1):
    return {"results": vysledky, "numberOfRecords": len(vysledky) * stran, "numberOfPages": stran, "currentPage": strana}


def vystup(funkce, *argumenty):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        funkce(*argumenty)
    return out.getvalue()


class BrnoScitaniTest(unittest.TestCase):

    def test_dum_rok_po_roce_a_odkaz_do_prohlizece(self):
        with mock.patch.object(brno_scitani, "cti", return_value=odpoved(OPERATY)):
            out = vystup(brno_scitani.vypis_dum, "Kröna", "75")
        self.assertLess(out.index("1870 | Kröna 75 | osob 205"), out.index("1880 | Kröna 75 | osob 32"))
        self.assertIn("osob 205 | snímek operátu ne", out)
        self.assertIn("/search/operates?streetName=Kr%C3%B6na&houseNumber=75", out)

    def test_osoby_razene_podle_rejstriku_a_prazdna_jmena_zvlast(self):
        def cti(cesta, telo):
            return odpoved(LIDE_1880) if "surname" in telo else odpoved(OPERATY[:1])
        with mock.patch.object(brno_scitani, "cti", side_effect=cti) as volani:
            out = vystup(brno_scitani.vypis_osoby, "Kröna", "75")
        self.assertEqual(volani.call_args.args[1], {"streetName": "Kröna", "houseNumber": "75", "yearOfCensus": "1880",
                                                    "surname": "%"})
        self.assertIn("1 řádků bez čitelného jména", out)
        radky = [r.split(" | ")[0].strip() for r in out.splitlines() if r.startswith("   ") and "rejstřík " in r]
        self.assertEqual(radky, ["Beranek Stefan", "Chafranek Josefa", "Jeřabek Mathias"])   # 62a před 143b

    def test_strankovani_skonci_na_posledni_strane(self):
        strany = [odpoved(LIDE_1880[:2], stran=2, strana=1), odpoved(LIDE_1880[2:3], stran=2, strana=2)]
        with mock.patch.object(brno_scitani, "cti", side_effect=strany) as volani:
            lide, celkem = brno_scitani.vsechny_strany("/search", {"surname": "X"})
        self.assertEqual(len(lide), 3)
        self.assertEqual([c.args[0] for c in volani.call_args_list], ["/search?page=1", "/search?page=2"])

    def test_hledej_hlasi_neuplny_vypis(self):
        with mock.patch.object(brno_scitani, "NEJVIC_STRAN", 1), \
             mock.patch.object(brno_scitani, "cti", return_value=odpoved(LIDE_1880[:2], stran=5)):
            out = vystup(brno_scitani.vypis_hledej, "Chafranek", None, "1880")
        self.assertIn("vypsáno 2 z 10", out)

    def test_rok_v_argumentech_neni_cislo_domu(self):
        with mock.patch.object(brno_scitani, "vypis_dum") as dum, \
             mock.patch.object(sys, "argv", ["brno_scitani.py", "dum", "Kröna", "75", "1880"]):
            brno_scitani.main()
        dum.assert_called_once_with("Kröna", "75", "1880")


if __name__ == "__main__":
    unittest.main()
