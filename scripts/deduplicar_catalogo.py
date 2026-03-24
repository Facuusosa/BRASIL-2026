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
    
    maxi_path = os.path.join(base_dir, "output_maxiconsumo.json")
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

    # Cargar Master EAN
    master_path = os.path.join(base_dir, "processed", "master_ean.json")
    if os.path.exists(master_path):
        with open(master_path, "r", encoding="utf-8") as f:
            master_dict = json.load(f)
    else:
        master_dict = {}

    maxi_data = load_json(maxi_path, "maxiconsumo")
    yaguar_data = load_json(yaguar_path, "yaguar")
    carre_data = load_json(carre_path, "maxicarrefour")
    
    all_products = []
    all_products.extend([p for p in maxi_data if p.get('precio', 0) > 0])
    all_products.extend([p for p in yaguar_data if p.get('precio', 0) > 0])
    all_products.extend([p for p in carre_data if p.get('precio', 0) > 0])
    
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
    en_master = 0
    
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
                if p_max > p_min * 2.5:
                    # Diferencia sospechosa de bulto vs unidad
                    # Separar — no unir
                    merged = False
                else:
                    if fuente not in target['precios']:
                        target['precios'][fuente] = precio_val
                        
                        # Prioridad de imagen: maxicarrefour > maxiconsumo > yaguar
                        score_map = {'maxicarrefour': 3, 'maxiconsumo': 2, 'yaguar': 1}
                        current_source = target.get('fuente_imagen', '')
                        if score_map.get(fuente, 0) > score_map.get(current_source, 0) and p.get('imagen'):
                            if not ('0000-3078' in p.get('imagen','') and fuente == 'yaguar'):
                                target['imagen'] = p.get('imagen', '')
                                target['fuente_imagen'] = fuente
                                
                        if p['_ean_limpio'] in master_dict:
                            target['nombre_display'] = master_dict[p['_ean_limpio']]['nombre']
                            target['sector'] = master_dict[p['_ean_limpio']]['depto']
                        elif len(p.get('nombre', '')) > len(target['nombre_display']):
                            target['nombre_display'] = p.get('nombre', '')
                    matches_ean += 1
                    merged = True
            
        # Si no hubo match por EAN válido, crear producto individual y aislado
        if not merged:
            unique_id = p['_ean_limpio'] if p['_ean_limpio'] else f"{fuente}_{p['_norm_name']}"
            
            nombre_final = p.get('nombre', '')
            sector_final = p.get('sector', '')
            if p['_ean_limpio'] in master_dict:
                nombre_final = master_dict[p['_ean_limpio']]['nombre']
                sector_final = master_dict[p['_ean_limpio']]['depto']

            new_item = {
                "id_unificado": unique_id,
                "nombre_display": nombre_final,
                "precios": { fuente: precio_val },
                "imagen": p.get('imagen', '') if not ('0000-3078' in p.get('imagen', '') and fuente == 'yaguar') else '',
                "fuente_imagen": fuente,
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
    
    en_master = sum(1 for p in unified_catalog if p.get('ean') and p['ean'] in master_dict)

    print("-" * 50)
    print("REPORTE DE DEDUPLICACIÓN 100% EXACTA (EAN ONLY)")
    print(f"Total Crudo Evaluado:          {len(all_products)}")
    print(f"Productos Únicos Finales:      {len(unified_catalog)}")
    print("-" * 50)
    print(f"Match Real (2 o más fuentes):  {productos_con_2_mas}")
    print(f"Productos Aislados (1 fuente): {productos_solos}")
    print(f"Bautizados por Master DB:      {en_master}")
    print("-" * 50)

if __name__ == "__main__":
    main()
