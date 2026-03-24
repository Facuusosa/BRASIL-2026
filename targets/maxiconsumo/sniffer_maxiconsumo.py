import os
import json
import re
import requests
import time
from bs4 import BeautifulSoup
from collections import Counter

# --- CONFIGURACIÓN ---
URL_BASE_SITE = "https://maxiconsumo.com"
LINKS_FILE = "C:/tmp/final_nav_links.txt"
OUTPUT_FILE = "output_maxiconsumo.json"
DELAY = 1.0 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

SECTOR_MAP = {
    "almacen": "Almacén", "bebidas": "Bebidas", "frescos": "Frescos",
    "limpieza": "Limpieza", "perfumeria": "Perfumería", "mascotas": "Mascotas",
    "hogar-y-bazar": "Hogar y Bazar", "electro": "Electro"
}

def clean_price(price_str):
    if not price_str: return 0
    cleaned = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
    try: return float(cleaned)
    except: return 0

def get_links_to_scrape():
    raw_categories = []
    if not os.path.exists(LINKS_FILE): return []
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if " → " not in line: continue
            name, url = line.strip().split(" → ")
            exclude = ["solo-por-hoy", "ofertas", "customer", "checkout", "contact"]
            if any(x in url for x in exclude): continue
            
            sector = "Otros"
            for key, val in SECTOR_MAP.items():
                if f"/{key}" in url:
                    sector = val
                    break
            if sector == "Otros": continue

            # Extraer subcategoría del path de la URL
            parts = url.replace("https://maxiconsumo.com/sucursal_burzaco/", "").split("/")
            # Tomamos el último antes del .html si es posible
            if len(parts) >= 1:
                sc_raw = parts[-1].replace(".html", "").replace("-", " ").title()
                # Si el último es muy genérico, subimos un nivel
                if sc_raw.lower() in ["index", "view"] and len(parts) > 1:
                    sc_raw = parts[-2].replace("-", " ").title()
                
                # Mapeo manual de urgencia para Yerbas
                if "Yerba" in sc_raw or "Mate" in sc_raw or "Infusiones" in sc_raw:
                    subcategoria = "Yerba Mate"
                elif "Aceite" in sc_raw:
                    subcategoria = "Aceites"
                else:
                    subcategoria = sc_raw
            else:
                subcategoria = sector
            raw_categories.append({"nombre": name, "url": url, "sector": sector, "subcat": subcategoria})
    
    leaf_categories = []
    paths = [c['url'].split("sucursal_burzaco/")[-1].replace(".html", "") for c in raw_categories]
    for i, cat in enumerate(raw_categories):
        current_path = paths[i]
        is_parent = any(other_path.startswith(current_path + "/") for other_path in paths)
        if not is_parent:
            leaf_categories.append(cat)
    return leaf_categories

def save_data(unique_products):
    output_dir = os.path.dirname(os.path.abspath(__file__))
    final_output = os.path.join(output_dir, OUTPUT_FILE)
    result_list = list(unique_products.values())
    
    with open(final_output, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=2)
        
    next_data_dir = os.path.join(output_dir, "..", "..", "BRUJULA-DE-PRECIOS", "data")
    if os.path.isdir(next_data_dir):
        sync_output = os.path.join(next_data_dir, OUTPUT_FILE)
        with open(sync_output, "w", encoding="utf-8") as f:
            json.dump(result_list, f, ensure_ascii=False, indent=2)

def scrape_page_with_pagination(base_url, sector, subcat, unique_products):
    nuevos_cat = 0
    for pg in range(1, 101): 
        url = f"{base_url}?p={pg}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200: break
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select(".product-item")
            if not items: break
            
            for item in items:
                name_elem = item.select_one(".product-item-name a")
                if not name_elem: continue
                nombre = name_elem.get_text(strip=True)
                # FIX 4: Capturar precio unitario real (evitar bulto cerrado)
                # Maxiconsumo suele tener IDs que empiezan con 'price-including-tax-' para la unidad
                # y 'highest-price-including-tax-' para el bulto.
                price_elem = item.select_one('span[id^="price-including-tax-"] .price')
                
                # Fallback por si el selector anterior falla
                if not price_elem:
                    price_elem = item.select_one(".price")
                
                precio_raw = price_elem.get_text(strip=True) if price_elem else ""
                precio = clean_price(precio_raw)
                
                item_text = item.get_text(separator=' ', strip=True)
                sku_match = re.search(r'SKU\s+(\d+)', item_text, re.IGNORECASE)
                sku = sku_match.group(1) if sku_match else ""
                if not sku: continue
                
                img_elem = item.select_one("img.product-image-photo")
                img_url = img_elem.get("src") if img_elem else ""
                stock = bool(re.search(r'En stock', item_text, re.IGNORECASE))
                
                # Ignorar si no hay precio real o no hay stock (según preferencia de limpieza)
                if precio <= 0 or not stock:
                    continue
                
                if sku not in unique_products:
                    unique_products[sku] = {
                        "nombre": nombre, "precio": precio, "sku": sku,
                        "sector": sector, "subcategoria": subcat,
                        "imagen": img_url, "stock": stock,
                        "fuente": "Maxiconsumo"
                    }
                    nuevos_cat += 1
            time.sleep(0.2)
        except: break
    return nuevos_cat

def main():
    categories = get_links_to_scrape()
    unique_products = {}
    total_cats = len(categories)
    
    print(f"🚀 Iniciando barrido incremental sobre {total_cats} categorías.")
    
    for i, cat in enumerate(categories, 1):
        print(f"[{i:3}/{total_cats}] {cat['sector']} - {cat['nombre']}...", end=" ", flush=True)
        nuevos = scrape_page_with_pagination(cat['url'], cat['sector'], cat['subcat'], unique_products)
        print(f"+{nuevos} nuevos (Total: {len(unique_products):,})")
        
        # Guardar cada 5 categorías para que el frontend vea progreso
        if i % 5 == 0:
            save_data(unique_products)
            print("💾 Snapshot guardado.")
        
        time.sleep(DELAY)

    save_data(unique_products)
    print(f"\n✅ Scraping finalizado. Total Global Maxi: {len(unique_products)} materiales.")

if __name__ == "__main__":
    main()
