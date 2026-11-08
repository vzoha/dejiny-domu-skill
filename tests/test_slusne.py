"""Testy limitu rychlosti (slusne.py), hooku (hlidac.py) a jeho zápisu do projektu (novy_projekt.py).

Bez internetu: odpovědi 200/403/429/503 dává lokální HTTP server. Stav limitu je v dočasné složce (SLUSNE_DIR).
"""
import email.utils, http.server, json, os, shutil, subprocess, sys, tempfile, threading, time, unittest, urllib.request

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "dejiny-domu", "tools")
sys.path.insert(0, TOOLS)
import slusne  # noqa: E402


class Server(http.server.BaseHTTPRequestHandler):
    pocet = 0
    robots = ""   # text robots.txt testovacího webu
    ua = None     # User-Agent posledního dotazu

    def do_GET(self):
        if self.path == "/robots.txt":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(Server.robots.encode())
            return
        Server.pocet += 1
        Server.ua = self.headers.get("User-Agent")
        if "pomalu" in self.path:
            time.sleep(0.5)
        if self.path.startswith("/presmeruj"):   # na jiný web: localhost místo 127.0.0.1
            self.send_response(302)
            self.send_header("Location", f"http://localhost:{self.server.server_port}/429")
            self.end_headers()
            return
        kod = next((int(k) for k in ("403", "429", "503") if k in self.path), 200)
        self.send_response(kod)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


class SlusneTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Server)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_port}"
        slusne.instaluj()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="slusne_test_")
        os.environ["SLUSNE_DIR"] = self.tmp
        slusne.LIMITY["127.0.0.1"] = (0.3, 0.01)
        Server.pocet = 0
        Server.robots = ""

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def get(self, path):
        return urllib.request.urlopen(self.url + path, timeout=10).read()

    def test_retry_after_jako_datum(self):
        za_dve_hodiny = email.utils.formatdate(time.time() + 7200, usegmt=True)
        self.assertAlmostEqual(slusne.sekund_z_retry_after(za_dve_hodiny), 7200, delta=5)
        self.assertEqual(slusne.sekund_z_retry_after("120"), 120)
        self.assertIsNone(slusne.sekund_z_retry_after("brzy"))
        with self.assertRaises(slusne.Zablokovano):
            slusne.posoudit("archiv.example", "dotaz", 429, za_dve_hodiny)
        self.assertGreater(slusne.blokace("archiv.example")[0], time.time() + 7000)   # ne jen výchozích 30 min

    @unittest.skipUnless(shutil.which("curl"), "chybí curl")
    def test_curl_dve_adresy_odmitne(self):
        with self.assertRaises(SystemExit) as e:
            slusne.curl(["-s", self.url + "/ok", "http://localhost/ok"])
        self.assertIn("jedna adresa", str(e.exception.code))
        self.assertEqual(Server.pocet, 0)

    @unittest.skipUnless(shutil.which("curl"), "chybí curl")
    def test_curl_po_presmerovani_posoudi_cilovy_web(self):
        with self.assertRaises(slusne.Zablokovano):
            slusne.curl(["-s", "-L", "-o", os.devnull, self.url + "/presmeruj"])
        self.assertTrue(slusne.blokace("localhost"))
        self.assertIsNone(slusne.blokace("127.0.0.1"))

    def test_strop_dlazdic(self):
        slusne.strop_dlazdic(slusne.MAX_DLAZDIC, "x")   # na stropu ještě projde
        with self.assertRaises(SystemExit) as e:
            slusne.strop_dlazdic(slusne.MAX_DLAZDIC + 1, "https://archiv/snimek")
        self.assertIn("nic nestahuji", str(e.exception.code))

    def test_rozestup_dotazu(self):
        t = time.time()
        for _ in range(3):
            self.get("/hledat")
        self.assertGreaterEqual(time.time() - t, 0.55)

    def test_rozestup_se_pocita_od_odpovedi(self):
        t = time.time()
        for _ in range(2):
            self.get("/pomalu")
        self.assertGreaterEqual(time.time() - t, 1.25)   # 2× 0,5 s odpověď + 0,3 s rozestup

    def test_odpoved_nezkrati_rezervovany_termin(self):
        budouci = time.time() + 60
        with open(slusne._soubor("127.0.0.1", "dotaz"), "w") as f:
            f.write(repr(budouci))
        slusne.odpovedel("127.0.0.1", "dotaz")
        with open(slusne._soubor("127.0.0.1", "dotaz")) as f:
            self.assertEqual(float(f.read()), budouci)

    def test_obrazky_volneji(self):
        t = time.time()
        for i in range(5):
            self.get(f"/dlazdice/{i}.jpg")
        self.assertLess(time.time() - t, 0.5)

    def test_limit_spolecny_procesum(self):
        kod = ("import sys, time; sys.path.insert(0, sys.argv[1]); import slusne; "
               "slusne.LIMITY['127.0.0.1'] = (0.4, 0.01); slusne.pockej('127.0.0.1', 'dotaz')")
        t = time.time()
        ps = [subprocess.Popen([sys.executable, "-c", kod, TOOLS]) for _ in range(3)]
        for p in ps:
            self.assertEqual(p.wait(), 0)
        self.assertGreaterEqual(time.time() - t, 0.75)   # 3 procesy = aspoň 2 rozestupy

    def test_429_zablokuje_web_pro_vsechny(self):
        self.get("/ok")
        with self.assertRaises(slusne.Zablokovano):
            self.get("/429")
        self.assertTrue(slusne.blokace("127.0.0.1"))
        pred = Server.pocet
        with self.assertRaises(slusne.Zablokovano):
            self.get("/ok")
        self.assertEqual(Server.pocet, pred)   # další dotaz už na server nedošel
        p = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import slusne, urllib.request;"
                            "slusne.instaluj(); urllib.request.urlopen(sys.argv[2])", TOOLS, self.url + "/ok"],
                           capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)   # i jiný proces
        self.assertIn("STOP", p.stderr)

    def test_503_zablokuje_i_obrazky(self):
        with self.assertRaises(slusne.Zablokovano):
            self.get("/503/snimek.jpg")
        self.assertTrue(slusne.blokace("127.0.0.1"))

    def test_403_na_prvni_dotaz_jen_skonci(self):
        with self.assertRaises(SystemExit) as e:
            self.get("/403")
        self.assertNotIsInstance(e.exception, slusne.Zablokovano)
        self.assertIsNone(slusne.blokace("127.0.0.1"))

    def test_403_uprostred_prace_zablokuje(self):
        self.get("/ok")
        with self.assertRaises(slusne.Zablokovano):
            self.get("/403")

    def test_403_po_uspechu_jineho_procesu_zablokuje(self):
        subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import slusne, urllib.request;"
                        "slusne.instaluj(); urllib.request.urlopen(sys.argv[2])", TOOLS, self.url + "/ok"],
                       check=True, env=dict(os.environ, SLUSNE_DIR=self.tmp))
        with self.assertRaises(slusne.Zablokovano):   # nový proces, ale web před chvílí odpovídal → ban, ne User-Agent
            self.get("/403")

    def test_blokace_behem_cekani(self):
        slusne.LIMITY["127.0.0.1"] = (0.5, 0.01)
        slusne.pockej("127.0.0.1", "dotaz")
        threading.Timer(0.2, slusne.zablokuj, ("127.0.0.1", "HTTP 429")).start()
        with self.assertRaises(slusne.Zablokovano):   # termín zabraný před blokací, po probuzení už nepustí
            slusne.pockej("127.0.0.1", "dotaz")

    def test_fronta_nad_limit_ceka_nezabere_termin(self):
        slusne.LIMITY["127.0.0.1"] = (5.0, 0.01)
        slusne.pockej("127.0.0.1", "dotaz")
        with self.assertRaises(slusne.Fronta):
            slusne.pockej("127.0.0.1", "dotaz", nejdele=1)

    def test_403_na_obrazek_nezablokuje(self):
        self.get("/ok")
        with self.assertRaises(Exception):
            self.get("/403/snimek.jpg")   # běžná chyba HTTP, ne blokace
        self.assertIsNone(slusne.blokace("127.0.0.1"))

    def test_robots_zakaz_pro_claude_user_plati(self):
        Server.robots = "User-agent: Claude-User\nDisallow: /tajne\n"
        with self.assertRaises(slusne.RobotsZakazuje):
            self.get("/tajne/1")
        self.assertEqual(Server.pocet, 0)
        self.assertEqual(self.get("/jinde"), b"ok")

    def test_robots_zakaz_jinych_robotu_neplati(self):
        Server.robots = ("User-agent: ClaudeBot\nDisallow: /\n\nUser-agent: Claude-SearchBot\nDisallow: /\n\n"
                         "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nDisallow: /\n")
        self.assertEqual(self.get("/cokoli"), b"ok")

    def test_robots_jednou_za_den(self):
        self.get("/a")
        Server.robots = "User-agent: Claude-User\nDisallow: /\n"   # změna se projeví až po dni
        self.assertEqual(self.get("/b"), b"ok")

    def test_predstavi_se_jako_claude_user(self):
        urllib.request.urlopen(urllib.request.Request(self.url + "/ok", headers={"User-Agent": "Mozilla/5.0 (vlastni)"}),
                               timeout=10).read()
        self.assertEqual(Server.ua, slusne.UA)
        self.assertIn("Claude-User", slusne.UA)

    def test_curl_vlastni_user_agent_nahradi(self):
        self.assertEqual(slusne._bez_user_agentu(["-s", "-A", "x", "-H", "User-Agent: y", "-H", "Accept: z",
                                                  "--user-agent=w", "https://a/"]), ["-s", "-H", "Accept: z", "https://a/"])
        p = slusne.curl(["-s", "-A", "vlastni", self.url + "/ok"], stdout=subprocess.PIPE)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(Server.ua, slusne.UA)

    def test_druh(self):
        for url in ("https://x/iipsrv/iipsrv.fcgi?IIIF=/a.jp2/full/full/0/default.jpg", "https://x/a_files/12/3_4.jpg",
                    "https://images.archives.cz/ximage/matriky/zoomify/a/ImageProperties.xml"):
            self.assertEqual(slusne.druh(url), "obr", url)
        for url in ("https://www.mza.cz/actapublica/matrika/hledani_obec?obec_id=1", "https://aron/api/aron/apu/listview"):
            self.assertEqual(slusne.druh(url), "dotaz", url)

    @unittest.skipUnless(shutil.which("curl"), "chybí curl")
    def test_curl_429(self):
        env = dict(os.environ, SLUSNE_DIR=self.tmp)
        cmd = [sys.executable, "-I", os.path.join(TOOLS, "slusne.py"), "curl", "-s", "-o", os.devnull]
        self.assertEqual(subprocess.run(cmd + [self.url + "/ok"], env=env).returncode, 0)
        p = subprocess.run(cmd + [self.url + "/429"], env=env, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertTrue(slusne.blokace("127.0.0.1"))
        p = subprocess.run(cmd + ["-w", "kod=%{http_code}", self.url + "/ok"], env=env, capture_output=True, text=True)
        self.assertIn("STOP", p.stderr)

    @unittest.skipUnless(shutil.which("curl"), "chybí curl")
    def test_curl_host_podle_cile_ne_refereru(self):
        env = dict(os.environ, SLUSNE_DIR=self.tmp)
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "slusne.py"), "curl", "-s", "-o", os.devnull,
                            "-e", "https://www.mza.cz/", self.url + "/429"], env=env, capture_output=True, text=True)
        self.assertIn("127.0.0.1", p.stderr)
        self.assertTrue(slusne.blokace("127.0.0.1"))
        self.assertIsNone(slusne.blokace("www.mza.cz"))

    def test_skript_pres_slusne(self):
        skript = os.path.join(self.tmp, "s.py")
        with open(skript, "w") as f:
            f.write("import sys, urllib.request, slusne\nfor _ in range(3): urllib.request.urlopen(sys.argv[1]).read()\n"
                    "print(slusne._instalovano)\n")
        t = time.time()
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "slusne.py"), skript, self.url + "/ok"],
                           capture_output=True, text=True, env=dict(os.environ, SLUSNE_DIR=self.tmp))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "True")   # `import slusne` ve skriptu = stejný modul (žádné dvojí čekání)
        self.assertGreaterEqual(time.time() - t, 3.9)   # výchozí 2 s mezi dotazy (LIMITY z testu do skriptu nejdou)


class HlidacTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hlidac_test_")
        os.makedirs(os.path.join(self.tmp, "tools"))
        os.makedirs(os.path.join(self.tmp, "pracovni"))
        for jmeno, text in (("pracovni/sit.py", "import urllib.request\n"), ("pracovni/bez.py", "print(1)\n"),
                            ("pracovni/x.sh", "curl -s https://www.mza.cz/\n"), ("tools/ahmp_search.sh", "curl x\n")):
            with open(os.path.join(self.tmp, jmeno), "w") as f:
                f.write(text)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rozhodni(self, cmd, nastroj="Bash"):
        vstup = {"tool_name": nastroj, "cwd": self.tmp,
                 "tool_input": {"command": cmd} if nastroj == "Bash" else {"url": cmd}}
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "hlidac.py")], input=json.dumps(vstup),
                           capture_output=True, text=True, env=dict(os.environ, SLUSNE_DIR=self.tmp))
        self.assertEqual(p.returncode, 0, p.stderr)
        if not p.stdout.strip():
            return "povoleno"
        return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]

    def test_zamitne(self):
        for cmd in ('curl -s "https://www.mza.cz/actapublica/matrika/hledani_obec?obec_id=1"',
                    "cd pracovni && wget https://digi.ceskearchivy.cz/4250/5",
                    'for i in 1 2 3; do curl -s "$U&page=$i"; done',
                    'python3 -c "import urllib.request; urllib.request.urlopen(\'https://www.mza.cz\')"',
                    "python3 -I - <<'E'\nimport requests\nrequests.get('https://www.mza.cz')\nE",
                    "/usr/bin/python3 pracovni/sit.py",
                    "python3 -I tools/trebon.py misto X && curl https://www.mza.cz/",
                    "bash pracovni/x.sh",
                    'python3 "pracovni/sit.py"',
                    'python3 -Ic "import urllib.request"'):
            self.assertEqual(self.rozhodni(cmd), "deny", cmd)

    def test_povoli(self):
        for cmd in ("python3 -I tools/trebon.py misto Chyšky",
                    "python3 -I -X utf8 tools/mza.py snimek 3090 5 pracovni/x.jpg",
                    "python3 -I tools/slusne.py curl -s https://www.mza.cz/",
                    "python3 -I tools/slusne.py pracovni/sit.py",
                    "python3 pracovni/bez.py",
                    "curl -s http://localhost:4321/",
                    "bash tools/ahmp_search.sh Smíchov",
                    "python3 -m unittest discover tests",
                    "git status && npm run build",
                    "python3 - <<'E'\nimport json\nprint(json.dumps({}))\nE",
                    'python3 -c "import urllib.parse; print(urllib.parse.quote(\'Smíchov\'))"',
                    'python3 -I "$CLAUDE_PROJECT_DIR/tools/slusne.py" curl -s https://www.mza.cz/'):
            self.assertEqual(self.rozhodni(cmd), "povoleno", cmd)

    def test_webfetch_dlouha_fronta(self):
        os.environ["SLUSNE_DIR"] = self.tmp
        with open(os.path.join(self.tmp, "www.mza.cz.dotaz"), "w") as f:
            f.write(repr(time.time() + 120))   # pomocníci zabrali termíny na 2 minuty dopředu
        self.assertEqual(self.rozhodni("https://www.mza.cz/actapublica/", "WebFetch"), "deny")

    def test_webfetch_zablokovany_web(self):
        self.assertEqual(self.rozhodni("https://www.mza.cz/actapublica/", "WebFetch"), "povoleno")
        os.environ["SLUSNE_DIR"] = self.tmp
        slusne.zablokuj("www.mza.cz", "HTTP 429")
        self.assertEqual(self.rozhodni("https://www.mza.cz/actapublica/", "WebFetch"), "deny")


class NovyProjektHookTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hook_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def zaloz(self):
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "novy_projekt.py"), self.tmp],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        with open(os.path.join(self.tmp, ".claude", "settings.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_hook_jednou_a_slouceni(self):
        os.makedirs(os.path.join(self.tmp, ".claude"))
        with open(os.path.join(self.tmp, ".claude", "settings.json"), "w") as f:
            json.dump({"permissions": {"allow": ["Bash(git status)"]}}, f)
        cfg = self.zaloz()
        cfg = self.zaloz()   # aktualizace – hook se nepřidá podruhé
        self.assertEqual(cfg["permissions"], {"allow": ["Bash(git status)"]})
        hooky = [h for m in cfg["hooks"]["PreToolUse"] for h in m["hooks"] if "hlidac.py" in h["command"]]
        self.assertEqual(len(hooky), 1)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "tools", "hlidac.py")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "tools", "slusne.py")))


if __name__ == "__main__":
    unittest.main()
