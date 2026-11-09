"""Testy zanikleobce.py: výběr míst podle polohy a názvu, rozbor stránky místa. Bez internetu."""
import os, sys, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import zanikleobce  # noqa: E402

# zkrácené záznamy z mapy webu (9. 11. 2026)
KOLINUV = {"id": 19495, "n": "Kolínů mlýn", "lat": 48.8296, "lon": 14.5886, "kat": "prumysl", "url": "/misto/19495-kolinu-mlyn/"}
STITINA = {"id": 4131, "n": "Štítina", "lat": 49.9152, "lon": 18.0142, "kat": "hrad", "url": "/misto/4131-stitina/",
           "img": "/img/x_s.jpg", "popis": "Jméno Štítina se poprvé\nobjevuje v r. 1282"}
MISTA = [KOLINUV, STITINA]

# zkrácená stránka místa (Pleticha, 9. 11. 2026)
STRANKA = """<div class="card">
	<h1 class="misto-nazev">
		Pleticha		 <span style="font-weight:400;">(Pleticher)</span></h1>
		<p class="misto-altnazvy">Alternativní názvy: Pletichův dvůr, Těžák,</p>
		<p class="datum">[místo vložil <a href="/prispevatel/1726-zdenek-pechar/">Zdeněk Pechar</a>, 16.5.2009]</p>
	<p>
		<b>Okres:</b> <a href="/databaze/?okr=3302">Český Krumlov</a><br>		<b>Typ:</b> <a href="/databaze/?typ=165">Dvůr</a><br>
	</p>
	</div>
<div class="section-title">Vývoj počtu obyvatel a domů</div><table><tr><td>Rok</td><td>1921</td></tr></table>
<div class="section-title">Dobové fotografie</div>
<div class="foto-grid"> <figure> <a href="/obrazek/27087-pozdrav/"> <img src="/img/00/27087_s.jpg" alt="pozdrav"> </a> <figcaption>pozdrav</figcaption> </figure> </div>
<div class="section-title">Historie a další články</div>
<div class="card"> <p> <a href="/clanek/1458721-pleticha/"><b>Pleticha</b></a> <span class="datum">[<a href="/prispevatel/5916-kamil-klusak/">Kamil Klusák</a>, 10.1.2012]</span><br> zemědělská usedlost ,stavení č.p.96 a 97 ,patřící rodině Lischka. </p> </div>
<div class="section-title" id="komentare">Komentáře</div>
<div class="card"><p class="datum">Žádné záznamy.</p></div>
<script>var MISTA = [];</script>"""


class NajdiTest(unittest.TestCase):

    def test_okruh(self):
        nalez = zanikleobce.najdi(MISTA, 48.82986, 14.61558, polomer=3)
        self.assertEqual([m["id"] for _, m in nalez], [19495])
        self.assertAlmostEqual(nalez[0][0], 2.0, delta=0.1)

    def test_podle_nazvu_bez_polohy(self):
        self.assertEqual([m["id"] for _, m in zanikleobce.najdi(MISTA, obec="Štítina")], [4131])

    def test_radek(self):
        self.assertEqual(zanikleobce.radek(0.42, STITINA),
                         "  4131 | Štítina | hrad, tvrz | 0.4 km | fotky | https://www.zanikleobce.cz/misto/4131-stitina/\n"
                         "      Jméno Štítina se poprvé objevuje v r. 1282")


class DetailTest(unittest.TestCase):

    def test_hlavicka(self):
        self.assertEqual(zanikleobce.hlavicka(STRANKA), [
            ("Název", "Pleticha (Pleticher)"), ("Jiné názvy", "Pletichův dvůr, Těžák"),
            ("Vložil", "Zdeněk Pechar, 16.5.2009"), ("Okres", "Český Krumlov"), ("Typ", "Dvůr")])

    def test_sekce_fotky_clanky(self):
        s = zanikleobce.sekce(STRANKA)
        self.assertEqual(list(s), ["Vývoj počtu obyvatel a domů", "Dobové fotografie", "Historie a další články", "Komentáře"])
        self.assertEqual(zanikleobce.fotky(s["Dobové fotografie"]),
                         [("pozdrav", "https://www.zanikleobce.cz/obrazek/27087-pozdrav/")])
        self.assertEqual(zanikleobce.clanky(s["Historie a další články"]),
                         [("Pleticha", "Kamil Klusák, 10.1.2012", "zemědělská usedlost, stavení č.p.96 a 97, patřící rodině Lischka.",
                           "https://www.zanikleobce.cz/clanek/1458721-pleticha/")])

    def test_detail(self):
        with mock.patch.object(zanikleobce, "stahni", return_value=STRANKA):
            radky = zanikleobce.detail("9459")
        vystup = "\n".join(radky)
        self.assertIn("Vývoj počtu obyvatel a domů: Rok 1921", vystup)
        self.assertIn("Dobové fotografie: 1\n  pozdrav |", vystup)
        self.assertIn("č.p.96 a 97", vystup)
        self.assertNotIn("Komentáře:", vystup)
        self.assertIn("Citace: Pleticha (Pleticher), Zaniklé obce a objekty (zanikleobce.cz), místo vložil Zdeněk Pechar, "
                      "16.5.2009, https://www.zanikleobce.cz/misto/9459/", vystup)

    def test_detail_spatne_id(self):
        with self.assertRaises(SystemExit):
            zanikleobce.detail("pleticha")


if __name__ == "__main__":
    unittest.main()
