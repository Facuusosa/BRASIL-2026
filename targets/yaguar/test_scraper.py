#!/usr/bin/env python3
"""
Test del scraper Yaguar actualizado
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scraper_pro import YaguarProScraper

def test_scraper():
    print("🚀 Test del scraper Yaguar actualizado")
    print("=" * 50)
    
    scraper = YaguarProScraper()
    
    # Test 1: Scrapeo de categoría Bebidas
    print("\n📂 Test 1: Scrapeo categoría Bebidas")
    productos_bebidas = scraper.scraear_categoria("bebidas", "Bebidas")
    
    if productos_bebidas:
        print(f"✅ Categoría Bebidas: {len(productos_bebidas)} productos")
        for i, prod in enumerate(productos_bebidas[:5]):
            print(f"  {i+1}. {prod['nombre']} - ${prod['precio']}")
    else:
        print("❌ Categoría Bebidas no scrapeada")
    
    # Test 2: Scrapeo de categoría Almacén
    print("\n📂 Test 2: Scrapeo categoría Almacén")
    productos_almacen = scraper.scraear_categoria("almacen", "Almacén")
    
    if productos_almacen:
        print(f"✅ Categoría Almacén: {len(productos_almacen)} productos")
        for i, prod in enumerate(productos_almacen[:5]):
            print(f"  {i+1}. {prod['nombre']} - ${prod['precio']}")
    else:
        print("❌ Categoría Almacén no scrapeada")
    
    # Test 3: Scrapeo completo (limitado)
    print("\n🔄 Test 3: Scrapeo completo (limitado)")
    scraper.categorias = [
        {"slug": "bebidas", "sector": "Bebidas", "terminos": ["gaseosa"]},
        {"slug": "almacen", "sector": "Almacén", "terminos": ["aceite"]}
    ]
    
    productos_completos = scraper.scraear_completo()
    
    if productos_completos:
        print(f"✅ Total productos: {len(productos_completos)}")
        
        # Guardar resultados
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_output_yaguar_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(productos_completos, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Resultados guardados en: {output_file}")
        
        # Sincronizar con frontend
        sync_file = os.path.join(os.path.dirname(__file__), "..", "..", "BRUJULA-DE-PRECIOS", "data", "output_yaguar.json")
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(productos_completos, f, ensure_ascii=False, indent=2)
        
        print(f"🔄 Sincronizado con frontend")
        
        return True
    else:
        print("❌ No se encontraron productos")
        return False

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("\n🎉 Scraper Yaguar funcionando correctamente!")
    else:
        print("\n💀 Scraper necesita más ajustes")
