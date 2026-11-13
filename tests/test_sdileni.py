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
                         ("ahmp", "ahmp", "144286c6"))
        self.assertIsNone(sdileni.kniha_z_url("https://aron.vychodoceskearchivy.cz/apu/abc"))
        self.assertIsNone(sdileni.kniha_z_url("https://www.mza.cz/actapublica/"))

    def test_kniha_z_url_dalsi_archivy(self):
        # archivy, které sběrná schránka mapy přijímá od mapa-matrik#121; index matrik je zatím nemá
        for url, cekam in [
            ("https://digi.ceskearchivy.cz/127297", ("soa-trebon", None, "127297")),
            ("https://digi.ceskearchivy.cz/DA?lang=cs&id=123456&page=65", ("soa-trebon", None, "123456")),
            ("https://www.mza.cz/actapublica/matrika/detail/3877", ("mza-brno", None, "3877")),
            ("https://digi.archives.cz/da/permalink?xid=30C10FB1ABF54A70AC9B3E54E52E3FD9", ("za-opava", None, "30c10fb1-abf5-4a70-ac9b-3e54e52e3fd9")),
            ("https://digi.archives.cz/da/permalink?xid=be930f8c-f13c-102f-8255-0050568c0263",   # mapa má xid s pomlčkami
             ("za-opava", None, "be930f8c-f13c-102f-8255-0050568c0263")),
            ("https://digi.soalitomerice.cz/da/permalink?xid=6e4224c5253a499fa16337279f1a0daf", ("soa-litomerice", None, "6e4224c5-253a-499f-a163-37279f1a0daf")),
            ("https://aron.vychodoceskearchivy.cz/apu/1b2c3d4e-0000-4a5b-8c9d-0123456789ab",
             ("soa-zamrsk", None, "1b2c3d4e-0000-4a5b-8c9d-0123456789ab")),
            ("https://katalog.ahmp.cz/pragapublica/permalink?xid=168D806EE15440A2BA47401D7F3EAA53&scan=1", ("ahmp", "ahmp", "168d806e")),
        ]:
            self.assertEqual(sdileni.kniha_z_url(url), cekam, url)

    def test_rozsah_knihy(self):
        self.assertEqual(sdileni.rozsah_knihy("Beroun 52, N 1900–1905"), {"N": "1900–1905"})
        self.assertEqual(sdileni.rozsah_knihy("Matrika N, O, Z Rynárec 1757–1849, kniha 2"),
                         {"N": "1757–1849", "O": "1757–1849", "Z": "1757–1849"})
        self.assertEqual(sdileni.rozsah_knihy("Matrika narozených Rynárec 1842-1857, kniha 6"), {"N": "1842–1857"})
        self.assertEqual(sdileni.rozsah_knihy("Dolní Kounice, narození a oddaní 1676–1758, zemřelí 1686–1758"), {})  # dva rozsahy
        self.assertEqual(sdileni.rozsah_knihy("127 1840-1881"), {})                  # druh neznámý
        self.assertEqual(sdileni.rozsah_knihy("Kožlany 22, Matrika zemřelých"), {})  # bez let

    def test_podpis_knihy(self):
        # schránka z podpisu odvodí farnost (ořízne číslo na konci), proto „Farnost číslo“
        for popis, cekam in [
            ("Beroun 52, N 1900–1905", "Beroun 52"),
            ("Matrika Trhové Sviny 9, N 1846-1859", "Trhové Sviny 9"),
            ("Trhové Sviny 21 1874-1911", "Trhové Sviny 21"),
            ("Matrika narozených Rynárec 1842–1857, kniha 6 (Pavlov a další obce)", "Rynárec 6"),
            ("Matrika N, O, Z Rynárec 1757–1849, kniha 2 (celá farnost)", "Rynárec 2"),
            ("Matrika N 1805–1837 Svatoslav (Radoškov sn. 57–95)", "Svatoslav"),
            ("Matrika O 1841–1896 Dolní Loučky", "Dolní Loučky"),
            ("Neslovice, narození 1784–1855 (kniha 1413), oddíl Hlína snímky 88–136", "Neslovice 1413"),
        ]:
            self.assertEqual(sdileni.podpis_knihy(popis), cekam, popis)

    def test_schranka_posle_rozsah_knihy(self):
        json.dump({"eb": {"url": "https://ebadatelna.soapraha.cz/d/14161/", "svazek": "Beroun 52, N 1900–1905", "snimku": 408},
                   "tr": {"url": "https://digi.ceskearchivy.cz/127297", "svazek": "Rynárec 7, N 1857–1872"}},
                  open(f"{sdileni.DATA}/svazky.json", "w"))
        poslano = []

        class Odpoved:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{"mapa": null, "index": null}'
        puvodni = sdileni.urllib.request.urlopen, sdileni.brzda
        sdileni.urllib.request.urlopen = lambda req, timeout: poslano.append(json.loads(req.data)) or Odpoved()
        sdileni.brzda = lambda url: None
        try:
            body = [{"svazek": "eb", "scan": 40, "type": "N", "year": 1902}, {"svazek": "tr", "scan": 9, "type": "N", "year": 1860}]
            b, _ = sdileni.odeslat_schrankou(sdileni.nastaveni(), body, lambda x: x["svazek"], False)
        finally:
            sdileni.urllib.request.urlopen, sdileni.brzda = puvodni
        self.assertEqual(b, ["eb", "tr"])
        eb, tr = poslano[0]["body"]
        self.assertEqual(eb["records"], {"N": "1900–1905"})          # Beroun 52 pak mapa najde i pro rok 1904
        self.assertEqual((tr["archive"], tr["portal_id"], tr["url"], tr["signature"]),
                         ("soa-trebon", "127297", "https://digi.ceskearchivy.cz/127297", "Rynárec 7"))
        self.assertEqual(poslano[0]["nastroj"], "dejiny-domu/sdileni.py")

    def test_zapisy_jen_z_archivu_indexu(self):
        json.dump({"tr": {"url": "https://digi.ceskearchivy.cz/127297", "svazek": "Rynárec 2, N, O, Z 1757–1849"}},
                  open(f"{sdileni.DATA}/svazky.json", "w"))
        json.dump([{"klic": "t1", "svazek": "tr", "snimek": 12, "druh": "N", "datum": "1. 1. 1800"}], open(f"{sdileni.DATA}/zaznamy.json", "w"))
        json.dump({"t1": {"orig": "…"}}, open(f"{sdileni.DATA}/prepisy.json", "w"))
        b, z, mimo, _ = sdileni.nove()
        self.assertEqual(([x["svazek"] for x in b], z, mimo), (["tr"], [], set()))   # bod do mapy ano, do indexu ne

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
