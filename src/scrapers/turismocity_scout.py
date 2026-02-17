import asyncio
from curl_cffi import requests
from datetime import datetime
import json
import sys

# Configuración básica
ORIGIN = "BUE"
DESTINATION = "FLN"
DATE_OUT = "2026-03-08"
DATE_IN = "2026-03-15"

def scout_turismocity():
    """
    Intento de exploración inicial a Turismocity para obtener precios de referencia.
    Simula una búsqueda desde un navegador Chrome.
    """
    print(f"🕵️ SCOUT TURISMOCITY: Iniciando reconocimiento {ORIGIN}-{DESTINATION} ({DATE_OUT} / {DATE_IN})...")

    # URL de búsqueda (reverse-engineered)
    # Turismocity suele usar una estructura de API interna o renderizado SSR.
    # Probamos primero el endpoint que autocompleta o inicia la búsqueda.
    
    # URL Típica de búsqueda web: https://www.turismocity.com.ar/vuelos-baratos-a-FLN-Florianopolis-desde-BUE-Buenos_Aires?d=2026-03-08&r=2026-03-15
    
    url = "https://www.turismocity.com.ar/api/w/flight_search"
    # Nota: Es probable que este endpoint requiera payload específico.
    # Vamos a intentar primero acceder a la home para obtener cookies de sesión.

    session = requests.Session(impersonate="chrome124")
    
    try:
        # 1. Visitar Home para 'calentar' la sesión (cookies, headers)
        print("   1. Estableciendo contacto con Home (cookies)...")
        resp_home = session.get("https://www.turismocity.com.ar/")
        if resp_home.status_code != 200:
            print(f"   ❌ Fallo al acceder a Home: {resp_home.status_code}")
            return
        print("   ✅ Contacto establecido.")

        # 2. Intentar query simulada (esto requerirá ingeniería inversa más profunda si falla)
        # Turismocity usa un payload complejo. Por ahora, hacemos un GET a la ruta de búsqueda
        # para ver si el HTML nos trae un 'initialState' o JSON embebido (técnica común).
        
        search_url = f"https://www.turismocity.com.ar/vuelos-baratos-a-{DESTINATION}-Florianopolis-desde-{ORIGIN}-Buenos_Aires"
        params = {
            "from": ORIGIN,
            "to": DESTINATION,
            "d": DATE_OUT,
            "r": DATE_IN
        }
        
        print(f"   2. Solicitando página de resultados: {search_url} ...")
        resp_search = session.get(search_url, params=params)
        
        if resp_search.status_code == 200:
            html = resp_search.text
            print(f"   ✅ Respuesta recibida ({len(html)} bytes). Analizando...")
            
            # Busqueda heurística de precios en el HTML (muy básico, para validar acceso)
            # Buscamos patrones como "$ 1.234.567" o "price":1234567
            if "recaptcha" in html.lower() or "cloudflare" in html.lower():
                print("   ⚠️ DETECTADO: Captcha/Cloudflare challenge.")
            elif "precio" in html.lower():
                print("   ✅ Posibles precios detectados en el HTML.")
                
                # Guardar HTML para inspección (Nivel 2 de Autonomía: Inspección)
                with open("turismocity_scout.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("   💾 HTML guardado en 'turismocity_scout.html' para análisis forense.")
                
            else:
                print("   ⚠️ No se detectaron patrones de precio obvios. Posible renderizado JS (Client Side).")
        else:
            print(f"   ❌ Error en búsqueda HTTP: {resp_search.status_code}")

    except Exception as e:
        print(f"   ❌ EXCEPCIÓN CRÍTICA: {e}")

if __name__ == "__main__":
    scout_turismocity()
