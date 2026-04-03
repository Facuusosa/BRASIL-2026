#!/usr/bin/env python3
"""
Test de búsqueda por nombre en Yaguar
"""

from curl_cffi import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_search():
    print("🔍 Test búsqueda por nombre Yaguar")
    print("=" * 40)
    
    session = requests.Session()
    
    # Términos de búsqueda comunes
    terminos = ["aceite", "gaseosa", "arroz", "fideos", "coca cola"]
    
    for termino in terminos:
        print(f"\n🔍 Buscando: {termino}")
        
        # URL de búsqueda WooCommerce
        search_url = f"https://yaguar.com.ar/?s={urllib.parse.quote(termino)}&post_type=product"
        
        try:
            response = session.get(search_url, impersonate='safari15_3', timeout=15)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar productos
                productos = soup.select('div.product, li.type-product, article.product, .woocommerce-loop-product')
                print(f"  📦 Productos encontrados: {len(productos)}")
                
                if productos:
                    # Analizar primeros productos
                    for i, prod in enumerate(productos[:3]):
                        # Buscar nombre
                        nombre_elem = prod.select_one('h2, h3, .product-title, .woocommerce-loop-product__title')
                        nombre = nombre_elem.get_text().strip() if nombre_elem else 'Sin nombre'
                        
                        # Buscar precio
                        precio_elem = prod.select_one('.price, .amount, .woocommerce-Price-amount')
                        precio = precio_elem.get_text().strip() if precio_elem else 'Sin precio'
                        
                        # Buscar enlace
                        link_elem = prod.select_one('a')
                        link = link_elem.get('href') if link_elem else 'Sin link'
                        
                        print(f"    {i+1}. {nombre} - {precio}")
                        print(f"       Link: {link}")
                
                # Buscar mensaje de "no hay resultados"
                no_results = soup.select('.woocommerce-info, .woocommerce-no-products-found, [class*="no-results"]')
                if no_results:
                    print(f"  ❌ Mensaje: {no_results[0].get_text().strip()}")
                
                # Guardar si hay productos
                if len(productos) > 0:
                    filename = f"yaguar_search_{termino.replace(' ', '_')}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"  💾 Guardado en {filename}")
                    break  # Encontramos productos con búsqueda
                    
            else:
                print(f"  ❌ Error {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Excepción: {e}")
    
    return False

if __name__ == "__main__":
    test_search()
