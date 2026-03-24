import json
import os

def check_sanity():
    unificado_path = r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\data\processed\catalogo_unificado.json"
    if not os.path.exists(unificado_path):
        print("No se encuentra el unificado.")
        return

    with open(unificado_path, "r", encoding="utf-8") as f:
        catalogo = json.load(f)

    # 1. Buscar discrepancias Nombre vs URL de Imagen
    # Si la imagen tiene "ayudin" pero el nombre es "Fideos", hay error de match
    discrepancias = []
    for p in catalogo:
        name = p['nombre_display'].lower()
        img = p['imagen'].lower()
        
        # Filtros de cruce comunes
        fideos_keywords = ["fideos", "pasta", "tallarines", "tirabuzon", "mostachol"]
        limpieza_keywords = ["ayudin", "detergente", "lavandina", "desinfectante", "jabon"]
        
        is_fideo = any(k in name for k in fideos_keywords)
        is_limpieza_img = "ayudin" in img or "limpieza" in img or "lavandina" in img
        
        if is_fideo and is_limpieza_img:
            discrepancias.append({
                "id": p['id_unificado'],
                "nombre": p['nombre_display'],
                "img": p['imagen'],
                "precios": p['precios']
            })

    print(f"=== REPORTE DE DISCREPANCIAS NOMBRE/IMAGEN ({len(discrepancias)} halladas) ===")
    for d in discrepancias[:10]:
        print(f"ID: {d['id']}")
        print(f"Nom: {d['nombre']}")
        print(f"Img: {d['img']}")
        print(f"Precios: {d['precios']}")
        print("-" * 20)

    # 2. Análisis de PRECIOS SUSPICACES (Diferencia > 200%)
    print("\n=== REPORTE DE PRECIOS SOSPECHOSOS (>200% gap) ===")
    sospechosos = []
    for p in catalogo:
        precios = [v for v in p['precios'].values() if v > 0]
        if len(precios) > 1:
            p_max = max(precios)
            p_min = min(precios)
            if p_max > p_min * 2:
                sospechosos.append(p)
                
    sospechosos.sort(key=lambda x: max(x['precios'].values()) / min(x['precios'].values()), reverse=True)
    for p in sospechosos[:10]:
        print(f"ID: {p['id_unificado']} | {p['nombre_display']}")
        print(f"Gap: {(max(p['precios'].values()) / min(p['precios'].values())):.2f}x")
        for f, v in p['precios'].items():
            print(f"  {f}: {v}")
        print("-" * 20)

if __name__ == "__main__":
    check_sanity()
