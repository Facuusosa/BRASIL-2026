"""
Script de inspección profunda de Flybondi.
Busca: promos ocultas, endpoints, códigos, descuentos.
"""
import json
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

try:
    from curl_cffi import requests as cffi_requests
    HAS_CFFI = True
except:
    import requests as cffi_requests
    HAS_CFFI = False

API_URL = "https://flybondi.com/graphql"
API_KEY = os.getenv(
    "FLYBONDI_API_KEY",
    "b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa"
)
SESSION_COOKIE = os.getenv("FLYBONDI_SESSION", "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8")

HEADERS = {
    "accept": "application/json",
    "accept-language": "es-ES,es;q=0.9",
    "authorization": f"Key {API_KEY}",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/ar/search/dates",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
    "x-fo-ui-version": "2.209.0",
}

def query(gql, variables):
    payload = {"query": gql, "variables": variables}
    cookies = {"SFO": SESSION_COOKIE}
    if HAS_CFFI:
        r = cffi_requests.post(API_URL, json=payload, headers=HEADERS, cookies=cookies, impersonate="chrome120")
    else:
        r = cffi_requests.post(API_URL, json=payload, headers=HEADERS, cookies=cookies)
    return r.json()

# ============================================================
# TEST 1: Probar códigos promo conocidos de Flybondi
# ============================================================
print("=" * 60)
print("TEST 1: PROBANDO CODIGOS PROMO")
print("=" * 60)

PROMO_CODES = [
    "FLYBONDI",
    "FO20",
    "FO30",
    "CLUB20",
    "VERANO",
    "VERANO2026",
    "MARZO",
    "BRASIL",
    "PROMO",
    "DESCUENTO",
    "BIENVENIDO",
    "WELCOME",
    "CARNAVAL",
    "CARNAVAL2026",
    "SUMMER",
    "AMIGO",
    "2X1",
    "FLYCLUB",
    "SALE",
    "HOTDEAL",
    "FLASH",
    "FIRSTFLIGHT",
    "PRIMERVIAJE",
    "SAVE20",
    "OFF20",
    "OFF30",
    "OFF40",
    "VUELA",
    "VOLAR",
]

QUERY_FLIGHTS = """
query FlightSearchContainerQuery($input: FlightsQueryInput!) {
  viewer {
    flights(input: $input) {
      edges {
        node {
          flightNo
          origin
          destination
          departureDate
          fares {
            type
            class
            availability
            passengerType
            prices {
              afterTax
              beforeTax
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

# Primero: precio BASE sin promo
base_vars = {
    "input": {
        "origin": "BUE",
        "destination": "FLN",
        "departureDate": "2026-03-08",
        "returnDate": "2026-03-17",
        "currency": "ARS",
        "pax": {"adults": 2, "children": 0, "infants": 0},
        "promoCode": None,
    }
}

print("\nPrecio BASE (sin promo):")
try:
    base = query(QUERY_FLIGHTS, base_vars)
    if "data" in base and base["data"]["viewer"]["flights"]:
        edges = base["data"]["viewer"]["flights"]["edges"]
        if edges:
            first = edges[0]["node"]
            base_price = first["fares"][0]["prices"]["afterTax"] if first["fares"] else 0
            promo_amt = first["fares"][0]["prices"].get("promotionAmount", 0) if first["fares"] else 0
            print(f"  Vuelo FO{first['flightNo']}: ${base_price:,.0f}/pp | promotionAmount: {promo_amt}")
        else:
            print("  Sin vuelos")
            base_price = 0
    else:
        print(f"  Error: {json.dumps(base.get('errors', base), indent=2)[:500]}")
        base_price = 0
except Exception as e:
    print(f"  Error: {e}")
    base_price = 0

# Probar cada código promo
print(f"\nProbando {len(PROMO_CODES)} códigos promo...")
for code in PROMO_CODES:
    try:
        promo_vars = {
            "input": {
                "origin": "BUE",
                "destination": "FLN",
                "departureDate": "2026-03-08",
                "returnDate": "2026-03-17",
                "currency": "ARS",
                "pax": {"adults": 2, "children": 0, "infants": 0},
                "promoCode": code,
            }
        }
        result = query(QUERY_FLIGHTS, promo_vars)
        if "data" in result and result["data"]["viewer"]["flights"]:
            edges = result["data"]["viewer"]["flights"]["edges"]
            if edges:
                first_fare = edges[0]["node"]["fares"][0] if edges[0]["node"]["fares"] else None
                if first_fare:
                    price = first_fare["prices"]["afterTax"]
                    promo = first_fare["prices"].get("promotionAmount", 0)
                    diff = base_price - price if base_price else 0
                    marker = ""
                    if promo and promo > 0:
                        marker = f" *** PROMO ACTIVA: ${promo:,.0f} descuento ***"
                    elif diff > 100:
                        marker = f" ** PRECIO DISTINTO: ${diff:,.0f} menos **"
                    print(f"  {code:20s} -> ${price:>10,.0f}/pp  promo: ${promo or 0:>8,.0f}  diff: ${diff:>8,.0f}{marker}")
                else:
                    print(f"  {code:20s} -> sin fares")
            else:
                print(f"  {code:20s} -> sin vuelos")
        else:
            errors = result.get("errors", [])
            msg = errors[0].get("message", "unknown") if errors else "unknown"
            print(f"  {code:20s} -> ERROR: {msg[:80]}")
    except Exception as e:
        print(f"  {code:20s} -> EXCEPTION: {str(e)[:80]}")

# ============================================================
# TEST 2: Probar con moneda USD (a veces el precio es distinto)
# ============================================================
print()
print("=" * 60)
print("TEST 2: COMPARAR PRECIO ARS vs USD")
print("=" * 60)

for currency in ["ARS", "USD", "BRL"]:
    try:
        vars_curr = {
            "input": {
                "origin": "BUE",
                "destination": "FLN",
                "departureDate": "2026-03-08",
                "returnDate": "2026-03-17",
                "currency": currency,
                "pax": {"adults": 2, "children": 0, "infants": 0},
                "promoCode": None,
            }
        }
        result = query(QUERY_FLIGHTS, vars_curr)
        if "data" in result and result["data"]["viewer"]["flights"]:
            edges = result["data"]["viewer"]["flights"]["edges"]
            if edges:
                first_fare = edges[0]["node"]["fares"][0] if edges[0]["node"]["fares"] else None
                if first_fare:
                    price = first_fare["prices"]["afterTax"]
                    before = first_fare["prices"]["beforeTax"]
                    print(f"  {currency}: afterTax={price:>12,.2f}  beforeTax={before:>12,.2f}  (impuestos: {price-before:>12,.2f})")
    except Exception as e:
        print(f"  {currency}: Error - {e}")

# ============================================================
# TEST 3: Probar market-origin diferente (comprar "desde Brasil")
# ============================================================
print()
print("=" * 60)
print("TEST 3: CAMBIAR MARKET ORIGIN (ar vs br vs py)")
print("=" * 60)

for market in ["ar", "br", "py", "uy", "us"]:
    try:
        headers_mod = HEADERS.copy()
        headers_mod["x-fo-market-origin"] = market
        
        vars_mkt = {
            "input": {
                "origin": "BUE",
                "destination": "FLN",
                "departureDate": "2026-03-08",
                "returnDate": "2026-03-17",
                "currency": "USD",
                "pax": {"adults": 2, "children": 0, "infants": 0},
                "promoCode": None,
            }
        }
        payload = {"query": QUERY_FLIGHTS, "variables": vars_mkt}
        cookies = {"SFO": SESSION_COOKIE}
        if HAS_CFFI:
            r = cffi_requests.post(API_URL, json=payload, headers=headers_mod, cookies=cookies, impersonate="chrome120")
        else:
            r = cffi_requests.post(API_URL, json=payload, headers=headers_mod, cookies=cookies)
        result = r.json()
        
        if "data" in result and result["data"]["viewer"]["flights"]:
            edges = result["data"]["viewer"]["flights"]["edges"]
            if edges:
                first_fare = edges[0]["node"]["fares"][0] if edges[0]["node"]["fares"] else None
                if first_fare:
                    price = first_fare["prices"]["afterTax"]
                    print(f"  Market '{market}': USD {price:>10,.2f}/pp")
    except Exception as e:
        print(f"  Market '{market}': Error - {str(e)[:60]}")

# ============================================================
# TEST 4: Buscar SOLO IDA (a veces 2 one-ways es más barato)
# ============================================================
print()
print("=" * 60)
print("TEST 4: SOLO IDA vs ROUND-TRIP (¿es más barato separado?)")
print("=" * 60)

# Solo ida
try:
    vars_ow = {
        "input": {
            "origin": "BUE",
            "destination": "FLN",
            "departureDate": "2026-03-08",
            "currency": "ARS",
            "pax": {"adults": 2, "children": 0, "infants": 0},
            "promoCode": None,
        }
    }
    result = query(QUERY_FLIGHTS, vars_ow)
    if "data" in result and result["data"]["viewer"]["flights"]:
        edges = result["data"]["viewer"]["flights"]["edges"]
        if edges:
            cheapest = min(
                (f["prices"]["afterTax"] for e in edges for f in e["node"]["fares"] if f["prices"]["afterTax"] > 0),
                default=0
            )
            print(f"  Solo IDA 08/03: ${cheapest:,.0f}/pp")
except Exception as e:
    print(f"  Solo IDA: Error - {e}")

# Solo vuelta
try:
    vars_ow2 = {
        "input": {
            "origin": "FLN",
            "destination": "BUE",
            "departureDate": "2026-03-17",
            "currency": "ARS",
            "pax": {"adults": 2, "children": 0, "infants": 0},
            "promoCode": None,
        }
    }
    result = query(QUERY_FLIGHTS, vars_ow2)
    if "data" in result and result["data"]["viewer"]["flights"]:
        edges = result["data"]["viewer"]["flights"]["edges"]
        if edges:
            cheapest = min(
                (f["prices"]["afterTax"] for e in edges for f in e["node"]["fares"] if f["prices"]["afterTax"] > 0),
                default=0
            )
            print(f"  Solo VUELTA 17/03: ${cheapest:,.0f}/pp")
except Exception as e:
    print(f"  Solo VUELTA: Error - {e}")

# Round trip que ya tenemos
print(f"  Round-trip cheapest (de log): ida ${179262:,.0f}/pp + vuelta ${178163:,.0f}/pp = ${179262+178163:,.0f}/pp")

print()
print("=" * 60)
print("ANALISIS COMPLETO")
print("=" * 60)
