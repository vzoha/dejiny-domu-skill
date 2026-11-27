"""Testy elipsa.py: elipsa a popisek v obrázku, vodicí čára z nejbližšího bodu elipsy. Bez internetu."""
import os, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import elipsa  # noqa: E402
from PIL import Image  # noqa: E402


class ElipsaTest(unittest.TestCase):

    def test_nejblizsi_bod(self):
        x, y = elipsa.nejblizsi_bod(100, 100, 50, 20, 0, (300, 100))
        self.assertAlmostEqual(x, 150, delta=0.5)
        self.assertAlmostEqual(y, 100, delta=0.5)
        x, y = elipsa.nejblizsi_bod(100, 100, 50, 20, 90, (100, 300))   # natočená o 90°: dlouhá osa svisle
        self.assertAlmostEqual(y, 150, delta=0.5)

    def test_kresli_elipsu_i_popisek(self):
        im = elipsa.oznac(Image.new("RGBA", (600, 400), (128, 128, 128, 255)), 200, 200, 100, 40, 20, "čp. 12")
        modre = lambda box: any(p[2] > 120 and p[0] < 60 for p in im.crop(box).getdata())
        self.assertTrue(modre((290, 150, 320, 250)))    # pravý okraj elipsy
        self.assertFalse(modre((180, 180, 220, 220)))   # střed elipsy zůstal
        self.assertTrue(modre((300, 0, 600, 150)))      # popisek vpravo nahoře

    def test_spocitej_sikmou_parcelu_bez_souseda(self):
        dum = [(100, 300), (400, 150), (420, 190), (120, 340)]        # šikmá stodola
        soused = [(100, 250), (380, 110), (150, 400), (450, 260)]    # stavení nad a pod ní
        cx, cy, a, b, uhel, rezerva = elipsa.spocitej(dum, soused)
        self.assertLess(uhel, -15)                                    # natočená podél stodoly
        self.assertGreater(a, b)
        self.assertGreaterEqual(rezerva, 1)
        self.assertTrue(all(elipsa.vzdalenost(p, cx, cy, a, b, uhel) <= 1 for p in dum))

    def test_vzdalenost_natocene_elipsy(self):
        self.assertAlmostEqual(elipsa.vzdalenost((100, 150), 100, 100, 50, 20, 90), 1)   # dlouhá osa svisle
        self.assertGreater(elipsa.vzdalenost((150, 100), 100, 100, 50, 20, 90), 1)

    def test_silnejsi_cara(self):
        modre = lambda im: sum(p[2] > 120 and p[0] < 60 for p in im.getdata())
        tenka = elipsa.oznac(Image.new("RGBA", (600, 400), (128, 128, 128, 255)), 300, 200, 150, 80)
        silna = elipsa.oznac(Image.new("RGBA", (600, 400), (128, 128, 128, 255)), 300, 200, 150, 80, cara=10)
        self.assertGreater(modre(silna), 2 * modre(tenka))

    XML = """<FeatureCollection><member><cp:CadastralParcel gml:id="CP.1"><cp:geometry><gml:Polygon>
      <gml:exterior><gml:LinearRing><gml:posList>0 0 10 0 10 -20 0 -20</gml:posList></gml:LinearRing></gml:exterior>
      </gml:Polygon></cp:geometry><cp:label>st. 12</cp:label>
      <cp:zoning xlink:type="simple" xlink:title="Horní Lhota" /></cp:CadastralParcel></member>
      <member><cp:CadastralParcel gml:id="CP.2"><cp:geometry><gml:Polygon>
      <gml:exterior><gml:LinearRing><gml:posList>10 0 20 0 20 -20 10 -20</gml:posList></gml:LinearRing></gml:exterior>
      </gml:Polygon></cp:geometry><cp:label>13</cp:label></cp:CadastralParcel></member></FeatureCollection>"""

    def test_parcely_z_xml(self):
        parcely = elipsa.parcely_z_xml(self.XML)
        self.assertEqual([(o, ku) for o, ku, _ in parcely], [("st. 12", "Horní Lhota"), ("13", "")])
        self.assertEqual(parcely[0][2], [(0, 0), (10, 0), (10, -20), (0, -20)])

    def test_soused_bez_spolecne_hranice(self):
        dum, sousede = elipsa.body_parcely(elipsa.parcely_z_xml(self.XML), "st. 12")
        self.assertEqual(len(dum), 4)
        self.assertEqual(sorted(sousede), [(20, -20), (20, 0)])   # lomy na společné hranici x = 10 nepočítá

    def test_na_pixely_sever_nahore(self):
        px = elipsa.na_pixely([(0, 0), (10, -20)], (0, -20, 20, 0), 200, 400)
        self.assertEqual(px, [(0, 0), (100, 400)])


if __name__ == "__main__":
    unittest.main()
