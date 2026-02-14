"""
config.py - Configuración general del Flight Monitor Bot

Carga las variables de entorno desde el archivo .env y define las constantes
de configuración que usan todos los módulos del proyecto.

RESTRICCIÓN: Este bot SOLO monitorea precios, NUNCA compra vuelos.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ============================================================================
# RUTAS DEL PROYECTO
# ============================================================================

# Directorio raíz del proyecto (un nivel arriba de src/)
PROJECT_ROOT = Path(__file__).parent.parent

# Directorio de datos (base de datos, logs, cache)
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Cargar variables de entorno desde .env
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)

# ============================================================================
# CONFIGURACIÓN DE TELEGRAM
# ============================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ============================================================================
# CONFIGURACIÓN DE BÚSQUEDA DE VUELOS
# ============================================================================

# Fechas del viaje (principal)
DEPARTURE_DATE = os.getenv("DEPARTURE_DATE", "2026-03-09")
RETURN_DATE = os.getenv("RETURN_DATE", "2026-03-16")

# Pasajeros y equipaje
PASSENGERS = int(os.getenv("PASSENGERS", "2"))
LUGGAGE_KG = int(os.getenv("LUGGAGE_KG", "20"))

# Ruta del viaje
ORIGIN_CITY = "Buenos Aires"
ORIGIN_AIRPORTS = ["AEP", "EZE"]  # Aeroparque y Ezeiza
DESTINATION_CITY = "Florianópolis"
DESTINATION_AIRPORT = "FLN"

# Flexibilidad de fechas (±X días para buscar fechas alternativas)
DATE_FLEXIBILITY_DAYS = int(os.getenv("DATE_FLEXIBILITY_DAYS", "2"))

# ============================================================================
# UMBRALES DE ALERTA (en pesos argentinos y USD)
# ============================================================================

# --- ALERTA CRÍTICA 🔴 ---
# Precio por debajo del cual se dispara alerta máxima
CRITICAL_PRICE_ARS = int(os.getenv("CRITICAL_PRICE_ARS", "850000"))
CRITICAL_PRICE_USD = int(os.getenv("CRITICAL_PRICE_USD", "450"))

# --- ALERTA IMPORTANTE 🟡 ---
# Precio por debajo del cual se notifica (silencioso)
IMPORTANT_PRICE_ARS = int(os.getenv("IMPORTANT_PRICE_ARS", "950000"))
IMPORTANT_PRICE_USD = int(os.getenv("IMPORTANT_PRICE_USD", "550"))

# --- OTROS UMBRALES ---
# Caída de precio que dispara alerta (en porcentaje)
PRICE_DROP_THRESHOLD_PERCENT = float(os.getenv("PRICE_DROP_THRESHOLD_PERCENT", "15"))

# Ahorro mínimo por cambio de fecha para sugerir fecha alternativa (en ARS)
MIN_SAVINGS_FOR_SUGGESTION_ARS = int(os.getenv("MIN_SAVINGS_FOR_SUGGESTION_ARS", "100000"))

# Disponibilidad crítica (últimos X asientos)
CRITICAL_AVAILABILITY_THRESHOLD = int(os.getenv("CRITICAL_AVAILABILITY_THRESHOLD", "3"))

# ============================================================================
# CONFIGURACIÓN DE SCRAPING
# ============================================================================

# Modo headless (sin ventana de navegador visible)
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"

# Modo stealth (anti-detección de bots)
STEALTH_MODE = os.getenv("STEALTH_MODE", "true").lower() == "true"

# Delays aleatorios entre requests (en segundos)
RANDOM_DELAY_MIN = int(os.getenv("RANDOM_DELAY_MIN", "5"))
RANDOM_DELAY_MAX = int(os.getenv("RANDOM_DELAY_MAX", "15"))

# Timeout de carga de página (en milisegundos)
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))

# Máximo de reintentos por scraper cuando falla
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# ============================================================================
# CONFIGURACIÓN VPN (OPCIONAL - Fase 2)
# ============================================================================

VPN_ENABLED = os.getenv("VPN_ENABLED", "false").lower() == "true"
VPN_COUNTRY = os.getenv("VPN_COUNTRY", "BR")

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "bot.log"))

# Tamaño máximo del archivo de log antes de rotar (en bytes, 10MB default)
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))

# Cantidad de archivos de log rotados a mantener
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

# Ruta de la base de datos SQLite
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "flights.db"))

# Cantidad de días después de los cuales limpiar registros viejos
DB_CLEANUP_DAYS = int(os.getenv("DB_CLEANUP_DAYS", "30"))

# ============================================================================
# CONFIGURACIÓN DEL DAEMON (ejecución continua)
# ============================================================================

# Intervalo entre búsquedas (en segundos) — 6 horas = 21600 segundos
MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "21600"))

# Horarios de ejecución preferidos (hora Argentina, UTC-3)
PREFERRED_SEARCH_HOURS = [6, 12, 18, 0]  # 06:00, 12:00, 18:00, 00:00

# ============================================================================
# PLATAFORMAS DE BÚSQUEDA (ordenadas por prioridad)
# ============================================================================

PLATFORMS = {
    "turismo_city": {
        "name": "Turismo City",
        "priority": "CRITICA",
        "enabled": True,
        "base_url": "https://www.turismocity.com.ar",
        "incognito": True,  # Funciona en modo incógnito
        "notes": "Mejores precios (30-40% menos que Despegar). Precios en USD.",
    },
    "despegar": {
        "name": "Despegar",
        "priority": "CRITICA",
        "enabled": True,
        "base_url": "https://www.despegar.com.ar",
        "incognito": True,  # Funciona en modo incógnito
        "notes": "Precios finales con equipaje. Variedad de aerolíneas.",
    },
    # --- Fase 2 (desactivadas por defecto) ---
    "edreams": {
        "name": "eDreams",
        "priority": "MEDIA",
        "enabled": False,
        "base_url": "https://www.edreams.com.ar",
        "incognito": True,
        "notes": "Agregador, apareció en resultados de Perplexity.",
    },
    "kayak": {
        "name": "Kayak Argentina",
        "priority": "MEDIA",
        "enabled": False,
        "base_url": "https://www.kayak.com.ar",
        "incognito": True,
        "notes": "Para validación de precios.",
    },
    "google_flights": {
        "name": "Google Flights",
        "priority": "BAJA",
        "enabled": False,
        "base_url": "https://www.google.com/travel/flights",
        "incognito": True,
        "notes": "Como referencia general.",
    },
}

# ============================================================================
# AEROLÍNEAS A MONITOREAR (ordenadas por prioridad)
# ============================================================================

AIRLINES = {
    "flybondi": {
        "name": "Flybondi",
        "priority": "CRITICA",
        "incognito_works": True,
        "notes": "La más económica. Horarios de madrugada frecuentes.",
    },
    "jetsmart": {
        "name": "JetSmart",
        "priority": "CRITICA",
        "incognito_works": False,  # ⚠️ NO funciona en modo incógnito
        "notes": "Buen balance precio/horario. Requiere sesión con cookies.",
    },
    "gol": {
        "name": "GOL",
        "priority": "MEDIA",
        "incognito_works": True,
        "notes": "Opciones nocturnas disponibles.",
    },
    "aerolineas_argentinas": {
        "name": "Aerolíneas Argentinas",
        "priority": "BAJA",
        "incognito_works": True,
        "notes": "Premium pricing, más confiable.",
    },
    "latam": {
        "name": "LATAM",
        "priority": "BAJA",
        "incognito_works": True,
        "notes": "Generalmente la más cara.",
    },
}

# ============================================================================
# PRECIOS DE REFERENCIA (baseline del research manual)
# ============================================================================

BASELINE_PRICES = {
    # Mejores precios encontrados en investigación (USD para 2 personas con equipaje)
    "best_price_usd": 484,         # Flybondi x2 en Turismo City
    "good_price_usd": 537,         # Flybondi + JetSmart en Turismo City
    "average_price_usd": 700,      # JetSmart x2 en Despegar
    "expensive_price_usd": 800,    # Por encima de esto es caro
    # En ARS (aproximados al dólar blue ~$1.333 de Feb 2026)
    "best_price_ars": 645120,      # USD 484 * 1333
    "good_price_ars": 715821,      # USD 537 * 1333
    "average_price_ars": 933100,   # USD 700 * 1333
    "expensive_price_ars": 1066400,  # USD 800 * 1333
    # Tipo de cambio de referencia
    "exchange_rate_blue": 1333,     # Dólar blue Feb 2026
    "exchange_rate_oficial": 1721,  # Dólar oficial Feb 2026
}

# ============================================================================
# USER-AGENTS PARA ROTACIÓN (simular dispositivos diferentes)
# ============================================================================

USER_AGENTS = [
    # Chrome Windows (más común)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def get_flexible_dates() -> list[dict]:
    """
    Genera la lista de combinaciones de fechas a buscar,
    incluyendo la fecha principal y las fechas flexibles (±N días).
    
    Returns:
        list[dict]: Lista de combinaciones con 'departure' y 'return' como strings YYYY-MM-DD
    """
    base_departure = datetime.strptime(DEPARTURE_DATE, "%Y-%m-%d")
    base_return = datetime.strptime(RETURN_DATE, "%Y-%m-%d")
    
    dates = []
    
    # Fecha principal siempre primero
    dates.append({
        "departure": DEPARTURE_DATE,
        "return": RETURN_DATE,
        "is_primary": True,
        "label": "Fecha principal",
    })
    
    # Generar fechas flexibles
    for dep_delta in range(-DATE_FLEXIBILITY_DAYS, DATE_FLEXIBILITY_DAYS + 1):
        for ret_delta in range(-DATE_FLEXIBILITY_DAYS, DATE_FLEXIBILITY_DAYS + 1):
            # Saltar la fecha principal (ya está incluida)
            if dep_delta == 0 and ret_delta == 0:
                continue
            
            dep_date = base_departure + timedelta(days=dep_delta)
            ret_date = base_return + timedelta(days=ret_delta)
            
            # Asegurar que la vuelta sea después de la ida y mínimo 5 días de viaje
            if ret_date <= dep_date or (ret_date - dep_date).days < 5:
                continue
            
            dep_str = dep_date.strftime("%Y-%m-%d")
            ret_str = ret_date.strftime("%Y-%m-%d")
            
            dates.append({
                "departure": dep_str,
                "return": ret_str,
                "is_primary": False,
                "label": f"Flexible ({dep_delta:+d}/{ret_delta:+d} días)",
            })
    
    return dates


def validate_config() -> list[str]:
    """
    Valida que la configuración esencial esté presente.
    
    Returns:
        list[str]: Lista de errores encontrados (vacía si todo OK)
    """
    errors = []
    
    # Validar Telegram (necesario para alertas)
    if not TELEGRAM_BOT_TOKEN:
        errors.append("⚠️  TELEGRAM_BOT_TOKEN no configurado en .env")
    if not TELEGRAM_CHAT_ID:
        errors.append("⚠️  TELEGRAM_CHAT_ID no configurado en .env")
    
    # Validar fechas
    try:
        dep = datetime.strptime(DEPARTURE_DATE, "%Y-%m-%d")
        ret = datetime.strptime(RETURN_DATE, "%Y-%m-%d")
        if ret <= dep:
            errors.append("❌ RETURN_DATE debe ser posterior a DEPARTURE_DATE")
    except ValueError:
        errors.append("❌ Formato de fecha inválido (usar YYYY-MM-DD)")
    
    # Validar que los delays sean razonables
    if RANDOM_DELAY_MIN < 3:
        errors.append("⚠️  RANDOM_DELAY_MIN menor a 3 segundos (riesgo de detección)")
    
    if RANDOM_DELAY_MAX > 30:
        errors.append("⚠️  RANDOM_DELAY_MAX mayor a 30 segundos (scraping muy lento)")
    
    return errors


def print_config_summary():
    """
    Imprime un resumen legible de la configuración actual.
    Útil para verificar que todo esté bien antes de ejecutar.
    """
    print("=" * 60)
    print("🛫 FLIGHT MONITOR BOT - Configuración")
    print("=" * 60)
    print(f"📅 Fechas:      {DEPARTURE_DATE} → {RETURN_DATE}")
    print(f"👥 Pasajeros:   {PASSENGERS} adultos")
    print(f"💼 Equipaje:    {LUGGAGE_KG}kg por persona")
    print(f"🗺️  Ruta:        {ORIGIN_CITY} → {DESTINATION_CITY}")
    print(f"✈️  Aeropuertos: {'/'.join(ORIGIN_AIRPORTS)} → {DESTINATION_AIRPORT}")
    print(f"📊 Flexibilidad: ±{DATE_FLEXIBILITY_DAYS} días")
    print("-" * 60)
    print(f"🔴 Alerta Crítica:    < ${CRITICAL_PRICE_ARS:,} ARS / < USD ${CRITICAL_PRICE_USD}")
    print(f"🟡 Alerta Importante: < ${IMPORTANT_PRICE_ARS:,} ARS / < USD ${IMPORTANT_PRICE_USD}")
    print(f"📉 Caída de precio:   > {PRICE_DROP_THRESHOLD_PERCENT}% en 24hs")
    print("-" * 60)
    
    # Plataformas habilitadas
    enabled_platforms = [p["name"] for p in PLATFORMS.values() if p["enabled"]]
    print(f"🌐 Plataformas: {', '.join(enabled_platforms)}")
    print(f"🔄 Intervalo:   cada {MONITOR_INTERVAL_SECONDS // 3600} horas")
    print(f"👻 Headless:    {'Sí' if HEADLESS_MODE else 'No'}")
    print(f"🥷 Stealth:     {'Sí' if STEALTH_MODE else 'No'}")
    print(f"⏱️  Delays:      {RANDOM_DELAY_MIN}-{RANDOM_DELAY_MAX} seg")
    print("-" * 60)
    
    # Telegram
    telegram_ok = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    print(f"📱 Telegram:    {'✅ Configurado' if telegram_ok else '❌ Sin configurar'}")
    print(f"💾 Base de datos: {DATABASE_PATH}")
    print(f"📝 Logs:        {LOG_FILE}")
    print("=" * 60)
    
    # Validación
    errors = validate_config()
    if errors:
        print("\n⚠️  ADVERTENCIAS:")
        for error in errors:
            print(f"   {error}")
    else:
        print("\n✅ Configuración válida - Listo para ejecutar")


# Si se ejecuta directamente, mostrar configuración
if __name__ == "__main__":
    print_config_summary()
