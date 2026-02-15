"""
Script de inspección v2 - output limpio
"""
import json, os, sys, time

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from curl_cffi import requests as cffi_requests

API_URL = "https://flybondi.com/graphql"
API_KEY = os.getenv("FLYBONDI_API_KEY", "b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa")
SESSION_COOKIE = os.getenv("FLYBONDI_SESSION", "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8")

HEADERS = {
    "accept": "application/json",
    "authorization": f"Key {API_KEY}",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/ar/search/dates",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 Chrome/144.0.0.0 Mobile Safari/537.36",
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
    "x-fo-ui-version": "2.209.0",
}

GQL = """
query Q($input: FlightsQueryInput!) {
  viewer {
    flights(input: $input) {
      edges {
        node {
          flightNo
          origin
          destination
          departureDate
          direction
          fares {
            type
            class
            basis
            availability
            passengerType
            prices {
              afterTax
              beforeTax
              baseBeforeTax
              promotionAmount
            }
          }
        }
      }
    }
    id
  }
}
""".strip()

def do_query(variables, headers_override=None):
    h = headers_override or HEADERS
    payload = {"query": GQL, "variables": variables}
    cookies = {"SFO": SESSION_COOKIE}
    r = cffi_requests.post(API_URL, json=payload, headers=h, cookies=cookies, impersonate="chrome120", timeout=15)
    return r.json()

def get_cheapest(result):
    """Returns (cheapest_afterTax, promotion_amount, fare_class, availability) or None"""
    try:
        edges = result["data"]["viewer"]["flights"]["edges"]
        best = None
        for e in edges:
            for f in e["node"]["fares"]:
                p = f["prices"]["afterTax"]
                if best is None or p < best[0]:
                    best = (p, f["prices"].get("promotionAmount", 0), f["class"], f["availability"], e["node"]["flightNo"])
        return best
    except:
        return None

out = open("inspect_results_v2.txt", "w", encoding="utf-8")
def p(s=""):
    print(s)
    out.write(s + "\n")
    out.flush()

# === TEST 1: CODIGOS PROMO ===
p("=" * 60)
p("TEST 1: CODIGOS PROMO DE FLYBONDI")
p("=" * 60)

base_vars = {
    "input": {
        "origin": "BUE", "destination": "FLN",
        "departureDate": "2026-03-08", "returnDate": "2026-03-17",
        "currency": "ARS",
        "pax": {"adults": 2, "children": 0, "infants": 0},
        "promoCode": None,
    }
}

base_result = do_query(base_vars)
base = get_cheapest(base_result)
if base:
    p(f"  BASE (sin promo): ${base[0]:,.0f}/pp - FO{base[4]} clase {base[2]}")
else:
    p("  ERROR obteniendo base")
    sys.exit(1)

PROMOS = ["FLYBONDI","FO20","FO30","CLUB20","VERANO","VERANO2026","MARZO",
          "BRASIL","PROMO","DESCUENTO","BIENVENIDO","WELCOME","CARNAVAL",
          "CARNAVAL2026","SUMMER","2X1","FLYCLUB","SALE","FLASH","OFF20","OFF30",
          "VUELA","VOLAR","SAVE20","HOTDEAL","PRIMERVIAJE","AMIGO","FIRSTFLIGHT"]

p(f"\nProbando {len(PROMOS)} codigos...")
found_promos = []
for code in PROMOS:
    time.sleep(0.3)
    vars_p = {
        "input": {
            "origin": "BUE", "destination": "FLN",
            "departureDate": "2026-03-08", "returnDate": "2026-03-17",
            "currency": "ARS",
            "pax": {"adults": 2, "children": 0, "infants": 0},
            "promoCode": code,
        }
    }
    try:
        r = do_query(vars_p)
        c = get_cheapest(r)
        if c:
            diff = base[0] - c[0]
            promo_amt = c[1] or 0
            status = ""
            if promo_amt > 0:
                status = f" <<< PROMO ACTIVA! descuento: ${promo_amt:,.0f}"
                found_promos.append((code, promo_amt, c[0]))
            elif diff > 100:
                status = f" ** precio distinto: ${diff:,.0f} menos"
            p(f"  {code:20s} ${c[0]:>10,.0f}/pp  promo=${promo_amt:>8,.0f}  diff=${diff:>8,.0f}{status}")
        else:
            p(f"  {code:20s} -> sin resultados")
    except Exception as e:
        p(f"  {code:20s} -> error: {str(e)[:50]}")

if found_promos:
    p(f"\n*** PROMOS ENCONTRADAS: {len(found_promos)} ***")
    for code, desc, price in found_promos:
        p(f"  {code}: descuento ${desc:,.0f} -> precio final ${price:,.0f}/pp")
else:
    p("\n  Ningun codigo promo funciono.")

# === TEST 2: MONEDAS ===
p("\n" + "=" * 60)
p("TEST 2: ARBITRAJE DE MONEDA (ARS vs USD vs BRL)")
p("=" * 60)

for curr in ["ARS", "USD", "BRL"]:
    time.sleep(0.3)
    vars_c = {
        "input": {
            "origin": "BUE", "destination": "FLN",
            "departureDate": "2026-03-08", "returnDate": "2026-03-17",
            "currency": curr,
            "pax": {"adults": 2, "children": 0, "infants": 0},
            "promoCode": None,
        }
    }
    try:
        r = do_query(vars_c)
        c = get_cheapest(r)
        if c:
            p(f"  {curr}: {c[0]:>12,.2f}/pp (clase {c[2]}, FO{c[4]})")
    except Exception as e:
        p(f"  {curr}: error - {str(e)[:50]}")

# === TEST 3: MARKET ORIGIN ===
p("\n" + "=" * 60)
p("TEST 3: MARKET ORIGIN (simular comprar desde otro pais)")
p("=" * 60)

for market in ["ar", "br", "py", "uy"]:
    time.sleep(0.3)
    h = HEADERS.copy()
    h["x-fo-market-origin"] = market
    vars_m = {
        "input": {
            "origin": "BUE", "destination": "FLN",
            "departureDate": "2026-03-08", "returnDate": "2026-03-17",
            "currency": "USD",
            "pax": {"adults": 2, "children": 0, "infants": 0},
            "promoCode": None,
        }
    }
    try:
        r = do_query(vars_m, h)
        c = get_cheapest(r)
        if c:
            p(f"  Market '{market}': USD {c[0]:>10,.2f}/pp (clase {c[2]}, FO{c[4]})")
    except Exception as e:
        p(f"  Market '{market}': error - {str(e)[:50]}")

# === TEST 4: 1 ADULTO vs 2 ADULTOS ===
p("\n" + "=" * 60)
p("TEST 4: PRECIO 1 ADULTO vs 2 ADULTOS")
p("=" * 60)

for adults in [1, 2]:
    time.sleep(0.3)
    vars_a = {
        "input": {
            "origin": "BUE", "destination": "FLN",
            "departureDate": "2026-03-08", "returnDate": "2026-03-17",
            "currency": "ARS",
            "pax": {"adults": adults, "children": 0, "infants": 0},
            "promoCode": None,
        }
    }
    try:
        r = do_query(vars_a)
        c = get_cheapest(r)
        if c:
            p(f"  {adults} adulto(s): ${c[0]:>10,.0f}/pp x{adults} = ${c[0]*adults:>12,.0f} total")
    except Exception as e:
        p(f"  {adults} adultos: error")

p("\n" + "=" * 60)
p("FIN DEL ANALISIS")
p("=" * 60)
out.close()
