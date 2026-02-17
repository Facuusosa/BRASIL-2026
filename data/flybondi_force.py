from curl_cffi import requests
import json
import uuid
import datetime

# CONFIGURACIÓN
ORIGIN = "BUE"
DESTINATION = "FLN" # Objetivo: Brasil
# FECHAS: Rango solicitado por usuario (8-12 Marzo)
DATE_START = "2026-03-08"
DATE_END = "2026-03-13" # Un día extra por las dudas

# URL GraphQL
URL = "https://flybondi.com/graphql"

# HEADERS (Copiados de identity.txt)
HEADERS = {
    "accept": "application/json",
    "accept-language": "es-ES,es;q=0.9",
    # Token - CRÍTICO: Si falla, este token expiró.
    "authorization": "Key b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/ar/search/results?adults=1&currency=ARS&from=BUE&to=FLN",
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
    "x-fo-ui-version": "2.209.0",
}

# QUERY BASE LIMPIA (Solo lo que usamos)
QUERY_TEMPLATE = """
query (
  $origin: String!
  $destination: String!
  $currency: String!
) {{
  airports(onlyActive: false) {{
    code
    location {{
      cityName
    }}
  }}
  departures: fares(origin: $origin, destination: $destination, currency: $currency, start: {start}, end: {end}, sort: "departure") {{
    id
    departure
    fares {{
      price
      fCCode
      fBCode
      roundtrip
      hasRestrictions
    }}
    lowestPrice
  }}
}}
"""

def get_prices(origin=ORIGIN, destination=DESTINATION, date_start=DATE_START, date_end=DATE_END):
    print(f"🚀 Iniciando FLYBONDI FORCE (CLEAN QUERY) | {origin}-{destination} | {date_start}")
    
    # Timestamps (Milisegundos)
    dt_start = datetime.datetime.strptime(date_start, "%Y-%m-%d")
    dt_end = datetime.datetime.strptime(date_end, "%Y-%m-%d")
    ts_start = int(dt_start.timestamp() * 1000)
    ts_end = int(dt_end.timestamp() * 1000)

    # Inyectar timestamps
    query_final = QUERY_TEMPLATE.format(start=ts_start, end=ts_end)

    # Variables (Solo las declaradas en la query)
    variables = {
        "origin": origin,
        "destination": destination,
        "currency": "ARS"
    }

    payload = {
        "operationName": None, # Forzar query ad-hoc
        "query": query_final,
        "variables": variables
    }

    try:
        # Petición Stealth con curl_cffi
        response = requests.post(
            URL,
            json=payload,
            headers=HEADERS,
            impersonate="chrome110",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # GUARDAR RAW SIEMPRE (Debug Mode)
            with open("flybondi_force_raw.json", "w") as f:
                json.dump(data, f, indent=2)
            print("💾 JSON crudo guardado en flybondi_force_raw.json")

            if "errors" in data:
                print(f"❌ Errores en la respuesta API: {data['errors']}")
                return None

            print("✅ ¡RESPUESTA 200 OK! Payload recibido.")
            
            # Extraer precios de Salida (Departures)
            fares_dep = data.get("data", {}).get("departures", [])
            print(f"📦 Vuelos de IDA encontrados: {len(fares_dep)}")
            
            prices = []
            for flight in fares_dep:
                # Cada 'flight' es un día/vuelo con 'lowestPrice' y lista de 'fares'
                lp = flight.get("lowestPrice")
                fecha = flight.get("departure")
                
                if lp:
                    prices.append(lp)
                    print(f"   ✈️ {fecha[:10]}: ${lp:,.2f}")
            
            if prices:
                min_p = min(prices)
                print(f"💰 MEJOR PRECIO ENCONTRADO: ${min_p:,.2f}")
                
                # Guardar resultado JSON limpio
                res_file = f"flybondi_success_{date_start}.json"
                with open(res_file, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"📁 Datos guardados en {res_file}")
                
                return min_p
            else:
                print("⚠️ No hay precios disponibles para estas fechas.")
                return 0
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(response.text[:500])
            return None

    except Exception as e:
        print(f"💥 Error Fatal: {e}")
        return None

if __name__ == "__main__":
    get_prices()
