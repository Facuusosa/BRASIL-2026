#!/usr/bin/env python3
"""
Test de la página tienda de Yaguar
"""

from curl_cffi import requests
from bs4 import BeautifulSoup

def test_tienda():
    print("🔍 Test página tienda Yaguar")
    print("=" * 40)
    
    session = requests.Session()
    
    response = session.get('https://yaguar.com.ar/tienda/', impersonate='safari15_3', timeout=15)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar productos
        productos = soup.select('div.product, li.type-product, article.product, .woocommerce-loop-product')
        print(f'Productos encontrados: {len(productos)}')
        
        # Buscar grids de productos
        grids = soup.select('.products, .product-grid')
        print(f'Grids de productos: {len(grids)}')
        
        # Buscar cualquier contenido que parezca producto
        content_divs = soup.find_all('div', class_=True)
        product_divs = [div for div in content_divs if any('product' in str(cls).lower() for cls in div.get('class', []))]
        print(f'Divs con "product" en clase: {len(product_divs)}')
        
        # Buscar precios
        precios = soup.select('.price, .amount, [class*="price"]')
        print(f'Elementos de precio: {len(precios)}')
        
        # Mostrar primeros precios si existen
        for i, precio in enumerate(precios[:5]):
            print(f'  Precio {i+1}: {precio.get_text().strip()}')
        
        # Guardar HTML
        with open('yaguar_tienda.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print('HTML guardado en yaguar_tienda.html')
        
        # Buscar formulario de búsqueda
        search_forms = soup.select('form[role="search"], .search-form, [class*="search"]')
        print(f'Formularios de búsqueda: {len(search_forms)}')
        
        if search_forms:
            for i, form in enumerate(search_forms[:2]):
                inputs = form.select('input[type="search"], input[name="s"], input[placeholder*="buscar"]')
                print(f'  Form {i+1}: {len(inputs)} inputs de búsqueda')
        
        return len(productos) > 0
    else:
        print('Error cargando tienda')
        return False

if __name__ == "__main__":
    success = test_tienda()
    if success:
        print("\n✅ Tienda tiene productos")
    else:
        print("\n❌ Tienda sin productos visibles")
