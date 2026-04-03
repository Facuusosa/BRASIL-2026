#!/usr/bin/env python3
"""
🔧 ENRIQUECEDOR DE SCRAPING - Sistema de EANs y SKUs
Usa datos maestros de Excel para enriquecer y validar el scraping
"""

import pandas as pd
import json
import os
import re
from typing import Dict, Set, List, Optional, Tuple
from collections import defaultdict
import hashlib

class EnriquecedorScraping:
    def __init__(self):
        self.base_dir = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
        self.data_dir = os.path.join(self.base_dir, "data", "raw")
        
        # Estructura de datos maestros
        self.ean_to_sku = defaultdict(dict)  # EAN -> {mayorista: sku}
        self.sku_to_ean = defaultdict(dict)  # SKU -> {mayorista: ean}
        self.ean_to_metadata = {}  # EAN -> metadata completa
        self.sku_to_metadata = {}  # SKU -> metadata completa
        
        # Cargar datos maestros
        self.cargar_datos_maestros()
        
    def cargar_datos_maestros(self):
        """Carga todos los datos de Excel en memoria"""
        print("📊 Cargando datos maestros...")
        
        # 1. Cargar CODIGOS.xlsx
        path_codigos = os.path.join(self.data_dir, "CODIGOS.xlsx")
        if os.path.exists(path_codigos):
            xl_codigos = pd.ExcelFile(path_codigos)
            
            for sheet_name in xl_codigos.sheet_names:
                df = pd.read_excel(path_codigos, sheet_name=sheet_name)
                self._procesar_hoja_codigos(df, sheet_name.lower())
                print(f"✅ {sheet_name}: {len(df)} registros procesados")
        
        # 2. Cargar Listado Maestro
        path_maestro = os.path.join(self.data_dir, "Listado Maestro 09-03.xlsx")
        if os.path.exists(path_maestro):
            df_maestro = pd.read_excel(path_maestro)
            self._procesar_listado_maestro(df_maestro)
            print(f"✅ Listado Maestro: {len(df_maestro)} registros procesados")
        
        # Estadísticas
        print(f"\n📈 Estadísticas de carga:")
        print(f"  - EANs únicos: {len(self.ean_to_metadata)}")
        print(f"  - SKUs únicos: {len(self.sku_to_metadata)}")
        print(f"  - Mayoristas mapeados: {list(self._get_mayoristas_disponibles())}")
    
    def _procesar_hoja_codigos(self, df: pd.DataFrame, mayorista: str):
        """Procesa una hoja específica de CODIGOS.xlsx"""
        
        # Mapeo de columnas por mayorista
        column_mapping = {
            'diarco': {
                'ean': 'Ean 13',
                'sku': 'Material',
                'nombre': 'Nombre',
                'descripcion': 'Descripción del Material'
            },
            'yaguar': {
                'ean': 'ean',
                'sku': 'SKU YAGUAR',
                'nombre': 'DESCRIPCION',
                'material': 'MATERIAL'
            },
            'maxiconsumo': {
                'ean': 'Código de barras',
                'sku': 'SKU',
                'nombre': 'Descripción',
                'descripcion': 'Descripción del Material',
                'material': 'Material'
            }
        }
        
        if mayorista not in column_mapping:
            print(f"⚠️ Mayorista {mayorista} no configurado")
            return
        
        cols = column_mapping[mayorista]
        
        for _, row in df.iterrows():
            # Extraer EAN
            ean = self._limpiar_ean(row.get(cols['ean']))
            
            # Extraer SKU
            sku = str(row.get(cols['sku'], '')).strip()
            
            # Extraer nombre/descripción
            nombre = str(row.get(cols.get('nombre', cols.get('descripcion', '')), '')).strip()
            
            # Extraer material si existe
            material = str(row.get(cols.get('material', ''), '')).strip()
            
            # Guardar relaciones
            if ean and ean.startswith('779') and len(ean) == 13:
                # EAN -> SKU
                if sku:
                    self.ean_to_sku[ean][mayorista] = sku
                    self.sku_to_ean[sku][mayorista] = ean
                
                # Metadata del EAN
                self.ean_to_metadata[ean] = {
                    'nombre': nombre,
                    'mayorista': mayorista,
                    'sku': sku,
                    'material': material,
                    'fuente': 'CODIGOS.xlsx'
                }
            
            # Metadata del SKU
            if sku:
                self.sku_to_metadata[sku] = {
                    'nombre': nombre,
                    'mayorista': mayorista,
                    'ean': ean,
                    'material': material,
                    'fuente': 'CODIGOS.xlsx'
                }
    
    def _procesar_listado_maestro(self, df: pd.DataFrame):
        """Procesa el Listado Maestro"""
        
        for _, row in df.iterrows():
            # Extraer EANs (hay dos columnas)
            for ean_col in ['Código EAN', 'CODIGO DE BARRAS']:
                ean = self._limpiar_ean(row.get(ean_col))
                
                if ean and ean.startswith('779') and len(ean) == 13:
                    # Metadata completa del maestro
                    metadata = {
                        'nombre': str(row.get('Texto breve material', '')).strip(),
                        'sector': str(row.get('SECTOR', '')).strip(),
                        'familia': str(row.get('Familia', '')).strip(),
                        'categoria': str(row.get('CATEGORIAS', '')).strip(),
                        'marca': str(row.get('Marca del producto', '')).strip(),
                        'material': str(row.get('Material', '')).strip(),
                        'descripcion_ecommerce': str(row.get('Texto E-commerce', '')).strip(),
                        'fuente': 'Listado Maestro'
                    }
                    
                    # Actualizar metadata si no existe o si es más completa
                    if ean not in self.ean_to_metadata:
                        self.ean_to_metadata[ean] = metadata
                    else:
                        # Si el metadata existente viene de CODIGOS.xlsx, lo enriquecemos con datos del maestro
                        if self.ean_to_metadata[ean].get('fuente') == 'CODIGOS.xlsx':
                            self.ean_to_metadata[ean].update(metadata)
    
    def _limpiar_ean(self, ean_raw) -> Optional[str]:
        """Limpia y valida un EAN"""
        if pd.isna(ean_raw):
            return None
        
        ean_str = str(ean_raw).strip().replace('-', '').replace(' ', '')
        
        # Validar formato argentino (779 + 10 dígitos)
        if re.match(r'^779\d{10}$', ean_str):
            return ean_str
        
        return None
    
    def _get_mayoristas_disponibles(self) -> Set[str]:
        """Obtiene la lista de mayoristas disponibles"""
        mayoristas = set()
        for ean_data in self.ean_to_sku.values():
            mayoristas.update(ean_data.keys())
        return mayoristas
    
    def enriquecer_producto_scrapeado(self, producto: dict, mayorista: str) -> dict:
        """Enriquece un producto scrapeado con datos maestros"""
        
        producto_enriquecido = producto.copy()
        
        # 1. Buscar por EAN si existe
        if 'ean' in producto and producto['ean']:
            ean = self._limpiar_ean(producto['ean'])
            if ean and ean in self.ean_to_metadata:
                metadata = self.ean_to_metadata[ean]
                producto_enriquecido.update({
                    'nombre_enriquecido': metadata.get('nombre', ''),
                    'sector': metadata.get('sector', ''),
                    'categoria': metadata.get('categoria', ''),
                    'marca': metadata.get('marca', ''),
                    'validado_ean': True
                })
        
        # 2. Buscar por SKU si existe
        if 'sku' in producto and producto['sku']:
            sku = str(producto['sku']).strip()
            if sku in self.sku_to_metadata:
                metadata = self.sku_to_metadata[sku]
                producto_enriquecido.update({
                    'nombre_enriquecido': metadata.get('nombre', ''),
                    'ean_validado': metadata.get('ean', ''),
                    'validado_sku': True
                })
                
                # Si encontramos EAN por SKU, buscar metadata adicional
                ean_encontrado = metadata.get('ean')
                if ean_encontrado and ean_encontrado in self.ean_to_metadata:
                    metadata_ean = self.ean_to_metadata[ean_encontrado]
                    producto_enriquecido.update({
                        'sector': metadata_ean.get('sector', ''),
                        'categoria': metadata_ean.get('categoria', ''),
                        'marca': metadata_ean.get('marca', '')
                    })
        
        # 3. Buscar por nombre (fuzzy matching) como fallback
        if 'nombre' in producto and not producto_enriquecido.get('validado_ean') and not producto_enriquecido.get('validado_sku'):
            coincidencias = self._buscar_por_nombre(producto['nombre'], mayorista)
            if coincidencias:
                mejor_coincidencia = coincidencias[0]
                producto_enriquecido.update({
                    'nombre_enriquecido': mejor_coincidencia['nombre'],
                    'sector': mejor_coincidencia.get('sector', ''),
                    'categoria': mejor_coincidencia.get('categoria', ''),
                    'marca': mejor_coincidencia.get('marca', ''),
                    'ean_sugerido': mejor_coincidencia.get('ean', ''),
                    'validado_nombre': True,
                    'coincidencia_score': mejor_coincidencia['score']
                })
        
        return producto_enriquecido
    
    def _buscar_por_nombre(self, nombre: str, mayorista: str, limite: int = 3) -> List[dict]:
        """Búsqueda por nombre usando coincidencias parciales"""
        nombre_lower = nombre.lower()
        coincidencias = []
        
        # Buscar en metadata de EANs
        for ean, metadata in self.ean_to_metadata.items():
            if metadata.get('mayorista') == mayorista or mayorista == 'maxicarrefour':
                nombre_meta = metadata.get('nombre', '').lower()
                
                # Cálculo simple de similitud
                score = self._calcular_similitud(nombre_lower, nombre_meta)
                
                if score > 0.6:  # Umbral de similitud
                    coincidencias.append({
                        'ean': ean,
                        'nombre': metadata.get('nombre', ''),
                        'sector': metadata.get('sector', ''),
                        'categoria': metadata.get('categoria', ''),
                        'marca': metadata.get('marca', ''),
                        'score': score
                    })
        
        # Ordenar por score y devolver las mejores
        coincidencias.sort(key=lambda x: x['score'], reverse=True)
        return coincidencias[:limite]
    
    def _calcular_similitud(self, str1: str, str2: str) -> float:
        """Calcula similitud simple entre dos strings"""
        palabras1 = set(str1.split())
        palabras2 = set(str2.split())
        
        if not palabras1 or not palabras2:
            return 0.0
        
        interseccion = palabras1.intersection(palabras2)
        union = palabras1.union(palabras2)
        
        return len(interseccion) / len(union)
    
    def obtener_sku_desde_ean(self, ean: str, mayorista: str) -> Optional[str]:
        """Obtiene SKU de un mayorista específico desde un EAN"""
        ean_limpio = self._limpiar_ean(ean)
        if ean_limpio and ean_limpio in self.ean_to_sku:
            return self.ean_to_sku[ean_limpio].get(mayorista)
        return None
    
    def obtener_ean_desde_sku(self, sku: str, mayorista: str) -> Optional[str]:
        """Obtiene EAN desde SKU de un mayorista específico"""
        sku_str = str(sku).strip()
        if sku_str in self.sku_to_ean:
            return self.sku_to_ean[sku_str].get(mayorista)
        return None
    
    def generar_reporte_enriquecimiento(self, productos_scrapeados: List[dict], mayorista: str) -> dict:
        """Genera reporte de enriquecimiento para un lote de productos"""
        
        stats = {
            'total_productos': len(productos_scrapeados),
            'enriquecidos': 0,
            'validados_ean': 0,
            'validados_sku': 0,
            'validados_nombre': 0,
            'sin_enriquecer': 0,
            'mayorista': mayorista
        }
        
        productos_enriquecidos = []
        
        for producto in productos_scrapeados:
            enriquecido = self.enriquecer_producto_scrapeado(producto, mayorista)
            productos_enriquecidos.append(enriquecido)
            
            # Actualizar estadísticas
            if enriquecido.get('validado_ean') or enriquecido.get('validado_sku') or enriquecido.get('validado_nombre'):
                stats['enriquecidos'] += 1
                
                if enriquecido.get('validado_ean'):
                    stats['validados_ean'] += 1
                if enriquecido.get('validado_sku'):
                    stats['validados_sku'] += 1
                if enriquecido.get('validado_nombre'):
                    stats['validados_nombre'] += 1
            else:
                stats['sin_enriquecer'] += 1
        
        # Calcular porcentajes
        if stats['total_productos'] > 0:
            stats['porcentaje_enriquecido'] = (stats['enriquecidos'] / stats['total_productos']) * 100
            stats['porcentaje_validado_ean'] = (stats['validados_ean'] / stats['total_productos']) * 100
            stats['porcentaje_validado_sku'] = (stats['validados_sku'] / stats['total_productos']) * 100
        else:
            stats['porcentaje_enriquecido'] = 0
            stats['porcentaje_validado_ean'] = 0
            stats['porcentaje_validado_sku'] = 0
        
        return {
            'estadisticas': stats,
            'productos': productos_enriquecidos
        }
    
    def guardar_datos_mapeo(self):
        """Guarda los datos de mapeo para uso futuro"""
        output_dir = os.path.join(self.base_dir, "BRUJULA-DE-PRECIOS", "data", "processed")
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar mapeos
        with open(os.path.join(output_dir, "ean_to_sku_mapping.json"), "w", encoding="utf-8") as f:
            json.dump(dict(self.ean_to_sku), f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(output_dir, "sku_to_ean_mapping.json"), "w", encoding="utf-8") as f:
            json.dump(dict(self.sku_to_ean), f, ensure_ascii=False, indent=2)
        
        # Guardar metadata
        with open(os.path.join(output_dir, "ean_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(self.ean_to_metadata, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(output_dir, "sku_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(self.sku_to_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Datos de mapeo guardados en {output_dir}")


def demo_enriquecimiento():
    """Demostración del enriquecedor"""
    enriquecedor = EnriquecedorScraping()
    
    # Ejemplo de producto scrapeado
    productos_ejemplo = [
        {
            'nombre': 'Aceite Cocinero 1.5 Lt',
            'precio': 4399.0,
            'sku': '103',
            'mayorista': 'maxiconsumo'
        },
        {
            'nombre': 'Yogur La Serenisima 1Lt',
            'precio': 1250.0,
            'ean': '7790123456789',
            'mayorista': 'yaguar'
        }
    ]
    
    for producto in productos_ejemplo:
        print(f"\n🔍 Producto original: {producto['nombre']}")
        enriquecido = enriquecedor.enriquecer_producto_scrapeado(producto, producto['mayorista'])
        print(f"✅ Enriquecido: {enriquecido.get('nombre_enriquecido', 'Sin cambios')}")
        print(f"   Sector: {enriquecido.get('sector', 'N/A')}")
        print(f"   Validado: {enriquecido.get('validado_ean', enriquecido.get('validado_sku', False))}")


if __name__ == "__main__":
    enriquecedor = EnriquecedorScraping()
    enriquecedor.guardar_datos_mapeo()
    
    # Demo
    demo_enriquecimiento()
