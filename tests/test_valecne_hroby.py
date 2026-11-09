"""Testy valecne_hroby.py (Centrální evidence válečných hrobů MO): čtení detailu, výpis hrobu a padlého, filtr obce
a ORP. Bez internetu."""
import contextlib, io, json, os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import valecne_hroby  # noqa: E402

# zkrácené skutečné stránky detailu (9. 11. 2026)
HROB = """
<div class="mb-3"><label class="form-label" for="Region">Kraj</label>
<input class="k-input" id="Region" readonly="True" value="Jihočeský" /><script>kendo.x({"value":"Jihočeský"});</script></div>
<div class="mb-3"><label class="form-label" for="Orp">ORP</label><input value="Trhové Sviny" /></div>
<div class="mb-3"><label class="form-label" for="Municipality">Obec/újezd</label><input value="Slavče" /></div>
<div class="mb-3"><label class="form-label" for="Street">Ulice / č.p.</label><input value="náves - osada Lniště" /></div>
<div class="mb-3"><label for="HistoricEventsLocalisedText">Historick&#233; ud&#225;losti</label>
<span class="k-input preline">2. světová válka
1. světová válka</span></div>
<div class="mb-3"><label class="form-label" for="Remark">Pozn&#225;mka</label>
<span class="k-input preline">N&#225;pis: &quot;Na věčnou paměť.&quot;
Zhotovil: Karel Dvoř&#225;k</span>
        </div>
    </div>
    <div class="col-md-6"><h5>Dokumenty</h5></div>
"""
PADLY = """
<div class="mb-3"><label for="ICP">IČP</label><input value="1" /></div>
<div class="mb-3"><label for="FirstName">Jméno</label><input value="Václav" /><input value="Wenzel" /></div>
<div class="mb-3"><label for="BirthPlace">M&#237;sto narozen&#237;</label><input value="Obora" /></div>
<div class="mb-3"><label for="Home">Obec (Rakousko-Uhersko)</label><input value="Obora" /></div>
<div class="mb-3"><label for="District">Okres (Rakousko-Uhersko)</label><input value="Prachatitz / Prachatice" /></div>
<div class="mb-3"><label for="Death">Den úmrtí</label><input value="30.03.1915" /></div>
<div class="mb-3"><label for="DeathPlace">Místo úmrtí</label><input value="Jaworzec" /></div>
<div class="mb-3"><label for="Kramerius_dokument">Kramerius dokument</label>
  <p><a href="https://digitalnistudovna.army.cz/uuid/uuid:870d">V&#218;A–VHA, Kartot&#233;ka, Žemlička V&#225;clav 1885-1915.</a></p>
  <p><a href="https://digitalnistudovna.army.cz/uuid/uuid:0f87">Verlustliste Nr. 181, s. 46.</a></p>
</div>
"""
JMENA = [{"FullName": "Jakub Bícha", "DateOfBirth": "1881", "BirthLocation": "", "DeathLabel": "1914",
          "CauseOfDeath": "Padl v boji"},
         {"FullName": "Jan Šafránek", "DateOfBirth": "1893", "BirthLocation": "", "DeathLabel": "", "CauseOfDeath": "Jiné"}]


class PoleTest(unittest.TestCase):

    def test_hodnoty_z_inputu_a_textu(self):
        d = valecne_hroby.pole(HROB)
        self.assertEqual(d["Kraj"], "Jihočeský")   # skript s „value“ se nepočítá
        self.assertEqual(d["Ulice / č.p."], "náves - osada Lniště")
        self.assertEqual(d["Historické události"], "2. světová válka\n1. světová válka")
        self.assertEqual(d["Poznámka"], 'Nápis: "Na věčnou paměť."\nZhotovil: Karel Dvořák')   # bez nadpisů za polem

    def test_vic_hodnot_a_prameny_s_odkazem(self):
        d = valecne_hroby.pole(PADLY)
        self.assertEqual(d["Jméno"], "Václav, Wenzel")
        self.assertEqual(d["Kramerius dokument"],
                         "VÚA–VHA, Kartotéka, Žemlička Václav 1885-1915. (https://digitalnistudovna.army.cz/uuid/uuid:870d); "
                         "Verlustliste Nr. 181, s. 46. (https://digitalnistudovna.army.cz/uuid/uuid:0f87)")


class VypisTest(unittest.TestCase):

    def test_hrob(self):
        h = {"Id": "291a", "Identifier": "CZE3113-31463", "Character": "Pietní místo - objekt", "Municipality": "Slavče"}
        radky = valecne_hroby.vypis_hrobu(h, valecne_hroby.pole(HROB), JMENA).splitlines()
        self.assertEqual(radky[1], "CZE3113-31463 | Pietní místo - objekt | Slavče, náves - osada Lniště | ORP Trhové Sviny | ")
        self.assertIn("  Historické události: 2. světová válka / 1. světová válka", radky)
        self.assertIn("    Jakub Bícha, * 1881, † 1914 – Padl v boji", radky)
        self.assertIn("    Jan Šafránek, * 1893 – Jiné", radky)

    def test_padly(self):
        o = {"ICP": 1, "FirstName": "Václav (Wenzel)", "Surname": "Žemlička", "BirthYear": "1885"}
        radky = valecne_hroby.vypis_padleho(o, valecne_hroby.pole(PADLY)).splitlines()
        self.assertEqual(radky[1], "IČP 1 | Václav (Wenzel) Žemlička | * 1885 Obora | domovská obec: Obora, Prachatitz / Prachatice")
        self.assertEqual(radky[2], "  † 30.03.1915, Jaworzec")
        self.assertTrue(radky[-1].startswith("  prameny: VÚA–VHA, Kartotéka"))


class FiltrTest(unittest.TestCase):
    """hroby_obce a padli s podvrženým serverem."""

    def setUp(self):
        self.puvodni = valecne_hroby.otevri
        self.dotazy = []

    def tearDown(self):
        valecne_hroby.otevri = self.puvodni

    def server(self, odpovedi):
        def otevri(url, data=None):
            self.dotazy.append(url)
            for cast, odpoved in odpovedi.items():
                if cast in url:
                    return odpoved
            raise AssertionError(url)
        valecne_hroby.otevri = otevri

    def vystup(self, f, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            f(*args)
        return out.getvalue()

    def test_obec_jen_presny_nazev_a_orp(self):
        hroby = [{"Id": "a", "Identifier": "CZE1", "Character": "deska", "Municipality": "Pavlov"},
                 {"Id": "b", "Identifier": "CZE2", "Character": "deska", "Municipality": "Pavlov"},
                 {"Id": "c", "Identifier": "CZE3", "Character": "deska", "Municipality": "Velké Pavlovice"}]
        self.server({"Graves/Select": json.dumps({"Total": 3, "Data": hroby}),
                     "Detail/a": '<div><label>ORP</label><input value="Pelhřimov" /></div>',
                     "Detail/b": '<div><label>ORP</label><input value="Mikulov" /></div>',
                     "People/Select/a": json.dumps({"Total": 0, "Data": []})})
        out = self.vystup(valecne_hroby.hroby_obce, "pavlov", "Pelhrimov")
        self.assertIn("CZE1 | deska", out)
        self.assertNotIn("CZE2", out)
        self.assertIn("v ORP: Mikulov", out)
        self.assertFalse(any("Detail/c" in u or "People/Select/b" in u for u in self.dotazy))

    def test_padli_podle_obce(self):
        lide = [{"ICP": 1, "FirstName": "Václav", "Surname": "Žemlička", "BirthYear": "1885"},
                {"ICP": 2, "FirstName": "Václav", "Surname": "Žemlička", "BirthYear": "1890"}]
        self.server({"FallenPeople/Select": json.dumps({"Total": 2, "Data": lide}),
                     "Detail/1": PADLY, "Detail/2": '<div><label>Obec (Rakousko-Uhersko)</label><input value="Wien" /></div>'})
        out = self.vystup(valecne_hroby.padli, "Žemlička", None, "Obora")
        self.assertIn("IČP 1 |", out)
        self.assertNotIn("IČP 2 |", out)
        self.assertIn("Vynecháno 1", out)


if __name__ == "__main__":
    unittest.main()
