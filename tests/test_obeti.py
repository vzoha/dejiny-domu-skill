"""Testy obeti.py (Databáze obětí holocaust.cz): výpis hledání, detail, filtr ulice a čísla, souhlas. Bez internetu."""
import contextlib, io, os, sys, tempfile, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import obeti, souhlas  # noqa: E402

# zkrácené skutečné stránky (14. 11. 2026)
HLEDANI = """<p>Celkem nalezeno: 2</p>
<div class="victims-wrapper">
<a href="https://www.holocaust.cz/databaze-obeti/obet/10001-jan-novak/"><img src="x.png"></a>
<p>
    <a href="https://www.holocaust.cz/databaze-obeti/obet/10001-jan-novak/">Jan Novák</a><br/>
        Narozen 03. 04. 1890.<br/>
        Terezín. 
        Osvětim. 
    <br/>
    Zahynul.<br/>
</p>
<a href="https://www.holocaust.cz/databaze-obeti/obet/10001-jan-novak/" class="more">Více</a>
</div>
<div class="victims-wrapper">
<p><a href="https://www.holocaust.cz/databaze-obeti/obet/10002-josef-dvorak/">Josef Dvořák</a><br/>Narozen 5. 6. 1891.<br/></p>
</div>
"""
DETAIL = """<div class="detailvictim">
<h1>
        Josef Dvořák
</h1>
<div class="wrapper">
    <img src="x.jpg" width="200">
    <p>
        <b>Narozen 5. 6. 1891</b><br/>Poslední bydliště před deportací: Praha I<br/>Adresa/místo registrace v Protektorátu: Praha I, Dlouhá 18<br/>Transport X, č. 100&nbsp;(16. 07. 1942, Praha -> Terezín)<br/>Zahynul<br/>
    </p>
</div>
<h2>související dokumenty</h2>
    <div class="victim-documents">
        <a href="https://www.holocaust.cz/databaze-dokumentu/dokument/20001-dvorak-josef-nezpracovano/">
            <div class="victim-documents-picture"><img src="y.jpg"></div>
            <span>Dvořák Josef: NEZPRACOVÁNO</span>
"""


class Cteni(unittest.TestCase):
    def test_vysledky(self):
        v = obeti.vysledky(HLEDANI)
        self.assertEqual([r["jmeno"] for r in v], ["Jan Novák", "Josef Dvořák"])
        self.assertEqual(v[0]["info"], "Narozen 03. 04. 1890. | Terezín. Osvětim. | Zahynul.")
        self.assertEqual(obeti.celkem(HLEDANI), 2)
        self.assertIsNone(obeti.dalsi(HLEDANI))

    def test_detail(self):
        d = obeti.detail_z(DETAIL)
        self.assertEqual(d["jmeno"], "Josef Dvořák")
        self.assertEqual(d["adresa"], "Praha I, Dlouhá 18")
        self.assertIn("Transport X, č. 100 (16. 07. 1942, Praha -> Terezín)", d["radky"])
        self.assertEqual(d["dokumenty"][0][0], "Dvořák Josef: NEZPRACOVÁNO")
        self.assertIsNone(obeti.detail_z("<html></html>"))


class Ulice(unittest.TestCase):
    def test_cisla(self):
        self.assertEqual(obeti.cisla_adresy("Praha I, Dlouhá 13/745", "Dlouha"), {"13", "745"})
        self.assertEqual(obeti.cisla_adresy("Praha I, Rybná 16", "Dlouhá"), set())

    def test_filtr(self):
        a = "Praha I, Dlouhá 13/745"
        self.assertTrue(obeti.v_ulici(a, "Dlouhá"))
        self.assertTrue(obeti.v_ulici(a, "dlouha", ["745"], "Praha I"))
        self.assertFalse(obeti.v_ulici(a, "Dlouhá", ["27"]))
        self.assertFalse(obeti.v_ulici(a, "Dlouhá", obec="Praha XIII"))
        self.assertFalse(obeti.v_ulici("Praha XIII, Kolínská 2205", "Dlouhá", ["2205"]))

    def test_ulice_bez_cisla_a_vypis(self):
        stranky = {obeti.BASE: HLEDANI, "https://www.holocaust.cz/databaze-obeti/obet/10001-jan-novak/":
                   DETAIL.replace("Josef Dvořák", "Jan Novák").replace("Dlouhá 18", "Dlouhá 13/745"),
                   "https://www.holocaust.cz/databaze-obeti/obet/10002-josef-dvorak/": DETAIL}
        dotazy = []

        def get(url, data=None):
            dotazy.append(data)
            return stranky[url]
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(obeti, "get", get), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            obeti.cmd_ulice("Dlouhá 27", ["18"], "", 100)
        self.assertEqual(dotazy[0]["searchPlaceLast"], "Dlouhá")
        self.assertIn("Praha I, Dlouhá 18\n  Josef Dvořák", out.getvalue())
        self.assertNotIn("Jan Novák", out.getvalue())
        self.assertIn("1 obětí na 1 adresách z 2 prověřených", err.getvalue())


class Souhlas(unittest.TestCase):
    def test_bez_souhlasu_skonci(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"SOUHLAS_STAV": d}), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            obeti.main(["detail", "1-x"])
        self.assertEqual(e.exception.code, souhlas.KOD)

    def test_souhlas_jen_v_terminalu(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"SOUHLAS_STAV": d}), \
                mock.patch("sys.stdin.isatty", return_value=False), contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit):
            obeti.main(["souhlas"])
        self.assertFalse(souhlas.ma_souhlas(obeti.SOUHLAS_KLIC, obeti.SOUHLAS_ZNENI))


if __name__ == "__main__":
    unittest.main()
