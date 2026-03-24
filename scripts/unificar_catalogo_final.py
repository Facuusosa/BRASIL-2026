import os
import json
import pandas as pd

# CONFIGURACIÓN DE RUTAS
BASE_DIR = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS"
DATA_DIR = os.path.join(BASE_DIR, "BRUJULA-DE-PRECIOS", "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

def main():
    # 1. Rutas de archivos
    codigos_path = os.path.join(RAW_DIR, "CODIGOS.xlsx")
    master_ean_path = os.path.join(PROCESSED_DIR, "master_ean.json")
    
    # JSONs de scraping
    maxi_json = os.path.join(DATA_DIR, "output_maxiconsumo.json")
    yaguar_json = os.path.join(DATA_DIR, "output_yaguar.json")
    # El usuario dijo output_carrefour.json, pero en el disco es output_maxicarrefour.json
    carrefour_json = os.path.join(DATA_DIR, "output_maxicarrefour.json")
    
    # 2. Cargar Diccionarios de Mapeo (CODIGOS.xlsx)
    print("Cargando diccionarios SKU -> EAN...")
    dict_maxi = {}
    dict_yaguar = {}
    
    try:
        # Maxi
        df_maxi = pd.read_excel(codigos_path, sheet_name="MAXICONSUMO")
        for _, row in df_maxi.iterrows():
            sku = str(row.get('SKU', '')).strip().replace(".0", "")
            ean = str(row.get('Código de barras', '')).strip().replace(".0", "")
            if sku and ean and ean.lower() != 'nan':
                dict_maxi[sku] = ean
                
        # Yaguar
        df_yaguar = pd.read_excel(codigos_path, sheet_name="YAGUAR")
        for _, row in df_yaguar.iterrows():
            sku = str(row.get('SKU YAGUAR', '')).strip().replace(".0", "")
            ean = str(row.get('ean', '')).strip().replace(".0", "")
            if sku and ean and ean.lower() != 'nan':
                dict_yaguar[sku] = ean
        print(f"Diccionarios cargados. Maxi: {len(dict_maxi)} | Yaguar: {len(dict_yaguar)}")
    except Exception as e:
        print(f"Error cargando Excel: {e}")

    # 3. Cargar Maestro para nombres limpios y fotos
    print("Cargando Master EAN...")
    master_data = {}
    if os.path.exists(master_ean_path):
        with open(master_ean_path, "r", encoding="utf-8") as f:
            master_data = json.load(f)
    print(f"Master cargado con {len(master_data)} referencias.")

    # 4. Procesar y Unificar
    catalogo = {}
    fuentes = [
        {"file": carrefour_json, "key": "carrefour", "map": None},
        {"file": maxi_json, "key": "maxiconsumo", "map": dict_maxi},
        {"file": yaguar_json, "key": "yaguar", "map": dict_yaguar}
    ]
    
    stats = {
        "totales": 0,
        "con_ean": 0,
        "limpios_maestro": 0,
        "foto_maestro": 0
    }

    for src in fuentes:
        if not os.path.exists(src["file"]):
            print(f"Saltando {src['file']} (No existe)")
            continue
            
        print(f"Procesando {src['key']}...")
        with open(src["file"], "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for item in data:
            stats["totales"] += 1
            sku = str(item.get('sku', '')).strip()
            
            # Obtener EAN
            ean = None
            if src["key"] == "carrefour":
                ean = sku # Carrefour usa EAN como SKU
            elif src["map"] and sku in src["map"]:
                ean = src["map"][sku]
            
            if not ean:
                continue # Sin EAN no hay comparación confiable
                
            stats["con_ean"] += 1
            
            # Si el producto ya existe, agregamos el precio
            if ean in catalogo:
                catalogo[ean]["precios"][src["key"]] = item.get("precio", 0)
                # Si es Carrefour, priorizamos su imagen si el maestro no tiene
                if src["key"] == "carrefour" and not catalogo[ean].get("imagen"):
                    catalogo[ean]["imagen"] = item.get("imagen", "")
            else:
                # Nuevo producto en el catálogo unificado
                prod_unificado = {
                    "id_unificado": ean,
                    "ean": ean,
                    "nombre_display": item.get("nombre", ""),
                    "imagen": item.get("imagen", ""),
                    "sector": item.get("sector", ""),
                    "subcategoria": item.get("subcategoria", ""),
                    "precios": {
                        "carrefour": 0, "maxiconsumo": 0, "yaguar": 0
                    }
                }
                prod_unificado["precios"][src["key"]] = item.get("precio", 0)
                
                # ENRIQUECIMIENTO CON EL MAESTRO
                if ean in master_data:
                    m = master_data[ean]
                    # Nombre limpio
                    if m.get("nombre"):
                        prod_unificado["nombre_display"] = m["nombre"]
                        stats["limpios_maestro"] += 1
                    # Foto del Maestro (si existe el campo)
                    if m.get("imagen") or m.get("foto"):
                        prod_unificado["imagen"] = m.get("imagen") or m.get("foto")
                        stats["foto_maestro"] += 1
                
                catalogo[ean] = prod_unificado

    # 5. Guardar resultado
    output_path = os.path.join(PROCESSED_DIR, "catalogo_unificado.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(list(catalogo.values()), f, ensure_ascii=False, indent=2)

    # 6. Reporte Final
    productos_unf = list(catalogo.values())
    varias_fuentes = [p for p in productos_unf if sum(1 for v in p["precios"].values() if v > 0) >= 2]
    
    print("\n" + "="*50)
    print("REPORTE DE UNIFICACIÓN FINAL")
    print("="*50)
    print(f"Productos únicos (con EAN):    {len(productos_unf)}")
    print(f"Productos con 2+ mayoristas:   {len(varias_fuentes)}")
    print(f"Nombres limpios del Maestro:   {stats['limpios_maestro']}")
    print(f"Fotos del Maestro asignadas:   {stats['foto_maestro']}")
    print(f"Archivo guardado en: {output_path}")
    print("="*50)

if __name__ == "__main__":
    main()
