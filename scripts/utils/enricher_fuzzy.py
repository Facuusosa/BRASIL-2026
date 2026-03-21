
import pandas as pd
import json
import os
from rapidfuzz import process, fuzz

def enrich():
    print("⌛ Cargando Master de Vital (560k)...")
    path_vital = "VITAL-all-products-20250921.xlsx"
    # Cargamos solo lo necesario
    df_vital = pd.read_excel(path_vital, usecols=['Material', 'productName', 'ean', 'sector', 'categories'], engine='openpyxl')
    
    # Limpiamos nombres para matching
    df_vital['clean_name'] = df_vital['productName'].astype(str).str.upper().str.strip()
    vital_names = df_vital['clean_name'].tolist()
    
    # Diccionario para metadata una vez encontrado el nombre
    mapping = df_vital.set_index('clean_name').to_dict('index')
    
    print(f"📊 Maestro cargado: {len(vital_names)} nombres.")

    # Cargamos el JSON del sniffer
    json_path = "targets/maxiconsumo/output_maxiconsumo.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} no encontrado.")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        productos = json.load(f)

    print(f"🔎 Empezando matching de {len(productos)} productos...")
    enriquecidos = 0
    for i, p in enumerate(productos):
        name_maxi = str(p['nombre']).upper().strip()
        
        # Buscamos el mejor match (usamos WRatio que es flexible)
        match = process.extractOne(name_maxi, vital_names, scorer=fuzz.WRatio)
        
        if match and match[1] >= 85: # Umbral de confianza
            best_name = match[0]
            meta = mapping[best_name]
            p['ean'] = str(meta['ean'])
            p['material'] = str(meta['Material'])
            p['nombre_normalizado'] = meta['productName']
            p['subcategoria'] = meta['categories']
            p['sector'] = meta['sector']
            
            # Forzar Yerba
            if "YERBA" in best_name:
                p['categoria_forzada'] = "Yerba Mate"
            
            enriquecidos += 1
            
        if i % 100 == 0:
            print(f"Progreso: {i}/{len(productos)}... ({enriquecidos} matched)")

    print(f"✅ Enriquecidos {enriquecidos} de {len(productos)} productos.")
    
    # Guardamos el resultado (pisamos el viejo para que el front lo tome)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)
    print(f"💾 Guardado en {json_path}")

if __name__ == "__main__":
    enrich()
