# Rules: Testing

## Bucle verificador (obligatorio después de TODA tarea)
```
MIENTRAS resultado no sea óptimo:
  1. Verificar concretamente — leer archivo, contar productos, revisar logs
  2. Juzgar — ¿los números tienen sentido? ¿hay algo raro?
  3. Si hay problema → identificar causa → corregir → volver a 1
  4. Si está bien → reportar qué se verificó y el resultado
FIN
```
No es una verificación única. Es un bucle. Nunca decir "listo" después de un solo check.

## Verificación post-scraping
1. ¿Se generó `output_mayorista_YYYYMMDD_HHMMSS.json`?
2. ¿Cuántos productos? (Yaguar >3000, Carrefour >3000, Maxiconsumo >500)
3. ¿Precios > 0 en la mayoría de productos?
4. ¿`catalogo_unificado.json` tiene fecha de hoy?

## Verificación post-cambio frontend
1. `npx tsc --noEmit` — sin errores TypeScript
2. `npm run lint` — sin warnings críticos
3. Las 4 vistas cargan en `localhost:3000`
4. El calculador funciona end-to-end (precio compra → margen → precio venta)
5. Sin errores en consola del browser

## Verificación post-pipeline completo
```bash
python scrape_yaguar.py        # verifica output + producto count
python scrape_maxicarrefour.py # verifica output + producto count
python scrape_maxiconsumo.py   # verifica output + producto count
# catalogo_unificado.json actualizado automáticamente
python start_web.py            # localhost:3000 con data fresca
```

## Principios
- Tests de tipo + lint verifican corrección del código — no corrección de features
- Si no se puede testear la UI, decirlo explícitamente en vez de asumir que funciona
- No mockear la DB o scrapers en tests — mejor datos reales aunque sean lentos
