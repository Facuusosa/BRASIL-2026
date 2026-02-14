# 🛫 Flight Price Monitor Bot - BUE → FLN

## 📋 Información del Proyecto

**Ruta:** Buenos Aires (AEP/EZE) → Florianópolis (FLN)  
**Fechas Principal:** 9 marzo 2026 (ida) - 16 marzo 2026 (vuelta)  
**Fechas Flexibles:** ±2 días (7-11 marzo / 14-18 marzo)  
**Pasajeros:** 2 adultos  
**Equipaje:** 20kg por persona (bodega)  
**Objetivo:** Monitorear precios 24/7 y recibir alertas inteligentes  
**Estado:** 🟡 En Desarrollo

---

## ⚠️ RESTRICCIONES CRÍTICAS

### 🚫 El bot NO puede:
- ❌ Comprar vuelos automáticamente (nunca, bajo ninguna circunstancia)
- ❌ Guardar datos de tarjetas de crédito o información de pago
- ❌ Hacer checkout o completar formularios de pago
- ❌ Tomar decisiones de compra sin autorización explícita del usuario
- ❌ Acceder a cuentas personales de aerolíneas o plataformas

### ✅ El bot SÍ puede:
- ✅ Monitorear precios automáticamente cada 6 horas
- ✅ Recopilar y almacenar histórico de precios en base de datos local
- ✅ Enviar notificaciones por Telegram cuando detecte ofertas
- ✅ Calcular "scores" de vuelos basados en precio/horario/aeropuerto
- ✅ Comparar múltiples plataformas simultáneamente
- ✅ Sugerir fechas alternativas si ahorran >$100.000 ARS
- ✅ Generar reportes diarios con análisis de tendencias

---

## 💰 Baseline de Precios (Research Manual + Perplexity)

### Precios Referenciales (2 personas, con equipaje 20kg):

| Aerolínea/Combo | Precio Total (ARS) | Precio USD* | Horarios | Observaciones |
|-----------------|-------------------|-------------|----------|---------------|
| 🏆 **Flybondi puro** | **$927.806** | ~$484 | 18:05-20:00 / 04:25-06:30 | Más económico, vuelta madrugada |
| Flybondi + JetSmart | $983.000 | ~$537 | 18:05-20:00 / 08:15-10:30 | Buen balance precio/horario |
| JetSmart puro | $1.190.000 | ~$700 | 12:15-14:20 / 08:15-10:30 | Horarios diurnos |
| GOL + Flybondi | $1.020.000 | ~$636 | Mix | Vuelos nocturnos |
| LATAM | $1.206.000+ | ~$750+ | Varios | Más confiable, más caro |
| Aerolíneas ARG | $1.197.000+ | ~$756+ | Varios | Premium pricing |

*USD aproximado al dólar blue/tarjeta ~$1.333 (Feb 2026)

### 🔥 Insight Crítico: Flexibilidad de Fechas
**Cambiar 1 día las fechas ahorra ~$128.000 ARS:**
- Salir **martes 10** en vez de lunes 9: ahorro $86.000
- Volver **martes 17** en vez de lunes 16: ahorro $42.000

**El bot DEBE monitorear fechas adyacentes y sugerirlas si el ahorro es significativo.**

---

## 🎯 Criterios de Búsqueda

### Aerolíneas a Monitorear (por prioridad):
1. 🔴 **Flybondi** - Prioridad CRÍTICA (la más barata)
2. 🔴 **JetSmart** - Prioridad CRÍTICA (buen balance)
3. 🟡 **GOL** - Prioridad MEDIA (opciones nocturnas)
4. 🟢 **Aerolíneas Argentinas** - Prioridad BAJA (más cara, más confiable)
5. 🟢 **LATAM** - Prioridad BAJA (generalmente más cara)

### Plataformas a Scrapear (por prioridad):
1. 🔴 **Turismo City** - Prioridad CRÍTICA (USD $484-537 detectados)
2. 🔴 **Despegar** - Prioridad CRÍTICA (USD $700-767 detectados)
3. 🟡 **eDreams** - Prioridad MEDIA (apareció en agregadores)
4. 🟡 **Kayak Argentina** - Prioridad MEDIA (validación)
5. 🟢 **Google Flights** - Prioridad BAJA (como referencia)
6. ⚪ **Webs directas** - Prioridad BAJA (JetSmart no funciona en incógnito)

### ⚠️ Nota Técnica Importante:
- **JetSmart.com NO funciona en modo incógnito** → requiere sesión normal con cookies
- **Flybondi** funciona perfectamente en incógnito
- Los **metabuscadores son consistentemente más baratos** que webs directas

---

## 📊 Datos a Extraer por Cada Vuelo

### Información Esencial:
- ✈️ **Aerolínea** (Flybondi, JetSmart, GOL, etc.)
- 💰 **Precio TOTAL** (ARS con equipaje incluido)
- 💵 **Precio USD** (si disponible)
- 🕐 **Horario salida** (formato HH:MM)
- 🕐 **Horario llegada** (formato HH:MM)
- ⏱️ **Duración total** (en minutos)
- 🔄 **Tipo** (directo / 1 escala / 2+ escalas)
- 🛫 **Aeropuerto origen** (AEP / EZE)
- 🛬 **Aeropuerto destino** (FLN)

### Información Complementaria:
- 🌐 **Plataforma** (Turismo City, Despegar, etc.)
- 📅 **Fecha búsqueda** (timestamp ISO 8601)
- 📅 **Fecha vuelo ida** (9 marzo o ±2 días)
- 📅 **Fecha vuelo vuelta** (16 marzo o ±2 días)
- 🔢 **Disponibilidad** (ej: "Últimos 6 asientos")
- 💼 **Equipaje** (incluido/no incluido/detalles)
- 🪑 **Asiento** (incluido/selección extra)
- 🎫 **Código vuelo** (si disponible)

### Flags Especiales:
- ⚠️ **aeropuertos_distintos** (Boolean): TRUE si AEP→FLN pero FLN→EZE
- 🌙 **horario_nocturno** (Boolean): TRUE si salida/llegada entre 22:00-06:00
- 🔥 **poca_disponibilidad** (Boolean): TRUE si "últimos X asientos" con X < 10
- ⏰ **cambio_dia** (Boolean): TRUE si el vuelo llega al día siguiente

---

## 🚨 Sistema de Alertas Inteligente

### Niveles de Prioridad:

#### 🔴 ALERTA CRÍTICA (Telegram + sonido):
1. **Precio < $850.000 ARS** (por debajo del baseline Flybondi)
2. **Precio < USD $450** (si está en dólares)
3. **Disponibilidad crítica** ("Últimos 3 asientos" o menos)
4. **Caída brusca de precio** (>15% en menos de 24hs)

#### 🟡 ALERTA IMPORTANTE (Telegram silencioso):
1. **Precio < $950.000 ARS** con horarios decentes (8am-10pm)
2. **Nuevo vuelo directo** que antes no existía
3. **Ahorro por flexibilidad** (>$100k cambiando 1 día de fecha)
4. **Mismo aeropuerto** (AEP-AEP o EZE-EZE) a buen precio

#### 🟢 ALERTA INFORMATIVA (solo log):
1. Precio estable (sin cambios significativos)
2. Nueva aerolínea disponible
3. Cambios menores en horarios

### Formato de Notificación Telegram:

```
🔴 ALERTA CRÍTICA - PRECIO BAJO DETECTADO

💰 Precio: $845.000 ARS ($100k menos que promedio)
✈️ Aerolínea: Flybondi + JetSmart
📅 Fechas: 9-16 marzo 2026
🕐 Horarios: 18:05-20:00 / 08:15-10:30
🛫 Aeropuertos: EZE → FLN → EZE (mismo)
🌐 Plataforma: Turismo City
⏱️ Duración: 1h55 ida / 2h15 vuelta
💼 Equipaje: 20kg incluido

🎯 Score: 92/100 (excelente relación precio/horario)

🔗 [Ver en Turismo City](link)

⚠️ Última actualización: hace 5 minutos
```

---

## 🧮 Sistema de Scoring (Calidad-Precio)

Cada vuelo recibe un score de 0-100 basado en:

### Fórmula de Score:
```python
Score = (
    peso_precio * (1000 - precio_usd) / 10 +  # 50% del peso
    peso_horario * multiplicador_horario +      # 30% del peso
    peso_aeropuerto * multiplicador_aeropuerto + # 10% del peso
    peso_duracion * multiplicador_duracion       # 10% del peso
)

# Multiplicadores de Horario:
- Horario ideal (8am-8pm salida/llegada): 1.0
- Horario aceptable (6am-10pm): 0.85
- Horario nocturno (10pm-6am): 0.6
- Horario madrugada (12am-5am): 0.4

# Multiplicadores de Aeropuerto:
- Mismo aeropuerto (AEP-AEP o EZE-EZE): 1.0
- Aeropuertos mixtos: 0.85

# Multiplicadores de Duración:
- Vuelo directo: 1.0
- 1 escala (<4hs espera): 0.7
- 2+ escalas o >6hs espera: 0.4
```

---

## 🛠️ Stack Técnico

### Lenguaje y Framework:
- **Python 3.11+** (lenguaje principal)
- **Playwright** (automatización de navegador)
- **playwright-stealth** (anti-detección de bots)

### Base de Datos:
- **SQLite** (histórico de precios, vuelos encontrados)
- Tablas: `flights`, `price_history`, `alerts_sent`

### Notificaciones:
- **Telegram Bot API** (alertas en tiempo real)
- **Python-telegram-bot** library

### Gestión de Sesiones:
- **Rotación de User-Agents** (simular dispositivos diferentes)
- **Delays aleatorios** (5-15 segundos entre requests)
- **Modo headless** (sin abrir ventanas de navegador)
- **Incógnito forzado** (sesiones limpias en cada ejecución)

### Anti-Detección:
- `playwright-stealth` (ocultar automatización)
- Headers personalizados (Accept-Language, Referer, etc.)
- Cookies management (limpiar entre búsquedas)

### Opcional (Fase 2):
- **Proxies rotativos** (si detectan IP)
- **VPN integration** (via CLI: Mullvad, ProtonVPN)

---

## ⏰ Configuración de Ejecución

### Frecuencia de Monitoreo:
- **Cada 6 horas** (4 búsquedas diarias)
- Horarios: **06:00, 12:00, 18:00, 00:00** (hora Argentina)

### Estrategia de Búsqueda:
Cada ciclo ejecuta:
1. Turismo City (fecha principal)
2. Turismo City (fechas ±1 día)
3. Despegar (fecha principal)
4. Despegar (fechas ±1 día si hay tiempo)

**Total:** ~8-12 búsquedas por ciclo

### Modo de Ejecución:
- **Desarrollo:** Manual (ejecutar `python main.py`)
- **Producción:** Cron job o systemd timer
- **Cloud (opcional):** DigitalOcean Droplet / AWS EC2

---

## 📁 Estructura del Proyecto

```
flight-monitor-bot/
│
├── README.md                  # Este archivo (documentación principal)
├── requirements.txt           # Dependencias Python
├── .env.example              # Plantilla de variables de entorno
├── .gitignore                # Archivos a ignorar en Git
│
├── docs/                     # Documentación del proyecto
│   ├── 01-research.md        # Research manual (datos recopilados)
│   ├── 02-architecture.md    # Arquitectura técnica
│   ├── 03-scraping-guide.md  # Guía de scraping por plataforma
│   ├── 04-ai-prompts.md      # Prompts para IA (Gemini/Claude)
│   └── 05-deployment.md      # Guía de deploy
│
├── src/                      # Código fuente
│   ├── __init__.py
│   ├── main.py               # Punto de entrada principal
│   ├── config.py             # Configuración general
│   ├── scrapers/             # Scrapers por plataforma
│   │   ├── __init__.py
│   │   ├── base_scraper.py   # Clase base abstracta
│   │   ├── turismo_city.py   # Scraper Turismo City
│   │   ├── despegar.py       # Scraper Despegar
│   │   └── utils.py          # Utilidades de scraping
│   ├── database/             # Gestión de base de datos
│   │   ├── __init__.py
│   │   ├── models.py         # Modelos de datos (SQLAlchemy)
│   │   └── db_manager.py     # CRUD operations
│   ├── notifier/             # Sistema de notificaciones
│   │   ├── __init__.py
│   │   └── telegram_bot.py   # Bot de Telegram
│   ├── analyzer/             # Análisis de precios
│   │   ├── __init__.py
│   │   ├── scorer.py         # Sistema de scoring
│   │   └── trends.py         # Análisis de tendencias
│   └── utils/                # Utilidades generales
│       ├── __init__.py
│       ├── logger.py         # Logging
│       └── helpers.py        # Funciones auxiliares
│
├── data/                     # Datos del bot
│   ├── flights.db            # Base de datos SQLite
│   ├── logs/                 # Logs de ejecución
│   │   └── bot.log
│   └── cache/                # Cache temporal
│
└── tests/                    # Tests unitarios
    ├── __init__.py
    ├── test_scrapers.py
    ├── test_scorer.py
    └── test_notifier.py
```

---

## 🔐 Variables de Entorno (.env)

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# Configuración de Búsqueda
DEPARTURE_DATE=2026-03-09
RETURN_DATE=2026-03-16
PASSENGERS=2
LUGGAGE_KG=20

# Umbrales de Alerta
CRITICAL_PRICE_ARS=850000
IMPORTANT_PRICE_ARS=950000
CRITICAL_PRICE_USD=450
IMPORTANT_PRICE_USD=550

# Configuración de Scraping
HEADLESS_MODE=true
STEALTH_MODE=true
RANDOM_DELAY_MIN=5
RANDOM_DELAY_MAX=15

# VPN (Opcional - Fase 2)
VPN_ENABLED=false
VPN_COUNTRY=BR

# Logging
LOG_LEVEL=INFO
LOG_FILE=data/logs/bot.log
```

---

## 🚀 Instalación y Uso

### Requisitos Previos:
- Python 3.11 o superior
- pip (gestor de paquetes Python)
- Cuenta de Telegram + Bot Token

### Instalación:

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/flight-monitor-bot.git
cd flight-monitor-bot

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar Playwright browsers
playwright install chromium

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus datos

# 6. Inicializar base de datos
python src/database/db_manager.py --init

# 7. Ejecutar primera búsqueda (test)
python src/main.py --test
```

### Uso:

```bash
# Ejecutar una vez (modo manual)
python src/main.py

# Ejecutar en modo continuo (cada 6 horas)
python src/main.py --daemon

# Ejecutar solo análisis de datos existentes
python src/main.py --analyze-only

# Ver histórico de precios
python src/main.py --report

# Modo debug (verbose logging)
python src/main.py --debug
```

---

## 📅 Roadmap de Desarrollo

### ✅ Fase 0: Research & Planificación (COMPLETADO)
- [x] Investigación manual de precios
- [x] Validación con Perplexity
- [x] Definición de arquitectura
- [x] Creación de README

### 🟡 Fase 1: MVP Básico (EN PROGRESO)
- [ ] Scraper de Turismo City (fecha fija)
- [ ] Base de datos SQLite simple
- [ ] Sistema de notificaciones Telegram
- [ ] Ejecución manual

### 🔵 Fase 2: Scraping Avanzado
- [ ] Scraper de Despegar
- [ ] Scraper de eDreams
- [ ] Soporte de fechas flexibles (±2 días)
- [ ] Sistema de scoring de vuelos

### 🟣 Fase 3: Automatización
- [ ] Cron job / systemd timer
- [ ] Análisis de tendencias de precios
- [ ] Reportes diarios automáticos
- [ ] Logs y monitoreo

### 🟠 Fase 4: Features Avanzados (Opcional)
- [ ] Integración con VPN
- [ ] Proxies rotativos
- [ ] Scraping de Google Flights
- [ ] Dashboard web (Flask/FastAPI)
- [ ] Deploy en cloud (DigitalOcean/AWS)

---

## 📝 Notas Técnicas Importantes

### Anti-Detección:
- ⚠️ **JetSmart bloquea modo incógnito** → usar sesión normal con limpieza de cookies
- ✅ **Flybondi funciona perfecto en incógnito**
- ✅ **Metabuscadores (Turismo City, Despegar) funcionan en incógnito**

### Rate Limiting:
- No hacer más de 1 búsqueda por minuto en la misma plataforma
- Usar delays aleatorios (5-15 seg) entre requests
- Si detectan bot → esperar 30 min antes de reintentar

### Mantenimiento:
- Los selectores CSS/XPath de las webs pueden cambiar
- Revisar logs semanalmente para detectar errores de scraping
- Actualizar scrapers si cambian los diseños de las páginas

---

## 🤝 Contribuciones

Este es un proyecto personal, pero si querés sugerir mejoras:

1. Fork del repositorio
2. Crear branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## 📄 Licencia

MIT License - Uso personal y educativo

---

## 📞 Contacto / Soporte

- **Telegram:** @tu_usuario (para notificaciones del bot)
- **Email:** tu_email@example.com
- **Issues:** GitHub Issues

---

## 🎯 Objetivos Finales

1. **Ahorrar >$100.000 ARS** encontrando el mejor momento de compra
2. **Reducir estrés** monitoreando 24/7 sin intervención manual
3. **Aprender** sobre web scraping, automation y análisis de datos
4. **Viajar a Floripa** con la tranquilidad de haber conseguido el mejor precio 🏖️

---

**Última actualización:** 12 febrero 2026  
**Versión:** 0.1.0 (Pre-Alpha)
