import os
import json
import re
import requests
import time
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
# Carrefour Maxi (comerciante.carrefour.com.ar) es el formato mayorista
URL_BASE = "https://comerciante.carrefour.com.ar"
API_URL = "https://comerciante.carrefour.com.ar/products"
OUTPUT_FILE = "output_maxicarrefour.json"
DELAY = 1.0  # Delay entre categorías

HEADERS = {
    'accept': '*/*',
    'accept-language': 'es-ES,es;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'cookie': r"_fbp=fb.2.1762720184774.210392897523026321.AQYBAQIA; vtex-search-anonymous=e8f94bfdb91c4a03b5f440bb28df389a; _dyid=-9061242199398614599; PHPSESSID=qir2kj35b0rknq9gng18oe2om0; _dy_soct=1774061404!1594828.0'1598112.-11341218'1792788.-1'2288309.-1'2745823.-7686485'2992584.-8398287'3571772.0!ct4f7cas2dhmi95tjdxl8za7evhkfwxr~3563031.-1; dtm_token_sc=AQAHbKSKVCWLkwELGIGQAQBFAQABAQCba06DqgEBAJwPTb1w; __cf_bm=0y0CR58Lv9rMH3MaPbw60KRBjSvObauEW6OGvB7FX5A-1774111999-1.0.1.1-qnpVRnc1i74LBdvJWwEmSUtB7D1GzzZ.Zb5Nb4PA4Vg3EUGScuX2y2ZjJiBAEo7StdIf.eaTVCQmnDooEsgmJ2qdolPVTz7CF8SNFE2tAdU; cf_clearance=Q4Mat6RQBSOQJc38Z8crKI3KHDrDcDywgpGp1omsjes-1774112409-1.2.1.1-fcAIEUR.I1K3punOTYR4TsKvVdcb8FAYviIn83nWwV23RFRTTL29UGRs057k1mpXwdCQnIovJ.ewHg_pgSgZxH5I8i3_ChW.dwodlGKCgyfYkwp42wYivb.IBuwS2w2HIaGj0Ks7.FZ.MiRaPQRmMEacp2U4WUFmlve32Dkdh_nnUp0RqoS.qk52PZXoZCK6k7Zqp4FbrMCrMjYztwH76LKpTt0pBjg_g2RUAtC73r0",
    'priority': 'u=1, i',
    'referer': 'https://comerciante.carrefour.com.ar/sec/almac%C3%A9n',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
}

CATEGORIES = [
    {"name": "Almacén", "url_part": "sec/almacén"},
    {"name": "Bebidas", "url_part": "sec/bebidas"},
    {"name": "Frescos", "url_part": "sec/frescos"},
    {"name": "Limpieza", "url_part": "sec/limpieza"},
    {"name": "Perfumería", "url_part": "sec/perfumería"},
    {"name": "Mascotas", "url_part": "sec/mascotas"},
    {"name": "Congelados", "url_part": "sec/congelados"},
    {"name": "Lácteos", "url_part": "sec/lácteos"},
]

def clean_price(price_str):
    if not price_str or "private" in price_str: return 0.0
    # En la API el formato suele ser '4399.00' (con punto decimal)
    # Por seguridad quitamos cualquier carácter no numérico excepto el punto.
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try: return float(cleaned)
    except: return 0.0

def scrape_category(category_name, url_part, unique_products):
    new_found = 0
    page = 1
    items_per_page = 48 # Intentamos pedir una cantidad razonable por página
    
    while True:
        params = {
            "method": "productsList",
            "currentPage": page,
            "itemsPerPage": items_per_page,
            "currentUrl": url_part
        }
        
        try:
            r = requests.get(API_URL, headers=HEADERS, params=params, timeout=20)
            if r.status_code != 200:
                print(f"  [!] Error en Pag {page}: {r.status_code}")
                break
                
            html_content = r.text
            if not html_content.strip() or "No se encontraron productos" in html_content:
                break
                
            soup = BeautifulSoup(html_content, "html.parser")
            items = soup.select(".item_card")
            if not items:
                break
                
            for item in items:
                # Extraer datos de los atributos data- en el botón
                btn = item.select_one(".cart_button")
                if not btn: continue
                
                ean = btn.get("data-ean")
                if not ean: continue
                
                # Precio: Carrefour lo pone en data-price
                price_raw = btn.get("data-price", "0")
                precio = clean_price(price_raw)
                
                nombre = item.select_one(".item_card__description").get_text(strip=True).upper()
                img_elem = item.select_one("img.principal_img")
                img_url = img_elem.get("src") if img_elem else ""
                
                # Metadata adicional de categoría/subcategoría
                section = btn.get("data-section", category_name).capitalize()
                
                if ean not in unique_products:
                    unique_products[ean] = {
                        "nombre": nombre,
                        "precio": precio,
                        "sku": ean,
                        "sector": category_name,
                        "subcategoria": section,
                        "imagen": img_url,
                        "fuente": "MaxiCarrefour",
                        "stock": True
                    }
                    new_found += 1
            
            print(f"  Página {page} completada. +{new_found} nuevos ({len(unique_products)} totales en sesión)")
            page += 1
            time.sleep(0.3)
            
            # Control de seguridad para no entrar en bucles infinitos si fallara el escape
            if page > 150: break 
            
        except Exception as e:
            print(f"  [!] Error fatal en bucle: {e}")
            break
            
    return new_found

def save_data(unique_products):
    output_dir = os.path.dirname(os.path.abspath(__file__))
    final_output = os.path.join(output_dir, OUTPUT_FILE)
    result_list = list(unique_products.values())
    
    # Guardar localmente
    with open(final_output, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=2)
        
    # Sincronizar con el dashboard de Brújula de Precios
    dashboard_data_dir = "c:/Users/Facun/OneDrive/Escritorio/PROYECTOS PERSONALES/PRECIOS/BRUJULA-DE-PRECIOS/data"
    if os.path.isdir(dashboard_data_dir):
        sync_output = os.path.join(dashboard_data_dir, OUTPUT_FILE)
        with open(sync_output, "w", encoding="utf-8") as f:
            json.dump(result_list, f, ensure_ascii=False, indent=2)

def main():
    unique_products = {}
    print(f"🚀 INICIANDO SCRAPING MAXICARREFOUR")
    print(f"📍 Sucursal: Maxi Avellaneda (sesión activa)")
    
    for cat in CATEGORIES:
        print(f"\n🔎 Sector: {cat['name']}...")
        nuevos = scrape_category(cat['name'], cat['url_part'], unique_products)
        print(f"✅ Finalizado {cat['name']}. Total sesión: {len(unique_products)}")
        save_data(unique_products)
        time.sleep(DELAY)

    print(f"\n✨ SCRAPING FINALIZADO EXITOSAMENTE")
    print(f"📦 Total de productos extraídos de Carrefour: {len(unique_products)}")

if __name__ == "__main__":
    main()
