#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER MAXICONSUMO - VERSIÓN PRO
Para uso con acceso a internet real
"""

import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from curl_cffi import requests as curl_requests
import hashlib

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

class MaxiconsumoProScraper:
    def __init__(self):
        # Usar curl_cffi con impersonate safari15_3 (funciona!)
        self.session = curl_requests.Session()
        self.impersonate = "safari15_3"  # 🔥 CLAVE: Esto evita el bloqueo
        
        # Headers actualizados para Safari
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15'
        }
        self.session.headers.update(self.headers)
        
        # Cookies se obtendrán dinámicamente
        self.cookies = {}
        
        self.base_url = "https://maxiconsumo.com"
        self.sucursal = "sucursal_burzaco"
        
        # Cargar Listado Maestro
        self.listado_maestro = self.cargar_listado_maestro()
        
        # Categorías principales basadas en el Listado Maestro
        self.categorias = [
            {"nombre": "Almacén", "terminos": ["aceite", "arroz", "fideos", "harina", "yerba", "azucar", "galletitas", "dulces", "conservas", "sal", "condimentos"]},
            {"nombre": "Bebidas", "terminos": ["gaseosa", "agua", "jugo", "vino", "cerveza", "fernet", "aperitivo"]},
            {"nombre": "Lácteos", "terminos": ["leche", "queso", "yogur", "manteca", "crema", "postre"]},
            {"nombre": "Limpieza", "terminos": ["detergente", "lavandina", "limpiador", "papel", "jabon", "perfume"]},
            {"nombre": "Cuidado Personal", "terminos": ["shampoo", "desodorante", "crema", "jabon", "dental"]},
            {"nombre": "Carnicería", "terminos": ["carne", "pollo", "milanesa", "hamburguesa"]},
            {"nombre": "Congelados", "terminos": ["helado", "pizza", "empanada", "papas"]},
            {"nombre": "Quesos", "terminos": ["queso", "crema", "manteca", "dulce"]},
            {"nombre": "Fiambrería", "terminos": ["jamón", "queso", "salame", "longaniza"]},
            {"nombre": "Verdulería", "terminos": ["fruta", "verdura", "lechuga", "tomate"]},
            {"nombre": "Bazar", "terminos": ["vaso", "plato", "cuchillo", "bolsa", "film"]},
            {"nombre": "Bebés", "terminos": ["pañal", "toallita", "mamadera", "formula"]},
            {"nombre": "Mascotas", "terminos": ["alimento", "perro", "gato", "balanceado"]}
        ]
    
    def _get_session_cookies(self):
        """Obtener cookies dinámicamente si no existen"""
        if not self.cookies:
            try:
                response = self.session.get(
                    self.base_url,
                    impersonate=self.impersonate,
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    self.cookies = dict(response.cookies)
                    print(f"🍪 Cookies obtenidas: {list(self.cookies.keys())}")
                    
                    # Extraer form_key del HTML
                    import re
                    form_key_match = re.search(r'"form_key":"([^"]+)"', response.text)
                    if form_key_match:
                        self.cookies['form_key'] = form_key_match.group(1)
                        print(f"🔑 form_key extraído: {form_key_match.group(1)}")
                        
            except Exception as e:
                print(f"❌ Error obteniendo cookies: {e}")
                
        return self.cookies
    
    def cargar_listado_maestro(self):
        """Cargar el Listado Maestro"""
        try:
            df = pd.read_excel(os.path.join(RAW_DIR, "Listado Maestro 09-03.xlsx"))
            print(f"✅ Listado Maestro cargado: {len(df)} productos")
            return df
        except Exception as e:
            print(f"❌ Error cargando Listado Maestro: {e}")
            return pd.DataFrame()
    
    def limpiar_precio(self, precio_str):
        """Limpiar y convertir precio a número"""
        if not precio_str:
            return 0.0
        
        cleaned = re.sub(r'[^\d,.]', '', str(precio_str))
        
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except:
            return 0.0
    
    def buscar_por_ean(self, ean):
        """Buscar producto por EAN"""
        try:
            # Asegurar cookies actualizadas
            cookies = self._get_session_cookies()
            
            search_url = f"{self.base_url}/{self.sucursal}/catalogsearch/result/?q={ean}"
            
            response = self.session.get(
                search_url, 
                impersonate=self.impersonate,
                headers=self.headers, 
                cookies=cookies, 
                timeout=30
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar productos usando selectores específicos
                items = soup.find_all('li', class_='item product product-item')
                
                if not items:
                    items = soup.find_all('li', class_='item')
                
                for item in items:
                    try:
                        # Extraer nombre
                        nombre_elem = (item.find('strong', class_='product name product-item-name') or
                                     item.find('a', class_='product-item-link') or
                                     item.find('h2', class_='product-name'))
                        
                        # Extraer precio
                        precio_elem = (item.find('span', class_='price-wrapper price-including-tax') or
                                     item.find('span', class_='price') or
                                     item.find('div', class_='price-box') or
                                     item.find('[data-price-type="finalPrice"]'))
                        
                        # Extraer precio del atributo data-price si existe
                        if precio_elem and precio_elem.has_attr('data-price'):
                            precio_text = precio_elem['data-price']
                        elif precio_elem:
                            precio_text = precio_elem.get_text()
                        else:
                            precio_text = "0"
                        
                        # Extraer SKU
                        sku_elem = (item.find('span', class_='product-sku') or
                                  item.find('div', class_='sku') or 
                                  item.find('span', class_='sku'))
                        
                        # Extraer imagen
                        imagen_elem = item.find('img')
                        
                        if nombre_elem and precio_text != "0":
                            nombre = nombre_elem.get_text().strip()
                            precio = self.limpiar_precio(precio_text)
                            sku = sku_elem.get_text().strip() if sku_elem else ""
                            imagen = imagen_elem.get('src', '') if imagen_elem else ""
                            
                            if precio > 0:
                                return {
                                    'nombre': nombre,
                                    'precio': precio,
                                    'sku': sku,
                                    'ean_buscado': ean,
                                    'imagen': imagen,
                                    'fuente': 'Maxiconsumo',
                                    'stock': True,
                                    'fecha_scraping': datetime.now().isoformat()
                                }
                    
                    except Exception as e:
                        continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error buscando EAN {ean}: {e}")
            return None
    
    def buscar_por_nombre(self, nombre, sector=""):
        """Buscar producto por nombre"""
        try:
            # Asegurar cookies actualizadas
            cookies = self._get_session_cookies()
            
            # Limpiar nombre para búsqueda
            nombre_limpio = re.sub(r'[^\w\s]', '', nombre).strip()
            palabras = nombre_limpio.split()[:3]  # Primeras 3 palabras
            termino_busqueda = ' '.join(palabras)
            
            search_url = f"{self.base_url}/{self.sucursal}/catalogsearch/result/?q={termino_busqueda}"
            
            response = self.session.get(
                search_url, 
                impersonate=self.impersonate,
                headers=self.headers, 
                cookies=cookies, 
                timeout=30
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                items = soup.find_all('li', class_='item product product-item')
                
                if not items:
                    items = soup.find_all('li', class_='item')
                
                for item in items:
                    try:
                        nombre_elem = (item.find('strong', class_='product name product-item-name') or
                                     item.find('a', class_='product-item-link') or
                                     item.find('h2', class_='product-name'))
                        
                        precio_elem = (item.find('span', class_='price-wrapper price-including-tax') or
                                     item.find('span', class_='price') or
                                     item.find('div', class_='price-box') or
                                     item.find('[data-price-type="finalPrice"]'))
                        
                        # Extraer precio del atributo data-price si existe
                        if precio_elem and precio_elem.has_attr('data-price'):
                            precio_text = precio_elem['data-price']
                        elif precio_elem:
                            precio_text = precio_elem.get_text()
                        else:
                            precio_text = "0"
                        
                        if nombre_elem and precio_text != "0":
                            nombre_encontrado = nombre_elem.get_text().strip()
                            precio = self.limpiar_precio(precio_text)
                            
                            if precio > 0:
                                return {
                                    'nombre': nombre_encontrado,
                                    'precio': precio,
                                    'sector': sector,
                                    'imagen': '',
                                    'fuente': 'Maxiconsumo',
                                    'stock': True,
                                    'nombre_original': nombre,
                                    'termino_busqueda': termino_busqueda
                                }
                    
                    except Exception as e:
                        continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error buscando nombre {nombre}: {e}")
            return None
    
    def scraear_por_categorias(self):
        """Scraear por categorías principales"""
        print("\n📂 Scrapeando por categorías...")
        
        productos = []
        
        # Asegurar cookies actualizadas
        cookies = self._get_session_cookies()
        
        for categoria in self.categorias:
            print(f"  📂 {categoria['nombre']}")
            
            for termino in categoria['terminos']:
                try:
                    search_url = f"{self.base_url}/{self.sucursal}/catalogsearch/result/?q={termino}"
                    
                    response = self.session.get(
                        search_url, 
                        impersonate=self.impersonate,
                        headers=self.headers, 
                        cookies=cookies, 
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        items = soup.find_all('li', class_='item product product-item')
                        
                        if not items:
                            items = soup.find_all('li', class_='item')
                        
                        for item in items[:10]:  # Limitar a 10 por término
                            try:
                                nombre_elem = (item.find('strong', class_='product name product-item-name') or
                                             item.find('a', class_='product-item-link') or
                                             item.find('h2', class_='product-name'))
                                
                                precio_elem = (item.find('span', class_='price-wrapper price-including-tax') or
                                             item.find('span', class_='price') or
                                             item.find('div', class_='price-box') or
                                             item.find('[data-price-type="finalPrice"]'))
                                
                                # Extraer precio del atributo data-price si existe
                                if precio_elem and precio_elem.has_attr('data-price'):
                                    precio_text = precio_elem['data-price']
                                elif precio_elem:
                                    precio_text = precio_elem.get_text()
                                else:
                                    precio_text = "0"
                                
                                if nombre_elem and precio_text != "0":
                                    nombre = nombre_elem.get_text().strip()
                                    precio = self.limpiar_precio(precio_text)
                                    
                                    if precio > 0:
                                        productos.append({
                                            'nombre': nombre,
                                            'precio': precio,
                                            'sector': categoria['nombre'],
                                            'subcategoria': termino,
                                            'imagen': '',
                                            'fuente': 'Maxiconsumo',
                                            'stock': True,
                                            'termino_busqueda': termino
                                        })
                            except:
                                continue
                    
                    time.sleep(1.5)  # Delay entre búsquedas
                    
                except Exception as e:
                    print(f"    ❌ Error con término {termino}: {e}")
                    continue
        
        return productos
    
    def scraear_desde_listado_maestro(self, limite=500):
        """Scraear usando EANs del Listado Maestro"""
        print(f"\n📋 Scrapeando desde Listado Maestro (límite: {limite})...")
        
        if self.listado_maestro.empty:
            print("❌ Listado Maestro no disponible")
            return []
        
        productos = []
        
        # Tomar productos con EAN
        productos_con_ean = self.listado_maestro[self.listado_maestro['Código EAN'].notna()]
        
        # Limitar la cantidad
        muestra = productos_con_ean.head(limite)
        
        for idx, row in muestra.iterrows():
            try:
                ean = str(row['Código EAN']).strip()
                nombre = str(row['Texto breve material']).strip()
                sector = str(row['SECTOR']).strip()
                
                if len(ean) >= 10:  # EAN válido
                    resultado = self.buscar_por_ean(ean)
                    
                    if resultado:
                        resultado['sector'] = sector
                        resultado['subcategoria'] = str(row.get('CATEGORIAS', ''))
                        productos.append(resultado)
                        print(f"  ✅ EAN {ean}: {resultado['nombre']}")
                    else:
                        # Si no encuentra por EAN, intentar por nombre
                        resultado = self.buscar_por_nombre(nombre, sector)
                        if resultado:
                            productos.append(resultado)
                            print(f"  🔍 Nombre {nombre}: {resultado['nombre']}")
                
                time.sleep(2)  # Delay importante para no ser bloqueado
                
            except Exception as e:
                continue
        
        return productos
    
    def scraear_completo(self):
        """Ejecutar scraping completo con acceso Pro"""
        print("🚀 Iniciando Scraper Maxiconsumo PRO")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        todos_los_productos = []
        
        # Estrategia 1: Por categorías
        productos_categorias = self.scraear_por_categorias()
        todos_los_productos.extend(productos_categorias)
        
        # Estrategia 2: Desde Listado Maestro (limitado para prueba)
        productos_maestro = self.scraear_desde_listado_maestro(limite=300)
        todos_los_productos.extend(productos_maestro)
        
        # Eliminar duplicados
        productos_unicos = {}
        for prod in todos_los_productos:
            # Usar EAN si está disponible, sino hash del nombre
            key = prod.get('ean_buscado', '') or prod.get('sku', '') or hashlib.md5(prod['nombre'].encode()).hexdigest()
            
            if key not in productos_unicos or prod['precio'] < productos_unicos[key]['precio']:
                productos_unicos[key] = prod
        
        productos_finales = list(productos_unicos.values())
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(os.path.dirname(__file__), f"output_maxiconsumo_pro_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(productos_finales, f, ensure_ascii=False, indent=2)
        
        # Sincronizar con BRUJULA-DE-PRECIOS
        sync_file = os.path.join(BASE_DIR, "BRUJULA-DE-PRECIOS", "data", "output_maxiconsumo.json")
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(productos_finales, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scrapeo PRO completado:")
        print(f"  📦 Total productos únicos: {len(productos_finales)}")
        print(f"  📂 Por categorías: {len(productos_categorias)}")
        print(f"  📋 Desde Listado Maestro: {len(productos_maestro)}")
        print(f"  💾 Archivo guardado: {output_file}")
        print(f"  🔄 Sincronizado con BRUJULA-DE-PRECIOS")
        
        # Estadísticas por sector
        print(f"\n📊 Productos por sector:")
        sectores_count = {}
        for prod in productos_finales:
            sector = prod['sector']
            sectores_count[sector] = sectores_count.get(sector, 0) + 1
        
        for sector, count in sorted(sectores_count.items()):
            print(f"  📁 {sector}: {count} productos")
        
        return productos_finales

if __name__ == "__main__":
    scraper = MaxiconsumoProScraper()
    scraper.scraear_completo()
