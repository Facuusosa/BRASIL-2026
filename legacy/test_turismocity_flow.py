from curl_cffi import requests
import json
import time
import random

def test_turismocity_flow():
    print("🕵️ Iniciando ingeniería inversa del flujo Turismocity...")
    
    session = requests.Session(impersonate="chrome124")
    
    # Headers base extraidos de su cURL
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'es-ES,es;q=0.9',
        'origin': 'https://www.turismocity.com.ar',
        'referer': 'https://www.turismocity.com.ar/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36'
    }
    
    # PASO 1: Iniciar búsqueda para obtener un ID nuevo
    # La URL de inicio suele ser así según la web:
    # https://www.turismocity.com.ar/api/w/flight_search?from=BUE&to=FLN&d=2026-03-08&r=2026-03-15&currency=ARS
    
    # Fechas de prueba (mismas que Flybondi)
    params = {
        "from": "BUE",
        "to": "FLN",
        "d": "2026-03-10",  # Ida
        "r": "2026-03-17",  # Vuelta
        "currency": "ARS",
        "cabin": "Y",       # Economy
        "adults": 2,
        "children": 0,
        "infants": 0
    }
    
    # Endpoint probable de inicio (descubierto por patrón común)
    init_url = "https://www.turismocity.com.ar/api/w/flight_search" 
    
    print(f"1. Solicitando inicio de búsqueda: {init_url}")
    try:
        resp = session.get(init_url, params=params, headers=headers)
        print(f"   Status: {resp.status_code}")
        
        search_id = None
        if resp.status_code == 200:
            data = resp.json()
            search_id = data.get("id") or data.get("searchId")
            print(f"   ✅ ID obtenido: {search_id}")
        else:
            print("   ❌ Falló el inicio. Intentando método alternativo (HTML parse)...")
            # Método B: La búsqueda se inicia al cargar la web y el ID viene en el HTML
            web_url = f"https://www.turismocity.com.ar/vuelos-baratos-a-FLN-Florianopolis-desde-BUE-Buenos_Aires"
            resp_web = session.get(web_url, params={"d": "2026-03-10", "r": "2026-03-17"}, headers=headers)
            # Buscar patrón de ID en el HTML... complejo sin ver el raw response.
            
        if not search_id:
            print("⚠️ No se pudo obtener ID automático. Usaremos el ID manual que me pasó para probar el endpoint de resultados.")
            search_id = "0b99b6c71bd453ca05a868fb5b849b1d" # ID MANUAL DE EJEMPLO

        # PASO 2: Consultar resultados (rpull)
        print(f"\n2. Consultando resultados para ID: {search_id}")
        rpull_url = f"https://api.turismocity.com/flights/rpull/{search_id}"
        
        # Consultamos version 'final' directo
        rpull_params = {"v": "final"}
        
        resp_pull = session.get(rpull_url, params=rpull_params, headers=headers)
        
        if resp_pull.status_code == 200:
            results = resp_pull.json()
            print(f"   ✅ ÉXITO! Recibidos {len(str(results))} bytes de datos.")
            
            # Guardar muestra para analizar estructura
            with open("turismocity_sample.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print("   💾 Guardado en 'turismocity_sample.json'")
            
            # Intentar ver precios
            if "flights" in results:
                print(f"   ✈️ Vuelos encontrados: {len(results['flights'])}")
                # Imprimir el primero de muestra
                if len(results['flights']) > 0:
                    first = results['flights'][0]
                    price = first.get("price", {}).get("totalAmount")
                    print(f"   💰 Precio ejemplo: {price}")
            else:
                print("   ⚠️ JSON recibido pero sin clave 'flights'. Revisar estructura en archivo.")
                
        elif resp_pull.status_code == 404:
            print("   ❌ Error 404: El ID de búsqueda ha caducado (necesito generar uno nuevo).")
        else:
            print(f"   ❌ Error {resp_pull.status_code} en rpull.")

    except Exception as e:
        print(f"💥 Error crítico: {e}")

if __name__ == "__main__":
    test_turismocity_flow()
