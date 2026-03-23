import os
import json
import re

def normalize_name(name):
    name = str(name).upper()
    name = re.sub(r'[^\w\s\.]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def main():
    base_dir = r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\data"
    
    maxi_path = os.path.join(base_dir, "processed", "maxiconsumo_con_ean.json")
    yaguar_path = os.path.join(base_dir, "output_yaguar.json")
    carre_path = os.path.join(base_dir, "output_maxicarrefour.json")
    
    out_dir = os.path.join(base_dir, "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "catalogo_unificado.json")

    def load_json(path, fuente_override=None):
        if not os.path.exists(path):
            print(f"ATENCION: No existe {path}")
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if fuente_override:
                for d in data: d['fuente'] = fuente_override
            return data

    maxi_data = load_json(maxi_path, "maxiconsumo")
    yaguar_data = load_json(yaguar_path, "yaguar")
    carre_data = load_json(carre_path, "maxicarrefour")
    
    all_products = []
    all_products.extend(maxi_data)
    all_products.extend(yaguar_data)
    all_products.extend(carre_data)
    
    # 1. Extracción y validación rigurosa del EAN
    for p in all_products:
        p['_norm_name'] = normalize_name(p.get('nombre', ''))
        
        if p.get('fuente') == 'maxicarrefour':
            val = str(p.get('sku', '')).strip()
            if val.isdigit() and len(val) > 8:
                p['_ean_limpio'] = val
            else:
                p['_ean_limpio'] = None
        else:
            val = str(p.get('ean', '')).strip()
            if val and val != "None":
                p['_ean_limpio'] = val
            else:
                p['_ean_limpio'] = None

    unified_catalog = []
    ean_index = {}
    
    matches_ean = 0
    productos_individuales = 0
    
    print("Procesando consolidación ESTRICTA POR EAN...")
    
    for p in all_products:
        fuente = p.get('fuente', 'desc')
        precio_val = p.get('precio', 0)
        merged = False
        
        # Intentar Match Exacto SOLO por EAN
        if p['_ean_limpio'] and p['_ean_limpio'] in ean_index:
            target = ean_index[p['_ean_limpio']]
            # REGLA: Filtro de coherencia de precios (Diferencia máxima del 300%)
            # Para evitar unir Bulto vs Unidad
            existing_prices = list(target['precios'].values())
            if existing_prices and precio_val > 0:
                all_prices = existing_prices + [precio_val]
                p_max = max(all_prices)
                p_min = min(all_prices)
                if p_max > p_min * 4:
                    # Diferencia sospechosa de bulto vs unidad
                    # Separar — no unir
                    merged = False
                else:
                    if fuente not in target['precios']:
                        target['precios'][fuente] = precio_val
                        if len(p['nombre']) > len(target['nombre_display']):
                            target['nombre_display'] = p['nombre']
                    matches_ean += 1
                    merged = True
            
        # Si no hubo match por EAN válido, crear producto individual y aislado
        if not merged:
            # Si tiene EAN, se usará. Si no, forzamos un ID único por fuente y nombre para que nunca colisione 
            # con otro mayorista intentando hacerle match.
            unique_id = p['_ean_limpio'] if p['_ean_limpio'] else f"{fuente}_{p['_norm_name']}"
            
            new_item = {
                "id_unificado": unique_id,
                "nombre_display": p.get('nombre', ''),
                "precios": { fuente: precio_val },
                "imagen": p.get('imagen', ''),
                "sector": p.get('sector', '')
            }
            if p['_ean_limpio']:
                new_item['ean'] = p['_ean_limpio']
                ean_index[p['_ean_limpio']] = new_item
            
            unified_catalog.append(new_item)
            productos_individuales += 1
            
    print(f"Guardando {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unified_catalog, f, ensure_ascii=False, indent=2)
        
    # Calcular metricas ricas finales
    productos_con_2_mas = sum(1 for p in unified_catalog if len(p['precios']) > 1)
    productos_solos = sum(1 for p in unified_catalog if len(p['precios']) == 1)

    print("-" * 50)
    print("REPORTE DE DEDUPLICACIÓN 100% EXACTA (EAN ONLY)")
    print(f"Total Crudo Evaluado:          {len(all_products)}")
    print(f"Productos Únicos Finales:      {len(unified_catalog)}")
    print("-" * 50)
    print(f"Match Real (2 o más fuentes):  {productos_con_2_mas}")
    print(f"Productos Aislados (1 fuente): {productos_solos}")
    print("-" * 50)

if __name__ == "__main__":
    main()
