# BRÚJULA DE PRECIOS — Claude Context

**App:** Comparador de precios mayoristas para comerciantes de Buenos Aires.  
**Stack:** Next.js 16 + Python scrapers + JSON catalog.  
**Estado:** MVP lanzando semana del 22/04/2026. Bloqueador real: ventas.

## Mayoristas activos
- Yaguar (`targets/yaguar/scraper_pro.py`)
- MaxiCarrefour (`targets/maxicarrefour/scraper_pro.py`) — cookies en `.env`, renovar cada ~30 días
- Maxiconsumo (`targets/maxiconsumo/scraper_pro.py`)

## Entrypoints clave
- Frontend: `BRUJULA-DE-PRECIOS/app/page.tsx`
- Data: `BRUJULA-DE-PRECIOS/lib/data.ts`
- Catálogo: `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`
- Unificador: `actualizar_catalogo.py`
- Config: `config.py` + `.env`

## Instrucciones detalladas
- Reglas del proyecto → `.claude/rules/`
- Arquitectura, tiers, operaciones → `.claude/docs/`
