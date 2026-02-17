from playwright.sync_api import sync_playwright
import time
import os
import json
import logging

def get_fresh_flybondi_session(headless=True):
    """
    Inicia un navegador real, navega a Flybondi y extrae la cookie de sesión.
    """
    logging.info("🕵️‍♂️ Iniciando Session Refresher (Playwright)...")
    
    session_cookie = None
    
    with sync_playwright() as p:
        # Lanzamos navegador (Chrome/Chromium)
        # Usamos args para parecer lo más real posible
        browser = p.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        
        try:
            logging.info("🌍 Navegando a flybondi.com/ar/search/results...")
            # Vamos a una URL de búsqueda para forzar la generación de cookies de sesión de búsqueda
            page.goto("https://flybondi.com/ar/search/results?adults=1&currency=ARS&from=BUE&to=FLN&date=2026-03-10&children=0&infants=0", timeout=60000)
            
            logging.info("⏳ Esperando carga y resolución de desafíos (10s)...")
            # Esperar a que cargue algo clave o simplemente esperar a que Cloudflare pase
            time.sleep(10)
            
            # Intentar scrollear para simular humano
            page.mouse.wheel(0, 500)
            time.sleep(2)
            
            # Extraer cookies
            cookies = context.cookies()
            for cookie in cookies:
                if "FBSession" in cookie['name']: # El nombre suele contener FBSession
                    logging.info(f"✅ Cookie encontrada: {cookie['name']}")
                    session_cookie = cookie['value']
                    # Podríamos buscar específicamente 'FBSessionX-ar-ibe' pero a veces varía
            
            if not session_cookie:
                logging.warning("⚠️ No se encontró cookie con 'FBSession' en el nombre. Buscando 'ar-ibe'...")
                for cookie in cookies:
                     if "ar-ibe" in cookie['name'] or "flybondi" in cookie['domain']:
                         # Fallback: Agarramos la más larga o la que parezca de sesión
                         pass

            # Guardar todas las cookies por si acaso en un JSON
            with open("flybondi_cookies.json", "w") as f:
                json.dump(cookies, f, indent=2)
            logging.info("💾 Cookies guardadas en flybondi_cookies.json")

        except Exception as e:
            logging.error(f"❌ Error en Playwright: {e}")
        finally:
            browser.close()
            
    return session_cookie

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cookie = get_fresh_flybondi_session(headless=True) # Headless False para ver qué pasa si falla
    if cookie:
        print(f"\n🎯 SESSION COOKIE: {cookie}")
    else:
        print("\n❌ No se pudo obtener la cookie.")
