"""Testy sdileni.py bez sítě: knihy z adres, odhad snímku, body a zápisy z dat projektu, fronta, souhlas.
Převzato ze skillu rodokmen (sarsonj/rodokmen-skill#185); navíc sčítání se nesdílí a souhlas „jen mapa“."""
import json, os, shutil, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import sdileni  # noqa: E402

PF = "https://www.portafontium.eu/register/soap-pn/kozlany-22"


class SdileniTest(unittest.TestCase):

    def setUp(self):
        self.puvodni = os.getcwd()
        self.projekt = tempfile.mkdtemp(prefix="sdileni_test_")
        os.makedirs(os.path.join(self.projekt, "data"))
        self.cesty = {k: getattr(sdileni, k) for k in ("ROOT", "DATA", "NASTAVENI", "FRONTA", "NAVRH")}
        sdileni.ROOT = self.projekt
        sdileni.DATA = os.path.join(self.projekt, "data")
        sdileni.NASTAVENI = os.path.join(sdileni.DATA, "sdileni.json")
        sdileni.FRONTA = os.path.join(self.projekt, "pracovni", "sdileni", "body.jsonl")
        sdileni.NAVRH = os.path.join(self.projekt, "pracovni", "sdileni")
        d = sdileni.DATA
        json.dump({"pf_k22": {"url": PF, "svazek": "Kožlany 22, Matrika zemřelých"},
                   "aron_x": {"url": "https://aron.vychodoceskearchivy.cz/apu/x"}}, open(f"{d}/svazky.json", "w"))
        json.dump([{"klic": "stary", "svazek": "pf_k22", "snimek": 74, "druh": "Z", "datum": "17. 1. 1918"},
                   {"klic": "mlady", "svazek": "pf_k22", "snimek": 140, "druh": "Z", "datum": "3. 2. 1960"},
                   {"klic": "aron", "svazek": "aron_x", "snimek": 5, "druh": "N", "datum": "1. 1. 1800"},
                   {"klic": "scitani", "svazek": "pf_k22", "snimek": 9, "druh": "S", "datum": "1880"}],
                  open(f"{d}/zaznamy.json", "w"))
        json.dump({"stary": {"orig": "…"}, "mlady": {"orig": "…"}, "scitani": {"orig": "…"}}, open(f"{d}/prepisy.json", "w"))

    def tearDown(self):
        for k, v in self.cesty.items():
            setattr(sdileni, k, v)
        os.chdir(self.puvodni)
        shutil.rmtree(self.projekt, ignore_errors=True)

    def test_kniha_z_url(self):
        self.assertEqual(sdileni.kniha_z_url(PF), ("soa-plzen", "portafontium", "kozlany-22"))
        self.assertEqual(sdileni.kniha_z_url("https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/4888"),
                         ("soa-praha", "soapraha", "4888"))
        self.assertEqual(sdileni.kniha_z_url("https://ebadatelna.soapraha.cz/d/11973/15")[2], "11973")
        self.assertEqual(sdileni.kniha_z_url("https://katalog.ahmp.cz/pragapublica/permalink?xid=144286C6CCB648968F0C7879316827D0"),
                         (None, "ahmp", "144286c6"))
        self.assertIsNone(sdileni.kniha_z_url("https://aron.vychodoceskearchivy.cz/apu/abc"))

    def test_odhad(self):
        body = [{"scan": 10, "year": 1800}, {"scan": 30, "year": 1810}, {"scan": 40, "year": 1812, "year_to": 1813}]
        self.assertEqual(sdileni.odhad(body, 1805), (20, "odhad mezi sn. 10 (1800) a 30 (1810)"))
        self.assertEqual(sdileni.odhad(body, 1813)[0], 40)
        self.assertIsNone(sdileni.odhad(body, 1700))
        self.assertEqual(sdileni.slug("Nová Ves u Plzně"), "nova-ves-u-plzne")

    def test_body_a_zapisy(self):
        b, z, mimo, klic = sdileni.nove()
        self.assertEqual({x["year"] for x in b}, {1918, 1960})       # sčítání (S) do mapy jako druh zápisu nejde
        self.assertEqual([x["klic"] for x in z], ["stary"])          # do indexu jen zápis starší lhůty, bez sčítání
        self.assertEqual(mimo, {"aron_x"})
        sdileni.bod("pf_k22", "3", "rok=1900", "druh=Z", "rejstrik=A–C")
        b2, _, _, _ = sdileni.nove()
        self.assertTrue(any(x.get("type") == "iZ" and x.get("letters") == "A–C" for x in b2))
        n = sdileni.nastaveni()
        n["odeslano"]["body"] = [klic(x) for x in b2]
        n["odeslano"]["zapisy"] = ["stary"]
        self.assertEqual(sdileni.nove(n)[:2], ([], []))              # odeslané se znovu nenabízí

    def test_souhlas_jen_mapa(self):
        with self.assertRaises(SystemExit):
            sdileni.odeslat()                                        # bez souhlasu nic
        sdileni.souhlas("mapa")
        self.assertEqual(sdileni.nastaveni()["souhlas"], "mapa")
        with self.assertRaises(SystemExit) as e:
            sdileni.odeslat("index")
        self.assertIn("jen pro mapu", str(e.exception))

    def test_kanal_schranka(self):
        sdileni.souhlas("mapa")
        sdileni.kanal("schranka")
        volano = []
        puvodni = sdileni.odeslat_schrankou, sdileni.ma_github
        sdileni.odeslat_schrankou = lambda n, body, klic, se_zapisy: volano.append((len(body), se_zapisy)) or ([], [])
        sdileni.ma_github = lambda: True                             # i s přihlášeným gh jde přes schránku
        try:
            sdileni.odeslat()
        finally:
            sdileni.odeslat_schrankou, sdileni.ma_github = puvodni
        self.assertEqual(volano, [(2, False)])                       # dva body, žádné zápisy do indexu


if __name__ == "__main__":
    unittest.main()
