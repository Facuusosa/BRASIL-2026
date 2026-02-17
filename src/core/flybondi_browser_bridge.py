from playwright.sync_api import sync_playwright
import json
import logging
import sys
import time

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - BRIDGE - %(message)s')

def fetch_search_data_via_browser(departure_date, return_date, origin="BUE", destination="FLN"):
    """
    Estrategia "Sniffing Pasivo":
    Navega a la URL de búsqueda y ESCUCHA la respuesta de la API GraphQL legítima.
    No inyecta tráfico, solo lo captura.
    """
    logging.info(f"🕸️ [SNIFFER] Iniciando interceptación para {departure_date} - {return_date}...")
    
    captured_data = []

    def handle_response(response):
        try:
            # Filtrar solo respuestas de GraphQL
            if "graphql" in response.url and response.request.method == "POST":
                # Verificar si es la query de vuelos (por tamaño o contenido)
                if response.status == 200:
                    try:
                        json_data = response.json()
                        # Chequear si tiene estructura de vuelos
                        if "data" in json_data and "viewer" in json_data["data"]:
                            logging.info("🎯 ¡CAPTURA CONFIRMADA! Payload GraphQL interceptado.")
                            captured_data.append(json_data)
                    except:
                        pass
        except Exception as e:
            pass

    with sync_playwright() as p:
        # Lanzar navegador VISIBLE para que el Humano ayude con Captchas
        browser = p.chromium.launch(
            headless=False,  # <--- MODO CYBORG ACTIVADO
            args=[
                '--no-sandbox', 
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--start-maximized'
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Ocultar webdriver
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()
        
        # Activar la escucha de red
        page.on("response", handle_response)
        
        # Construir URL de búsqueda REAL
        search_url = f"https://flybondi.com/ar/search/results?adults=2&currency=ARS&from={origin}&to={destination}&date={departure_date}&return_date={return_date}&children=0&infants=0&roundtrip=true"
        
        try:
            logging.info(f"🌍 Navegando: {search_url}")
            logging.info("👤 ACCIÓN REQUERIDA: Si aparece un Captcha/Cloudflare, resuélvelo manualmente.")
            page.goto(search_url, timeout=90000, wait_until="domcontentloaded")
            
            # Esperar a que aparezcan resultados o se capture el JSON
            # Damos 60s (TIEMPO DE SOBRA para humanos)
            logging.info("⏳ Esperando tráfico de red (60s)...")
            start_time = time.time()
            while time.time() - start_time < 60:
                if captured_data:
                    break
                page.wait_for_timeout(1000) # Wait 1s
            
            if captured_data:
                logging.info(" Misión de intercepción exitosa.")
                return captured_data[0] # Devolvemos el primer payload válido
            else:
                logging.warning("⚠️ Tiempo agotado. No se capturó tráfico GraphQL relevante.")
                # Screenshot de debug
                page.screenshot(path="debug_sniffing_fail.png")
                
        except Exception as e:
            logging.error(f"❌ Error en el navegador: {e}")
        finally:
            browser.close()
            
    return None

if __name__ == "__main__":
    # Prueba rápida
    res = fetch_search_data_via_browser("2026-03-08", "2026-03-15")
    if res:
        print(json.dumps(res, indent=2))
        # Guardar evidencia
        with open("browser_bridge_result.json", "w") as f:
            json.dump(res, f, indent=2)
    else:
        print("FALLÓ EL PUENTE")
