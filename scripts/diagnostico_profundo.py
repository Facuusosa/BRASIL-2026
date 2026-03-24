import json
import os

def diagnostico():
    import json
    import os
    base_dir = r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\data"
    unificado_path = os.path.join(base_dir, "processed", "catalogo_unificado.json")
    
    with open(unificado_path, "r", encoding="utf-8") as f:
        catalogo = json.load(f)

    with open(r"C:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\reporte_diagnostico.txt", "w", encoding="utf-8") as out:
        out.write("=== DANDO CAZA AL BUG DE LAS IMÁGENES ===\n")
        matarazzo = next((p for p in catalogo if "TIRABUZON" in p['nombre_display'].upper() and "MATARAZZO" in p['nombre_display'].upper()), None)
        if matarazzo:
            out.write(f"Producto: {matarazzo['nombre_display'].strip()}\n")
            out.write(f"EAN guardado: {matarazzo['id_unificado']}\n")
            out.write(f"Imagen unificada que se está mostrando: {matarazzo['imagen']}\n")
            out.write(f"Precios unificados: {matarazzo['precios']}\n")
        else:
            out.write("No se encontró el matarazzo en el unificado.\n")
            
        out.write("\n=== ANALISIS DE IMAGENES GENERICAS (YAGUAR) ===\n")
        img_yaguar_generica = sum(1 for p in catalogo if "0000-3078.png" in p.get('imagen', ''))
        img_vacias = sum(1 for p in catalogo if not p.get('imagen', ''))
        out.write(f"Productos con imagen placeholder de Yaguar (0000-3078): {img_yaguar_generica}\n")
        out.write(f"Productos sin imagen: {img_vacias}\n")
        
        out.write("\n=== ANALISIS DE PRECIOS $0 ===\n")
        precios_totales = 0
        precios_cero = 0
        for p in catalogo:
            for fuente, precio in p['precios'].items():
                precios_totales += 1
                if precio <= 0:
                    precios_cero += 1
        out.write(f"Total de reportes de precio: {precios_totales}\n")
        out.write(f"Precios en $0: {precios_cero}\n")
        
        out.write("\n=== TOP 10 DIFERENCIAS DE PRECIOS ENTRE MAYORISTAS ===\n")
        multiples = [p for p in catalogo if len(p['precios']) > 1]
        anomalias = []
        for p in multiples:
            precios_validos = [v for v in p['precios'].values() if v > 0]
            if len(precios_validos) > 1:
                p_max = max(precios_validos)
                p_min = min(precios_validos)
                diferencia_pct = ((p_max - p_min) / p_max) * 100
                anomalias.append((p['nombre_display'].strip(), p['id_unificado'], diferencia_pct, p['precios']))
                
        anomalias.sort(key=lambda x: x[2], reverse=True)
        for i, a in enumerate(anomalias[:10]):
            out.write(f"{i+1}. {a[0]} (EAN: {a[1]})\n")
            out.write(f"   Diferencia: {a[2]:.2f}%\n")
            out.write(f"   Precios: {a[3]}\n")

if __name__ == "__main__":
    diagnostico()
