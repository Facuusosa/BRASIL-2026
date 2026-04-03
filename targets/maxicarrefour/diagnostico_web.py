#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO WEB MAXICARREFOUR
Para entender qué está pasando con el scraper
"""

import requests
from bs4 import BeautifulSoup
import json
import time

def diagnosticar_maxicarrefour():
    print("🔍 DIAGNÓSTICO WEB MAXICARREFOUR")
    print("=" * 50)
    
    # Headers actualizados
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1'
    }
    
    # Cookies actualizadas
    cookies = {
        '_fbp': 'fb.2.1762720184774.210392897523026321.AQYBAQIA',
        'vtex-search-anonymous': 'e8f94bfdb91c4a03b5f440bb28df389a',
        'PHPSESSID': 'qir2kj35b0rknq9gng18oe2om0'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(cookies)
    
    # 1. Probar página principal
    print("\n1. 🔍 Probando página principal...")
    try:
        response = session.get("https://comerciante.carrefour.com.ar", timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar elementos clave
            search_input = soup.find('input', {'type': 'search'})
            search_form = soup.find('form')
            
            print(f"   ✅ Página cargada")
            print(f"   📝 Input de búsqueda: {'Sí' if search_input else 'No'}")
            print(f"   📝 Formulario: {'Sí' if search_form else 'No'}")
            
            # Guardar HTML para análisis
            with open('diagnostico_pagina_principal.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"   💾 HTML guardado: diagnostico_pagina_principal.html")
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Probar búsqueda por EAN
    print("\n2. 🔍 Probando búsqueda por EAN 7790895000997...")
    ean_prueba = "7790895000997"
    
    # Intentar diferentes URLs de búsqueda
    urls_busqueda = [
        f"https://comerciante.carrefour.com.ar/search/{ean_prueba}",
        f"https://comerciante.carrefour.com.ar/products?currentUrl=search/{ean_prueba}",
        f"https://comerciante.carrefour.com.ar/products?currentUrl=search/{ean_prueba}&page=1&filters=&orderBy=default&method=getSubCategory",
        f"https://comerciante.carrefour.com.ar/api/catalog_system/pub/products/search?ft={ean_prueba}",
        f"https://comerciante.carrefour.com.ar/api/catalog_system/pub/products/search?fq=sku:{ean_prueba}"
    ]
    
    for i, url in enumerate(urls_busqueda, 1):
        print(f"\n   2.{i} Probando URL: {url}")
        try:
            response = session.get(url, timeout=30)
            print(f"       Status: {response.status_code}")
            print(f"       Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"       Content-Length: {len(response.text)}")
            
            if response.status_code == 200:
                # Intentar parsear como JSON
                try:
                    data = response.json()
                    print(f"       ✅ Respuesta JSON con {len(data)} elementos")
                    
                    # Guardar JSON
                    with open(f'diagnostico_respuesta_{i}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"       💾 JSON guardado: diagnostico_respuesta_{i}.json")
                    
                except:
                    # Parsear como HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Buscar productos
                    items = soup.find_all('div', class_='item') or soup.find_all('[class*="product"]') or soup.find_all('[class*="shelf-item"]')
                    print(f"       ✅ HTML con {len(items)} productos")
                    
                    # Guardar HTML
                    with open(f'diagnostico_respuesta_{i}.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"       💾 HTML guardado: diagnostico_respuesta_{i}.html")
                    
                    # Mostrar primeros productos encontrados
                    if items:
                        for j, item in enumerate(items[:3]):
                            nombre_elem = item.find('span', class_='product-name') or item.find('h2') or item.find('h3') or item.find('[class*="name"]')
                            precio_elem = item.find('span', class_='product-price') or item.find('[class*="price"]')
                            
                            if nombre_elem:
                                nombre = nombre_elem.get_text().strip()
                                precio = precio_elem.get_text().strip() if precio_elem else 'N/A'
                                print(f"          📦 Producto {j+1}: {nombre[:50]}... - ${precio}")
            else:
                print(f"       ❌ Error HTTP {response.status_code}")
                
        except Exception as e:
            print(f"       ❌ Error: {e}")
        
        time.sleep(1)  # Delay entre peticiones
    
    print("\n🏁 DIAGNÓSTICO COMPLETADO")
    print("📂 Revisa los archivos generados para analizar la estructura")

if __name__ == "__main__":
    diagnosticar_maxicarrefour()
