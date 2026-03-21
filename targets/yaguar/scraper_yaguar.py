import os
import json
import re
import time
import sys
from bs4 import BeautifulSoup
from curl_cffi import requests

# Arreglo para salida en consola Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# --- CONFIGURACIÓN ---
URL_BASE = "https://yaguar.com.ar/"
OUTPUT_FILE = "output_yaguar.json"
DATA_DIR = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\data"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "es-ES,es;q=0.9",
    "referer": "https://yaguar.com.ar/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
}

# Cookies de la sesión activa de 'martin' (Parque Chacabuco)
COOKIES = {
    "wordpress_sec_yaguar2025v2": "martin|1774142258|wGtbHgH45rKFSkBHAY8oCijPI6sIjRANanwhW1Udl1u|baaab4d77e9809cfff8e83cca9d52ce7e297b515aac4af627af9f98f8d5bb32e",
    "wordpress_logged_in_yaguar2025v2": "martin|1774142258|wGtbHgH45rKFSkBHAY8oCijPI6sIjRANanwhW1Udl1u|1f99ec0d9a5e58f19174a13b74615d567e11bc45f9a947136d2f190e5a8ccccf"
}

# Categorías completas basadas en el filtro del sitio
CATEGORIES = [
    {"name": "Almacén", "slug": "almacen"},
    {"name": "Bebidas", "slug": "bebidas"},
    {"name": "Bodega", "slug": "bodega"},
    {"name": "Desayuno", "slug": "desayuno"},
    {"name": "Frescos", "slug": "frescos"},
    {"name": "Kiosco", "slug": "kiosco"},
    {"name": "Limpieza", "slug": "limpieza"},
    {"name": "Mascotas", "slug": "mascotas"},
    {"name": "Papeles", "slug": "papeles"},
    {"name": "Perfumería", "slug": "perfumeria"},
    {"name": "Bazar", "slug": "bazar"}
]

def clean_price(p):
    if not p: return 0
    c = re.sub(r'[^\d]', '', p) # Eliminar todo lo no numérico
    try: return float(c)
    except: return 0

def save_data(unique_products):
    res = list(unique_products.values())
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    if os.path.exists(DATA_DIR):
        sync_path = os.path.join(DATA_DIR, OUTPUT_FILE)
        with open(sync_path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)

def scrape(sector, slug, unique_products):
    url_base = f"{URL_BASE}categoria-producto/{slug}/"
    page = 1
    found_in_category = 0
    
    while True:
        url = url_base if page == 1 else f"{url_base}page/{page}/"
        print(f"   📄 Page {page}...", end=" ", flush=True)
        
        try:
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, impersonate="chrome110", timeout=30)
            
            if "login" in r.url.lower():
                print("REBOTE A LOGIN. Sesión expirada.")
                break

            if r.status_code != 200:
                print(f"ERROR {r.status_code}")
                break
                
            soup = BeautifulSoup(r.text, "html.parser")
            btns = soup.select("a.add_to_cart_button")
            
            if not btns:
                btns = soup.select(".elementor-add-to-cart a")
                if not btns:
                    print("Vacío")
                    break
            
            for b in btns:
                try:
                    sku = b.get("data-product_sku")
                    name_raw = b.get("aria-label", "")
                    match = re.search(r'“(.+?)”', name_raw)
                    nombre = match.group(1) if match else name_raw.replace("Añadir al carrito:", "").strip(" “ ”")

                    price = 0
                    curr = b
                    for _ in range(10):
                        curr = curr.parent
                        if not curr: break
                        p_el = curr.select_one(".amount, .woocommerce-Price-amount")
                        if p_el:
                            price = clean_price(p_el.get_text())
                            if price > 0: break
                    
                    img = ""
                    curr_img = b
                    for _ in range(10):
                        curr_img = curr_img.parent
                        if not curr_img: break
                        i_el = curr_img.select_one("img")
                        if i_el:
                            img = i_el.get("src") or i_el.get("data-src", "")
                            if img: break

                    if not sku: sku = f"ID-{hash(nombre)}"

                    if sku not in unique_products:
                        unique_products[sku] = {
                            "nombre": nombre, "precio": price, "sku": sku,
                            "sector": sector, "subcategoria": sector,
                            "imagen": img, "stock": True, "fuente": "Yaguar"
                        }
                        found_in_category += 1
                except: continue
            
            print(f"OK ({len(btns)} items)")
            
            if not soup.select_one("a.next.page-numbers") or page >= 250: # Subimos el límite para cubrir todo el catálogo
                break
            page += 1
            time.sleep(0.5)
            
        except Exception as e:
            print(f"CRITICAL: {e}")
            break
    return found_in_category

def main():
    print(f"🚀 Iniciando Scraper Yaguar (Sesión: MARTIN)")
    unique_products = {}
    for cat in CATEGORIES:
        print(f"\n🔍 Buscando en {cat['name']}...")
        nuevos = scrape(cat['name'], cat['slug'], unique_products)
        save_data(unique_products)
        print(f"💰 Acumulado Yaguar: {len(unique_products)} materiales")
    
    print(f"\n✅ Scraping Finalizado.")
    print(f"📊 Total General Yaguar: {len(unique_products)} materiales")

if __name__ == "__main__":
    main()
