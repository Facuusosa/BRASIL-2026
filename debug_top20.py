import json

with open('BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json', 'r', encoding='utf-8') as f:
    uni = json.load(f)

resultados = []
for p in uni:
    precios = {k: v for k, v in p.get('precios', {}).items() if v > 0}
    if len(precios) >= 2:
        val_list = list(precios.values())
        max_p = max(val_list)
        min_p = min(val_list)
        
        # Ahorro vs el mas caro %
        ahorro_pct = round(((max_p - min_p) / max_p) * 100, 2)
        
        resultados.append({
            'nombre': p.get('nombre_display', ''),
            'ean': p.get('ean', p.get('id_unificado', 'Sin EAN')),
            'precios': precios,
            'ahorro': ahorro_pct
        })

resultados.sort(key=lambda x: x['ahorro'], reverse=True)

with open('debug_out.txt', 'w', encoding='utf-8') as f:
    f.write(f'TOTAL: {len(resultados)}\n\n')
    for i, r in enumerate(resultados[:20]):
        f.write(f"{i+1}. {r['nombre']}\n")
        f.write(f"   EAN: {r['ean']}\n")
        f.write(f"   Maxi: ${r['precios'].get('maxiconsumo', 'N/A')}\n")
        f.write(f"   Yaguar: ${r['precios'].get('yaguar', 'N/A')}\n")
        f.write(f"   Carrefour: ${r['precios'].get('maxicarrefour', 'N/A')}\n")
        f.write(f"   Ahorro: {r['ahorro']}%\n\n")
