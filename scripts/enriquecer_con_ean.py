import os
import json
import pandas as pd
import math

def main():
    base_dir = r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
    codigos_path = os.path.join(base_dir, "data", "raw", "CODIGOS.xlsx")
    maxi_json_path = os.path.join(base_dir, "BRUJULA-DE-PRECIOS", "data", "output_maxiconsumo.json")
    
    out_dir = os.path.join(base_dir, "BRUJULA-DE-PRECIOS", "data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_json_path = os.path.join(out_dir, "maxiconsumo_con_ean.json")

    print(f"Cargando {codigos_path}...")
    df = pd.read_excel(codigos_path)
    
    # Construir el diccionario { "Art": "Ean 13" }
    # Nos aseguramos de limpiar NA y castear a string limpio
    ean_dict = {}
    for idx, row in df.iterrows():
        art = row.get("Art")
        ean = row.get("Ean 13")
        
        if pd.notna(art) and pd.notna(ean):
            # Limpiar posible .0 en articulos o ean
            art_str = str(art).split('.')[0].strip()
            ean_str = str(ean).split('.')[0].strip()
            ean_dict[art_str] = ean_str

    print(f"Diccionario construido con {len(ean_dict)} mappings Art -> EAN.")
    
    print(f"Cargando {maxi_json_path}...")
    with open(maxi_json_path, "r", encoding="utf-8") as f:
        maxi_data = json.load(f)
        
    encontrados = 0
    no_encontrados = 0
    
    for p in maxi_data:
        sku = str(p.get("sku", "")).strip()
        
        if sku in ean_dict:
            p["ean"] = ean_dict[sku]
            encontrados += 1
        else:
            p["ean"] = None
            no_encontrados += 1
            
    print(f"Guardando {out_json_path}...")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(maxi_data, f, ensure_ascii=False, indent=2)
        
    print("-" * 30)
    print("REPORTE DE ENRIQUECIMIENTO EAN - MAXICONSUMO")
    print(f"Productos Totales procesados: {encontrados + no_encontrados}")
    print(f"Productos CON EAN encontrado: {encontrados}")
    print(f"Productos SIN EAN encontrado: {no_encontrados}")
    print(f"Tasa de éxito: {round((encontrados / (encontrados + no_encontrados)) * 100, 2)}%")
    print("-" * 30)

if __name__ == "__main__":
    main()
