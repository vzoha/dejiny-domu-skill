"""Testy rejstrik.py (ARES: subjekty se sídlem v domě, detail z veřejného rejstříku). Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import rejstrik  # noqa: E402

# zkrácené skutečné odpovědi ARES (8. 11. 2026)
ADRESY = {"standardizovaneAdresy": [
    {"kodCastiObce": 490067, "typCisloDomovni": 1, "textovaAdresa": "Dlouhá 812/5, Holešovice, 17000 Praha 7"},
    {"kodCastiObce": 490067, "typCisloDomovni": 1, "textovaAdresa": "Krátká 812/9, Holešovice, 17000 Praha 7"},
    {"kodCastiObce": 490067, "typCisloDomovni": 2, "textovaAdresa": "č.ev. 812, Holešovice, 17000 Praha 7"},
    {"kodCastiObce": 123456, "typCisloDomovni": 1, "textovaAdresa": "č.p. 812, Holešovice"}]}
SVJ = {"ico": "12345678", "obchodniJmeno": "Společenství vlastníků jednotek Dlouhá 5, Krátká 9/812, Praha 7",
       "pravniForma": "145", "datumVzniku": "2001-10-23",
       "sidlo": {"typCisloDomovni": 1, "textovaAdresa": "Krátká 812/9, Holešovice, 17000 Praha 7"}}
ZIVNOSTNIK = {"ico": "18442846", "obchodniJmeno": "Ing. Radek Šmejkal", "pravniForma": "101",
              "sidlo": {"typCisloDomovni": 1, "textovaAdresa": "Dlouhá 812/5, Holešovice, 17000 Praha 7"}}
EVIDENCNI = {"ico": "1", "obchodniJmeno": "Chata s.r.o.", "pravniForma": "112",
             "sidlo": {"typCisloDomovni": 2, "textovaAdresa": "č.ev. 812"}}
FORMY = {"145": "Společenství vlastníků jednotek", "101": "Fyzická osoba podnikající dle živnostenského zákona",
         "112": "Společnost s ručením omezeným", "421": "Zahraniční fyzická osoba"}
VR = {"zaznamy": [
    {"primarniZaznam": False, "stavSubjektu": "HISTORICKY", "obchodniJmeno": [{"hodnota": "Starý záznam"}]},
    {"primarniZaznam": True, "stavSubjektu": "AKTIVNI", "datumZapisu": "2001-10-23",
     "obchodniJmeno": [{"datumZapisu": "2001-10-23", "hodnota": SVJ["obchodniJmeno"]}],
     "adresy": [{"datumZapisu": "2001-10-23", "datumVymazu": "2016-12-07", "typAdresy": "SIDLO",
                 "adresa": {"textovaAdresa": "Krátká 812/9, Holešovice, 17000 Praha 7"}},
                {"typAdresy": "DORUCOVACI", "adresa": {"textovaAdresa": "jinde"}}],
     "ostatniSkutecnosti": [{"datumZapisu": "2001-10-23", "hodnota": "Datum vzniku společenství: 1.7.2000."}],
     "spisovaZnacka": [{"soud": "MSPH", "oddil": "A", "vlozka": 45573, "datumVymazu": "2016-12-07"},
                       {"soud": "MSPH", "oddil": "S", "vlozka": 1429}],
     "statutarniOrgany": [{"clenoveOrganu": [{"fyzickaOsoba": {"jmeno": "Jan", "prijmeni": "Žijící"}}]}]}]}


def http_404(*_):
    raise rejstrik.urllib.error.HTTPError("u", 404, "Not Found", {}, None)


class RejstrikTest(unittest.TestCase):

    def test_domy_jen_popisna_cisla_po_castech_obce(self):
        domy = rejstrik.domy("Holešovice", 812, nacti=lambda cesta, telo: ADRESY)
        self.assertEqual(domy, {490067: ["Dlouhá 812/5, Holešovice, 17000 Praha 7",
                                         "Krátká 812/9, Holešovice, 17000 Praha 7"],
                                123456: ["č.p. 812, Holešovice"]})

    def test_subjekty_strankuje_a_vynecha_evidencni_cislo(self):
        strany = [{"pocetCelkem": 3, "ekonomickeSubjekty": [SVJ, EVIDENCNI]},
                  {"pocetCelkem": 3, "ekonomickeSubjekty": [ZIVNOSTNIK]}]
        telo = []
        nalez = rejstrik.subjekty(490067, 812, nacti=lambda cesta, t: telo.append(t) or strany[len(telo) - 1])
        self.assertEqual([s["ico"] for s in nalez], ["12345678", "18442846"])
        self.assertEqual([t["start"] for t in telo], [0, 2])

    def test_je_clovek(self):
        self.assertTrue(rejstrik.je_clovek(ZIVNOSTNIK, FORMY))
        self.assertTrue(rejstrik.je_clovek({"pravniForma": "421"}, FORMY))
        self.assertFalse(rejstrik.je_clovek(SVJ, FORMY))

    def test_pravni_formy_dnesni_nazev(self):
        ciselnik = {"ciselniky": [{"polozkyCiselniku": [
            {"kod": "801", "platnostDo": "2001-12-31", "nazev": [{"kodJazyka": "cs", "nazev": "Obec (obecní úřad)"}]},
            {"kod": "801", "platnostDo": "9999-09-09", "nazev": [{"kodJazyka": "cs", "nazev": "Obec nebo městská část"}]},
            {"kod": "103", "platnostDo": "2009-04-30", "nazev": [{"kodJazyka": "cs", "nazev": "Samostatně hospodařící rolník"}]}]}]}
        formy = rejstrik.pravni_formy(nacti=lambda cesta, telo: ciselnik)
        self.assertEqual(formy, {"801": "Obec nebo městská část", "103": "Samostatně hospodařící rolník"})

    def test_radek(self):
        self.assertEqual(rejstrik.radek(SVJ, FORMY), "  12345678 | " + SVJ["obchodniJmeno"] + " | Společenství vlastníků "
                         "jednotek | od 2001-10-23 | Krátká 812/9, Holešovice, 17000 Praha 7 | "
                         "https://or.justice.cz/ias/ui/rejstrik-$firma?ico=12345678&jenPlatne=VSECHNY")

    def test_detail_z_rejstriku_bez_osob(self):
        radky = rejstrik.detail("12345678", nacti=lambda cesta: VR)
        self.assertIn("Stav: AKTIVNI, zápis 2001-10-23", radky)
        self.assertIn("Sídlo 2001-10-23–2016-12-07: Krátká 812/9, Holešovice, 17000 Praha 7", radky)
        self.assertIn("Ostatní skutečnosti 2001-10-23–dosud: Datum vzniku společenství: 1.7.2000.", radky)
        self.assertIn("Spisová značka: S 1429, MSPH", radky)
        self.assertNotIn("Spisová značka: A 45573, MSPH", radky)
        self.assertFalse(any("jinde" in r or "Žijící" in r or "Starý záznam" in r for r in radky))

    def test_detail_mimo_rejstrik(self):
        zakladni = {"obchodniJmeno": "Základní škola", "sidlo": {"textovaAdresa": "Školní 713"}, "datumVzniku": "1995-01-24"}
        radky = rejstrik.detail("1", nacti=lambda cesta: http_404() if "-vr/" in cesta else zakladni)
        self.assertIn("Název: Základní škola", radky)
        self.assertIn("Vznik: 1995-01-24", radky)

    def test_detail_prazdny_rejstrik_ze_zakladnich_udaju(self):
        zakladni = {"obchodniJmeno": "Spolek", "sidlo": {"textovaAdresa": "Náves 1"}}
        radky = rejstrik.detail("2", nacti=lambda cesta: {"zaznamy": []} if "-vr/" in cesta else zakladni)
        self.assertIn("Název: Spolek", radky)

    def test_detail_neni(self):
        with self.assertRaises(SystemExit):
            rejstrik.detail("99999999", nacti=http_404)


if __name__ == "__main__":
    unittest.main()
