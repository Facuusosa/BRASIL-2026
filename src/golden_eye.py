
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# Intentamos importar undetected_chromedriver, si no, usamos standard
try:
    import undetected_chromedriver as uc
    # USE_UC = True  <-- Desactivado por inestabilidad
    USE_UC = False
except ImportError:
    USE_UC = False

def get_flybondi_session():
    print("🕵️ INICIANDO GOLDEN EYE (Session Harvester)...")
    
    # Configurar Chrome
    if USE_UC:
        print("✅ Usando Undetected Chrome Driver (Modo Sigilo Activado)")
        options = uc.ChromeOptions()
    else:
        print("⚠️ Usando Selenium Standard (Puede ser detectado por Cloudflare)")
        options = Options()
        # Habilitar logging de performance (CDP)
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # Argumentos anti-detección básicos
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

    # Opciones comunes
    # options.add_argument("--headless=new") # DESACTIVAR HEADLESS para asegurar carga de recursos y red
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        if USE_UC:
            driver = uc.Chrome(options=options)
        else:
            driver = webdriver.Chrome(options=options)

        # 1. Navegar a una búsqueda real para disparar la API
        print("🌍 Navegando a RESULTADOS DE BÚSQUEDA para interceptar API...")
        # URL que dispara peticiones
        search_target = "https://flybondi.com/ar/search/results?adults=1&children=0&currency=ARS&departureDate=2026-03-10&from=BUE&infants=0&returnDate=2026-03-20&to=FLN"
        driver.get(search_target)
        
        # 2. Esperar a que cargue y dispare peticiones
        print("⏳ Esperando 20 segundos para captura de tráfico...")
        time.sleep(20)
        
        # 3. Procesar Logs de Performance
        print("🕵️ Analizando tráfico de red...")
        logs = driver.get_log('performance')
        
        graphql_headers = None
        
        import json
        for entry in logs:
            try:
                message = json.loads(entry['message'])['message']
                if message['method'] == 'Network.requestWillBeSent':
                    request = message['params']['request']
                    url = request['url']
                    if "graphql" in url or "search" in url: # Buscar llamadas clave
                        if request['method'] == 'POST':
                            print(f"🎯 Petición POST detectada: {url}")
                            # Guardar headers
                            graphql_headers = request['headers']
                            post_data = request.get('postData')
                            
                            # Validar que sea la que buscamos
                            if "graphql" in url:
                                print("🔥 ¡HITO! Headers GraphQL capturados.")
                                break
            except Exception:
                pass
        
        # 4. Guardar Cookies (siempre útil)
        cookies = driver.get_cookies()
        session_cookies = {c['name']: c['value'] for c in cookies}
        
        # 5. Guardar Todo
        output_data = {
            "cookies": session_cookies,
            "user_agent": driver.execute_script("return navigator.userAgent;"),
            "headers": graphql_headers
        }
        
        with open("flybondi_cookies.json", "w") as f: # Guardamos en el mismo archivo para simplificar
            json.dump(output_data, f, indent=2)
            
        print("✅ ÉXITO: Credenciales complejas guardadas.")
        if graphql_headers:
            print("   🛠️ Headers capturados:")
            for k, v in graphql_headers.items():
                if "auth" in k.lower() or "token" in k.lower() or "x-" in k.lower():
                    print(f"      {k}: {v[:20]}...")
        else:
            print("⚠️ ADVERTENCIA: No se capturaron headers GraphQL específicos.")
        
        return True

    except Exception as e:
        print(f"💥 Error crítico: {e}")
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = get_flybondi_session()
    if not success:
        print("💀 Falló la obtención de sesión.")
        exit(1)
