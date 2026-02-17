import requests
import json

# URL y Headers (Mismos del monitor)
URL = "https://flybondi.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Query Específica para ver VUELTAS del 18 de Marzo (FLN -> BUE)
QUERY = """
query GetFlight($origin: String!, $destination: String!, $date: Timestamp!) {
  flights(input: {
    origin: $origin,
    destination: $destination,
    from: $date,
    adults: 2,
    currency: "ARS",
    brand: "flybondi"
  }) {
    edges {
      node {
        departureDate
        prices {
          total
          base
          taxes
          fees
          afterTax
          beforeTax
          breakdown {
            description
            amount
          }
        }
      }
    }
  }
}
"""

# Variables para el 18 de Marzo
VARIABLES = {
    "origin": "FLN",
    "destination": "BUE",
    "date": "2026-03-18T00:00:00"
}

print(f"🕵️‍♂️ INSPECCIONANDO VUELO FLN->BUE DEL 18 MARZO...")
try:
    # Intento 1: Estructura simple (a veces cambia la API)
    payload = {
        "operationName": "GetFlight",
        "variables": VARIABLES,
        "query": QUERY
    }
    
    # NOTA: La API de Flybondi es compleja. Usaremos la query del monitor si esta falla.
    # Pero primero probemos una introspección directa.
    
    # ---------------------------------------------------------
    # ESTRATEGIA 2: Usar la misma query del monitor pero IMPRIMIR TODO
    # ---------------------------------------------------------
    from monitor_flybondi import query_flybondi, parse_flights
    
    print("🔄 Usando motor del Monitor para obtener JSON crudo...")
    data = query_flybondi("2026-03-08", "2026-03-18") # Ida 8, Vuelta 18
    
    if not data:
        print("❌ Error: No data received")
        exit()

    # Buscar ESPECÍFICAMENTE el vuelo de vuelta del 18
    flights = data.get("data", {}).get("viewer", {}).get("flights", {}).get("edges", [])
    
    found = False
    print("\n📦 ANÁLISIS DE PRECIOS RAW (CRUDO):")
    for edge in flights:
        node = edge["node"]
        dep = node["departureDate"]
        
        if "2026-03-18" in dep and node["origin"] == "FLN":
            found = True
            print(f"\n==========================================")
            print(f"✈️ VUELO ENCONTRADO: {dep}")
            print(f"🆔 ID: {node['id']}")
            
            p = node["prices"]
            print(f"💰 AfterTax (Final?): {p['afterTax']}")
            print(f"💰 BeforeTax (Base?): {p['beforeTax']}")
            print(f"💰 BaseBeforeTax:     {p['baseBeforeTax']}")
            print(f"💰 PromotionAmount:   {p.get('promotionAmount', 0)}")
            
            # Ver si hay desglose extra
            print(f"\n🔍 DATOS COMPLETOS DEL NODO:")
            print(json.dumps(node, indent=2))
            print(f"==========================================\n")
            
    if not found:
        print("❌ No se encontró el vuelo del 18 de Marzo en la respuesta.")

except Exception as e:
    print(f"💥 Error fatal: {e}")
