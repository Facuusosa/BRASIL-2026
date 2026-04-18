#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
from datetime import datetime

def main():
    print("=== SCRAPER YAGUAR ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    result = subprocess.run(["python", "targets/yaguar/scraper_pro.py"], cwd=os.getcwd())

    if result.returncode == 0:
        print("\n=== UNIFICANDO DATOS ===")
        subprocess.run(["python", "actualizar_catalogo.py"], cwd=os.getcwd())
        print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER YAGUAR")

if __name__ == "__main__":
    main()
