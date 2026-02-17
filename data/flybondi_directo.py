
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def buscar_vuelos_selenium(origen, destino, fecha_ida, fecha_vuelta):
    print(f"🕵️ INICIANDO AGENTE DE CAMPO (Selenium Robusto)...")
    print(f"✈️ Misión: {origen}-{destino} | {fecha_ida} a {fecha_vuelta}")

    # Configuración Chrome Simplificada y Estable
    options = Options()
    # options.add_argument("--headless=new") # Desactivado para ver qué pasa
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    # Argumentos extra para estabilidad
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # User Agent genérico pero moderno
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # URL de Búsqueda
    search_url = f"https://flybondi.com/ar/search/results?adults=1&children=0&currency=ARS&departureDate={fecha_ida}&from={origen}&infants=0&returnDate={fecha_vuelta}&to={destino}"
    
    driver = None
    resultado = None
    
    try:
        # Inicializar Driver
        driver = webdriver.Chrome(options=options)
        
        print(f"🌍 Navegando a: {search_url}")
        driver.get(search_url)
        
        # Esperar a que cargue (Timeout generoso de 30s)
        # Buscamos algo que indique carga exitosa (header, precio, o el footer)
        print("⏳ Esperando renderizado de la página...")
        
        # Espera explicita inteligente
        try:
            WebDriverWait(driver, 30).until(
                lambda d: "flybondi" in d.page_source.lower()
            )
        except:
            print("⚠️ Timeout esperando carga básica. Continuando igual...")

        time.sleep(10) # Wait tactico para JS pesado

        # Extracción de Precios
        page_source = driver.page_source
        
        # Debug: Guardar HTML si no encontramos nada
        # with open("debug_page.html", "w", encoding="utf-8") as f:
        #    f.write(page_source)

        # Regex robusta para precios ARS
        # Busca: $ seguido de numeros, puntos y comas opcionales
        precios = re.findall(r'\$\s*([\d\.,]+)', page_source)
        
        if precios:
            # print(f"💰 Candidatos encontrados: {len(precios)}")
            precios_limpios = []
            for p in precios:
                try:
                    # Normalizar "123.456,00" -> 123456.00
                    # Normalizar "123,456" -> 123456
                    clean_p = p.replace('.', '').replace(',', '.')
                    # Si quedó algo tipo "123.456.789" (doble punto), fallará float, lo atrapamos
                    # Hack simple: flybondi usa 1.234
                    
                    val = float(clean_p)
                    
                    # Filtro de lógica de negocio
                    if 20000 < val < 5000000: 
                        precios_limpios.append(val)
                except:
                    pass
            
            if precios_limpios:
                min_price = min(precios_limpios)
                print(f"✅ ¡ÉXITO! Precio detectado: ${min_price:,.2f}")
                
                resultado = {
                    "origen": origen,
                    "destino": destino,
                    "fecha_ida": fecha_ida,
                    "fecha_vuelta": fecha_vuelta,
                    "precio_minimo": min_price,
                    "moneda": "ARS",
                    "timestamp": time.time()
                }
                
                # Guardar resultado
                filename = f"flybondi_directo_{fecha_ida}.json"
                with open(filename, "w") as f:
                    json.dump(resultado, f, indent=2)
            else:
                print("⚠️ Se encontraron números pero ninguno pasó el filtro de precio lógico.")
        else:
            print("❌ No se encontraron símbolos de precio ($) en el HTML.")

    except Exception as e:
        print(f"💥 Error en Selenium: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                print("🔌 Browser cerrado correctamente.")
            except:
                pass
        
    return resultado

if __name__ == "__main__":
    # Configuración de Misión
    year = "2025"
    ida = f"{year}-03-10"
    vuelta = f"{year}-03-20"
    
    max_retries = 3
    for i in range(max_retries):
        print(f"\n🔁 INTENTO {i+1}/{max_retries}")
        res = buscar_vuelos_selenium("BUE", "FLN", ida, vuelta)
        if res:
            print("🏆 ¡VICTORIA! Datos extraídos.")
            break
        print("⏳ Reintentando en 5s...")
        time.sleep(5)
    else:
        print("💀 Se agotaron los intentos.")
