"""
INTROSPECCIÓN GraphQL de Flybondi.
Preguntamos al API: ¿qué queries, mutations y types tenés?
Esto revela TODO lo que la API puede hacer, incluyendo cosas ocultas.
"""
import json, os
from curl_cffi import requests as cffi_requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

API_URL = "https://flybondi.com/graphql"
API_KEY = os.getenv("FLYBONDI_API_KEY", "b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa")
SESSION_COOKIE = os.getenv("FLYBONDI_SESSION", "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8")

HEADERS = {
    "accept": "application/json",
    "authorization": f"Key {API_KEY}",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/",
    "user-agent": "Mozilla/5.0 Chrome/144.0.0.0 Mobile Safari/537.36",
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
    "x-fo-ui-version": "2.209.0",
}

def do_query(gql, variables=None):
    payload = {"query": gql}
    if variables:
        payload["variables"] = variables
    cookies = {"SFO": SESSION_COOKIE}
    r = cffi_requests.post(API_URL, json=payload, headers=HEADERS, cookies=cookies, impersonate="chrome120", timeout=30)
    return r.json()

out = open("introspection_results.txt", "w", encoding="utf-8")
def p(s=""):
    print(s)
    out.write(s + "\n")
    out.flush()

# ============================================================
# 1. INTROSPECCIÓN COMPLETA DEL SCHEMA
# ============================================================
p("=" * 70)
p("INTROSPECCIÓN GraphQL — DESCUBRIENDO TODO LO QUE LA API PUEDE HACER")
p("=" * 70)

# Query de introspección: obtener todos los tipos, queries y mutations
INTROSPECTION = """
{
  __schema {
    queryType { name }
    mutationType { name }
    types {
      name
      kind
      description
      fields {
        name
        description
        type {
          name
          kind
          ofType { name kind }
        }
        args {
          name
          type { name kind ofType { name kind } }
        }
      }
      inputFields {
        name
        type { name kind ofType { name kind } }
      }
      enumValues {
        name
        description
      }
    }
  }
}
"""

p("\n[1] Ejecutando introspección del schema GraphQL...")
try:
    result = do_query(INTROSPECTION)
    
    if "errors" in result:
        p(f"  ERROR: {json.dumps(result['errors'], indent=2)[:500]}")
        p("  La introspección puede estar deshabilitada. Intentando método alternativo...")
    
    if "data" in result and result["data"].get("__schema"):
        schema = result["data"]["__schema"]
        types = schema.get("types", [])
        
        # Filtrar tipos internos de GraphQL
        custom_types = [t for t in types if not t["name"].startswith("__")]
        
        p(f"\n  SCHEMA DESCUBIERTO:")
        p(f"  Query type: {schema.get('queryType', {}).get('name', 'N/A')}")
        p(f"  Mutation type: {schema.get('mutationType', {}).get('name', 'N/A')}")
        p(f"  Total tipos: {len(types)} ({len(custom_types)} custom)")
        
        # Queries disponibles
        query_type = next((t for t in types if t["name"] == schema.get("queryType", {}).get("name")), None)
        if query_type and query_type.get("fields"):
            p(f"\n  === QUERIES DISPONIBLES ({len(query_type['fields'])}) ===")
            for field in query_type["fields"]:
                args_str = ", ".join([f"{a['name']}: {a['type'].get('name') or a['type'].get('ofType', {}).get('name', '?')}" for a in (field.get("args") or [])])
                ret_type = field["type"].get("name") or field["type"].get("ofType", {}).get("name", "?")
                desc = field.get("description", "")
                p(f"    {field['name']}({args_str}) -> {ret_type}")
                if desc:
                    p(f"      Desc: {desc}")
        
        # Mutations disponibles
        mutation_type = next((t for t in types if t["name"] == schema.get("mutationType", {}).get("name")), None)
        if mutation_type and mutation_type.get("fields"):
            p(f"\n  === MUTATIONS DISPONIBLES ({len(mutation_type['fields'])}) ===")
            for field in mutation_type["fields"]:
                args_str = ", ".join([f"{a['name']}: {a['type'].get('name') or a['type'].get('ofType', {}).get('name', '?')}" for a in (field.get("args") or [])])
                desc = field.get("description", "")
                p(f"    {field['name']}({args_str})")
                if desc:
                    p(f"      Desc: {desc}")
        
        # Tipos interesantes (buscar deals, promos, discounts, etc)
        interesting_keywords = ["promo", "deal", "discount", "coupon", "offer", "sale", "reward",
                               "club", "member", "loyalty", "voucher", "credit", "bundle", "pack",
                               "flex", "cheap", "low", "special", "gift", "refer"]
        
        p(f"\n  === TIPOS INTERESANTES (buscando keywords) ===")
        for t in custom_types:
            name_lower = t["name"].lower()
            desc_lower = (t.get("description") or "").lower()
            matched = [kw for kw in interesting_keywords if kw in name_lower or kw in desc_lower]
            if matched:
                p(f"    {t['name']} (kind: {t['kind']}) - matched: {matched}")
                if t.get("description"):
                    p(f"      Desc: {t['description']}")
                if t.get("fields"):
                    for f in t["fields"]:
                        p(f"      .{f['name']} -> {f['type'].get('name', '?')}")
                if t.get("enumValues"):
                    p(f"      Values: {[v['name'] for v in t['enumValues']]}")
                if t.get("inputFields"):
                    for f in t["inputFields"]:
                        p(f"      input .{f['name']} -> {f['type'].get('name') or f['type'].get('ofType', {}).get('name', '?')}")
        
        # Input types (ver qué parámetros acepta la búsqueda)
        p(f"\n  === INPUT TYPES (qué parámetros acepta la API) ===")
        for t in custom_types:
            if t["kind"] == "INPUT_OBJECT":
                p(f"    {t['name']}:")
                if t.get("inputFields"):
                    for f in t["inputFields"]:
                        type_name = f["type"].get("name") or f["type"].get("ofType", {}).get("name", "?")
                        p(f"      .{f['name']}: {type_name}")
        
        # Enums (valores fijos que acepta la API)
        p(f"\n  === ENUMS (valores fijos permitidos) ===")
        for t in custom_types:
            if t["kind"] == "ENUM" and t.get("enumValues"):
                vals = [v["name"] for v in t["enumValues"]]
                p(f"    {t['name']}: {vals}")
        
        # Guardar schema completo
        with open("flybondi_schema_full.json", "w", encoding="utf-8") as sf:
            json.dump(result["data"]["__schema"], sf, indent=2, ensure_ascii=False)
        p(f"\n  Schema completo guardado en flybondi_schema_full.json")
    else:
        p("  No se pudo obtener el schema.")
        
except Exception as e:
    p(f"  EXCEPTION: {e}")

# ============================================================
# 2. BUSCAR ENDPOINTS ADICIONALES
# ============================================================
p("\n" + "=" * 70)
p("BUSCANDO ENDPOINTS OCULTOS")
p("=" * 70)

# Probar distintos queries que podrían existir
POSSIBLE_QUERIES = [
    # Deals/Ofertas
    ('deals', '{ deals { id title price destination } }'),
    ('offers', '{ offers { id price route } }'),
    ('flashSales', '{ flashSales { id price } }'),
    ('promotions', '{ promotions { id code discount } }'),
    
    # Precios flexibles
    ('flexibleDates', '{ flexibleDates(origin: "BUE", destination: "FLN") { date price } }'),
    ('cheapestDates', '{ cheapestDates(origin: "BUE", destination: "FLN") { date price } }'),
    ('priceCalendar', '{ priceCalendar(origin: "BUE", destination: "FLN", month: "2026-03") { date price } }'),
    
    # Bundles
    ('bundles', '{ bundles { id name price includes } }'),
    ('packages', '{ packages { id price } }'),
    
    # Club/membership
    ('clubPrices', '{ clubPrices(origin: "BUE", destination: "FLN") { price discount } }'),
    ('membership', '{ membership { plans { name price discount } } }'),
    
    # Anywhere (destinos baratos)
    ('cheapestDestinations', '{ cheapestDestinations(origin: "BUE") { destination price } }'),
    ('explore', '{ explore(origin: "BUE") { destinations { code price } } }'),
]

for name, q in POSSIBLE_QUERIES:
    try:
        r = do_query(q)
        if "errors" in r:
            msg = r["errors"][0].get("message", "")[:80]
            # Si dice "Cannot query field" no existe; si dice otra cosa, interesante
            if "Cannot query field" not in msg:
                p(f"  {name}: RESPUESTA INUSUAL -> {msg}")
            else:
                p(f"  {name}: no existe")
        elif "data" in r:
            p(f"  {name}: *** EXISTE! *** -> {json.dumps(r['data'])[:200]}")
    except Exception as e:
        p(f"  {name}: error - {str(e)[:50]}")

# ============================================================
# 3. VERIFICAR SI HAY DIFERENTES FARE TYPES OCULTOS
# ============================================================
p("\n" + "=" * 70)
p("BUSCANDO FARE TYPES OCULTOS")
p("=" * 70)

GQL_DETAILED = """
query Q($input: FlightsQueryInput!) {
  viewer {
    flights(input: $input) {
      edges {
        node {
          flightNo
          origin
          destination
          departureDate
          equipmentId
          fares {
            fareRef
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
            taxes {
              taxRef
              taxCode
              codeType
              amount
              description
            }
          }
        }
      }
    }
    id
  }
}
"""

vars_detail = {
    "input": {
        "origin": "BUE", "destination": "FLN",
        "departureDate": "2026-03-08", "returnDate": "2026-03-17",
        "currency": "ARS",
        "pax": {"adults": 2, "children": 0, "infants": 0},
        "promoCode": "CARNAVAL",
    }
}

try:
    r = do_query(GQL_DETAILED, vars_detail)
    if "data" in r:
        edges = r["data"]["viewer"]["flights"]["edges"]
        p(f"  Vuelos encontrados: {len(edges)}")
        
        # Analizar primer vuelo en detalle
        if edges:
            node = edges[0]["node"]
            p(f"\n  VUELO DETALLADO: FO{node['flightNo']} {node['origin']}->{node['destination']} {node['departureDate']}")
            p(f"  Equipment: {node.get('equipmentId', '?')}")
            
            for fi, fare in enumerate(node.get("fares", [])):
                p(f"\n  FARE {fi+1}:")
                p(f"    fareRef: {fare.get('fareRef', '?')}")
                p(f"    type: {fare.get('type', '?')}")
                p(f"    class: {fare.get('class', '?')}")
                p(f"    basis: {fare.get('basis', '?')}")
                p(f"    availability: {fare.get('availability', '?')}")
                p(f"    passengerType: {fare.get('passengerType', '?')}")
                p(f"    afterTax: ${fare['prices']['afterTax']:,.2f}")
                p(f"    beforeTax: ${fare['prices']['beforeTax']:,.2f}")
                p(f"    baseBeforeTax: ${fare['prices'].get('baseBeforeTax', 0):,.2f}")
                p(f"    promotionAmount: ${fare['prices'].get('promotionAmount', 0):,.2f}")
                
                if fare.get("taxes"):
                    p(f"    TAXES ({len(fare['taxes'])}):")
                    for tax in fare["taxes"]:
                        p(f"      {tax.get('taxCode','?')} ({tax.get('codeType','?')}): ${tax.get('amount',0):,.2f} - {tax.get('description','?')}")
except Exception as e:
    p(f"  Error: {e}")

p("\n" + "=" * 70)
p("FIN")
p("=" * 70)
out.close()
