import os
import json
import re
import requests
import time
import sys
import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

# --- CONFIGURACIÓN ---
URL_BASE_SITE = "https://maxiconsumo.com"
SUCURSAL = "sucursal_burzaco" # Podés cambiar a sucursal_moreno si preferís
EXCEL_PATH = "data/raw/Listado Maestro 09-03.xlsx"
OUTPUT_FILE = "output_maxiconsumo.json"
DELAY = 1.0  # Un poco más lento para ser indetectable con cookies reales

# PEGAR ACÁ TU COOKIE (La parseamos automáticamente)
RAW_COOKIE = 'mage-banners-cache-storage=%7B%7D; customer_type=categorizado; form_key=TyKFVmlygVALWiHB; mage-cache-storage=%7B%7D; mage-cache-storage-section-invalidation=%7B%7D; mage-messages=; recently_viewed_product=%7B%7D; recently_viewed_product_previous=%7B%7D; recently_compared_product=%7B%7D; recently_viewed_product_previous=%7B%7D; product_data_storage=%7B%7D; private_content_version=c2af6ad8f19036f7db55f1a63f528168; form_key=TyKFVmlygVALWiHB; mage-cache-sessid=true; section_data_ids=%7B%22customer%22%3A1774473269%2C%22compare-products%22%3A1774473269%2C%22last-ordered-items%22%3A1774473269%2C%22cart%22%3A1774473269%2C%22directory-data%22%3A1774473269%2C%22captcha%22%3A1774473269%2C%22wishlist%22%3A1774473269%2C%22instant-purchase%22%3A1774473269%2C%22loggedAsCustomer%22%3A1774473269%2C%22multiplewishlist%22%3A1774473269%2C%22persistent%22%3A1774473269%2C%22review%22%3A1774473269%2C%22recently_viewed_product%22%3A1774473269%2C%22recently_compared_product%22%3A1774473269%2C%22product_data_storage%22%3A1774473269%2C%22paypal-billing-agreement%22%3A1774473269%7D'

def get_cookies_dict():
    return {c.split('=')[0].strip(): c.split('=')[1].strip() for c in RAW_COOKIE.split(';') if '=' in c}

def clean_price(price_str):
    if not price_str: return 0
    cleaned = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
    try: return float(cleaned)
    except: return 0

def extract_ean(item_soup):
    text = item_soup.get_text()
    match = re.search(r'779\d{10}', text)
    return match.group(0) if match else None

def save_data(unique_products, filename=OUTPUT_FILE):
    output_dir = os.path.dirname(os.path.abspath(__file__))
    final_output = os.path.join(output_dir, filename)
    result_list = list(unique_products.values())
    
    with open(final_output, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=2)
        
    next_data_dir = os.path.join(output_dir, "..", "..", "BRUJULA-DE-PRECIOS", "data")
    if os.path.isdir(next_data_dir):
        sync_output = os.path.join(next_data_dir, filename)
        with open(sync_output, "w", encoding="utf-8") as f:
            json.dump(result_list, f, ensure_ascii=False, indent=2)

def scrape_sku_deep(sku, unique_products, cookies):
    # Probamos con el SKU original (con ceros) y limpio
    variants = [sku, sku.lstrip('0')]
    for s in variants:
        url = f"{URL_BASE_SITE}/{SUCURSAL}/catalogsearch/result/?q={s}"
        try:
            r = curl_requests.get(url, impersonate="chrome110", timeout=15, cookies=cookies)
            if r.status_code != 200: continue
            
            soup = BeautifulSoup(r.text, "html.parser")
            item = soup.select_one(".product-item")
            if not item: continue
            
            nombre_elem = item.select_one(".product-item-name a")
            if not nombre_elem: continue
            nombre = nombre_elem.get_text(strip=True)
            
            price_elem = item.select_one('span[id^="price-including-tax-"] .price') or item.select_one(".price")
            precio = clean_price(price_elem.get_text(strip=True)) if price_elem else 0
            
            ean = extract_ean(item)
            img_url = ""
            img_tag = item.select_one("img.product-image-photo")
            if img_tag:
                img_url = img_tag.get('src') or img_tag.get('data-src') or ""

            if sku not in unique_products:
                unique_products[sku] = {
                    "nombre": nombre, "precio": precio, "sku": sku, "ean": ean,
                    "sector": "Almacén", "subcategoria": "Maestro",
                    "imagen": img_url, "fuente": "Maxiconsumo"
                }
                return True
        except Exception:
            continue
    return False

def main():
    use_maestro = "--maestro" in sys.argv
    unique_products = {}
    cookies = get_cookies_dict()

    from concurrent.futures import ThreadPoolExecutor
    
    if use_maestro:
        print(f"🚀 TURBO ACTIVADO: 5 Trabajadores en paralelo - {SUCURSAL}")
        df_maestro = pd.read_excel(EXCEL_PATH, sheet_name="Sheet1")
        df_maxi = pd.read_excel(EXCEL_PATH, sheet_name="MAXICONSUMO")
        
        df_maestro.columns = [str(c).strip().lower() for c in df_maestro.columns]
        df_maxi.columns = [str(c).strip().lower() for c in df_maxi.columns]
        
        col_ean = next((c for c in df_maestro.columns if 'barras' in c or 'ean' in c), None)
        col_sku_m = next((c for c in df_maxi.columns if 'sku' in c), None)
        col_ean_m = next((c for c in df_maxi.columns if 'barras' in c or 'ean' in c), None)

        eans = df_maestro[col_ean].dropna().unique().tolist()
        maxi_map = df_maxi.set_index(col_ean_m)[col_sku_m].to_dict() if col_ean_m else {}
        
        print(f"📦 Procesando {len(eans)} referencias. ¡Mirá la pantalla! 👇")

        def task(ean):
            try:
                ean_str = str(int(float(ean)))
                if not ean_str or len(ean_str) < 8: return
                sku_val = maxi_map.get(ean)
                sku_ref = str(sku_val).split('.')[0] if not pd.isna(sku_val) else ""
                
                if scrape_sku_deep(ean_str, unique_products, cookies):
                    print(f" ✅ EAN {ean_str} CAPTURADO")
                elif sku_ref and sku_ref != "nan" and scrape_sku_deep(sku_ref, unique_products, cookies):
                    print(f" ✅ SKU {sku_ref} CAPTURADO (extra)")
                else:
                    pass # Evitamos llenar la consola si no hay match
            except: pass

        with ThreadPoolExecutor(max_workers=5) as executor:
            for i, _ in enumerate(executor.map(task, eans), 1):
                if i % 100 == 0:
                    save_data(unique_products, "output_maxiconsumo.json")
                    print(f"--- 💾 Snapshot guardado: {len(unique_products)} total ---")
                    
        save_data(unique_products, "output_maxiconsumo.json")
        print(f"\n✅ Proceso finalizado. Total Global Maxi: {len(unique_products)} materiales.")
    else:
        print("🚶 MODO BARRIDO POR PASILLOS REQUERIDO")

if __name__ == "__main__":
    main()
