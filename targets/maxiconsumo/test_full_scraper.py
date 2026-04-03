#!/usr/bin/env python3
"""
Test del scraper completo con límite pequeño
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scraper_pro import MaxiconsumoProScraper

def test_full_scraper():
    print("🚀 Test del scraper completo (limitado)")
    print("=" * 50)
    
    scraper = MaxiconsumoProScraper()
    
    # Limitar categorías para test rápido
    scraper.categorias = [
        {"nombre": "Bebidas", "terminos": ["gaseosa", "agua"]},
        {"nombre": "Almacén", "terminos": ["aceite"]}
    ]
    
    # Ejecutar scrapeo por categorías
    productos_categoria = scraper.scraear_por_categorias()
    
    print(f"\n✅ Productos por categorías: {len(productos_categoria)}")
    
    # Mostrar primeros productos con precios
    productos_con_precio = [p for p in productos_categoria if p.get('precio', 0) > 0]
    
    print(f"\n💰 Productos con precio: {len(productos_con_precio)}")
    
    for i, prod in enumerate(productos_con_precio[:10]):
        print(f"  {i+1}. {prod['nombre']}")
        print(f"     Precio: ${prod['precio']}")
        print(f"     Sector: {prod['sector']}")
        print()
    
    # Guardar resultados
    if productos_categoria:
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_output_maxiconsumo_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(productos_categoria, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Resultados guardados en: {output_file}")
        
        # Sincronizar con frontend
        sync_file = os.path.join(os.path.dirname(__file__), "..", "..", "BRUJULA-DE-PRECIOS", "data", "output_maxiconsumo.json")
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(productos_categoria, f, ensure_ascii=False, indent=2)
        
        print(f"🔄 Sincronizado con frontend")
        
        return True
    else:
        print("❌ No se encontraron productos")
        return False

if __name__ == "__main__":
    success = test_full_scraper()
    if success:
        print("\n🎉 Scraper Maxiconsumo funcionando correctamente!")
    else:
        print("\n💀 Scraper necesita más ajustes")
