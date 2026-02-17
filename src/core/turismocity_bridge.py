from playwright.sync_api import sync_playwright
import time
import json
import logging

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - TURISMO-BRIDGE - %(message)s')

def fetch_turismocity_data(departure_date, return_date):
    """
    Navega a Turismocity y extrae precios usando interceptación de tráfico (Sniffing).
    Bypass total de Flybondi WAF al usar un intermediario.
    """
    logging.info(f"🕵️Iniciando Operación 'Ricochet' en Turismocity: {departure_date} al {return_date}")
    
    # URL de Búsqueda (Formato 2026)
    # Turismocity suele usar formato: /vuelos-baratos-a-DESTINO-desde-ORIGEN?d=YYYY-MM-DD&r=YYYY-MM-DD
    url = f"https://www.turismocity.com.ar/vuelos-baratos-a-Florianopolis-desde-Buenos_Aires-FLN-BUE?d={departure_date}&r={return_date}"
    
    captured_prices = []

    def handle_response(response):
        try:
            # Interceptamos llamadas a la API de Turismocity
            # Suelen ser /api/v1/flights o similar. Buscamos respuestas grandes JSON.
            if "api" in response.url and "json" in response.headers.get("content-type", ""):
                 if response.status == 200:
                    try:
                        data = response.json()
                        # Verificar si tiene estructura de vuelos
                        # Turismocity suele devolver "status": "success", "flights": [...]
                        # O a veces bloques de "items"
                        content_str = str(data)[:200]
                        
                        if "flights" in data or "items" in data or "fares" in data:
                            logging.info(f"🎯 Payload interceptado ({len(content_str)} bytes)...")
                            captured_prices.append(data)
                    except:
                        pass
        except:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, # Modo Visible para que el Usuario vea la magia
            args=['--start-maximized']
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # Activar sniffer
        page.on("response", handle_response)
        
        try:
            logging.info(f"🌍 Navegando a: {url}")
            page.goto(url, timeout=60000)
            
            logging.info("⏳ Esperando carga de resultados (30s)...")
            # Scroll para activar lazy loading si hace falta
            for _ in range(5):
                time.sleep(2)
                page.mouse.wheel(0, 500)
            
            # Tiempo extra para asegurar que lleguen todas las ofertas
            time.sleep(10)
            
            if captured_prices:
                logging.info(f"✅ Se capturaron {len(captured_prices)} paquetes de datos.")
                
                # Guardar evidencia
                with open("turismocity_dump.json", "w", encoding="utf-8") as f:
                    json.dump(captured_prices, f, indent=2, ensure_ascii=False)
                logging.info("💾 Datos guardados en turismocity_dump.json")
                return captured_prices
            else:
                logging.warning("⚠️ No se interceptaron datos de vuelo obvios.")
                
        except Exception as e:
            logging.error(f"❌ Error en Ricochet: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    # Prueba Manual
    fetch_turismocity_data("2026-03-08", "2026-03-15")
