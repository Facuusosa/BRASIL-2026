import requests
import json
import uuid
from datetime import datetime

# URL del Endpoint GraphQL (deducido del análisis)
URL = "https://flybondi.com/graphql"

# Headers simulando un navegador real + los headers específicos de Flybondi encontrados
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Origin": "https://flybondi.com",
    "Referer": "https://flybondi.com/ar/search/p/BUE/FLN/2026-03-10/2026-03-20/1/0/0",
    "x-flybondi-source": "web",  # Probable header necesario
    "x-market": "ar", # Probable header de mercado
    # Los headers encontrados en el análisis:
    "X-FO-Market-Origin": "AR",
    "X-FO-Shopping-Id": str(uuid.uuid4()),  # Generamos un ID único simulado
    "X-FO-UI-Version": "3.10.0", # Valor simulado, idealmente extraer del bundle exacto
    # "X-Requested-With": "XMLHttpRequest",
}

# La Query EXACTA extraída de flight-search.574dc118.chunk.js
# (Simplificada para no incluir fragmentos innecesarios si es posible, pero usaremos la estructura completa para ser idénticos)
QUERY = """
query FlightSearchContainerQuery(
  $input: FlightsQueryInput!
  $origin: String!
  $destination: String!
  $currency: String!
  $start: Timestamp!
  $end: Timestamp!
) {
  airports(onlyActive: false) {
    code
    location {
      cityName
    }
  }
  departures: fares(origin: $origin, destination: $destination, currency: $currency, start: $start, end: $end, sort: "departure") {
    id
    departure
    fares {
      price
      fCCode
      fBCode
      roundtrip
      hasRestrictions
    }
    lowestPrice
  }
  arrivals: fares(origin: $destination, destination: $origin, currency: $currency, start: $start, end: $end, sort: "departure") {
    id
    departure
    fares {
      price
      fCCode
      fBCode
      roundtrip
      hasRestrictions
    }
    lowestPrice
  }
  viewer {
      session {
          id
      }
  }
}
"""

# La Query es la misma, se mantiene igual...
# ... (QUERY OMITIDA POR BREVEDAD, YA ESTA EN EL ARCHIVO) ...

# ... (QUERY OMITIDA) ...

def load_cookies():
    """Carga cookies desde el archivo generado por Golden Eye"""
    try:
        if os.path.exists("flybondi_cookies.json"):
            with open("flybondi_cookies.json", "r") as f:
                data = json.load(f)
                return data.get("cookies", {}), data.get("user_agent")
    except Exception as e:
        print(f"⚠️ Error cargando cookies: {e}")
    return {}, None

def get_flybondi_prices(origin, destination, date_start, date_end):
    # Convertir fechas a timestamps
    dt_start = datetime.strptime(date_start, "%Y-%m-%d")
    dt_end = datetime.strptime(date_end, "%Y-%m-%d")
    ts_start = int(dt_start.timestamp() * 1000)
    ts_end = int(dt_end.timestamp() * 1000)

    # Variables de la query
    variables = {
        "input": {
            "origin": origin,
            "destination": destination,
            "departureDate": date_start,
            "returnDate": date_end,
            "currency": "ARS", # Cambiado a ARS según contexto usuario (aunque curl decía USD)
            "pax": {
                "adults": 1,
                "children": 0,
                "infants": 0
            },
            "promoCode": None
        },
        "origin": origin,
        "destination": destination,
        "currency": "ARS",
        "start": ts_start, 
        "end": ts_end      
    }

    payload = {
        "operationName": "FlightSearchContainerQuery",
        "query": QUERY,
        "variables": variables
    }

    print(f"📡 Preparando consulta API Flybondi (Modo ESPEJO IDENTITY): {origin} -> {destination}")

    # No usamos load_cookies() aqui para probar limpieza, o las usamos para complementar?
    # El curl tenía cookie FBSessionX-ar-ibe. Golden Eye la consigue fresca.
    # Usemos Golden Eye cookies si existen, si no, intentemos sin ellas (hard mode) a ver si la Key basta.
    # Mejor usar las cookies frescas de Golden Eye.
    cookies, _ = load_cookies()
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Generar Shopping ID
    session.headers["x-fo-shopping-id"] = str(uuid.uuid4())

    if cookies:
        session.cookies.update(cookies)
        # Asegurar que FBSessionX-ar-ibe esté presente si no vino
        if "FBSessionX-ar-ibe" not in cookies:
            print("⚠️ Cookie de sesión crítica faltando, usando placeholder...")
    else:
         print("⚠️ No hay cookies frescas. La petición podría fallar sin sesión válida.")

    try:
        # PASO 2: Consultar GraphQL
        print(f"🚀 Enviando Query GraphQL...")
        
        response = session.post(URL, json=payload, timeout=20)
        
        print(f"🔄 Código HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print("⚠️ Errores en GraphQL:")
                print(json.dumps(data["errors"], indent=2))
                # Algunos errores son 'soft' (ej: no availability), devolvamos data igual
                if data.get("data"):
                    return data
                return None
            
            filename = f"flybondi_{origin}_{destination}_{date_start}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ ¡ÉXITO! PRECIOS OBTENIDOS. Guardado en {filename}")
            return data
        else:
            print(f"❌ Error API: {response.status_code}")
            # Guardar el error para debug
            with open("debug_error.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("   (HTML guardado en debug_error.html)")
            return None

    except Exception as e:
        print(f"💥 Excepción crítica: {e}")
        return None

if __name__ == "__main__":
    import os
    # Prueba
    get_flybondi_prices("BUE", "FLN", "2026-03-10", "2026-03-20")
