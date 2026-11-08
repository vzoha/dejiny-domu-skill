"""Testy zesil_snimek.py: argumenty bez ImageMagicku, výstup jen když je ImageMagick nainstalovaný. Bez internetu."""
import os, shutil, subprocess, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import zesil_snimek  # noqa: E402


class ArgumentyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.snimek = os.path.join(self.tmp, "s.jpg")
        open(self.snimek, "wb").close()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_vyrez_a_zvetseni(self):
        self.assertEqual(zesil_snimek.nacti_argumenty([self.snimek, "0.1,0.2,0.5,0.6", "--zvetsit", "2"]),
                         (self.snimek, [0.1, 0.2, 0.5, 0.6], 2.0))

    def test_bez_vyrezu(self):
        self.assertEqual(zesil_snimek.nacti_argumenty([self.snimek]), (self.snimek, None, 1.0))

    def test_spatne_vstupy(self):
        for a in (["0.5,0,0.1,1"], ["a,b,c,d"], ["0,0,1"], ["--zvetsit"], ["--zvetsit", "0"], ["--zvetsit", "dva"]):
            with self.subTest(a=a), self.assertRaises(SystemExit):
                zesil_snimek.nacti_argumenty([self.snimek, *a])
        with self.assertRaises(SystemExit):
            zesil_snimek.nacti_argumenty([os.path.join(self.tmp, "chybi.jpg")])


@unittest.skipUnless(shutil.which("magick") or shutil.which("convert"), "chybí ImageMagick")
class VystupTest(unittest.TestCase):
    def test_porovnani_ma_dve_patra(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "stranka.jpg")
            m = zesil_snimek.magick()
            subprocess.run([m, "-size", "200x100", "xc:#c8c0b0", "-fill", "#8a8070",
                            "-draw", "line 20,50 180,52", src], check=True)
            subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "zesil_snimek.py"), src, "0,0,0.5,1",
                            "--zvetsit", "2"], check=True, capture_output=True)
            rozmer = lambda f: subprocess.run([m, f, "-format", "%w %h", "info:"], capture_output=True,
                                              text=True, check=True).stdout.split()
            self.assertEqual(rozmer(os.path.join(tmp, "stranka_zesil.jpg")), ["200", "200"])
            self.assertEqual(rozmer(os.path.join(tmp, "stranka_porovnani.jpg")), ["200", "416"])


if __name__ == "__main__":
    unittest.main()
