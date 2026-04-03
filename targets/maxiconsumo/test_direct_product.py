#!/usr/bin/env python3
"""
Test accediendo directamente a la página del producto
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scraper_pro import MaxiconsumoProScraper
from bs4 import BeautifulSoup
import re

def test_direct_product():
    print("🔍 Test acceso directo a página de producto")
    print("=" * 50)
    
    scraper = MaxiconsumoProScraper()
    cookies = scraper._get_session_cookies()
    
    # URL directa del producto Coca Cola
    product_url = "https://maxiconsumo.com/sucursal_burzaco/gaseosa-coca-cola-2-25-lt-3394.html"
    
    response = scraper.session.get(
        product_url, 
        impersonate=scraper.impersonate,
        headers=scraper.headers, 
        cookies=cookies, 
        timeout=30
    )
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"📄 Título página: {soup.title.string if soup.title else 'Sin título'}")
        
        # Buscar el precio en la página del producto
        precio_selectors = [
            '[data-price-type="finalPrice"]',
            '.price-final_price .price',
            '.price-box .price',
            '[data-role="priceBox"]',
            '.special-price .price',
            '.old-price .price',
            '.price-wrapper .price'
        ]
        
        for selector in precio_selectors:
            precio_elem = soup.select_one(selector)
            if precio_elem:
                # Buscar atributo data-price
                if precio_elem.has_attr('data-price'):
                    precio = precio_elem['data-price']
                    print(f"✅ Precio encontrado en {selector}: ${precio}")
                else:
                    precio_text = precio_elem.get_text().strip()
                    print(f"✅ Precio encontrado en {selector}: {precio_text}")
                
                # Buscar el precio en el texto del elemento
                precio_numbers = re.findall(r'[\d.,]+', precio_text if 'precio_text' in locals() else '')
                if precio_numbers:
                    print(f"  📊 Números extraídos: {precio_numbers}")
        
        # Guardar HTML para análisis
        with open('debug_product_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 HTML guardado en 'debug_product_page.html'")
        
    else:
        print(f"❌ Error HTTP {response.status_code}")

if __name__ == "__main__":
    test_direct_product()
