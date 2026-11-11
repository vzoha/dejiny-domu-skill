#!/usr/bin/env python3
"""Sčítání lidu v Brně 1850–1921 (Archiv města Brna, Digitální archiv digiarchiv.brno.cz).

Operáty jsou po domech: ulice a číslo, jak je psal sčítací komisař (do 1900 německy: „Adlergasse“, „Kröna“,
předměstí s číslem domu „Altbrünn 143“; 1921 česky, připojené obce „Královo Pole-Luční“). Ročníky 1850, 1857,
1870, 1880, 1890, 1900, 1921; 1910 jen v badatelně. Jmenný rejstřík (jméno, dům, svazek, strana, řádek) je vytěžený,
ale ne u všech domů a osob (chybí-li, čti snímky v prohlížeči, odkaz). Snímek operátu nemá každý dům a rok.

Použití:
  brno_scitani.py ulice "<část názvu>" [rok]        – názvy ulic v operátech (dnešní i tehdejší, výraz kdekoli v názvu)
  brno_scitani.py dum "<ulice>" <číslo> [rok]        – operáty domu: rok | osob | snímky | odkaz
  brno_scitani.py osoby "<ulice>" <číslo> [rok]      – lidé z rejstříku u operátů domu
  brno_scitani.py hledej "<příjmení>" [jméno] [rok]  – lidé podle jména s domem (nejvýš 200)
Snímky nestahuje: čte je uživatel v prohlížeči (odkaz), do výstupu přepis a citace, obrázek jen se souhlasem archivu."""
import json, os, re, ssl, sys, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (slusne.py)

WEB = "https://digiarchiv.brno.cz"
API = WEB + "/api/scitacioperaty"
ROKY = ("1850", "1857", "1870", "1880", "1890", "1900", "1921")
NEJVIC_ULIC = 100   # víc názvů ulic web nevrátí
NEJVIC_STRAN = 50   # 10 záznamů na stranu; velký činžák má v jednom roce až ~250 lidí
# Server neposílá mezilehlý certifikát (prohlížeč si ho dotáhne sám, Python ne → CERTIFICATE_VERIFY_FAILED).
# Thawte TLS RSA CA G1 (vydal DigiCert Global Root G2, platí do 2. 11. 2027, SHA-256 4B:CC:5E:23:…:53:EB:20:C2,
# z http://cacerts.thawte.com/ThawteTLSRSACAG1.crt) je přibalený, nestahuje se. Přidáme ho jen jako článek řetězce:
# bez PARTIAL_CHAIN se z něj kotva důvěry nestane, ověření pořád musí skončit u systémového kořenového certifikátu.
THAWTE_TLS_RSA_CA_G1 = """
-----BEGIN CERTIFICATE-----
MIIEizCCA3OgAwIBAgIQCQ7oxd5b+mLSri/3CXxIVzANBgkqhkiG9w0BAQsFADBh
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBH
MjAeFw0xNzExMDIxMjI0MjVaFw0yNzExMDIxMjI0MjVaMF4xCzAJBgNVBAYTAlVT
MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5j
b20xHTAbBgNVBAMTFFRoYXd0ZSBUTFMgUlNBIENBIEcxMIIBIjANBgkqhkiG9w0B
AQEFAAOCAQ8AMIIBCgKCAQEAxjngmPhVetC0b/ozbYJdzOBUA1sMog47030cAP+P
23ANUN8grXECL8NhDEF4F1R9tL0wY0mczHaR0a7lYanlxtwWo1s2uGnnyDs6mOCs
66ew2w3YETr6Tb14xgjpu1gGFtAeewaikO9Fud8hxGJTSwn8xeNkfKVWpD2L4vFN
36FNgxeilK6aE4ykgGAzNlokTp6hNOLAYpDySdLAPKzuJSQ7JCEZ6O+SDKywIdXL
oMTnpxuBKGSG88NWTo3CHCOGmQECia2yqdPDjgLqnEiYNjwQL8uMqj8rOvlMgviB
cHA7xty+7/uYLN6ZS7Vq1/F/lVhVOf5ej6jZdmB85szFbQIDAQABo4IBQDCCATww
HQYDVR0OBBYEFKWM/jLM6w8s1BnGCLgAJIhdw8W3MB8GA1UdIwQYMBaAFE4iVCAY
lebjbuYP+vq5Eu0GF485MA4GA1UdDwEB/wQEAwIBhjAdBgNVHSUEFjAUBggrBgEF
BQcDAQYIKwYBBQUHAwIwEgYDVR0TAQH/BAgwBgEB/wIBADA0BggrBgEFBQcBAQQo
MCYwJAYIKwYBBQUHMAGGGGh0dHA6Ly9vY3NwLmRpZ2ljZXJ0LmNvbTBCBgNVHR8E
OzA5MDegNaAzhjFodHRwOi8vY3JsMy5kaWdpY2VydC5jb20vRGlnaUNlcnRHbG9i
YWxSb290RzIuY3JsMD0GA1UdIAQ2MDQwMgYEVR0gADAqMCgGCCsGAQUFBwIBFhxo
dHRwczovL3d3dy5kaWdpY2VydC5jb20vQ1BTMA0GCSqGSIb3DQEBCwUAA4IBAQC6
km0KA4sTb2VYpEBm/uL2HL/pZX9B7L/hbJ4NcoBe7V56oCnt7aeIo8sMjCRWTCWZ
D1dY0+2KZOC1dKj8d1VXXAtnjytDDuPPf6/iow0mYQTO/GAg/MLyL6CDm3FzDB8V
tsH/aeMgP6pgD1XQqz+haDnfnJTKBuxhcpnx3Adbleue/QnPf1hHYa8L+Rv8Pi5U
h4V9FwHOfphdMXOxi14OqmsiTbc5cOs9/uukH+YVsuFdWTna6IVw1qh+tEtyH16R
vmi7pkqyZYULOPMIE7avrljVVBZuikwARtY8tCVV6Pp9l3VeagBqb2ffgqNJt3C0
TYNYQI+BXG1R1cABlold
-----END CERTIFICATE-----
"""
_otvirac = None


def otvirac():
    global _otvirac
    if _otvirac is None:
        kontext = ssl.create_default_context()
        kontext.verify_flags &= ~getattr(ssl, "VERIFY_X509_PARTIAL_CHAIN", 0)
        kontext.load_verify_locations(cadata=THAWTE_TLS_RSA_CA_G1)
        _otvirac = urllib.request.build_opener(urllib.request.HTTPSHandler(context=kontext))
    return _otvirac


def cti(cesta, telo):
    """POST na vyhledávací cestu, kterou volá i web (jen čte)."""
    pozadavek = urllib.request.Request(API + cesta, data=json.dumps(telo).encode(),
                                       headers={"Content-Type": "application/json"})
    with otvirac().open(pozadavek, timeout=60) as r:
        return json.load(r)


def vsechny_strany(cesta, telo):
    """Výsledky ze všech stran (nejvýš NEJVIC_STRAN). Vrací (výsledky, celkem podle webu)."""
    vysledky, celkem = [], 0
    for strana in range(1, NEJVIC_STRAN + 1):
        odpoved = cti(f"{cesta}?page={strana}", telo)
        vysledky += odpoved.get("results") or []
        celkem = odpoved.get("numberOfRecords") or 0
        if strana >= (odpoved.get("numberOfPages") or 0):
            break
    return vysledky, celkem


def s_rokem(telo, rok):
    return {**telo, "yearOfCensus": rok} if rok else telo


def ulice(vyraz, rok=None):
    dotaz = {"streetName": f"%{vyraz}%"} | ({"yearOfCensus": f"{rok}%"} if rok else {})
    return cti("/search/field/streetName?" + urllib.parse.urlencode(dotaz), {}).get("data") or []


def operaty(nazev, cislo, rok=None):
    return vsechny_strany("/search", s_rokem({"streetName": nazev, "houseNumber": cislo}, rok))[0]


def osoby_domu(nazev, cislo, rok):
    """Lidé z rejstříku v domě v daném roce (příjmení „%“ = všichni; jde i u operátů bez vazby na rejstřík)."""
    return vsechny_strany("/search", {"streetName": nazev, "houseNumber": cislo, "yearOfCensus": rok, "surname": "%"})


def odkaz(nazev, cislo, rok=None):
    return f"{WEB}/search/operates?" + urllib.parse.urlencode(s_rokem({"streetName": nazev, "houseNumber": cislo}, rok))


def jmeno(o):
    return " ".join(x.strip() for x in (o.get("surname"), o.get("firstName")) if x and x.strip())


def poradi_v_rejstriku(o):
    """Svazek, strana („143b“ za „31a“ podle čísla), řádek."""
    strana = re.match(r"(\d*)(.*)", o.get("regPage") or "")
    return o.get("regVolume") or "", int(strana[1] or 0), strana[2], o.get("regLine") or 0


def citace(o):
    return f"rejstřík {o.get('regVolume') or '?'}, s. {o.get('regPage') or '?'}, ř. {o.get('regLine') or '?'}"


def vypis_dum(nazev, cislo, rok=None):
    nalez = operaty(nazev, cislo, rok)
    if not nalez:
        print(f"Operát „{nazev} {cislo}“ nenalezen – zkus tehdejší název ulice (brno_scitani.py ulice …).")
        return
    for o in sorted(nalez, key=lambda o: o["year"]):
        print(f"{o['year']} | {o['streetName']} {o['houseNumber']} | osob {o.get('numberOfPeople') or '?'} | "
              f"snímek operátu {'ano' if o.get('existOperatImage') else 'ne'}")
    print(f"Prohlížeč: {odkaz(nazev, cislo, rok)}")
    print("Citace: Archiv města Brna, Sčítání lidu <rok>, <ulice> <číslo>, digiarchiv.brno.cz")


def vypis_osoby(nazev, cislo, rok=None):
    for o in sorted(operaty(nazev, cislo, rok), key=lambda o: o["year"]):
        lide, celkem = osoby_domu(nazev, cislo, str(o["year"]))
        print(f"== {o['year']} {o['streetName']} {o['houseNumber']}: osob {o.get('numberOfPeople') or '?'}, "
              f"v rejstříku {celkem}" + (f" (vypsáno {len(lide)})" if celkem > len(lide) else ""))
        se_jmenem = [p for p in lide if jmeno(p)]
        if len(se_jmenem) < len(lide):
            print(f"   {len(lide) - len(se_jmenem)} řádků bez čitelného jména – dočti ze snímků operátu (odkaz z „dum“)")
        for p in sorted(se_jmenem, key=poradi_v_rejstriku):
            print(f"   {jmeno(p)} | {citace(p)}")


def vypis_hledej(prijmeni, krestni=None, rok=None):
    telo = s_rokem({"surname": prijmeni} | ({"firstName": krestni} if krestni else {}), rok)
    lide, celkem = vsechny_strany("/search", telo)
    for p in lide:
        print(f"{p['year']} | {jmeno(p)} | {p.get('streetName')} {p.get('houseNumber')} | {citace(p)}")
    if celkem > len(lide):
        print(f"… vypsáno {len(lide)} z {celkem}, zpřesni jménem nebo rokem")
    elif not lide:
        print("Nikdo – rejstřík píše jména jako v operátu (Novak, Nowak) a nemá všechny osoby.")


def main():
    a = sys.argv[1:]
    prikazy = {"ulice": (1, 2), "dum": (2, 3), "osoby": (2, 3), "hledej": (1, 3)}
    if not a or a[0] not in prikazy or not prikazy[a[0]][0] <= len(a) - 1 <= prikazy[a[0]][1]:
        sys.exit(__doc__)
    rok = next((x for x in a[1:] if x in ROKY), None)
    argumenty = [x for x in a[1:] if x != rok]
    if a[0] == "ulice":
        nazvy = ulice(argumenty[0], rok)
        print("\n".join(nazvy) if nazvy else "Žádná ulice – zkus kratší část názvu nebo německý tvar (Gasse, Platz).")
        if len(nazvy) >= NEJVIC_ULIC:
            print(f"… web vrací nejvýš {NEJVIC_ULIC} názvů, zpřesni výraz nebo rok")
    elif a[0] == "dum":
        vypis_dum(*argumenty, rok)
    elif a[0] == "osoby":
        vypis_osoby(*argumenty, rok)
    else:
        vypis_hledej(*argumenty, rok=rok)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        sys.exit(f"Digitální archiv Brna neodpovídá: {e}")
