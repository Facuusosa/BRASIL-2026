#!/usr/bin/env python3
"""
Test del scraper Maxiconsumo actualizado
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scraper_pro import MaxiconsumoProScraper

def test_scraper():
    print("🚀 Test del scraper Maxiconsumo actualizado")
    print("=" * 50)
    
    scraper = MaxiconsumoProScraper()
    
    # Test 1: Búsqueda por EAN conocido
    print("\n🔍 Test 1: Búsqueda por EAN (Coca Cola)")
    resultado_ean = scraper.buscar_por_ean("7790895000997")
    
    if resultado_ean:
        print(f"✅ EAN encontrado:")
        print(f"  Nombre: {resultado_ean['nombre']}")
        print(f"  Precio: ${resultado_ean['precio']}")
        print(f"  SKU: {resultado_ean['sku']}")
    else:
        print("❌ EAN no encontrado")
    
    # Test 2: Búsqueda por nombre
    print("\n🔍 Test 2: Búsqueda por nombre (Aceite)")
    resultado_nombre = scraper.buscar_por_nombre("Aceite Cocinero", "Almacén")
    
    if resultado_nombre:
        print(f"✅ Nombre encontrado:")
        print(f"  Nombre: {resultado_nombre['nombre']}")
        print(f"  Precio: ${resultado_nombre['precio']}")
        print(f"  Sector: {resultado_nombre['sector']}")
    else:
        print("❌ Nombre no encontrado")
    
    # Test 3: Scrapeo de categoría (limitado)
    print("\n📂 Test 3: Scrapeo de categoría (Almacén - aceite)")
    scraper.categorias = [{"nombre": "Almacén", "terminos": ["aceite"]}]  # Limitar para test
    productos_categoria = scraper.scraear_por_categorias()
    
    if productos_categoria:
        print(f"✅ Categoría scrapeada: {len(productos_categoria)} productos")
        for i, prod in enumerate(productos_categoria[:3]):  # Mostrar primeros 3
            print(f"  {i+1}. {prod['nombre']} - ${prod['precio']}")
    else:
        print("❌ Categoría no scrapeada")

if __name__ == "__main__":
    test_scraper()
