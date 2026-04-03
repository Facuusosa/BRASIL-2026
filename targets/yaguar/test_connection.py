#!/usr/bin/env python3
"""
Test de conexión a Yaguar con curl_cffi impersonate
"""

from curl_cffi import requests
import re

def test_impersonate():
    # Probar diferentes impersonates según SCRAPING_MASTER_PLAN.md
    impersonates = ["safari15_3", "chrome120", "chrome119", "chrome118"]
    
    for impersonate in impersonates:
        print(f"\n🔍 Probando impersonate: {impersonate}")
        
        try:
            response = requests.get(
                'https://yaguar.com.ar',
                impersonate=impersonate,
                timeout=15
            )
            
            print(f"  Status: {response.status_code}")
            print(f"  Content-Length: {len(response.text)}")
            
            if response.status_code == 200:
                print(f"  ✅ ÉXITO con {impersonate}!")
                
                # Extraer cookies
                print(f"  🍪 Cookies: {list(response.cookies.keys())}")
                
                # Buscar WooCommerce/WordPress
                if 'woocommerce' in response.text.lower():
                    print(f"  🛒 WooCommerce detectado")
                
                if 'wordpress' in response.text.lower():
                    print(f"  📝 WordPress detectado")
                
                return True, impersonate, response
            else:
                print(f"  ❌ Fallido")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return False, None, None

if __name__ == "__main__":
    success, impersonate, response = test_impersonate()
    if success:
        print(f"\n🎉 Usar impersonate='{impersonate}' para el scraper")
    else:
        print("\n💀 Todos los impersonates fallaron")
