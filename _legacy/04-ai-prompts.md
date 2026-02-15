# 🤖 Prompts para IA - Flight Monitor Bot

Este documento contiene los prompts optimizados para que Gemini (o Claude) genere el código del bot de monitoreo de vuelos.

---

## 📋 Contexto Previo

Antes de usar estos prompts, asegurate de que la IA tenga acceso a:
1. `README.md` completo
2. `docs/01-research.md` (datos de investigación)
3. `requirements.txt`
4. `.env.example`

---

## 🎯 PROMPT MAESTRO - Para Generar el Bot Completo

```
Rol: Sos un Senior Python Developer especializado en web scraping ético y automatización de tareas.

Contexto: Necesito crear un bot de monitoreo de precios de vuelos para Buenos Aires → Florianópolis (9-16 marzo 2026, 2 personas). Ya hice investigación manual y tengo datos baseline (adjuntos en README.md y docs/01-research.md).

Misión: Crear un sistema de monitoreo automático que:
1. Scrapee precios de vuelos en Turismo City y Despegar
2. Almacene histórico en SQLite
3. Envíe alertas por Telegram cuando detecte ofertas
4. Calcule scores de "calidad-precio" para cada vuelo
5. Sugiera fechas alternativas si ahorran >$100k ARS

RESTRICCIONES OBLIGATORIAS:
❌ NO implementar funcionalidad de compra (ni siquiera como código comentado)
❌ NO guardar datos de tarjetas o información de pago
❌ NO hacer checkout en ninguna plataforma
✅ SOLO monitorear y notificar

REQUISITOS TÉCNICOS:
- Python 3.11+
- Playwright con playwright-stealth (anti-detección)
- Modo incógnito para Turismo City y Despegar
- Sesión normal con limpieza de cookies para JetSmart (si se implementa)
- Delays aleatorios 5-15 seg entre requests
- Logs detallados de TODO (errores, precios encontrados, timestamps)
- Respetar robots.txt

ESTRUCTURA DEL PROYECTO:
Usar la estructura definida en README.md:
```
flight-monitor-bot/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── scrapers/
│   │   ├── base_scraper.py
│   │   ├── turismo_city.py
│   │   └── despegar.py
│   ├── database/
│   │   ├── models.py
│   │   └── db_manager.py
│   ├── notifier/
│   │   └── telegram_bot.py
│   └── analyzer/
│       └── scorer.py
├── data/
│   └── flights.db
└── tests/
```

ENTREGABLES:
1. Código comentado línea por línea (en español)
2. Instrucciones de instalación paso a paso
3. Ejemplo de output esperado
4. Guía de troubleshooting para errores comunes

IMPORTANTE:
- NO asumas nada que no esté en el README o research
- Si algo no está claro, preguntame ANTES de implementar
- Prioriza CALIDAD sobre velocidad
- El código debe ser mantenible y extensible

¿Entendido? Comenzá con la arquitectura de alto nivel y el archivo main.py.
```

---

## 🎯 PROMPT ESPECÍFICO #1 - Scraper de Turismo City

```
Tarea: Crear el scraper para Turismo City (turismocity.com)

Contexto previo:
- La investigación manual mostró que Turismo City tiene los precios más bajos
- Funciona perfectamente en modo incógnito
- Precios vienen en USD con equipaje incluido
- Formato de URL: https://www.turismocity.com.ar/vuelos/...

Datos de ejemplo de Turismo City (ver docs/01-research.md):
- Flybondi x2: USD $484 (2 personas con equipaje)
- Flybondi + JetSmart: USD $537

Requisitos del scraper:

1. NAVEGACIÓN:
   - Usar Playwright con stealth mode
   - Modo incógnito obligatorio
   - User-Agent: Chrome Desktop (Windows)
   - Timeout: 30 segundos por página

2. PROCESO DE BÚSQUEDA:
   a) Navegar a turismocity.com.ar
   b) Ingresar origen: "Buenos Aires (AEP/EZE)" (permitir ambos)
   c) Ingresar destino: "Florianópolis (FLN)"
   d) Fecha ida: 9 marzo 2026 (parametrizable con ±2 días)
   e) Fecha vuelta: 16 marzo 2026 (parametrizable con ±2 días)
   f) Pasajeros: 2 adultos
   g) Hacer clic en "Buscar"
   h) Esperar resultados (puede tardar 10-20 seg)

3. EXTRACCIÓN DE DATOS:
   Para cada resultado, extraer:
   - Aerolíneas (nombre completo)
   - Precio total USD (2 personas)
   - Horarios ida (salida-llegada)
   - Horarios vuelta (salida-llegada)
   - Tipo (directo/escala)
   - Aeropuertos (AEP/EZE para ida, FLN-AEP/EZE para vuelta)
   - Disponibilidad si lo muestra ("Últimos X asientos")

4. MANEJO DE ERRORES:
   - Si la página no carga en 30seg → reintentar 1 vez → logear error
   - Si no hay resultados → logear y retornar lista vacía
   - Si el selector CSS cambió → logear warning y tomar screenshot

5. OUTPUT:
   Retornar lista de diccionarios:
   ```python
   [
       {
           "platform": "Turismo City",
           "airlines": ["Flybondi", "JetSmart"],
           "price_usd": 537,
           "price_ars": None,  # calcular después
           "outbound_departure": "2026-03-09 00:40",
           "outbound_arrival": "2026-03-09 02:35",
           "return_departure": "2026-03-16 19:45",
           "return_arrival": "2026-03-16 22:00",
           "flight_type": "direct",
           "origin_airport": "AEP",
           "destination_airport": "FLN",
           "return_airport": "EZE",
           "availability": None,
           "luggage_included": True,
           "search_timestamp": "2026-02-12T15:30:00Z",
           "url": "https://turismocity.com/..."
       },
       ...
   ]
   ```

ENTREGABLE:
- Archivo src/scrapers/turismo_city.py
- Clase TurismoCityScraper que hereda de BaseScraper
- Método search(origin, destination, date_out, date_return, passengers)
- Tests unitarios básicos
- Documentación de selectores CSS usados

NO implementes la lógica de Despegar todavía, solo Turismo City.
```

---

## 🎯 PROMPT ESPECÍFICO #2 - Sistema de Scoring

```
Tarea: Crear el sistema de scoring para rankear vuelos por "calidad-precio"

El score debe ser un número de 0-100 que refleje qué tan "bueno" es un vuelo considerando:
- Precio (50% del peso)
- Horarios (30% del peso)
- Aeropuertos (10% del peso)
- Duración/escalas (10% del peso)

Fórmula propuesta (ajustable):

```python
def calculate_score(flight: dict) -> float:
    """
    Calcula score 0-100 para un vuelo.
    
    Factores:
    - Precio: Mientras más bajo, mejor
    - Horario: Preferir 8am-10pm sobre madrugada
    - Aeropuerto: Preferir mismo aeropuerto ida/vuelta
    - Duración: Preferir directo sobre escalas
    
    Returns:
        float: Score entre 0-100
    """
    
    # 1. SCORE DE PRECIO (50 puntos máximo)
    baseline_usd = 484  # Precio baseline Flybondi (research)
    critical_usd = 450  # Precio crítico
    max_acceptable_usd = 800  # Precio máximo aceptable
    
    price = flight.get("price_usd", 999)
    
    if price <= critical_usd:
        price_score = 50
    elif price <= baseline_usd:
        price_score = 45
    elif price <= max_acceptable_usd:
        # Interpolación lineal
        price_score = 50 - ((price - baseline_usd) / (max_acceptable_usd - baseline_usd)) * 50
    else:
        price_score = 0
    
    # 2. SCORE DE HORARIO (30 puntos máximo)
    # ... implementar lógica de horarios
    
    # 3. SCORE DE AEROPUERTO (10 puntos máximo)
    # ... implementar lógica de aeropuertos
    
    # 4. SCORE DE DURACIÓN (10 puntos máximo)
    # ... implementar lógica de duración
    
    total_score = price_score + horario_score + aeropuerto_score + duracion_score
    
    return round(total_score, 2)
```

Requisitos:
1. Crear clase FlightScorer en src/analyzer/scorer.py
2. Método calculate_score(flight: dict) -> float
3. Método explain_score(flight: dict) -> dict con desglose
4. Tests con casos edge (precio $0, precio $10000, etc.)

ENTREGABLE:
- src/analyzer/scorer.py completo
- Documentación de la lógica de scoring
- Ejemplos de scores para los vuelos del research
```

---

## 🎯 PROMPT ESPECÍFICO #3 - Sistema de Notificaciones Telegram

```
Tarea: Implementar el bot de Telegram para enviar alertas

Requisitos:

1. CONFIGURACIÓN:
   - Usar python-telegram-bot library
   - Leer TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID desde .env
   - Manejar reconexiones automáticas

2. TIPOS DE ALERTAS:

   a) ALERTA CRÍTICA (con sonido):
      - Precio < USD $450
      - Disponibilidad "Últimos 3 asientos"
      - Caída de precio >15% en <24hs
   
   b) ALERTA IMPORTANTE (silenciosa):
      - Precio < USD $550
      - Ahorro >$100k cambiando fechas
      - Nuevo vuelo directo
   
   c) REPORTE DIARIO:
      - Resumen de precios del día
      - Tendencias (subiendo/bajando)
      - Próxima búsqueda programada

3. FORMATO DE MENSAJE:

```
🔴 ALERTA CRÍTICA - PRECIO BAJO

💰 Precio: USD $484 (2 personas)
📍 $160.884 menos que ayer

✈️ Aerolíneas: Flybondi x2
📅 Fechas: 9-16 marzo 2026
🕐 Salida: 00:40 AEP → 02:35 FLN
🕐 Regreso: 04:25 FLN → 06:30 AEP
⏱️ Duración: 1h55 ida / 2h05 vuelta
💼 Equipaje: 20kg incluido

🎯 Score: 95/100
⚠️ Horarios de madrugada

🔗 Ver en Turismo City
https://turismocity.com/...

Última actualización: hace 3 minutos
```

4. COMANDOS DEL BOT:

   /start - Info del bot
   /status - Estado actual del monitoreo
   /lastprice - Último precio encontrado
   /history - Histórico últimas 24hs
   /stop - Pausar alertas
   /resume - Reanudar alertas

ENTREGABLE:
- src/notifier/telegram_bot.py
- Clase TelegramNotifier
- Métodos send_critical_alert(), send_important_alert(), send_daily_report()
- Manejo de errores de API Telegram
- Tests (mockear API de Telegram)
```

---

## 🎯 PROMPT ESPECÍFICO #4 - Base de Datos

```
Tarea: Diseñar e implementar la base de datos SQLite para almacenar vuelos y alertas

TABLAS NECESARIAS:

1. flights (vuelos encontrados):
   - id (PK)
   - platform (Turismo City, Despegar, etc.)
   - airlines (JSON: ["Flybondi", "JetSmart"])
   - price_usd (REAL)
   - price_ars (REAL, nullable)
   - outbound_departure (DATETIME)
   - outbound_arrival (DATETIME)
   - return_departure (DATETIME)
   - return_arrival (DATETIME)
   - flight_type (directo/escala)
   - origin_airport (AEP/EZE)
   - destination_airport (FLN)
   - return_airport (AEP/EZE)
   - duration_minutes (INTEGER)
   - availability (TEXT, nullable)
   - luggage_included (BOOLEAN)
   - score (REAL, calculado)
   - url (TEXT)
   - search_timestamp (DATETIME)
   - created_at (DATETIME)

2. price_history (histórico):
   - id (PK)
   - flight_id (FK → flights.id)
   - price_usd (REAL)
   - timestamp (DATETIME)

3. alerts_sent (alertas enviadas):
   - id (PK)
   - flight_id (FK → flights.id)
   - alert_type (critical/important/info)
   - sent_at (DATETIME)
   - telegram_message_id (INTEGER, nullable)

REQUISITOS:
- Usar SQLAlchemy ORM
- Modelos en src/database/models.py
- CRUD operations en src/database/db_manager.py
- Método para limpiar registros >30 días
- Índices en: platform, search_timestamp, price_usd

ENTREGABLE:
- src/database/models.py (modelos SQLAlchemy)
- src/database/db_manager.py (clase DatabaseManager)
- Script de inicialización create_db.py
- Queries de ejemplo en comentarios
```

---

## 🎯 PROMPT ESPECÍFICO #5 - Main.py (Orquestador)

```
Tarea: Crear el archivo main.py que orquesta todo el flujo del bot

FLUJO PRINCIPAL:

1. Cargar configuración desde .env
2. Inicializar base de datos
3. Inicializar notificador de Telegram
4. Loop de monitoreo:
   a) Para cada plataforma (Turismo City, Despegar):
      - Para fecha principal (9-16 marzo):
        * Ejecutar scraper
        * Calcular score de cada vuelo
        * Guardar en BD
      - Para fechas flexibles (±1 día):
        * Ejecutar scraper
        * Comparar si ahorra >$100k
   b) Analizar resultados:
      - Detectar nuevos vuelos baratos
      - Detectar caídas de precio
      - Calcular tendencias
   c) Enviar alertas según triggers
   d) Esperar hasta próxima ejecución (6 horas)

MODOS DE EJECUCIÓN:

```bash
# Ejecutar una vez (test)
python src/main.py --test

# Ejecutar en modo daemon (cada 6 horas)
python src/main.py --daemon

# Solo analizar datos existentes
python src/main.py --analyze-only

# Generar reporte
python src/main.py --report
```

MANEJO DE ERRORES:
- Si un scraper falla → logear y continuar con el siguiente
- Si la BD está corrupta → intentar reparar o recrear
- Si Telegram falla → guardar alertas pendientes y reintentar
- Si hay crash total → enviar error por Telegram y reiniciar

LOGGING:
- Nivel INFO: Búsquedas exitosas, alertas enviadas
- Nivel WARNING: Scrapers fallidos, precios inusuales
- Nivel ERROR: Crashes, BD corrupta, API errors
- Guardar en data/logs/bot.log (rotación cada 10MB)

ENTREGABLE:
- src/main.py completo
- src/config.py con carga de .env
- src/utils/logger.py para logging
- Documentación de comandos CLI
```

---

## 🧪 PROMPT DE TESTING

```
Tarea: Crear suite de tests para el bot

Tests necesarios:

1. test_scrapers.py:
   - Test de conexión a Turismo City
   - Test de parsing de resultados
   - Test de manejo de errores (timeout, no results)
   - Test de modo incógnito

2. test_scorer.py:
   - Test de scoring con vuelos baratos ($400)
   - Test de scoring con vuelos caros ($900)
   - Test de scoring con horarios buenos vs malos
   - Test de edge cases (precio $0, precio null)

3. test_notifier.py:
   - Test de envío de alerta (mock Telegram API)
   - Test de formateo de mensajes
   - Test de manejo de errores de API

4. test_database.py:
   - Test de insert/select/update/delete
   - Test de queries complejas
   - Test de limpieza de registros viejos

Usar pytest + pytest-asyncio para tests async.

ENTREGABLE:
- tests/ completo
- requirements-dev.txt (con pytest, etc.)
- GitHub Actions workflow para CI (opcional)
```

---

## 📝 NOTAS PARA LA IA

### Cuando uses estos prompts:

1. **NO asumas tecnologías no mencionadas**
   - Si no está en requirements.txt, no lo uses

2. **Pregunta antes de agregar features extra**
   - El scope está definido en README.md
   - No agregues VPN, proxies, dashboard web, etc. sin consultar

3. **Prioriza código mantenible**
   - Comentarios en español
   - Nombres de variables descriptivos
   - Funciones pequeñas y cohesivas

4. **Sigue el principio DRY (Don't Repeat Yourself)**
   - Crea funciones auxiliares para código repetido
   - Usa herencia cuando tiene sentido (BaseScr aper)

5. **Manejo de errores exhaustivo**
   - Try/except en TODO acceso a red
   - Logs detallados de errores
   - Graceful degradation (si algo falla, el resto sigue)

---

## ✅ Checklist Final

Antes de considerar el bot "completo", verificar:

- [ ] Scrapers funcionan para Turismo City y Despegar
- [ ] Base de datos guarda vuelos correctamente
- [ ] Sistema de scoring rankea vuelos como esperado
- [ ] Notificaciones de Telegram llegan sin errores
- [ ] Logs se generan en data/logs/
- [ ] Tests pasan (al menos >80% cobertura)
- [ ] Documentación está actualizada
- [ ] .env.example tiene todas las variables necesarias
- [ ] El bot NO puede comprar vuelos (restricción crítica)

---

**Estos prompts están diseñados para ser usados secuencialmente:**
1. PROMPT MAESTRO (arquitectura general)
2. PROMPT #1 (Scraper Turismo City)
3. PROMPT #4 (Base de Datos)
4. PROMPT #2 (Sistema de Scoring)
5. PROMPT #3 (Notificaciones Telegram)
6. PROMPT #5 (Main.py orquestador)
7. PROMPT DE TESTING

**Tiempo estimado de desarrollo:** 2-4 días con IA asistiendo
