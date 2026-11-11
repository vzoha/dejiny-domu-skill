"""verze.py: porovnání skillu, projektu a GitHubu (GitHub z připravené mezipaměti, bez sítě)."""
import json, os, shutil, subprocess, sys, tempfile, time, unittest

TOOLS = os.path.join(os.path.dirname(__file__), "..", "skills", "dejiny-domu", "tools")
SKILL = open(os.path.join(TOOLS, "..", "VERZE"), encoding="utf-8").read().strip()


def vyssi(v):
    a, b, c = map(int, v.split("."))
    return f"{a}.{b + 1}.0"


class VerzeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="verze_test_")
        self.projekt = os.path.join(self.tmp, "projekt")
        os.makedirs(self.projekt)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def spust(self, github=None, projekt=None):
        cache = os.path.join(self.tmp, "dejiny-domu", "verze.json")
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        if github:
            json.dump({"cas": time.time(), "verze": github}, open(cache, "w"))
        if projekt:
            open(os.path.join(self.projekt, ".skill_verze"), "w").write(projekt)
        env = dict(os.environ, LOCALAPPDATA=self.tmp, DEJINY_VERZE_URL="http://127.0.0.1:9/")   # bez sítě
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "verze.py"), self.projekt],
                           env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        return next(r for r in p.stdout.splitlines() if r.startswith("→"))

    def test_aktualni(self):
        self.assertIn("AKTUALNI", self.spust(github=SKILL, projekt=SKILL))

    def test_nova_verze_na_githubu(self):
        self.assertIn("NOVA_VERZE_SKILLU", self.spust(github=vyssi(SKILL), projekt=SKILL))

    def test_starsi_projekt(self):
        self.assertIn("AKTUALIZUJ_PROJEKT", self.spust(github=SKILL, projekt="0.1.0"))

    def test_novejsi_projekt(self):
        self.assertIn("PROJEKT_NOVEJSI", self.spust(github=SKILL, projekt=vyssi(SKILL)))

    def test_bez_site_neselze(self):
        self.assertIn("AKTUALNI", self.spust(projekt=SKILL))


if __name__ == "__main__":
    unittest.main()
