# Skill: Verificar Precios

Verifica precios en vivo de productos sospechosos usando los scrapers existentes o el MCP Puppeteer.

## Cuándo usar
- Después de actualizar el catálogo y hay dudas sobre precios
- Cuando `auditoria_matches.json` tiene productos con ratio alto
- Cuando el usuario reporta un precio incorrecto en el frontend

## Pasos

### 1. Leer productos sospechosos
```bash
python -c "
import json
with open('BRUJULA-DE-PRECIOS/data/processed/auditoria_matches.json') as f:
    data = json.load(f)
top = data[:10]
for p in top:
    print(f'{p[\"nombre_display\"]} → ratio {p[\"ratio_precio\"]:.1f}x | fuentes: {list(p[\"precios\"].keys())}')
"
```

### 2. Verificar precio puntual con scraper Yaguar (sin Cloudflare)
```bash
python -c "
import requests, json
from targets.yaguar.scraper_pro import buscar_producto
resultado = buscar_producto('NOMBRE_PRODUCTO')
print(json.dumps(resultado, ensure_ascii=False, indent=2))
"
```

### 3. Verificar con Puppeteer MCP (si disponible)
Si el MCP `puppeteer` está activo:
- Navegar a la URL del producto en el mayorista
- Extraer el precio del DOM
- Comparar con el precio en catálogo

### 4. Corregir ratio incorrecto
Si el precio es correcto en el sitio pero incorrecto en el catálogo:
- Verificar si viene de scraper viejo (timestamp del output)
- Correr el scraper específico: `python scrape_{mayorista}.py`
- Correr `python actualizar_catalogo.py`

## Output esperado
```
VERIFICACIÓN — dd/mm/yyyy
Producto: [nombre]
Catálogo: $X (maxiconsumo) | $Y (carrefour)
Sitio real: $Z
Estado: ✅ OK / ❌ INCORRECTO (scraper tiene bug) / ⚠️ DESACTUALIZADO (correr scraper)
```
