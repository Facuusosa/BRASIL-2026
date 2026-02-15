# 🤖 Flybondi Smart Monitor

Este repositorio ha sido vitaminado con nuevas herramientas de monitoreo avanzado para detectar oportunidades de ahorro, errores de precio (glitches) y cambios ocultos en la plataforma de Flybondi.

---

## 🚀 Nuevos Módulos de Automatización

Todos los scripts se encuentran en la carpeta `src/` y pueden ejecutarse individualmente o a través del orquestador `smart_monitor.py`.

### 1. 🛫 Monitor de Precios (`monitor_flybondi.py`)
El script original, optimizado. Busca precios para marzo 2026.
- **Ejecución:** `python monitor_flybondi.py`
- **Output:** Consola + HTML Report + Alerta Telegram si el precio es bueno.

### 2. 🔬 Feature Flag Monitor (`src/feature_flag_monitor.py`)
Monitorea los experimentos y "flags" de Flybondi para detectar nuevas funcionalidades, promos ocultas o cambios en la lógica de precios (ej: `enable_usd_payment`, `enable_discount`).
- **Frecuencia ideal:** Cada 1 hora.
- **Alerta:** Si aparece una flag nueva o cambia de valor.

### 3. 🔍 Fare Glitch Detector (`src/fare_glitch_detector.py`)
Analiza *todas* las tarifas de cada vuelo buscando anomalías matemáticas:
- **Inversión Tarifaria:** Cuando la clase "Premium" o "Plus" es más barata que la "Economy".
- **Precios $0 o Negativos.**
- **Promos activas** que no se están aplicando correctamente.
- **Alerta:** Inmediata por Telegram si encuentra algo raro.

### 4. 🧪 Edge Case Tester (`src/edge_case_tester.py`)
Envía peticiones "locas" a la API una vez por día para ver si se rompe o revela precios ocultos:
- 0 adultos, fechas pasadas, rutas invertidas.
- Monedas extrañas (USD, BRL, EUR).
- PromoCodes de prueba (`ADMIN`, `TEST`, `CARNAVAL`).
- **Alerta:** Si la API devuelve un precio válido para una petición que debería fallar.

### 5. 📄 Source Analyzer (`src/source_analyzer.py`)
Descarga el código fuente de Flybondi y busca pistas dejadas por los desarrolladores:
- Comentarios HTML (`<!-- TODO: fix price logic -->`).
- Variables globales oculta (`window.DEBUG_MODE`).
- Endpoints de API internos.

---

## 🤖 Orquestador Inteligente (`smart_monitor.py`)

Para no tener que ejecutar 5 scripts por separado, usa el orquestador. Se encarga de correr todo en los intervalos óptimos.

### Modo Manual (una pasada)
Ejecuta todos los chequeos una sola vez y termina.
```bash
python smart_monitor.py
```

### Modo Daemon (Background)
Se queda corriendo indefinidamente y ejecuta cada módulo según su cronograma (Precios cada 1h, Glitches cada 1h, Source cada 6h, etc.).
```bash
python smart_monitor.py --daemon
```
**Tip:** Dejá esta ventana abierta o usá `pythonw` para correrlo en background total.

### Ejecutar solo un módulo
```bash
python smart_monitor.py --module flags    # Solo feature flags
python smart_monitor.py --module glitch   # Solo glitches
python smart_monitor.py --module edge     # Solo edge cases
```

---

## 📁 Estructura de Datos
Todos los logs y resultados se guardan en la carpeta `data/`:
- `data/flybondi_logs/`: Historial de precios y reportes HTML.
- `data/feature_flags/`: Cambios detectados en flags.
- `data/glitch_logs/`: Anomalías de precio encontradas.
- `data/edge_cases/`: Resultados de experimentos de API.
- `data/source_analysis/`: Hallazgos en el código fuente.

## ⚠️ Nota Importante
Estas herramientas usan la API pública de Flybondi pero hacen peticiones que un usuario normal no haría.
- El `smart_monitor.py` tiene pausas inteligentes para no saturar la API.
- Si ves errores HTTP 400 continuos, es probable que tu cookie de sesión haya expirado. Actualizala en el archivo `.env`.

¡Buena caza de ofertas! ✈️
