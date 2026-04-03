#!/usr/bin/env python3
"""
Debug profundo de Yaguar - estructura y selectores
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scraper_pro import YaguarProScraper
from bs4 import BeautifulSoup
import re

def debug_yaguar():
    print("🔍 Debug profundo de Yaguar")
    print("=" * 50)
    
    scraper = YaguarProScraper()
    cookies = scraper._get_session_cookies()
    
    # Test 1: Página principal
    print("\n📄 Test 1: Página principal")
    response = scraper.session.get(
        scraper.base_url, 
        impersonate=scraper.impersonate,
        headers=scraper.headers, 
        cookies=cookies, 
        timeout=30
    )
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✅ Página principal cargada: {len(response.text)} bytes")
        
        # Buscar enlaces a categorías
        enlaces_categoria = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(term in href.lower() for term in ['category', 'categoria', 'shop', 'almacen', 'bebidas']):
                enlaces_categoria.append({
                    'texto': link.get_text().strip(),
                    'href': href
                })
        
        print(f"🔗 Enlaces a categorías encontrados: {len(enlaces_categoria)}")
        for enlace in enlaces_categoria[:10]:
            print(f"  📂 {enlace['texto']}: {enlace['href']}")
        
        # Guardar HTML para análisis
        with open('debug_yaguar_home.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"💾 HTML guardado en 'debug_yaguar_home.html'")
    
    # Test 2: Probar URLs de categorías directamente
    print("\n📂 Test 2: URLs de categorías")
    urls_test = [
        "https://yaguar.com.ar/product-category/bebidas/",
        "https://yaguar.com.ar/product-category/almacen/",
        "https://yaguar.com.ar/bebidas/",
        "https://yaguar.com.ar/almacen/",
        "https://yaguar.com.ar/shop/",
        "https://yaguar.com.ar/tienda/"
    ]
    
    for url in urls_test:
        try:
            print(f"\n🔍 Probando: {url}")
            response = scraper.session.get(
                url, 
                impersonate=scraper.impersonate,
                headers=scraper.headers, 
                cookies=cookies, 
                timeout=15
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar productos
                productos_selectores = [
                    'div.product',
                    'li.type-product',
                    'div.woocommerce-loop-product',
                    'article.product',
                    '[class*="product"]'
                ]
                
                for selector in productos_selectores:
                    productos = soup.select(selector)
                    if productos:
                        print(f"  ✅ {len(productos)} productos con selector '{selector}'")
                        
                        # Analizar primer producto
                        if productos:
                            primer_producto = productos[0]
                            
                            # Buscar nombre
                            nombre_selectors = [
                                '.woocommerce-loop-product__title',
                                'h2',
                                'h3',
                                '.product-title',
                                '[class*="title"]'
                            ]
                            
                            for ns in nombre_selectors:
                                nombre_elem = primer_producto.select_one(ns)
                                if nombre_elem:
                                    print(f"    📝 Nombre: {nombre_elem.get_text().strip()[:50]}")
                                    break
                            
                            # Buscar precio
                            precio_selectors = [
                                '.price',
                                '.amount',
                                '[class*="price"]',
                                'span.woocommerce-Price-amount'
                            ]
                            
                            for ps in precio_selectores:
                                precio_elem = primer_producto.select_one(ps)
                                if precio_elem:
                                    print(f"    💰 Precio: {precio_elem.get_text().strip()}")
                                    break
                            
                            break
                
                # Guardar HTML de categoría exitosa
                filename = f"debug_yaguar_{url.split('/')[-2]}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"    💾 HTML guardado en '{filename}'")
                
            else:
                print(f"  ❌ Error {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Excepción: {e}")

if __name__ == "__main__":
    debug_yaguar()
