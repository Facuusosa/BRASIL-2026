import os
import json
import re
from bs4 import BeautifulSoup
from curl_cffi import requests

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
}

# Cookies del usuario
COOKIES = {
    "wordpress_sec_yaguar2025v2": "martin|1774142258|wGtbHgH45rKFSkBHAY8oCijPI6sIjRANanwhW1Udl1u|baaab4d77e9809cfff8e83cca9d52ce7e297b515aac4af627af9f98f8d5bb32e",
    "wordpress_logged_in_yaguar2025v2": "martin|1774142258|wGtbHgH45rKFSkBHAY8oCijPI6sIjRANanwhW1Udl1u|1f99ec0d9a5e58f19174a13b74615d567e11bc45f9a947136d2f190e5a8ccccf"
}

def clean_price(price_str):
    if not price_str: return 0
    cleaned = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
    try: return float(cleaned)
    except: return 0

def test():
    url = "https://yaguar.com.ar/categoria-producto/almacen/"
    r = requests.get(url, headers=HEADERS, cookies=COOKIES, impersonate="chrome110")
    print(f"Status: {r.status_code}")
    
    soup = BeautifulSoup(r.text, "html.parser")
    # Buscamos por botones de compra que suelen tener el SKU y el nombre en aria-label
    buttons = soup.select("a.add_to_cart_button")
    print(f"Encontrados {len(buttons)} botones.")
    
    for btn in buttons[:5]:
        sku = btn.get("data-product_sku", "N/A")
        label = btn.get("aria-label", "")
        # Extraer nombre: "Añadir al carrito: “NOMBRE”" -> "NOMBRE"
        nombre = re.search(r'“(.+?)”', label)
        nombre = nombre.group(1) if nombre else label
        
        # El precio suele estar en el mismo contenedor padre
        parent = btn.find_parent(".e-con") 
        if not parent: parent = btn.find_parent(".product")
        
        # Si Elementor usa contenedores, buscamos el precio en el bloque de arriba
        # O en todo el parent.
        price_elem = parent.select_one(".woocommerce-Price-amount.amount") if parent else None
        precio = clean_price(price_elem.get_text(strip=True)) if price_elem else 0
        
        print(f"SKU: {sku} | Precio: {precio} | Nombre: {nombre}")

if __name__ == "__main__":
    test()
