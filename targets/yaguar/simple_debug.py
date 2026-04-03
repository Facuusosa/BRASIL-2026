#!/usr/bin/env python3
"""
Debug simple de Yaguar - ver qué devuelve el sitio
"""

from curl_cffi import requests
from bs4 import BeautifulSoup

def simple_debug():
    print("🔍 Debug simple de Yaguar")
    print("=" * 40)
    
    session = requests.Session()
    
    # Test 1: Home
    print("\n📄 Test Home:")
    try:
        response = session.get('https://yaguar.com.ar', impersonate='safari15_3', timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Content-Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar menú de categorías
            menu_items = soup.select('nav a, .menu a, [class*="menu"] a')
            print(f"📋 Items de menú: {len(menu_items)}")
            
            for item in menu_items[:10]:
                text = item.get_text().strip()
                href = item.get('href', '')
                if text and href:
                    print(f"  • {text}: {href}")
            
            # Guardar HTML
            with open('yaguar_home.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Guardado en yaguar_home.html")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Buscar página de productos
    print("\n🔍 Buscando página de productos:")
    
    urls_comunes = [
        'https://yaguar.com.ar/shop/',
        'https://yaguar.com.ar/tienda/',
        'https://yaguar.com.ar/productos/',
        'https://yaguar.com.ar/product-category/bebidas/',
        'https://yaguar.com.ar/bebidas/'
    ]
    
    for url in urls_comunes:
        try:
            print(f"\n🔍 Probando: {url}")
            response = session.get(url, impersonate='safari15_3', timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                # Buscar productos
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Selectores comunes de WooCommerce
                productos = soup.select('div.product, li.type-product, article.product')
                print(f"  📦 Productos encontrados: {len(productos)}")
                
                if productos:
                    # Analizar primer producto
                    p = productos[0]
                    nombre = p.select_one('h2, h3, .product-title').get_text().strip() if p.select_one('h2, h3, .product-title') else 'Sin nombre'
                    precio = p.select_one('.price, .amount').get_text().strip() if p.select_one('.price, .amount') else 'Sin precio'
                    print(f"    📝 Ejemplo: {nombre} - {precio}")
                
                # Guardar si tiene productos
                if len(productos) > 0:
                    filename = f"yaguar_{url.split('/')[-2]}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"    💾 Guardado en {filename}")
                    break  # Encontramos una página con productos
            else:
                print(f"  ❌ Error {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Excepción: {e}")

if __name__ == "__main__":
    simple_debug()
