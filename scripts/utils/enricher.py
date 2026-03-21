
import pandas as pd
import json
import os

def enrich():
    print("⌛ Cargando Master de Vital (560k)...")
    path_vital = "VITAL-all-products-20250921.xlsx"
    # Cargamos solo lo necesario para que no explote la RAM
    df_vital = pd.read_excel(path_vital, usecols=['Material', 'productName', 'ean', 'sector', 'categories'], engine='openpyxl')
    
    # Creamos un diccionario para búsqueda ultra rápida
    # Convertimos Material a string para matchear con los SKUs del sniffer
    df_vital['Material_str'] = df_vital['Material'].astype(str)
    mapping = df_vital.set_index('Material_str').to_dict('index')
    
    print(f"📊 Maestro cargado: {len(mapping)} materiales.")

    # Cargamos el JSON del sniffer
    json_path = "targets/maxiconsumo/output_maxiconsumo.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} no encontrado.")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        productos = json.load(f)

    enriquecidos = 0
    for p in productos:
        sku = str(p['sku'])
        if sku in mapping:
            meta = mapping[sku]
            p['nombre_real'] = meta['productName']
            p['ean_real'] = meta['ean']
            p['sector_real'] = meta['sector']
            p['subcategoria_real'] = meta['categories']
            enriquecidos += 1
            # Si dice yerba en algún lado, forzamos categoría
            if "YERBA" in str(meta['productName']).upper() or "YERBA" in str(meta['categories']).upper():
                p['categoria_forzada'] = "Yerba Mate"

    print(f"✅ Enriquecidos {enriquecidos} de {len(productos)} productos.")
    
    # Guardamos el resultado
    with open("output_maxiconsumo_enriquecido.json", 'w', encoding='utf-8') as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)
    print("💾 Guardado en output_maxiconsumo_enriquecido.json")

if __name__ == "__main__":
    enrich()
