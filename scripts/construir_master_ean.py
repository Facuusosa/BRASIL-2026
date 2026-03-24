import os
import json
import pandas as pd

def main():
    base_dir = r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
    codigos_path = os.path.join(base_dir, "data", "raw", "CODIGOS.xlsx")
    
    yaguar_json_path = os.path.join(base_dir, "BRUJULA-DE-PRECIOS", "data", "output_yaguar.json")
    maxi_json_path = os.path.join(base_dir, "BRUJULA-DE-PRECIOS", "data", "output_maxiconsumo.json")
    # Es posible que estén en "data", pero vamos a buscar en ambas carpetas
    if not os.path.exists(yaguar_json_path):
        yaguar_json_path = os.path.join(base_dir, "data", "output_yaguar.json")
    if not os.path.exists(maxi_json_path):
        maxi_json_path = os.path.join(base_dir, "data", "output_maxiconsumo.json")

    print(f"Cargando {codigos_path}...")
    
    # PASO 1 - Construir diccionarios
    # Yaguar: col "SKU YAGUAR" + col "ean"
    try:
        df_yaguar = pd.read_excel(codigos_path, sheet_name="YAGUAR", engine='openpyxl')
        dict_yaguar = {}
        for _, row in df_yaguar.iterrows():
            sku = str(row.get('SKU YAGUAR', '')).strip().replace(".0", "")
            ean = str(row.get('ean', '')).strip().replace(".0", "")
            if sku and ean and ean != "nan" and sku != "nan":
                dict_yaguar[sku] = ean
    except Exception as e:
        print("Error YAGUAR hoja:", e)
        dict_yaguar = {}

    # Maxiconsumo: col "SKU" + col "Código de barras"
    try:
        df_maxi = pd.read_excel(codigos_path, sheet_name="MAXICONSUMO", engine='openpyxl')
        dict_maxi = {}
        for _, row in df_maxi.iterrows():
            sku = str(row.get('SKU', '')).strip().replace(".0", "")
            ean = str(row.get('Código de barras', '')).strip().replace(".0", "")
            if sku and ean and ean != "nan" and sku != "nan":
                dict_maxi[sku] = ean
    except Exception as e:
        print("Error MAXICONSUMO hoja:", e)
        dict_maxi = {}
        
    print(f"Diccionarios base -> Yaguar: {len(dict_yaguar)} EANs | Maxi: {len(dict_maxi)} EANs")

    # PASO 2 - Enriquecer los JSONs
    # Yaguar
    matches_yaguar = 0
    if os.path.exists(yaguar_json_path):
        with open(yaguar_json_path, "r", encoding="utf-8") as f:
            data_yaguar = json.load(f)
            
        for item in data_yaguar:
            sku = str(item.get('sku', '')).strip()
            if not sku:
                # Intenta extraerlo del link si existe
                link = item.get('link', '')
                if "-" in link:
                    sku = link.split("-")[-1].replace("/", "")
                    
            if sku in dict_yaguar:
                item['ean'] = dict_yaguar[sku]
                matches_yaguar += 1
                
        with open(yaguar_json_path, "w", encoding="utf-8") as f:
            json.dump(data_yaguar, f, ensure_ascii=False, indent=2)

    # Maxiconsumo
    matches_maxi = 0
    if os.path.exists(maxi_json_path):
        with open(maxi_json_path, "r", encoding="utf-8") as f:
            data_maxi = json.load(f)
            
        for item in data_maxi:
            sku = str(item.get('sku', '')).strip()
            # En tu json viejo teniamos maxiconsumo_con_ean, asi q usemos output_maxiconsumo
            if sku in dict_maxi:
                item['ean'] = dict_maxi[sku]
                matches_maxi += 1
                
        with open(maxi_json_path, "w", encoding="utf-8") as f:
            json.dump(data_maxi, f, ensure_ascii=False, indent=2)

    print("-" * 50)
    print("REPORTE ENRIQUECIMIENTO EAN SKUS")
    print("-" * 50)
    print(f"Productos Yaguar salvados con EAN: {matches_yaguar}")
    print(f"Productos Maxi salvados con EAN:   {matches_maxi}")
    print("-" * 50)

if __name__ == "__main__":
    main()
