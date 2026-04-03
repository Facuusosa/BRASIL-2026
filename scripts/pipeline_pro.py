#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COMPLETO - VERSIÓN PRO
Ejecuta todos los scrapeos con acceso a internet real
"""

import os
import json
import time
import subprocess
import sys
from datetime import datetime
import pandas as pd
import hashlib

# Configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGETS_DIR = os.path.join(BASE_DIR, "..", "targets")
DATA_DIR = os.path.join(BASE_DIR, "..", "BRUJULA-DE-PRECIOS", "data")
RAW_DIR = os.path.join(BASE_DIR, "..", "data", "raw")

class PipelinePro:
    def __init__(self):
        self.resultados = {
            'maxicarrefour': [],
            'maxiconsumo': [],
            'yaguar': []
        }
        self.listado_maestro = self.cargar_listado_maestro()
        
    def cargar_listado_maestro(self):
        """Cargar el Listado Maestro"""
        try:
            df = pd.read_excel(os.path.join(RAW_DIR, "Listado Maestro 09-03.xlsx"))
            print(f"✅ Listado Maestro cargado: {len(df)} productos")
            return df
        except Exception as e:
            print(f"❌ Error cargando Listado Maestro: {e}")
            return pd.DataFrame()
    
    def ejecutar_scraper_pro(self, competidor):
        """Ejecutar scraper específico con acceso Pro"""
        print(f"\n🚀 Ejecutando scraper PRO de {competidor.upper()}")
        print("=" * 50)
        
        scraper_path = os.path.join(TARGETS_DIR, competidor, "scraper_pro.py")
        
        if not os.path.exists(scraper_path):
            print(f"❌ No existe scraper PRO para {competidor}")
            return []
        
        try:
            # Ejecutar scraper PRO
            resultado = subprocess.run(
                [sys.executable, scraper_path], 
                capture_output=True, 
                text=True, 
                timeout=1800  # 30 minutos timeout
            )
            
            print(resultado.stdout)
            
            if resultado.returncode != 0:
                print(f"❌ Error ejecutando scraper PRO {competidor}:")
                print(resultado.stderr)
                return []
            
            # Buscar archivo de salida más reciente
            target_dir = os.path.join(TARGETS_DIR, competidor)
            output_files = [f for f in os.listdir(target_dir) if f.startswith(f"output_{competidor}_pro") and f.endswith(".json")]
            
            if output_files:
                # Ordenar por fecha (asumimos timestamp en nombre)
                latest_file = sorted(output_files)[-1]
                file_path = os.path.join(target_dir, latest_file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    productos = json.load(f)
                
                print(f"✅ {competidor} PRO: {len(productos)} productos scrapeados")
                return productos
            
            print(f"❌ No se encontró archivo de salida PRO para {competidor}")
            return []
            
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout ejecutando scraper PRO {competidor}")
            return []
        except Exception as e:
            print(f"❌ Error ejecutando scraper PRO {competidor}: {e}")
            return []
    
    def buscar_en_maestro(self, nombre_producto, ean=""):
        """Buscar información del producto en el Listado Maestro"""
        if self.listado_maestro.empty:
            return {}
        
        # Buscar por EAN primero
        if ean and ean != "":
            match_ean = self.listado_maestro[self.listado_maestro['Código EAN'].astype(str) == str(ean)]
            if not match_ean.empty:
                row = match_ean.iloc[0]
                return {
                    'ean': str(row['Código EAN']),
                    'sector': str(row['SECTOR']),
                    'subcategoria': str(row.get('CATEGORIAS', '')),
                    'material': str(row['Material']),
                    'familia': str(row.get('Desc. Familia', '')),
                    'marca': str(row.get('Marca del producto', ''))
                }
        
        # Buscar por similitud de nombre
        nombre_limpio = nombre_producto.lower().strip()
        
        # Búsqueda simple por palabras clave
        for idx, row in self.listado_maestro.iterrows():
            nombre_maestro = str(row['Texto breve material']).lower().strip()
            
            # Si hay coincidencia de palabras clave importantes
            palabras_producto = set(nombre_limpio.split())
            palabras_maestro = set(nombre_maestro.split())
            
            # Calcular similitud simple
            interseccion = palabras_producto.intersection(palabras_maestro)
            if len(interseccion) >= 2 and any(len(p) > 4 for p in interseccion):
                return {
                    'ean': str(row.get('Código EAN', '')),
                    'sector': str(row['SECTOR']),
                    'subcategoria': str(row.get('CATEGORIAS', '')),
                    'material': str(row['Material']),
                    'familia': str(row.get('Desc. Familia', '')),
                    'marca': str(row.get('Marca del producto', ''))
                }
        
        return {}
    
    def unificar_catalogo_pro(self):
        """Unificar todos los resultados en un catálogo único (versión Pro)"""
        print("\n🔄 Unificando catálogo PRO...")
        print("=" * 50)
        
        catalogo_unificado = []
        
        # Procesar cada competidor
        for competidor, productos in self.resultados.items():
            print(f"📊 Procesando {competidor}: {len(productos)} productos")
            
            for producto in productos:
                # Buscar información en el Listado Maestro
                info_maestro = self.buscar_en_maestro(
                    producto.get('nombre', ''), 
                    producto.get('ean', '')
                )
                
                # Crear entrada unificada
                entrada = {
                    'id_unificado': hashlib.md5(
                        f"{producto['nombre']}_{producto.get('sku', '')}_{competidor}".encode()
                    ).hexdigest(),
                    'ean': producto.get('ean', info_maestro.get('ean', '')),
                    'nombre_display': producto['nombre'],
                    'imagen': producto.get('imagen', ''),
                    'sector': info_maestro.get('sector', producto.get('sector', 'General')),
                    'subcategoria': info_maestro.get('subcategoria', producto.get('subcategoria', 'General')),
                    'precios': {competidor: producto['precio']},
                    'fuentes': {competidor: {
                        'nombre': producto['nombre'],
                        'imagen': producto.get('imagen', ''),
                        'sku': producto.get('sku', ''),
                        'fecha_scraping': producto.get('fecha_scraping', datetime.now().isoformat())
                    }},
                    'sku': producto.get('sku', ''),
                    'master_name': bool(info_maestro),
                    'nombre_original': producto['nombre'],
                    'competidor_principal': competidor,
                    'link': producto.get('link', ''),
                    'stock': producto.get('stock', True)
                }
                
                # Agregar información del maestro si está disponible
                if info_maestro:
                    entrada.update({
                        'material_maestro': info_maestro.get('material', ''),
                        'familia_maestro': info_maestro.get('familia', ''),
                        'marca_maestro': info_maestro.get('marca', '')
                    })
                
                catalogo_unificado.append(entrada)
        
        print(f"✅ Catálogo unificado PRO creado: {len(catalogo_unificado)} productos totales")
        return catalogo_unificado
    
    def cruzar_productos_pro(self, catalogo):
        """Cruzar productos para encontrar duplicados entre competidores (versión Pro)"""
        print("\n🔗 Cruzando productos entre competidores...")
        
        # Agrupar por similitud de nombre
        productos_agrupados = {}
        
        for producto in catalogo:
            nombre_base = producto['nombre_display'].lower().strip()
            
            # Crear clave de agrupación mejorada
            palabras_clave = re.findall(r'\b[a-z]{4,}\b', nombre_base)
            clave = '_'.join(sorted(palabras_clave[:4]))  # Primeras 4 palabras clave
            
            if clave not in productos_agrupados:
                productos_agrupados[clave] = []
            
            productos_agrupados[clave].append(producto)
        
        # Unificar productos cruzados
        catalogo_cruzado = []
        
        for clave, productos_grupo in productos_agrupados.items():
            if len(productos_grupo) == 1:
                # Producto único
                catalogo_cruzado.append(productos_grupo[0])
            else:
                # Productos cruzados - unificar precios
                producto_base = productos_grupo[0]
                
                # Unificar precios de todos los competidores
                precios_unificados = {}
                fuentes_unificadas = {}
                
                for prod in productos_grupo:
                    competidor = prod['competidor_principal']
                    precios_unificados[competidor] = list(prod['precios'].values())[0]
                    fuentes_unificadas[competidor] = prod['fuentes'][competidor]
                
                # Actualizar producto base
                producto_base['precios'] = precios_unificados
                producto_base['fuentes'] = fuentes_unificadas
                producto_base['crossed'] = True
                producto_base['competidores'] = list(precios_unificados.keys())
                
                catalogo_cruzado.append(producto_base)
        
        print(f"✅ Productos cruzados PRO: {len(catalogo_cruzado)}")
        print(f"   📊 Productos únicos: {len([p for p in catalogo_cruzado if not p.get('crossed', False)])}")
        print(f"   🔗 Productos cruzados: {len([p for p in catalogo_cruzado if p.get('crossed', False)])}")
        
        return catalogo_cruzado
    
    def generar_estadisticas_pro(self, catalogo):
        """Generar estadísticas del catálogo (versión Pro)"""
        print("\n📊 Generando estadísticas PRO...")
        
        stats = {
            'fecha_generacion': datetime.now().isoformat(),
            'total_productos': len(catalogo),
            'competidores': {},
            'sectores': {},
            'productos_con_precios_multiples': 0,
            'productos_del_maestro': 0,
            'productos_con_stock': 0,
            'promedio_precios': {},
            'rango_precios': {}
        }
        
        # Estadísticas por competidor
        for producto in catalogo:
            competidores = list(producto['precios'].keys())
            
            for competidor in competidores:
                if competidor not in stats['competidores']:
                    stats['competidores'][competidor] = 0
                    stats['promedio_precios'][competidor] = 0
                stats['competidores'][competidor] += 1
                
                precio = list(producto['precios'].values())[0]
                stats['promedio_precios'][competidor] += precio
                
                if len(competidores) > 1:
                    stats['productos_con_precios_multiples'] += 1
            
            if producto.get('master_name', False):
                stats['productos_del_maestro'] += 1
            
            if producto.get('stock', True):
                stats['productos_con_stock'] += 1
            
            # Estadísticas por sector
            sector = producto.get('sector', 'General')
            if sector not in stats['sectores']:
                stats['sectores'][sector] = 0
            stats['sectores'][sector] += 1
        
        # Calcular promedios
        for competidor in stats['competidores']:
            if stats['competidores'][competidor] > 0:
                stats['promedio_precios'][competidor] = round(
                    stats['promedio_precios'][competidor] / stats['competidores'][competidor], 2
                )
        
        # Guardar estadísticas
        stats_file = os.path.join(DATA_DIR, "processed", "estadisticas_catalogo_pro.json")
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print("📈 Estadísticas PRO guardadas")
        return stats
    
    def guardar_resultados_pro(self, catalogo, stats):
        """Guardar todos los resultados (versión Pro)"""
        print("\n💾 Guardando resultados PRO...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar catálogo unificado
        catalogo_file = os.path.join(DATA_DIR, "processed", f"catalogo_unificado_pro_{timestamp}.json")
        os.makedirs(os.path.dirname(catalogo_file), exist_ok=True)
        
        with open(catalogo_file, 'w', encoding='utf-8') as f:
            json.dump(catalogo, f, ensure_ascii=False, indent=2)
        
        # Actualizar catálogo principal
        main_catalogo_file = os.path.join(DATA_DIR, "processed", "catalogo_unificado.json")
        with open(main_catalogo_file, 'w', encoding='utf-8') as f:
            json.dump(catalogo, f, ensure_ascii=False, indent=2)
        
        # Crear backup
        backup_file = os.path.join(DATA_DIR, "processed", f"backup_catalogo_{timestamp}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(catalogo, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Catálogo PRO guardado:")
        print(f"   📄 Principal: {main_catalogo_file}")
        print(f"   📄 Timestamp: {catalogo_file}")
        print(f"   📄 Backup: {backup_file}")
        print(f"   📊 Estadísticas: {len(catalogo)} productos")
        
        return catalogo_file
    
    def ejecutar_pipeline_completo_pro(self):
        """Ejecutar pipeline completo con acceso Pro"""
        print("🚀 INICIANDO PIPELINE COMPLETO PRO")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Paso 1: Ejecutar scrapeos PRO
        print("\n📥 FASE 1: EJECUTANDO SCRAPEOS PRO")
        
        competidores = ['maxicarrefour', 'maxiconsumo', 'yaguar']
        
        for competidor in competidores:
            productos = self.ejecutar_scraper_pro(competidor)
            self.resultados[competidor] = productos
            
            # Delay entre competidores
            time.sleep(5)
        
        # Paso 2: Unificar catálogo
        print("\n🔄 FASE 2: UNIFICANDO CATÁLOGO PRO")
        catalogo = self.unificar_catalogo_pro()
        
        # Paso 3: Cruzar productos
        print("\n🔗 FASE 3: CRUZANDO PRODUCTOS PRO")
        catalogo_cruzado = self.cruzar_productos_pro(catalogo)
        
        # Paso 4: Generar estadísticas
        print("\n📊 FASE 4: GENERANDO ESTADÍSTICAS PRO")
        stats = self.generar_estadisticas_pro(catalogo_cruzado)
        
        # Paso 5: Guardar resultados
        print("\n💾 FASE 5: GUARDANDO RESULTADOS PRO")
        archivo_final = self.guardar_resultados_pro(catalogo_cruzado, stats)
        
        # Resumen final
        print("\n🎉 PIPELINE PRO COMPLETADO CON ÉXITO")
        print("=" * 60)
        print(f"📊 Total productos únicos: {len(catalogo_cruzado)}")
        print(f"🔗 Productos cruzados: {len([p for p in catalogo_cruzado if p.get('crossed', False)])}")
        print(f"📋 Productos del maestro: {stats['productos_del_maestro']}")
        print(f"📄 Archivo final: {archivo_final}")
        
        for competidor, cantidad in stats['competidores'].items():
            print(f"  📦 {competidor}: {cantidad} productos")
        
        print(f"\n📈 Sectores disponibles:")
        for sector, cantidad in sorted(stats['sectores'].items()):
            print(f"  📁 {sector}: {cantidad} productos")
        
        return catalogo_cruzado

if __name__ == "__main__":
    pipeline = PipelinePro()
    pipeline.ejecutar_pipeline_completo_pro()
