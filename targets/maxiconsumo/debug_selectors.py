#!/usr/bin/env python3
"""
Debug de selectores HTML para búsqueda por EAN
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scraper_pro import MaxiconsumoProScraper
from bs4 import BeautifulSoup

def debug_selectors():
    print("🔍 Debug de selectores para EAN 7790895000997")
    print("=" * 60)
    
    scraper = MaxiconsumoProScraper()
    cookies = scraper._get_session_cookies()
    
    search_url = f"{scraper.base_url}/{scraper.sucursal}/catalogsearch/result/?q=7790895000997"
    
    response = scraper.session.get(
        search_url, 
        impersonate=scraper.impersonate,
        headers=scraper.headers, 
        cookies=cookies, 
        timeout=30
    )
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"📄 Título página: {soup.title.string if soup.title else 'Sin título'}")
        
        # Buscar diferentes selectores de productos
        selectores_prueba = [
            'li.item.product.product-item',
            'li.item',
            'div.product-item-info',
            'div.product-item-details',
            '[class*="product"]',
            '[class*="item"]',
            'ol.products li',
            'div.products-grid li',
            '.product-item'
        ]
        
        for selector in selectores_prueba:
            items = soup.select(selector)
            print(f"🔍 Selector '{selector}': {len(items)} elementos")
            
            if items and len(items) > 0:
                # Analizar primer item
                first_item = items[0]
                
                # Buscar nombre
                nombre_selectors = [
                    'strong.product.name.product-item-name',
                    'a.product-item-link',
                    'h2.product-name',
                    '.product-item-link',
                    'h2',
                    'a',
                    '.product-name',
                    '[class*="name"]'
                ]
                
                print(f"  📝 Nombres encontrados:")
                for ns in nombre_selectors:
                    nombre_elem = first_item.select_one(ns)
                    if nombre_elem:
                        print(f"    ✅ {ns}: {nombre_elem.get_text().strip()[:50]}...")
                
                # Buscar precio
                precio_selectors = [
                    'span.price-wrapper.price-including-tax',
                    'span.price',
                    'div.price-box',
                    '.price',
                    '[class*="price"]',
                    '.special-price',
                    '[data-price-type]'
                ]
                
                print(f"  💰 Precios encontrados:")
                for ps in precio_selectors:
                    precio_elem = first_item.select_one(ps)
                    if precio_elem:
                        print(f"    ✅ {ps}: {precio_elem.get_text().strip()}")
                
                # Buscar SKU/EAN
                sku_selectors = [
                    'span.product-sku',
                    'div.sku',
                    'span.sku',
                    '[class*="sku"]',
                    '[class*="ean"]',
                    '.product-sku'
                ]
                
                print(f"  🏷️ SKU/EAN encontrados:")
                for ss in sku_selectors:
                    sku_elem = first_item.select_one(ss)
                    if sku_elem:
                        print(f"    ✅ {ss}: {sku_elem.get_text().strip()}")
                
                print(f"  🖼️ Imagen: {first_item.find('img').get('src', 'No encontrada') if first_item.find('img') else 'No encontrada'}")
                break
        
        # Guardar HTML para análisis manual
        with open('debug_ean_search.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 HTML guardado en 'debug_ean_search.html' para análisis manual")
        
    else:
        print(f"❌ Error HTTP {response.status_code}")

if __name__ == "__main__":
    debug_selectors()
