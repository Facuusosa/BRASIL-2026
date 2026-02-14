"""
helpers.py - Funciones auxiliares del Flight Monitor Bot

Contiene utilidades compartidas por múltiples módulos:
- Manejo de fechas y timestamps
- Formateo de precios en ARS y USD
- Selección aleatoria de User-Agent
- Cálculo de delays aleatorios
- Formateo de duración de vuelos
"""

import random
import asyncio
from datetime import datetime, timezone, timedelta

from src.config import (
    USER_AGENTS,
    RANDOM_DELAY_MIN,
    RANDOM_DELAY_MAX,
    BASELINE_PRICES,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Zona horaria de Argentina (UTC-3)
TIMEZONE_AR = timezone(timedelta(hours=-3))


# ============================================================================
# MANEJO DE FECHAS Y TIMESTAMPS
# ============================================================================

def now_argentina() -> datetime:
    """
    Retorna la fecha y hora actual en zona horaria de Argentina (UTC-3).
    
    Returns:
        datetime: Fecha/hora actual en Argentina
    """
    return datetime.now(TIMEZONE_AR)


def now_iso() -> str:
    """
    Retorna la fecha y hora actual en formato ISO 8601 con zona horaria.
    
    Returns:
        str: Timestamp ISO 8601 (ej: "2026-02-12T15:30:00-03:00")
    """
    return now_argentina().isoformat()


def format_date_display(date_str: str) -> str:
    """
    Formatea una fecha YYYY-MM-DD a formato legible en español.
    
    Args:
        date_str: Fecha en formato "2026-03-09"
    
    Returns:
        str: Fecha formateada (ej: "Lun 9 marzo 2026")
    """
    DAYS_ES = {
        0: "Lun", 1: "Mar", 2: "Mié",
        3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"
    }
    MONTHS_ES = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = DAYS_ES[date.weekday()]
        month_name = MONTHS_ES[date.month]
        return f"{day_name} {date.day} {month_name} {date.year}"
    except (ValueError, KeyError):
        return date_str


def time_ago(timestamp: datetime) -> str:
    """
    Calcula cuánto tiempo pasó desde un timestamp.
    
    Args:
        timestamp: Fecha/hora a comparar (debe tener timezone)
    
    Returns:
        str: Texto legible (ej: "hace 5 minutos", "hace 2 horas")
    """
    now = now_argentina()
    
    # Si el timestamp no tiene timezone, asumir Argentina
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=TIMEZONE_AR)
    
    diff = now - timestamp
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return "hace unos segundos"
    elif seconds < 3600:
        mins = seconds // 60
        return f"hace {mins} minuto{'s' if mins != 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"hace {hours} hora{'s' if hours != 1 else ''}"
    else:
        days = seconds // 86400
        return f"hace {days} día{'s' if days != 1 else ''}"


# ============================================================================
# FORMATEO DE PRECIOS
# ============================================================================

def format_price_ars(price: float | int) -> str:
    """
    Formatea un precio en pesos argentinos con separadores.
    
    Args:
        price: Precio en ARS (ej: 850000)
    
    Returns:
        str: Precio formateado (ej: "$850.000")
    """
    if price is None:
        return "N/D"
    return f"${int(price):,.0f}".replace(",", ".")


def format_price_usd(price: float | int) -> str:
    """
    Formatea un precio en dólares estadounidenses.
    
    Args:
        price: Precio en USD (ej: 484)
    
    Returns:
        str: Precio formateado (ej: "USD $484")
    """
    if price is None:
        return "N/D"
    return f"USD ${int(price):,}"


def usd_to_ars(price_usd: float, rate: str = "blue") -> float:
    """
    Convierte un precio de USD a ARS usando el tipo de cambio de referencia.
    
    Args:
        price_usd: Precio en dólares
        rate: Tipo de cambio a usar ("blue" o "oficial")
    
    Returns:
        float: Precio en pesos argentinos
    """
    if rate == "oficial":
        exchange_rate = BASELINE_PRICES["exchange_rate_oficial"]
    else:
        exchange_rate = BASELINE_PRICES["exchange_rate_blue"]
    
    return price_usd * exchange_rate


def price_vs_baseline(price_usd: float) -> dict:
    """
    Compara un precio USD contra los precios de referencia del research.
    
    Args:
        price_usd: Precio a comparar en USD
    
    Returns:
        dict: Análisis con diferencias y etiqueta de evaluación
    """
    baseline = BASELINE_PRICES["best_price_usd"]
    diff_usd = price_usd - baseline
    diff_ars = usd_to_ars(diff_usd)
    
    if price_usd <= BASELINE_PRICES["best_price_usd"]:
        label = "🏆 EXCELENTE"
    elif price_usd <= BASELINE_PRICES["good_price_usd"]:
        label = "✅ MUY BUENO"
    elif price_usd <= BASELINE_PRICES["average_price_usd"]:
        label = "🟡 ACEPTABLE"
    elif price_usd <= BASELINE_PRICES["expensive_price_usd"]:
        label = "🟠 CARO"
    else:
        label = "🔴 MUY CARO"
    
    return {
        "label": label,
        "diff_usd": diff_usd,
        "diff_ars": diff_ars,
        "diff_percent": (diff_usd / baseline * 100) if baseline > 0 else 0,
        "baseline_usd": baseline,
    }


# ============================================================================
# ANTI-DETECCIÓN Y SCRAPING
# ============================================================================

def get_random_user_agent() -> str:
    """
    Selecciona un User-Agent aleatorio de la lista de rotación.
    
    Returns:
        str: User-Agent string realista
    """
    return random.choice(USER_AGENTS)


async def random_delay(min_sec: int = None, max_sec: int = None):
    """
    Espera un tiempo aleatorio entre requests (anti-detección).
    Simula el comportamiento humano navegando.
    
    Args:
        min_sec: Mínimo de segundos (default: config RANDOM_DELAY_MIN)
        max_sec: Máximo de segundos (default: config RANDOM_DELAY_MAX)
    """
    min_sec = min_sec or RANDOM_DELAY_MIN
    max_sec = max_sec or RANDOM_DELAY_MAX
    
    delay = random.uniform(min_sec, max_sec)
    logger.debug(f"⏳ Esperando {delay:.1f} segundos (anti-detección)...")
    await asyncio.sleep(delay)


def random_delay_sync(min_sec: int = None, max_sec: int = None):
    """
    Versión sincrónica del delay aleatorio (para contextos no async).
    
    Args:
        min_sec: Mínimo de segundos
        max_sec: Máximo de segundos
    """
    import time
    
    min_sec = min_sec or RANDOM_DELAY_MIN
    max_sec = max_sec or RANDOM_DELAY_MAX
    
    delay = random.uniform(min_sec, max_sec)
    logger.debug(f"⏳ Esperando {delay:.1f} segundos (anti-detección)...")
    time.sleep(delay)


# ============================================================================
# FORMATEO DE VUELOS
# ============================================================================

def format_duration(minutes: int) -> str:
    """
    Formatea una duración en minutos a formato legible.
    
    Args:
        minutes: Duración en minutos (ej: 115)
    
    Returns:
        str: Duración formateada (ej: "1h 55min")
    """
    if minutes is None or minutes <= 0:
        return "N/D"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours == 0:
        return f"{mins}min"
    elif mins == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {mins}min"


def is_night_flight(hour: int) -> bool:
    """
    Determina si un horario corresponde a un vuelo nocturno/madrugada.
    
    Args:
        hour: Hora del vuelo (0-23)
    
    Returns:
        bool: True si es vuelo nocturno (22:00-06:00)
    """
    return hour >= 22 or hour < 6


def is_dawn_flight(hour: int) -> bool:
    """
    Determina si un horario es de madrugada extrema.
    
    Args:
        hour: Hora del vuelo (0-23)
    
    Returns:
        bool: True si es madrugada (00:00-05:00)
    """
    return 0 <= hour < 5


def classify_hour(hour: int) -> str:
    """
    Clasifica una hora de vuelo en categoría legible.
    
    Args:
        hour: Hora del vuelo (0-23)
    
    Returns:
        str: Categoría del horario
    """
    if 8 <= hour <= 20:
        return "🌞 Horario ideal"
    elif 6 <= hour < 8 or 20 < hour <= 22:
        return "🌅 Horario aceptable"
    elif hour >= 22 or hour < 6:
        if is_dawn_flight(hour):
            return "🌑 Madrugada"
        return "🌙 Nocturno"
    return "❓ Desconocido"


def airports_match(origin: str, return_dest: str) -> bool:
    """
    Verifica si los aeropuertos de ida y vuelta son el mismo.
    
    Args:
        origin: Aeropuerto de origen de la ida (ej: "EZE")
        return_dest: Aeropuerto de llegada de la vuelta (ej: "EZE")
    
    Returns:
        bool: True si es el mismo aeropuerto (ida desde EZE, vuelta a EZE)
    """
    return origin == return_dest


# ============================================================================
# LOGGING DE VUELOS (formateo bonito para logs)
# ============================================================================

def flight_summary_line(flight: dict) -> str:
    """
    Genera un resumen de una línea para un vuelo (para logging).
    
    Args:
        flight: Diccionario con datos del vuelo
    
    Returns:
        str: Resumen en una línea (ej: "Flybondi x2 | USD $484 | 00:40→02:35 / 04:25→06:30 | Turismo City")
    """
    airlines = flight.get("airlines", ["N/D"])
    if isinstance(airlines, list):
        airlines_str = " + ".join(airlines)
    else:
        airlines_str = str(airlines)
    
    price_usd = flight.get("price_usd", "N/D")
    price_str = f"USD ${price_usd}" if isinstance(price_usd, (int, float)) else str(price_usd)
    
    platform = flight.get("platform", "N/D")
    
    # Extraer horarios si están disponibles
    out_dep = flight.get("outbound_departure", "")
    out_arr = flight.get("outbound_arrival", "")
    ret_dep = flight.get("return_departure", "")
    ret_arr = flight.get("return_arrival", "")
    
    # Simplificar horarios (solo HH:MM)
    def short_time(dt_str):
        if not dt_str:
            return "??"
        try:
            if " " in dt_str:
                return dt_str.split(" ")[1][:5]
            return dt_str[:5]
        except (IndexError, TypeError):
            return "??"
    
    schedule = f"{short_time(out_dep)}→{short_time(out_arr)} / {short_time(ret_dep)}→{short_time(ret_arr)}"
    
    return f"{airlines_str} | {price_str} | {schedule} | {platform}"
