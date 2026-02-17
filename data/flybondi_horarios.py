from curl_cffi import requests
import json
import datetime
import time

# CONFIGURACIÓN USUARIO
ORIGIN = "BUE"
DESTINATION = "FLN"
FECHAS_IDA = ["2026-03-08", "2026-03-09", "2026-03-10", "2026-03-11", "2026-03-12"]
FECHA_VUELTA_REF = "2026-03-18" # Referencia para cerrar el roundtrip

# LÍMITES HORARIOS (Hora Local)
HORA_MIN_SALIDA = 5  # 05:00 AM
HORA_MAX_LLEGADA = 20 # 20:00 PM

# URL & HEADERS (Validado)
URL = "https://flybondi.com/graphql"
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# QUERY DETALLADA (Vuelos específicos)
QUERY_FLIGHTS = """
query FlightSearchContainerQuery($input: FlightsQueryInput!) {
  viewer {
    flights(input: $input) {
      edges {
        node {
          departureDate
          arrivalDate
          flightNo
          fares {
            prices {
              afterTax
            }
          }
          origin
          destination
        }
      }
    }
  }
}
"""

def buscar_vuelos_dia(fecha_ida):
    print(f"\n🔎 Analizando vuelos para: {fecha_ida}...")
    
    variables = {
        "input": {
            "adults": 1,
            "currency": "ARS",
            "from": fecha_ida,
            "to": FECHA_VUELTA_REF, # Vuelta dummy para que la API responda
            "origin": ORIGIN,
            "destination": DESTINATION,
            "roundtrip": True,
            "brand": "flybondi",
            "children": 0,
            "infants": 0
        }
    }

    payload = {
        "operationName": None,
        "query": QUERY_FLIGHTS,
        "variables": variables
    }

    try:
        response = requests.post(
            URL,
            json=payload,
            headers=HEADERS,
            impersonate="chrome110",
            timeout=15
        )

        if response.status_code != 200:
            print(f"❌ Error API: {response.status_code}")
            return

        data = response.json()
        edges = data.get("data", {}).get("viewer", {}).get("flights", {}).get("edges", [])
        
        vuelos_encontrados = 0
        
        for edge in edges:
            node = edge.get("node", {})
            
            # Filtrar solo la IDA (BUE -> FLN)
            if node.get("origin") != ORIGIN or node.get("destination") != DESTINATION:
                continue

            # Extraer fechas y horas
            dep_raw = node["departureDate"] # Ej: 2026-03-10T17:05:00
            arr_raw = node["arrivalDate"]
            
            # Solo queremos la fecha exacta que pedimos (a veces trae días adyacentes)
            if not dep_raw.startswith(fecha_ida):
                continue
                
            dep_dt = datetime.datetime.fromisoformat(dep_raw)
            arr_dt = datetime.datetime.fromisoformat(arr_raw)
            
            hora_salida = dep_dt.hour
            hora_llegada = arr_dt.hour
            
            # --- FILTRO DEL USUARIO ---
            cumple_salida = hora_salida >= HORA_MIN_SALIDA
            cumple_llegada = hora_llegada < HORA_MAX_LLEGADA # Estricto < 20:00 (llegar tipo 20hs max)
            
            # Precio
            fares = node.get("fares", [])
            precios = []
            for f in fares:
                p = f.get("prices", {}).get("afterTax")
                if p: precios.append(p)
            
            precio_final = min(precios) if precios else 0
            
            # Emoji status
            status = "✅"
            motivo = "OK"
            
            if not cumple_salida:
                status = "❌"
                motivo = f"Sale muy temprano ({dep_dt.strftime('%H:%M')})"
            elif not cumple_llegada:
                status = "❌"
                motivo = f"Llega muy tarde ({arr_dt.strftime('%H:%M')})"
            elif precio_final > 400000:
                status = "⚠️"
                motivo = "Muy caro"

            if status == "✅":
                vuelos_encontrados += 1
                print(f"  ✈️  {dep_dt.strftime('%H:%M')} -> {arr_dt.strftime('%H:%M')} | Vuelo {node['flightNo']}")
                print(f"      💰 Precio: ${precio_final:,.0f}")
                print(f"      🌟 ¡OPCIÓN VALIDA!")
            else:
                # Mostrar descartados en gris/detalle para que sepa que existen
                print(f"  💀  {dep_dt.strftime('%H:%M')} -> {arr_dt.strftime('%H:%M')} | {motivo} | ${precio_final:,.0f}")

        if vuelos_encontrados == 0:
            print("  ⚠️  No hay vuelos que cumplan tus requisitos este día.")

    except Exception as e:
        print(f"💥 Error técnico: {e}")

print("🚀 INICIANDO ESCANEO DE HORARIOS PRECISOS (05:00 - 20:00)")
print("=======================================================")

for dia in FECHAS_IDA:
    buscar_vuelos_dia(dia)
    time.sleep(2) # Respetar API

print("\n🏁 Escaneo finalizado.")
