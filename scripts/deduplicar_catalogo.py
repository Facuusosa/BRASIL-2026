import os
import json
import re
import sys
import subprocess

try:
    from rapidfuzz import process, fuzz
except ImportError:
    print("Instalando rapidfuzz...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rapidfuzz"], check=True)
    from rapidfuzz import process, fuzz

def normalize_name(name):
    name = str(name).upper()
    # Remove symbols but keep dots for decimals
    name = re.sub(r'[^\w\s\.]', ' ', name)
    # Remove double spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def main():
    base_dir = r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\data"
    
    maxi_path = os.path.join(base_dir, "processed", "maxiconsumo_con_ean.json")
    yaguar_path = os.path.join(base_dir, "output_yaguar.json")
    # Teniendo en cuenta que el valid es output_maxicarrefour.json (el viejo carrefour estaba vacío)
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
    
    # Normalización inicial para cada producto y extracción segura del EAN
    for p in all_products:
        p['_norm_name'] = normalize_name(p.get('nombre', ''))
        
        # En Maxicarrefour, el EAN real se guardó en "sku"
        if p.get('fuente') == 'maxicarrefour':
            val = str(p.get('sku', '')).strip()
            # Validar que parezca un EAN (solo números, >8 chars)
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
    
    # Indexes para busquedas rápidas:
    # mapeo: ean_limpio -> {referencia al producto unificado}
    ean_index = {}
    
    # Las listas de norm_names y ref_items para RapidFuzz
    # norm_name -> {referencia al producto unificado} (la primera vez que se inserta)
    name_keys = []
    
    matches_ean = 0
    matches_fuzzy = 0
    duplicados_evitados = 0
    
    print("Procesando consolidación...")
    
    for p in all_products:
        fuente = p.get('fuente', 'desc')
        precio_val = p.get('precio', 0)
        
        merged = False
        
        # 1. Intentar Match Exacto por EAN
        if p['_ean_limpio'] and p['_ean_limpio'] in ean_index:
            # Encontrado por EAN
            target = ean_index[p['_ean_limpio']]
            if fuente not in target['precios']:
                target['precios'][fuente] = precio_val
                # Si el nuevo nombre es más largo/descriptivo, lo actualizamos
                if len(p['nombre']) > len(target['nombre_display']):
                    target['nombre_display'] = p['nombre']
            matches_ean += 1
            duplicados_evitados += 1
            merged = True
            
        # 2. Si no matchó por EAN, intentar Fuzzy por Nombre Normalizado
        if not merged and p['_norm_name'] and len(name_keys) > 0:
            # Extraer mejor match
            # Limitamos a score_cutoff=85 (fuzz.ratio)
            # RapidFuzz retorna un tuple (best_match, score, index)
            # Usamos process.extractOne
            best = process.extractOne(p['_norm_name'], name_keys, scorer=fuzz.ratio, score_cutoff=85)
            
            if best:
                matched_name = best[0]
                # Buscar el producto unificado que tenia ese matched_name base
                # Recorremos el catalogo base para encontrarlo (como la key es unica base, lo buscamos en el catalog)
                # (Para ser O(1), podiamos mapear el nombre base al target, pero cuidado que si distintos EAN 
                # tenian el mismo nombre base colisionarian. Lo buscamos directo en unified_catalog por norm_name base)
                target = None
                for u in unified_catalog:
                    if u['_base_norm_name'] == matched_name:
                        target = u
                        break
                
                if target:
                    if fuente not in target['precios']:
                        target['precios'][fuente] = precio_val
                        if len(p['nombre']) > len(target['nombre_display']):
                            target['nombre_display'] = p['nombre']
                        
                    # Agregamos su EAN al target si no tenia y este si trae
                    if not target.get('ean') and p['_ean_limpio']:
                        target['ean'] = p['_ean_limpio']
                        ean_index[p['_ean_limpio']] = target
                        # Forzamos su unificado a ser este ean si es que tenia un id basado en nombre
                        target['id_unificado'] = p['_ean_limpio']
                        
                    matches_fuzzy += 1
                    duplicados_evitados += 1
                    merged = True
        
        # 3. Si no hizo match con nada, es un producto NUEVO en el catalogo
        if not merged:
            new_item = {
                "id_unificado": p['_ean_limpio'] if p['_ean_limpio'] else p['_norm_name'],
                "nombre_display": p.get('nombre', ''),
                "precios": { fuente: precio_val },
                "imagen": p.get('imagen', ''),
                "sector": p.get('sector', ''),
                "_base_norm_name": p['_norm_name']
            }
            # Guardar opcionalmente el ean original crudo
            if p['_ean_limpio']:
                new_item['ean'] = p['_ean_limpio']
                ean_index[p['_ean_limpio']] = new_item
            
            unified_catalog.append(new_item)
            name_keys.append(p['_norm_name'])
            
    # Limpieza pre-guardado
    for u in unified_catalog:
        del u['_base_norm_name']
        
    print(f"Guardando {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unified_catalog, f, ensure_ascii=False, indent=2)
        
    print("-" * 40)
    print("REPORTE DEDUPLICACION HIBRIDA")
    print(f"Total Crudo Evaluado:     {len(all_products)}")
    print(f"Productos Unicos Finales: {len(unified_catalog)}")
    print(f"Matches por EAN exacto:   {matches_ean}")
    print(f"Matches por Fuzzy (85%):  {matches_fuzzy}")
    print(f"Duplicados fusionados:    {duplicados_evitados}")
    print("-" * 40)

if __name__ == "__main__":
    main()
