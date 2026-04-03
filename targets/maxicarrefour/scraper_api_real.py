#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER API REAL MAXICARREFOUR
Basado en el análisis del JavaScript fetchFunctions.js
"""

import os
import json
import re
import time
import requests
from datetime import datetime
import pandas as pd

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

class MaxiCarrefourAPIScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://comerciante.carrefour.com.ar"
        self.api_url = f"{self.base_url}/products"
        
        # Headers actualizados basados en el análisis
        self.headers = {
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
        self.cookies = {
            '_fbp': 'fb.2.1762720184774.210392897523026321.AQYBAQIA',
            'vtex-search-anonymous': 'e8f94bfdb91c4a03b5f440bb28df389a',
            'PHPSESSID': 'qir2kj35b0rknq9gng18oe2om0'
        }
        
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)
        
        # Cargar Listado Maestro
        self.listado_maestro = self.cargar_listado_maestro()
        
    def cargar_listado_maestro(self):
        """Cargar el Listado Maestro"""
        try:
            maestro_file = os.path.join(RAW_DIR, "Listado Maestro 09-03.xlsx")
            df = pd.read_excel(maestro_file)
            print(f"📋 Listado Maestro cargado: {len(df)} productos")
            return df
        except Exception as e:
            print(f"❌ Error cargando Listado Maestro: {e}")
            return pd.DataFrame()
    
    def limpiar_precio(self, precio_str):
        """Limpiar y convertir precio a número"""
        if not precio_str:
            return 0.0
        cleaned = re.sub(r'[^\d,.]', '', str(precio_str))
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except:
            return 0.0
    
    def buscar_por_ean_api(self, ean):
        """Buscar producto por EAN usando la API real"""
        try:
            # URL de la API real basada en fetchFunctions.js
            params = {
                'currentUrl': f'search/{ean}',
                'filters': '',
                'orderBy': 'default',
                'currentPage': 1,
                'itemsPerPage': 12,
                'method': 'productsList'
            }
            
            print(f"  🔍 Buscando EAN {ean} via API...")
            
            response = self.session.get(self.api_url, params=params, timeout=30)
            
            print(f"    Status: {response.status_code}")
            print(f"    Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"    Content-Length: {len(response.text)}")
            
            if response.status_code == 200:
                # Intentar parsear como JSON
                try:
                    data = response.json()
                    print(f"    ✅ Respuesta JSON con {len(data)} elementos")
                    return data
                except:
                    # Parsear como HTML
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Buscar productos usando selectores del HTML
                    items = soup.find_all('div', class_='item_card') or soup.find_all('[class*="product"]') or soup.find_all('[class*="shelf-item"]')
                    
                    print(f"    ✅ HTML con {len(items)} productos")
                    
                    productos = []
                    for item in items:
                        try:
                            nombre_elem = item.find('h2') or item.find('h3') or item.find('[class*="name"]') or item.find('[class*="title"]')
                            precio_elem = item.find('span', class_=re.compile(r'price|Price')) or item.find('[class*="price"]')
                            sku_elem = item.find('[class*="sku"]') or item.find('[class*="ean"]')
                            imagen_elem = item.find('img')
                            
                            if nombre_elem:
                                nombre = nombre_elem.get_text().strip()
                                precio = self.limpiar_precio(precio_elem.get_text()) if precio_elem else 0.0
                                sku = sku_elem.get_text().strip() if sku_elem else ean
                                imagen = imagen_elem.get('src', '') if imagen_elem else ''
                                
                                if precio > 0:
                                    productos.append({
                                        'nombre': nombre,
                                        'precio': precio,
                                        'sku': sku,
                                        'ean_buscado': ean,
                                        'imagen': imagen,
                                        'sector': 'Por determinar',
                                        'subcategoria': 'Por determinar',
                                        'fuente': 'MaxiCarrefour-API',
                                        'stock': True
                                    })
                        except Exception as e:
                            continue
                    
                    return productos
            else:
                print(f"    ❌ Error HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"    ❌ Error buscando EAN {ean}: {e}")
            return []
    
    def probar_api_con_ean_conocido(self):
        """Probar la API con un EAN conocido"""
        print("🧪 PRUEBA API CON EAN CONOCIDO (Coca-Cola)")
        print("=" * 50)
        
        ean_prueba = "7790895000997"
        resultado = self.buscar_por_ean_api(ean_prueba)
        
        if resultado:
            print(f"\n✅ API FUNCIONA!")
            print(f"📦 Se encontraron {len(resultado)} productos:")
            for i, p in enumerate(resultado[:3]):
                print(f"  {i+1}. {p.get('nombre', 'Sin nombre')}")
                print(f"     Precio: ${p.get('precio', 0)}")
                print(f"     SKU: {p.get('sku', 'N/A')}")
                print(f"     Imagen: {p.get('imagen', 'N/A')[:50]}...")
                print()
        else:
            print(f"\n❌ API NO FUNCIONA")
            print(f"   EAN: {ean_prueba}")
            print(f"   Revisa los headers o cookies")
        
        return resultado
    
    def scraear_desde_listado_maestro_api(self, limite=50):
        """Scraear productos usando API y EANs del Listado Maestro"""
        print(f"📋 Scrapeando desde Listado Maestro usando API (límite: {limite})...")
        
        productos = []
        
        if self.listado_maestro.empty:
            print("❌ Listado Maestro no disponible")
            return productos
        
        # Tomar productos del maestro
        productos_maestro = self.listado_maestro.head(limite)
        
        for idx, row in productos_maestro.iterrows():
            try:
                ean = str(row['Código EAN']).strip()
                nombre_maestro = str(row['Texto breve material']).strip()
                sector_maestro = str(row['SECTOR']).strip()
                
                if len(ean) >= 10:  # EAN válido
                    print(f"  🔍 Buscando EAN {ean} ({nombre_maestro[:50]}...)")
                    
                    resultado = self.buscar_por_ean_api(ean)
                    
                    if resultado:
                        # Asignar sector y subcategoría del maestro
                        for p in resultado:
                            p['sector'] = sector_maestro
                            p['subcategoria'] = str(row.get('CATEGORIAS', ''))
                            p['nombre_maestro'] = nombre_maestro
                        
                        productos.extend(resultado)
                        print(f"    ✅ Encontrados: {len(resultado)} productos")
                    else:
                        print(f"    ❌ No encontrado: {ean}")
                
                # Delay entre búsquedas para no ser bloqueado
                time.sleep(2)
                
            except Exception as e:
                print(f"    ❌ Error procesando fila {idx}: {e}")
                continue
        
        print(f"📦 Se encontraron {len(productos)} productos de {limite} buscados")
        return productos

if __name__ == "__main__":
    scraper = MaxiCarrefourAPIScraper()
    
    # Probar API primero
    resultado_prueba = scraper.probar_api_con_ean_conocido()
    
    if resultado_prueba:
        print("\n" + "="*60)
        print("🚀 API FUNCIONA - PROBANDO CON LISTADO MAESTRO")
        print("="*60)
        
        # Probar con 50 productos de Bebidas
        productos_bebidas = scraper.listado_maestro[scraper.listado_maestro['SECTOR'] == 'Bebidas'].head(50)
        productos_encontrados = scraper.scraear_desde_listado_maestro_api(limite=len(productos_bebidas))
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"  📦 Total productos encontrados: {len(productos_encontrados)}")
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(os.path.dirname(__file__), f"output_api_maxicarrefour_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(productos_encontrados, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 Resultados guardados: {output_file}")
    else:
        print("\n❌ API NO FUNCIONA - REVISAR CONFIGURACIÓN")
