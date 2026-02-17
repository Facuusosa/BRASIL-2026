
import sys
import os
import json
import time
from datetime import datetime
try:
    from curl_cffi import requests
    print("✅ curl_cffi importado correctamente.")
except ImportError:
    print("❌ curl_cffi NO instalado.")
    sys.exit(1)

URL = "https://flybondi.com/graphql"
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

QUERY_TEMPLATE = """
query (
  $origin: String!
  $destination: String!
  $currency: String!
) {
  departures: fares(origin: $origin, destination: $destination, currency: $currency, start: {start}, end: {end}, sort: "departure") {
    departure
    lowestPrice
    fares {
      price
      availability
    }
  }
}
"""

def test_api():
    print("🦅 Probando conexión con Flybondi API...")
    
    date_str = "2026-03-10" # Martes (El barato)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    ts_start = int(dt.timestamp() * 1000)
    dt_end = dt + time.timedelta(hours=23, minutes=59) if hasattr(time, 'timedelta') else dt # fix
    # actually use datetime.timedelta
    from datetime import timedelta
    dt_end = dt + timedelta(hours=23, minutes=59)
    ts_end = int(dt_end.timestamp() * 1000)

    query_final = QUERY_TEMPLATE.replace("{start}", str(ts_start)).replace("{end}", str(ts_end))
    
    variables = {
        "origin": "BUE",
        "destination": "FLN",
        "currency": "ARS"
    }
    
    payload = {
        "operationName": None,
        "query": query_final,
        "variables": variables
    }
    
    try:
        print(f"📡 Enviando solicitud para {date_str}...")
        start_time = time.time()
        response = requests.post(
            URL,
            json=payload,
            headers=HEADERS, 
            impersonate="chrome110",
            timeout=20
        )
        end_time = time.time()
        print(f"⏱️ Tiempo de respuesta: {end_time - start_time:.2f}s")
        
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print("❌ API respondió con errores:")
                print(json.dumps(data["errors"], indent=2))
            else:
                departures = data.get("data", {}).get("departures", [])
                print(f"✅ ÉXITO: Se encontraron {len(departures)} vuelos.")
                if departures:
                    print(f"   Ejemplo: {departures[0]['departure']} - ${departures[0]['lowestPrice']}")
        else:
            print(f"❌ HTTP ERROR: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")

if __name__ == "__main__":
    test_api()
    print("\n---------------------------------------------------")
    print("Diagnóstico finalizado.")
    if os.path.exists("ODISEO_DASHBOARD.html"):
        print("📁 ODISEO_DASHBOARD.html existe.")
    else:
        print("⚠️ ODISEO_DASHBOARD.html NO existe.")
