#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVIDOR WEB - Comando Simple
"""

import os
import subprocess
import sys
from datetime import datetime

def main():
    print("=== SERVIDOR WEB ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar catálogo
    catalog_file = "BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json"
    if not os.path.exists(catalog_file):
        print("ERROR: No se encontró catalogo_unificado.json")
        print("Ejecuta primero un scraper:")
        print("python scrape_yaguar.py")
        print("python scrape_maxicarrefour.py")
        print("python scrape_maxiconsumo.py")
        return
    
    # Cambiar al directorio web
    web_dir = "BRUJULA-DE-PRECIOS"
    
    # Verificar node_modules
    if not os.path.exists(f"{web_dir}/node_modules"):
        print("Instalando dependencias Node.js...")
        subprocess.run(["npm", "install"], cwd=web_dir)
    
    # Iniciar servidor
    print("Iniciando servidor web...")
    print("Accede a: http://localhost:3000")
    print("Presiona Ctrl+C para detener")
    
    try:
        subprocess.run(["npm", "run", "dev"], cwd=web_dir)
    except KeyboardInterrupt:
        print("\nServidor detenido")

if __name__ == "__main__":
    main()
