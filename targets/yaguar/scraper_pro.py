#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER YAGUAR - VERSIÓN PRO
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

class YaguarProScraper:
    def __init__(self):
        # Usar curl_cffi con impersonate safari15_3 (funciona!)
        self.session = curl_requests.Session()
        self.impersonate = "safari15_3"  # 🔥 CLAVE: Esto evita el bloqueo
        
        # Headers actualizados para Safari
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
            'referer': 'https://yaguar.com.ar/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15'
        }
        self.session.headers.update(self.headers)
        
        # Cookies se obtendrán dinámicamente
        self.cookies = {}
        
        self.base_url = "https://yaguar.com.ar"
        
        # Cargar Listado Maestro
        self.listado_maestro = self.cargar_listado_maestro()
        
        # Categorías Yaguar basadas en análisis y Listado Maestro
        self.categorias = [
            {"slug": "almacen", "sector": "Almacén", "terminos": ["aceite", "arroz", "fideos", "harina", "yerba", "cafe", "azucar", "galletitas"]},
            {"slug": "bebidas", "sector": "Bebidas", "terminos": ["gaseosa", "agua", "jugo", "vino", "cerveza", "fernet"]},
            {"slug": "lacteos", "sector": "Frescos", "terminos": ["leche", "queso", "yogur", "manteca", "crema"]},
            {"slug": "limpieza", "sector": "Limpieza", "terminos": ["detergente", "lavandina", "limpiador", "papel"]},
            {"slug": "perfumeria", "sector": "Cuidado Personal", "terminos": ["shampoo", "jabon", "desodorante", "crema"]},
            {"slug": "carniceria", "sector": "Carnicería", "terminos": ["carne", "pollo", "milanesa"]},
            {"slug": "congelados", "sector": "Congelados", "terminos": ["helado", "pizza", "empanada"]},
            {"slug": "quesos", "sector": "Frescos", "terminos": ["queso", "crema", "manteca"]},
            {"slug": "fiambreria", "sector": "Fiambrería", "terminos": ["jamón", "queso", "salame"]},
            {"slug": "verduleria", "sector": "Verdulería", "terminos": ["fruta", "verdura", "lechuga"]},
            {"slug": "bazar", "sector": "Bazar", "terminos": ["vaso", "plato", "cuchillo", "bolsa"]},
            {"slug": "bebes", "sector": "Bebés", "terminos": ["pañal", "toallita", "mamadera"]},
            {"slug": "mascotas", "sector": "Mascotas", "terminos": ["alimento", "perro", "gato"]}
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
    
    def scraear_categoria(self, categoria_slug, sector):
        """Scraear una categoría específica"""
        try:
            # Asegurar cookies actualizadas
            cookies = self._get_session_cookies()
            
            # Probar diferentes URLs de categoría
            urls_categoria = [
                f"{self.base_url}/product-category/{categoria_slug}/",
                f"{self.base_url}/{categoria_slug}/",
                f"{self.base_url}/categoria/{categoria_slug}/",
                f"{self.base_url}/shop/{categoria_slug}/"
            ]
            
            for url in urls_categoria:
                try:
                    response = self.session.get(
                        url, 
                        impersonate=self.impersonate,
                        headers=self.headers, 
                        cookies=cookies, 
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        return self.procesar_pagina_categoria(response.text, sector, categoria_slug)
                except:
                    continue
            
            print(f"    ❌ No se encontró página para categoría {categoria_slug}")
            return []
            
        except Exception as e:
            print(f"    ❌ Error scrapeando categoría {categoria_slug}: {e}")
            return []
    
    def procesar_pagina_categoria(self, html, sector, categoria_slug):
        """Procesar HTML de página de categoría"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Selectores para productos WooCommerce
        productos_selectores = [
            'div.product',
            'li.type-product',
            'div.woocommerce-loop-product',
            'article.product',
            '[class*="product"]'
        ]
        
        items = []
        for selector in productos_selectores:
            items = soup.select(selector)
            if items:
                break
        
        productos = []
        for item in items[:30]:  # Limitar a 30 productos por categoría
            try:
                # Extraer nombre
                nombre_selectores = [
                    'h2.woocommerce-loop-product__title',
                    'h3',
                    'h2.product-title',
                    '.product-name',
                    'h2',
                    'h3'
                ]
                
                nombre = None
                for ns in nombre_selectores:
                    nombre_elem = item.select_one(ns)
                    if nombre_elem:
                        nombre = nombre_elem.get_text().strip()
                        break
                
                # Extraer precio
                precio_selectores = [
                    'span.price',
                    '.amount',
                    '.product-price',
                    '[class*="price"]',
                    'span.woocommerce-Price-amount'
                ]
                
                precio = None
                for ps in precio_selectores:
                    precio_elem = item.select_one(ps)
                    if precio_elem:
                        precio = self.limpiar_precio(precio_elem.get_text())
                        break
                
                # Extraer imagen
                imagen_elem = item.select_one('img')
                imagen = imagen_elem.get('src', '') if imagen_elem else ''
                
                # Extraer enlace
                link_elem = item.select_one('a')
                link = link_elem.get('href', '') if link_elem else ''
                
                if nombre and precio > 0:
                    productos.append({
                        'nombre': nombre,
                        'precio': precio,
                        'sector': sector,
                        'subcategoria': categoria_slug,
                        'imagen': imagen,
                        'link': link,
                        'fuente': 'Yaguar',
                        'stock': True,
                        'fecha_scraping': datetime.now().isoformat()
                    })
            
            except Exception as e:
                continue
        
        print(f"    📦 {len(productos)} productos encontrados")
        return productos
    
    def buscar_por_termino(self, termino):
        """Buscar por término de búsqueda"""
        try:
            # Búsqueda WordPress
            search_urls = [
                f"{self.base_url}/?s={termino}&post_type=product",
                f"{self.base_url}/search/{termino}/",
                f"{self.base_url}/buscar/{termino}/"
            ]
            
            for search_url in search_urls:
                try:
                    response = self.session.get(
                        search_url, 
                        headers=self.headers, 
                        cookies=self.cookies, 
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        productos = self.procesar_pagina_categoria(response.text, 'Búsqueda', termino)
                        if productos:
                            return productos
                except:
                    continue
            
            return []
            
        except Exception as e:
            print(f"    ❌ Error en búsqueda de {termino}: {e}")
            return []
    
    def scraear_desde_listado_maestro(self, limite=500):
        """Scraear usando nombres del Listado Maestro"""
        print(f"\n📋 Scrapeando desde Listado Maestro (límite: {limite})...")
        
        if self.listado_maestro.empty:
            print("❌ Listado Maestro no disponible")
            return []
        
        productos = []
        
        # Tomar muestra del Listado Maestro
        muestra = self.listado_maestro.head(limite)
        
        for idx, row in muestra.iterrows():
            try:
                nombre = str(row['Texto breve material']).strip()
                sector = str(row['SECTOR']).strip()
                
                # Extraer palabras clave del nombre
                palabras_clave = re.findall(r'\b[A-Za-z]{3,}\b', nombre.upper())
                palabras_clave = [p for p in palabras_clave if len(p) > 3][:3]
                
                if palabras_clave:
                    termino_busqueda = ' '.join(palabras_clave)
                    
                    resultados = self.buscar_por_termino(termino_busqueda)
                    
                    for resultado in resultados:
                        resultado['sector'] = sector
                        resultado['subcategoria'] = str(row.get('CATEGORIAS', ''))
                        resultado['nombre_original_maestro'] = nombre
                        productos.append(resultado)
                    
                    if resultados:
                        print(f"  ✅ {nombre}: {len(resultados)} productos")
                
                time.sleep(1.5)  # Delay entre búsquedas
                
            except Exception as e:
                continue
        
        return productos
    
    def scraear_completo(self):
        """Ejecutar scraping completo con acceso Pro"""
        print("🚀 Iniciando Scraper Yaguar PRO")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        todos_los_productos = []
        
        # Estrategia 1: Por categorías
        print("\n📂 Scrapeando por categorías...")
        for categoria in self.categorias:
            print(f"  📂 {categoria['sector']} - {categoria['slug']}")
            productos = self.scraear_categoria(categoria['slug'], categoria['sector'])
            todos_los_productos.extend(productos)
            time.sleep(2)  # Delay entre categorías
        
        # Estrategia 2: Por términos de búsqueda específicos
        print("\n🔍 Scrapeando por términos específicos...")
        terminos = [
            "aceite", "arroz", "fideos", "harina", "yerba", "cafe",
            "gaseosa", "agua", "vino", "cerveza", "fernet",
            "leche", "queso", "yogur", "manteca",
            "detergente", "lavandina", "papel", "jabon",
            "shampoo", "desodorante", "crema"
        ]
        
        for termino in terminos:
            productos = self.buscar_por_termino(termino)
            todos_los_productos.extend(productos)
            time.sleep(1.5)
        
        # Estrategia 3: Desde Listado Maestro (limitado)
        productos_maestro = self.scraear_desde_listado_maestro(limite=300)
        todos_los_productos.extend(productos_maestro)
        
        # Eliminar duplicados
        productos_unicos = {}
        for prod in todos_los_productos:
            key = hashlib.md5(prod['nombre'].encode()).hexdigest()
            
            if key not in productos_unicos or prod['precio'] < productos_unicos[key]['precio']:
                productos_unicos[key] = prod
        
        productos_finales = list(productos_unicos.values())
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(os.path.dirname(__file__), f"output_yaguar_pro_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(productos_finales, f, ensure_ascii=False, indent=2)
        
        # Sincronizar con BRUJULA-DE-PRECIOS
        sync_file = os.path.join(BASE_DIR, "BRUJULA-DE-PRECIOS", "data", "output_yaguar.json")
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(productos_finales, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scrapeo PRO completado:")
        print(f"  📦 Total productos únicos: {len(productos_finales)}")
        print(f"  📂 Por categorías: {len([p for p in productos_finales if p['sector'] != 'Búsqueda'])}")
        print(f"  🔍 Por búsquedas: {len([p for p in productos_finales if p['sector'] == 'Búsqueda'])}")
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
    scraper = YaguarProScraper()
    scraper.scraear_completo()
