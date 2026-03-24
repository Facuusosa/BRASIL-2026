import os
import json
import subprocess
import sys

# Asegurar dependencias
try:
    import pandas as pd
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"], check=True)
    import pandas as pd

def build_master_ean():
    base_dir = r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
    excel_path = os.path.join(base_dir, "data", "raw", "Listado Maestro 09-03.xlsx")
    out_dir = os.path.join(base_dir, "BRUJULA-DE-PRECIOS", "data", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "master_ean.json")
    
    print(f"Cargando {excel_path}...")
    # read_excel, header=None to read indices 0,1..90 directly without header row interference.
    # actually, maybe header=0 is better to skip the header row so we don't treat "Código EAN" string as an EAN!
    # Yes, header=0 reads the first row as columns, but then the columns are strings. But wait! We can just read the values.
    # To be safe: header=None will read all rows including header. Then we just filter by length and digit.
    df = pd.read_excel(excel_path, header=None, engine='openpyxl')
    
    master_dict = {}
    
    for _, row in df.iterrows():
        try:
            # Col 40: EAN
            raw_ean = str(row.get(40, "")).strip().replace(".0", "")
            if not raw_ean.isdigit() or len(raw_ean) < 12:
                continue
            
            # Col 90, 1 etc
            def clean_str(val):
                return str(val).strip() if pd.notna(val) else ""
            
            t_eco = clean_str(row.get(90, ""))
            t_breve = clean_str(row.get(1, ""))
            
            nombre = t_eco if t_eco else t_breve
            if not nombre:
                nombre = f"Producto {raw_ean}" # Fallback extemo
                
            marca = clean_str(row.get(44, ""))
            depto = clean_str(row.get(75, ""))
            cat = clean_str(row.get(79, ""))
            subcat = clean_str(row.get(81, ""))
            
            master_dict[raw_ean] = {
                "ean": raw_ean,
                "nombre": nombre,
                "marca": marca,
                "depto": depto,
                "categoria": cat,
                "subcategoria": subcat
            }
        except Exception as e:
            continue
            
    print(f"Resultado esperado y guardado: {len(master_dict)} productos maestros")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(master_dict, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    build_master_ean()
