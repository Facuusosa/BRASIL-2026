"""
Prueba de TODOS los códigos promo encontrados online + variantes.
"""
import json, os, time
from curl_cffi import requests as cffi_requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass

API_URL = "https://flybondi.com/graphql"
API_KEY = os.getenv("FLYBONDI_API_KEY", "b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa")
SESSION_COOKIE = os.getenv("FLYBONDI_SESSION", "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8")
HEADERS = {
    "accept": "application/json",
    "authorization": f"Key {API_KEY}",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/ar/search/dates",
    "user-agent": "Mozilla/5.0 Chrome/144.0.0.0 Mobile Safari/537.36",
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
          fares {
            type
            class
            availability
            prices { afterTax beforeTax promotionAmount }
          }
        }
      }
    }
    id
  }
}
""".strip()

def get_price(promo_code=None):
    variables = {
        "input": {
            "origin": "BUE", "destination": "FLN",
            "departureDate": "2026-03-08", "returnDate": "2026-03-17",
            "currency": "ARS",
            "pax": {"adults": 2, "children": 0, "infants": 0},
            "promoCode": promo_code,
        }
    }
    payload = {"query": GQL, "variables": variables}
    cookies = {"SFO": SESSION_COOKIE}
    r = cffi_requests.post(API_URL, json=payload, headers=HEADERS, cookies=cookies, impersonate="chrome120", timeout=15)
    data = r.json()
    try:
        edges = data["data"]["viewer"]["flights"]["edges"]
        best_price = float('inf')
        best_promo = 0
        best_info = ""
        for e in edges:
            for f in e["node"]["fares"]:
                p = f["prices"]["afterTax"]
                promo = f["prices"].get("promotionAmount", 0) or 0
                if p < best_price:
                    best_price = p
                    best_promo = promo
                    best_info = f"FO{e['node']['flightNo']} clase {f['class']}"
        return best_price, best_promo, best_info
    except:
        return None, None, str(data.get("errors", "unknown"))[:80]

# Codigos encontrados en búsqueda web + variantes
CODES = [
    # Encontrados en búsqueda web
    "CARNAVAL", "FIESTAS", "FINDELARGO",
    # Variantes de temporada
    "VERANO", "VERANO26", "VERANO2026", "SUMMER", "SUMMER26",
    # Variantes de carnaval
    "CARNAVAL26", "CARNAVAL2026",
    # Probables de febrero
    "FEBRERO", "FEBRERO26", "FEB26", "SANVALENTIN", "VALENTINE",
    # Club/membresía
    "CLUB", "CLUBFO", "CLUB20", "CLUB30", "FLYCLUB",
    # Descuentos genéricos
    "DESC10", "DESC15", "DESC20", "DESC30", "DESC40",
    "OFF10", "OFF15", "OFF20", "OFF25", "OFF30", "OFF40",
    "PROMO10", "PROMO15", "PROMO20", "PROMO30",
    # Incógnito (mencionado en la web!)
    "INCOGNITO", "DESCUENTO", "SECRETO", "OCULTO",
    # Destino
    "BRASIL", "BRASIL26", "FLORIPA", "FLN", "FLORIANOPOLIS",
    # Airline specific
    "FLYBONDI", "FO", "FLYB", "BONDI",
    "BIENVENIDO", "WELCOME", "HOLA", "PRIMERA",
    "PRIMERVIAJE", "FIRSTFLIGHT", "NEWUSER",
    # Marketing
    "NEWSLETTER", "EMAIL", "SUSCRIPTOR", "APP", "MOBILE",
    # Temporadas
    "MARZO", "MARZO26", "MAR26",
    # Sale
    "SALE", "SALE10", "SALE20", "SALE30",
    "FLASH", "FLASH20", "FLASHSALE",
    "HOTDEAL", "DEAL", "DEAL20",
    # Tarjetas
    "VISA", "MASTER", "NARANJAX", "MERCADOPAGO",
    # Referidos
    "AMIGO", "FRIEND", "REFERIDO", "REFER",
    # Aniversario
    "ANIVERSARIO", "BIRTHDAY", "CUMPLE",
    # La Nacion
    "LANACION", "NACION", "CLUBLNACION",
    # Ahorro
    "AHORRO", "SAVE", "SAVE10", "SAVE20", "SAVE30",
    # 2x1
    "2X1", "DOBLE", "DUO", "PAREJA",
]

# Deduplicar
CODES = list(dict.fromkeys(CODES))

print(f"Probando {len(CODES)} codigos promo contra la API de Flybondi...")
print()

# Precio base
base_price, _, base_info = get_price(None)
print(f"PRECIO BASE (sin codigo): ${base_price:,.0f}/pp - {base_info}")
print("=" * 80)

winners = []
for code in CODES:
    time.sleep(0.2)  # Ser amables
    price, promo, info = get_price(code)
    if price is None:
        print(f"  {code:20s} -> ERROR: {info}")
        continue
    
    diff = base_price - price
    if promo and promo > 0:
        print(f"  {code:20s} -> ${price:>10,.0f}/pp  PROMO: -${promo:,.0f}  ({info})  *** FUNCIONA! ***")
        winners.append((code, price, promo, diff))
    elif diff > 100:
        print(f"  {code:20s} -> ${price:>10,.0f}/pp  diff: -${diff:,.0f}  ** PRECIO DIFERENTE **")
        winners.append((code, price, 0, diff))
    else:
        print(f"  {code:20s} -> ${price:>10,.0f}/pp  (= base)")

print()
print("=" * 80)
if winners:
    print(f"\n*** {len(winners)} CODIGOS QUE FUNCIONAN: ***\n")
    winners.sort(key=lambda x: x[1])  # Ordenar por precio
    for code, price, promo, diff in winners:
        total_2pax = price * 2
        equiv_usd = total_2pax / 1440  # Dolar MEP aprox
        print(f"  Codigo: {code}")
        print(f"    Precio/pp: ${price:,.0f}")
        print(f"    Descuento: ${promo:,.0f}")
        print(f"    Total 2 personas (solo ida): ${total_2pax:,.0f} = USD {equiv_usd:.0f}")
        print(f"    Ahorro vs base: ${diff:,.0f}/pp = ${diff*2:,.0f} total")
        print()
else:
    print("Ningun codigo funciono :(")
