# Docs: Monetización

## Tiers

### FREE (Forever)
- Calculador: SÍ — solo 2 mayoristas (Yaguar + Maxiconsumo)
- Ver precios: SÍ
- Guardar en lista: máx 10 productos
- Alertas: NO
- Login: NO (guest mode)

### TIER 2 — $6.999 ARS/mes
- Calculador: SÍ — los 3 mayoristas (todos)
- Guardar en lista: ilimitado
- Alertas de precio: SÍ
- Login real: SÍ
- Historial de precios: NO (Tier3)
- Mapa/direcciones: NO (Tier3)

### TIER 3 — $14.999 ARS/mes
- TODO de Tier2, MÁS:
- Mapa/direcciones por zona: SÍ
- Historial de precios: SÍ
- Reportes en Excel: SÍ
- Soporte prioritario: SÍ

## Feature gating en código
Implementado en `lib/data.ts` con flag `userTier` — MVP usa dummy auth, Tier2+ requiere auth real (post-MVP).

## Métricas objetivo
- Semana 2: 3-5 usuarios pagando
- Conversión: >1% (100 contactos = 1 cliente)
- Churn mes 1: 0%
