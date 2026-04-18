#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
from datetime import datetime

def main():
    print("=== SCRAPER MAXICONSUMO ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    result = subprocess.run(["python", "targets/maxiconsumo/scraper_pro.py"], cwd=os.getcwd())

    if result.returncode == 0:
        print("\n=== ENRIQUECIENDO PRECIOS ===")
        subprocess.run(["python", "targets/maxiconsumo/enriquecer_precios.py"], cwd=os.getcwd())

        print("\n=== UNIFICANDO DATOS ===")
        subprocess.run(["python", "actualizar_catalogo.py"], cwd=os.getcwd())
        print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER MAXICONSUMO")

if __name__ == "__main__":
    main()
