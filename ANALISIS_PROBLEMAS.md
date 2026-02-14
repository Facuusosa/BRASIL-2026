# 🔍 ANÁLISIS COMPLETO DEL FLIGHT MONITOR BOT
## Estado actual, problemas detectados y evidencia

---

## 📁 ESTRUCTURA DEL PROYECTO

```
BRASIL 2026/
├── src/
│   ├── __init__.py
│   ├── main.py              (812 líneas - Orquestador principal)
│   ├── config.py             (403 líneas - Configuración + .env)
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py   (437 líneas - Clase abstracta con Playwright)
│   │   ├── turismo_city.py   (794 líneas - Scraper Turismo City) ← PROBLEMA PRINCIPAL
│   │   └── despegar.py       (405 líneas - Scraper Despegar)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py         (226 líneas - SQLAlchemy models)
│   │   └── db_manager.py     (487 líneas - CRUD)
│   ├── notifier/
│   │   ├── __init__.py
│   │   └── telegram_bot.py   (213 líneas - Alertas Telegram)
│   ├── analyzer/
│   │   ├── __init__.py
│   │   └── scorer.py         (140 líneas - Scoring 0-100)
│   └── utils/
│       ├── __init__.py
│       ├── logger.py         (149 líneas - Logging con colores)
│       └── helpers.py        (385 líneas - Utilidades generales)
├── data/
│   └── cache/                (Screenshots de errores guardados aquí)
├── requirements.txt          (Dependencias - YA CORREGIDO el conflicto pytest)
├── .env.example
├── setup.bat / setup.sh
├── test_bot.py
├── INSTALACION.md
└── .gitignore
```

---

## 🚨 PROBLEMA PRINCIPAL: SCRAPER DE TURISMO CITY

### Evidencia visual (screenshots capturados por el bot):

**Ejecuciones anteriores (antes de mi fix):**
- `turismo_city_no_results_20260212_2147xx.png` a `turismo_city_no_results_20260212_2155xx.png`: **11 screenshots idénticos mostrando página 404 de Turismo City**
  - La página muestra: "TURISMOCITY - 404 - Parece que la página que estás buscando no existe."
  - Tiene botones: VUELOS, HOTELES, PAQUETES

**Ejecuciones posteriores (después del primer fix que hice):**
- `turismo_city_origin_field_error_20260212_2156xx.png` y `turismo_city_origin_field_error_20260212_2157xx.png`: **2 screenshots mostrando la homepage de Turismo City cargada correctamente, PERO el scraper no encontró el campo de origen del formulario**
  - La homepage se carga OK (se ven ofertas de vuelos, precios, etc.)
  - El formulario de búsqueda es visible en la parte superior de la página
  - PERO: El scraper no puede encontrar el campo de input para escribir "Buenos Aires"

### ¿Qué pasó cronológicamente?

1. **Código original**: Usaba `_build_search_url()` que generaba una URL directa:
   ```
   https://www.turismocity.com.ar/vuelos/BUE/FLN/2026-03-09/2026-03-16/2
   ```
   **Resultado**: 404. Esa URL no existe en Turismo City.

2. **Mi primer fix**: Reescribí el código para que NO use URL directa, sino que:
   - Carga la homepage (`turismocity.com.ar`)
   - Intenta encontrar el campo de origen del formulario
   - Escribe "Buenos Aires" y selecciona del autocompletado
   
   **Resultado**: La homepage carga OK, pero `_fill_autocomplete_field()` no encuentra el campo de input. Retorna `False` → screenshot `origin_field_error`.

---

## 🔎 ANÁLISIS DEL FORMULARIO DE TURISMO CITY

Mirando el screenshot de la homepage exitosa, el formulario de búsqueda tiene:

- **Barra superior** con campos: "Viajes" (tabs), Origen, Destino, Fecha ida, Fecha vuelta, Pasajeros, botón azul "Buscar"
- Los campos del formulario **NO son inputs HTML estándar**. Turismo City usa un framework JavaScript moderno (probablemente React/Vue) con componentes custom
- Los selectores CSS que intenta el scraper son genéricos:
  ```python
  'input[placeholder*="origen"]', 'input[placeholder*="Origen"]',
  'input[placeholder*="salida"]', 'input[placeholder*="Salida"]',
  'input[name*="origin"]', '#origin',
  ```
  Estos selectores probablemente NO coinciden con los elementos reales del DOM

### Lo que necesitamos hacer:
**Inspeccionar el DOM real de turismocity.com.ar** para encontrar:
1. ¿Qué elemento es el campo de "Origen"? (¿es un `<input>`, `<div>` clickeable, un componente React?)
2. ¿Qué selectores CSS o atributos tiene?
3. ¿Cómo funciona el autocompletado? (¿dropdown, overlay, lista?)
4. ¿Cómo es el date picker? (¿calendario custom, input nativo?)
5. ¿El botón "Buscar" es un `<button>`, `<a>`, o es un `<div>` con onClick?

---

## 📊 ESTADO DE CADA COMPONENTE

| Componente | Estado | Detalle |
|---|---|---|
| `main.py` | ✅ OK | Orquesta correctamente los scrapers |
| `config.py` | ✅ OK | Config cargada desde .env |
| `base_scraper.py` | ✅ OK | Stealth mode arreglado (soporta v1 y v2 de playwright-stealth) |
| `turismo_city.py` | ❌ FALLA | No encuentra el formulario de búsqueda |
| `despegar.py` | ❓ SIN VERIFICAR | Usa URL directa, puede funcionar o no |
| `database/` | ✅ OK | Verificado, crea tablas correctamente |
| `scorer.py` | ✅ OK | Verificado, scoring funciona |
| `telegram_bot.py` | ⚠️ PENDIENTE | Requiere config de TELEGRAM_BOT_TOKEN y CHAT_ID |
| `requirements.txt` | ✅ OK | Conflicto de pytest ya corregido |

---

## 🔧 LO QUE HAY QUE HACER

### Opción A: Inspeccionar el DOM real de turismocity.com.ar
Alguien necesita abrir turismocity.com.ar en un navegador y:
1. Hacer click derecho en el campo "Origen" → Inspeccionar
2. Anotar: tag del elemento, clases CSS, atributos data-*, placeholder
3. Hacer lo mismo con: campo Destino, Date picker, botón Buscar
4. Probar escribir "Buenos Aires" y ver qué dropdown aparece → anotar selectores del dropdown
5. Con esa info, actualizar los SELECTORS en `turismo_city.py`

### Opción B: Usar un approach diferente (recomendado)
En vez de interactuar con el formulario (frágil, depende de selectores que cambian), se podría:
1. **Buscar si Turismo City tiene una API interna** que el frontend usa para buscar vuelos (interceptar network requests en DevTools)
2. **Usar otra plataforma directamente** como Google Flights o Kayak que tienen formatos de URL predecibles
3. **Usar la API de Despegar** si es que Despegar funciona con URL directa, y agregar más plataformas con URLs predecibles

### Opción C: Fix rápido - Selectores correctos
Si alguien puede dar los selectores reales del DOM de Turismo City, es un cambio de 5 minutos en el diccionario `SELECTORS` de `turismo_city.py` (líneas 62-86).

---

## 📝 CÓDIGO RELEVANTE PARA EL FIX

### 1. Selectores actuales (que NO funcionan) - `turismo_city.py` líneas 62-86:
```python
SELECTORS = {
    # --- Formulario de búsqueda ---
    "origin_input": 'input[placeholder*="origen"], input[name*="origin"], #origin',
    "destination_input": 'input[placeholder*="destino"], input[name*="destination"], #destination',
    "departure_date": 'input[name*="departure"], input[placeholder*="Ida"]',
    "return_date": 'input[name*="return"], input[placeholder*="Vuelta"]',
    "passengers_selector": '.passengers, .pax-selector, [data-testid="passengers"]',
    "search_button": 'button[type="submit"], .search-button, .btn-search',
    
    # --- Resultados ---
    "results_container": '.results, .flight-results, [data-testid="results"]',
    "result_card": '.result-card, .flight-card, .itinerary',
    "airline_name": '.airline-name, .carrier-name, .airline',
    "price_total": '.price, .total-price, .fare-price',
    # ... etc
}
```

### 2. Método que falla - `_fill_autocomplete_field()` (líneas ~409-507):
Intenta encontrar un input con múltiples selectores, pero ninguno coincide con el DOM real de Turismo City.

### 3. Configuración de ruta - `config.py`:
```python
ORIGIN_CITY = "Buenos Aires"
ORIGIN_AIRPORTS = ["AEP", "EZE"]
DESTINATION_CITY = "Florianópolis"
DESTINATION_AIRPORT = "FLN"
DEPARTURE_DATE = "2026-03-09"
RETURN_DATE = "2026-03-16"
PASSENGERS = 2
```

### 4. Despegar (probablemente funciona) - URL directa:
```python
# despegar.py genera:
# https://www.despegar.com.ar/vuelos/BUE/FLN/2026-03-09/2026-03-16/2/0/0
```
Este formato de URL de Despegar es conocido y público. Debería funcionar.

---

## ⚡ RESUMEN EJECUTIVO

| Pregunta | Respuesta |
|---|---|
| ¿El bot arranca? | ✅ Sí, `python src/main.py --test` ejecuta |
| ¿Abre el navegador? | ✅ Sí, Playwright + Chromium funcionan |
| ¿Carga Turismo City? | ✅ Sí, la homepage carga perfectamente |
| ¿Puede buscar vuelos? | ❌ No, no encuentra los campos del formulario |
| ¿Error principal? | **Selectores CSS incorrectos** para el formulario de Turismo City |
| ¿Qué se necesita? | Inspeccionar el DOM real de turismocity.com.ar y poner los selectores correctos |
| ¿Despegar funciona? | ❓ No verificado aún, pero debería por usar URL directa |

---

## 🎯 PARA RESOLVER CON OTRA IA

Necesitas una IA que pueda:
1. **Abrir turismocity.com.ar en un navegador real**
2. **Inspeccionar el DOM** del formulario de búsqueda
3. **Darte los selectores CSS exactos** para:
   - Campo de origen (para escribir "Buenos Aires")
   - Campo de destino (para escribir "Florianópolis")
   - Date picker de ida y vuelta
   - Botón "Buscar"
   - Cada resultado de vuelo (tarjeta, precio, aerolínea, etc.)
4. **Alternativamente**, interceptar los requests de red para ver si hay una API interna que podamos usar directo (sin necesidad de formulario)

Con esos selectores, el fix es reemplazar el diccionario `SELECTORS` en `turismo_city.py` y ajustar los métodos de interacción.
