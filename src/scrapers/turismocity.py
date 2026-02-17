import re
import json
import time
# curl_cffi es nuestra única dependencia externa fuerte
from curl_cffi import requests

# Configuración
ORIGIN = "BUE"
DESTINATION = "FLN"

class TurismocityScraper:
    def __init__(self):
        # Intentamos simular un Android antiguo para forzar versión ligera o SSR
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'accept-language': 'es-ES,es;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': 'https://www.google.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36'
        }

    def get_search_id(self, date_out, date_in):
        """Intenta obtener el SEARCH_ID visitando la página de resultados."""
        
        # URL de búsqueda estilo "SEO Friendly" que usa Turismocity
        # Esta URL suele redirigir o cargar el JS necesario
        search_url = f"https://www.turismocity.com.ar/vuelos-baratos-a-{DESTINATION}-Florianopolis-desde-{ORIGIN}-Buenos_Aires"
        params = {
            "from": ORIGIN,
            "to": DESTINATION,
            "d": date_out,
            "r": date_in
        }
        
        print(f"🕵️ Intentando extraer ID de: {search_url} ({date_out}/{date_in})")
        
        try:
            resp = self.session.get(search_url, params=params, headers=self.headers)
            if resp.status_code != 200:
                print(f"❌ Error HTTP {resp.status_code}")
                return None

            html = resp.text
            
            # --- PATRONES DE BÚSQUEDA DEL ID ---
            
            # Patrón 1: ID en variable JS 'searchId' (común en SPAs)
            # Ej: window.__INITIAL_STATE__ = {"searchId": "0b99b6c..."}
            match = re.search(r'"searchId":"([a-f0-9]{32})"', html)
            if match:
                print(f"✅ ID encontrado (JSON): {match.group(1)}")
                return match.group(1)
            
            # Patrón 2: ID en la URL de alguna llamada API embebida
            # Ej: fetch("/api/v1/search/0b99b6c...")
            match = re.search(r'/flights/rpull/([a-f0-9]{32})', html)
            if match:
                 print(f"✅ ID encontrado (URL API): {match.group(1)}")
                 return match.group(1)

            # Patrón 3: ID suelto en algún script de configuración
            # A veces aparece como 'id': '...'
            match = re.search(r"'id'\s*:\s*'([a-f0-9]{32})'", html)
            if match:
                print(f"✅ ID encontrado (Script): {match.group(1)}")
                return match.group(1)

            print("⚠️ No se encontró ID en el HTML plano.")
            # Guardamos el HTML "crudo" para analizar por qué falló
            with open("turismocity_fail.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("   💾 Log guardado: turismocity_fail.html")
            return None

        except Exception as e:
            print(f"💥 Error extrayendo ID: {e}")
            return None

    def get_prices(self, search_id):
        """Consulta la API rpull con el ID obtenido."""
        if not search_id:
            return None
            
        print(f"📡 Consultando API para ID: {search_id}")
        url = f"https://api.turismocity.com/flights/rpull/{search_id}"
        # Pedimos versión final directo
        params = {"v": "final"} 
        
        try:
            api_headers = self.headers.copy()
            api_headers.update({
                'accept': 'application/json, text/plain, */*',
                'origin': 'https://www.turismocity.com.ar',
                'referer': 'https://www.turismocity.com.ar/'
            })
            
            resp = self.session.get(url, params=params, headers=api_headers)
            
            if resp.status_code == 200:
                data = resp.json()
                # A veces devuelve una lista [] vacía si no terminó
                bytes_len = len(str(data))
                print(f"✅ Datos recibidos: {bytes_len} bytes")
                
                # Intentar parsear precios básicos
                if isinstance(data, dict) and "flights" in data:
                     count = len(data["flights"])
                     print(f"   ✈️ Vuelos encontrados: {count}")
                     if count > 0:
                         best = min(data["flights"], key=lambda x: x.get("price", {}).get("totalAmount", float('inf')))
                         amount = best.get("price", {}).get("totalAmount")
                         print(f"   🏆 Mejor precio TurismoCity: ${amount}")
                elif isinstance(data, list):
                     print(f"   ⚠️ Respuesta es una lista (posiblemente vacía o parcial): {data}")
                
                return data

            elif resp.status_code == 404:
                print("❌ ID Expirado o Inválido (404)")
            else:
                 print(f"❌ Error API: {resp.status_code}")
                 
        except Exception as e:
            print(f"💥 Error API: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Iniciando prueba MANUAL de Turismocity Scraper...")
    scraper = TurismocityScraper()
    
    # ID MANUAL PROVISTO POR EL DIRECTOR
    MANUAL_ID = "0b99b6c71bd453ca05a868fb5b849b1d"
    
    print(f"🔑 Usando ID Manual: {MANUAL_ID}")
    data = scraper.get_prices(MANUAL_ID)
    
    if data:
        print("\n✅ EXTRACCIÓN EXITOSA. Analizando precios...")
        # Guardar muestra para referencia futura
        with open("turismocity_success.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    else:
        print("❌ El ID manual ha caducado o no funciona. Se requiere uno fresco.")
