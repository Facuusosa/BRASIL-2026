"""
logger.py - Sistema de logging del Flight Monitor Bot

Configura logging con:
- Salida a consola (con colores)
- Salida a archivo (con rotación automática cada 10MB)
- Formato detallado con timestamps ISO 8601

Uso:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Búsqueda iniciada")
    logger.error("Error de conexión", exc_info=True)
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Importar configuración
from src.config import LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT


# ============================================================================
# COLORES PARA LA CONSOLA (ANSI escape codes)
# ============================================================================

class ColorFormatter(logging.Formatter):
    """
    Formatter personalizado que agrega colores ANSI a los mensajes de consola.
    Cada nivel de log tiene su propio color para facilitar la lectura.
    """
    
    # Códigos ANSI de colores
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Verde
        "WARNING": "\033[33m",    # Amarillo
        "ERROR": "\033[31m",      # Rojo
        "CRITICAL": "\033[41m",   # Fondo rojo
    }
    RESET = "\033[0m"  # Reset a color normal
    
    def format(self, record):
        # Obtener color según el nivel de log
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Aplicar color al nivel de log
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        return super().format(record)


# ============================================================================
# CONFIGURACIÓN DEL LOGGER
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Crea y configura un logger con salida a consola y archivo.
    
    Args:
        name: Nombre del módulo (usar __name__ del módulo que llama)
    
    Returns:
        logging.Logger: Logger configurado y listo para usar
    
    Ejemplo:
        logger = get_logger(__name__)
        logger.info("✅ Scraper de Turismo City iniciado")
        logger.warning("⚠️ Timeout en la carga de página")
        logger.error("❌ Error al parsear resultados", exc_info=True)
    """
    logger = logging.getLogger(name)
    
    # Evitar agregar handlers duplicados si ya fue configurado
    if logger.handlers:
        return logger
    
    # Establecer nivel de log
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # --- Handler de CONSOLA (con colores) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    console_format = ColorFormatter(
        fmt="%(asctime)s │ %(levelname)-18s │ %(name)-25s │ %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # --- Handler de ARCHIVO (con rotación) ---
    try:
        # Asegurar que el directorio de logs exista
        log_path = Path(LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=LOG_FILE,
            maxBytes=LOG_MAX_BYTES,        # 10MB por defecto
            backupCount=LOG_BACKUP_COUNT,  # 5 archivos rotados
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(funcName)-20s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
    except (OSError, PermissionError) as e:
        # Si no se puede crear el archivo de log, solo usar consola
        logger.warning(f"⚠️ No se pudo crear archivo de log: {e}. Usando solo consola.")
    
    return logger


def get_scraper_logger(platform_name: str) -> logging.Logger:
    """
    Logger especializado para scrapers. Agrega contexto de la plataforma.
    
    Args:
        platform_name: Nombre de la plataforma (ej: "turismo_city", "despegar")
    
    Returns:
        logging.Logger: Logger con namespace de scraper
    """
    return get_logger(f"scraper.{platform_name}")


def get_notifier_logger() -> logging.Logger:
    """Logger especializado para el módulo de notificaciones."""
    return get_logger("notifier.telegram")


def get_database_logger() -> logging.Logger:
    """Logger especializado para el módulo de base de datos."""
    return get_logger("database")


def get_analyzer_logger() -> logging.Logger:
    """Logger especializado para el módulo de análisis."""
    return get_logger("analyzer")
