"""Testy geolab.py (staré mapy Geolab UJEP): seznam listů ze stránky díla a dlaždice Zoomify výřezu. Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import geolab  # noqa: E402

# zkrácený úsek stránky geolab.cz/stare-mapy/2vm-mo (9. 11. 2026): JSON v řetězci Next.js s escapovanými uvozovkami
STRANKA = ('…\\"tilesBase\\":\\"https://oldmaps.geolab.cz/2vm/mo/\\",\\"index\\":{\\"src\\":\\"/oldmaps/klad/2vm-mo.webp\\",'
           '\\"width\\":1323,\\"height\\":1020},\\"sheets\\":[{\\"code\\":\\"O_10_I\\",\\"width\\":11811,\\"height\\":9752,'
           '\\"tileSize\\":256},{\\"code\\":\\"X_1\\",\\"width\\":512,\\"height\\":300,\\"tileSize\\":256,\\"tiles\\":\\"jine/X_1/\\"}]…')


class GeolabTest(unittest.TestCase):

    def test_nacti_dilo(self):
        base, klad, listy = geolab.nacti_dilo(STRANKA)
        self.assertEqual(base, "https://oldmaps.geolab.cz/2vm/mo/")
        self.assertEqual(klad, "/oldmaps/klad/2vm-mo.webp")
        self.assertEqual(listy["O_10_I"], (11811, 9752, 256, "O_10_I/zoomify/"))
        self.assertEqual(listy["X_1"][3], "jine/X_1/")   # vlastní cesta k dlaždicím

    def test_urovne(self):
        self.assertEqual(geolab.urovne(11811, 9752, 256)[0], (185, 153))     # nejmenší = jedna dlaždice
        self.assertEqual(geolab.urovne(11811, 9752, 256)[-1], (11811, 9752))
        self.assertEqual(len(geolab.urovne(11811, 9752, 256)), 7)

    def test_dlazdice_celeho_maleho_obrazku(self):
        seznam, velikost = geolab.dlazdice(512, 300, 256, 0, 0, 0, 1, 1)
        self.assertEqual(velikost, (512, 300))
        # úroveň 0 = 256×150 (1 dlaždice), úroveň 1 = plné rozlišení 2×2 dlaždice → pořadí od 1
        self.assertEqual([c for c, _, _ in seznam], ["TileGroup0/1-0-0.jpg", "TileGroup0/1-1-0.jpg",
                                                     "TileGroup0/1-0-1.jpg", "TileGroup0/1-1-1.jpg"])
        self.assertEqual(seznam[3][1:], (256, 256))

    def test_dlazdice_vyrezu(self):
        seznam, velikost = geolab.dlazdice(11811, 9752, 256, 0, 0.185, 0.80, 0.32, 0.885)
        self.assertEqual(velikost, (1595, 830))   # stejně jako ruční stažení Hlíny 9. 11.
        self.assertTrue(all(c.startswith("TileGroup") for c, _, _ in seznam))


    def test_citace(self):
        self.assertIn("Kriegsarchiv", geolab.citace("2vm-mo", "O_10_I"))
        self.assertIn("list O_10_I", geolab.citace("2vm-mo", "O_10_I"))
        self.assertNotIn("Kriegsarchiv", geolab.citace("mul-ce", "1"))   # původ Müllerových map nástroj nedomýšlí


if __name__ == "__main__":
    unittest.main()
