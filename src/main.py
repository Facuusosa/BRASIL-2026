"""
main.py - Punto de entrada principal del Flight Monitor Bot

Orquesta todo el flujo de monitoreo de precios de vuelos:
1. Carga configuración desde .env
2. Inicializa base de datos, scrapers, notificador
3. Ejecuta búsquedas en Turismo City y Despegar
4. Calcula scores para cada vuelo encontrado
5. Detecta alertas y las envía por Telegram
6. En modo daemon, repite cada 6 horas

RESTRICCIÓN CRÍTICA: Este bot SOLO monitorea precios.
❌ NUNCA compra vuelos, guarda tarjetas, ni hace checkout.
✅ SOLO busca, guarda histórico y notifica por Telegram.

Uso:
    python src/main.py --test        # Una búsqueda de prueba
    python src/main.py --daemon      # Monitoreo continuo cada 6 horas
    python src/main.py --analyze-only # Solo analizar datos existentes
    python src/main.py --report      # Generar reporte de precios
    python src/main.py --debug       # Modo verbose con logging detallado
"""

import sys
import asyncio
import argparse
import signal
from datetime import datetime, timedelta

# Agregar el directorio padre al path para poder importar src.*
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    MONITOR_INTERVAL_SECONDS,
    PLATFORMS,
    DEPARTURE_DATE,
    RETURN_DATE,
    PASSENGERS,
    CRITICAL_PRICE_USD,
    IMPORTANT_PRICE_USD,
    CRITICAL_PRICE_ARS,
    IMPORTANT_PRICE_ARS,
    PRICE_DROP_THRESHOLD_PERCENT,
    MIN_SAVINGS_FOR_SUGGESTION_ARS,
    CRITICAL_AVAILABILITY_THRESHOLD,
    get_flexible_dates,
    validate_config,
    print_config_summary,
)
from src.utils.logger import get_logger
from src.utils.helpers import (
    now_argentina,
    now_iso,
    format_price_ars,
    format_price_usd,
    price_vs_baseline,
    flight_summary_line,
    time_ago,
    random_delay,
    usd_to_ars,
)

logger = get_logger("main")

# ============================================================================
# IMPORTACIONES CONDICIONALES (se cargan cuando los módulos existen)
# ============================================================================

# Flag global para detener el daemon gracefully
_shutdown_requested = False


def _signal_handler(signum, frame):
    """Maneja señales de interrupción (Ctrl+C, SIGTERM) para apagado limpio."""
    global _shutdown_requested
    logger.info("🛑 Señal de apagado recibida. Terminando después del ciclo actual...")
    _shutdown_requested = True


# ============================================================================
# FUNCIONES PRINCIPALES DEL BOT
# ============================================================================

async def run_scrapers(dates: list[dict]) -> list[dict]:
    """
    Ejecuta todos los scrapers habilitados para las fechas dadas.
    
    Args:
        dates: Lista de combinaciones de fechas a buscar
               (viene de config.get_flexible_dates())
    
    Returns:
        list[dict]: Lista de vuelos encontrados en todas las plataformas
    """
    all_flights = []
    
    # Obtener plataformas habilitadas
    enabled_platforms = {
        key: info for key, info in PLATFORMS.items() if info["enabled"]
    }
    
    if not enabled_platforms:
        logger.warning("⚠️ No hay plataformas habilitadas para buscar")
        return all_flights
    
    logger.info(f"🔍 Iniciando búsqueda en {len(enabled_platforms)} plataforma(s)...")
    logger.info(f"📅 Buscando {len(dates)} combinación(es) de fechas")
    
    for platform_key, platform_info in enabled_platforms.items():
        platform_name = platform_info["name"]
        logger.info(f"\n{'='*50}")
        logger.info(f"🌐 Buscando en: {platform_name} (prioridad: {platform_info['priority']})")
        logger.info(f"{'='*50}")
        
        try:
            # Importar el scraper correspondiente dinámicamente
            scraper = _get_scraper(platform_key)
            
            if scraper is None:
                logger.warning(f"⚠️ Scraper para {platform_name} no implementado aún. Saltando.")
                continue
            
            # Buscar para cada combinación de fechas
            for date_combo in dates:
                dep_date = date_combo["departure"]
                ret_date = date_combo["return"]
                label = date_combo["label"]
                
                logger.info(f"  📅 {label}: {dep_date} → {ret_date}")
                
                try:
                    flights = await scraper.search(
                        departure_date=dep_date,
                        return_date=ret_date,
                        passengers=PASSENGERS,
                    )
                    
                    if flights:
                        logger.info(f"  ✅ {len(flights)} vuelo(s) encontrado(s)")
                        for f in flights:
                            logger.info(f"     ✈️ {flight_summary_line(f)}")
                        all_flights.extend(flights)
                    else:
                        logger.info(f"  📭 Sin resultados para estas fechas")
                    
                    # Delay entre búsquedas (anti-detección)
                    await random_delay()
                    
                except Exception as e:
                    logger.error(
                        f"  ❌ Error buscando {platform_name} ({dep_date}→{ret_date}): {e}",
                        exc_info=True,
                    )
                    # Continuar con la siguiente fecha
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error general con {platform_name}: {e}", exc_info=True)
            # Continuar con la siguiente plataforma
            continue
    
    logger.info(f"\n📊 Total de vuelos encontrados: {len(all_flights)}")
    return all_flights


def _get_scraper(platform_key: str):
    """
    Obtiene la instancia del scraper según la plataforma.
    Importa los módulos dinámicamente para manejar el caso de que
    aún no estén implementados.
    
    Args:
        platform_key: Clave de la plataforma (ej: "turismo_city")
    
    Returns:
        Instancia del scraper o None si no está implementado
    """
    try:
        if platform_key == "turismo_city":
            from src.scrapers.turismo_city import TurismoCityScraper
            return TurismoCityScraper()
        
        elif platform_key == "despegar":
            from src.scrapers.despegar import DespegarScraper
            return DespegarScraper()
        
        else:
            logger.debug(f"Scraper para '{platform_key}' no implementado")
            return None
            
    except ImportError as e:
        logger.warning(f"⚠️ No se pudo importar scraper para {platform_key}: {e}")
        return None


async def analyze_flights(flights: list[dict]) -> list[dict]:
    """
    Analiza los vuelos encontrados: calcula scores y detecta oportunidades.
    
    Args:
        flights: Lista de vuelos encontrados por los scrapers
    
    Returns:
        list[dict]: Vuelos enriquecidos con scores y análisis
    """
    if not flights:
        logger.info("📊 No hay vuelos para analizar")
        return flights
    
    logger.info(f"\n🧮 Analizando {len(flights)} vuelo(s)...")
    
    try:
        from src.analyzer.scorer import FlightScorer
        scorer = FlightScorer()
        
        for flight in flights:
            # Calcular score
            score = scorer.calculate_score(flight)
            flight["score"] = score
            
            # Explicar score
            explanation = scorer.explain_score(flight)
            flight["score_explanation"] = explanation
            
            # Comparar contra baseline
            price_usd = flight.get("price_usd")
            if price_usd:
                comparison = price_vs_baseline(price_usd)
                flight["price_comparison"] = comparison
        
        # Ordenar por score descendente (mejores primero)
        flights.sort(key=lambda f: f.get("score", 0), reverse=True)
        
        # Log del top 5
        logger.info(f"\n🏆 Top 5 vuelos por score:")
        for i, flight in enumerate(flights[:5], 1):
            score = flight.get("score", 0)
            comparison = flight.get("price_comparison", {})
            label = comparison.get("label", "")
            logger.info(
                f"  {i}. Score {score:.1f}/100 {label} | {flight_summary_line(flight)}"
            )
        
    except ImportError:
        logger.warning("⚠️ Módulo de scoring no implementado aún. Saltando análisis.")
    except Exception as e:
        logger.error(f"❌ Error en análisis: {e}", exc_info=True)
    
    return flights


async def save_to_database(flights: list[dict]):
    """
    Guarda los vuelos encontrados en la base de datos SQLite.
    
    Args:
        flights: Lista de vuelos a guardar
    """
    if not flights:
        return
    
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        
        saved_count = 0
        for flight in flights:
            try:
                db.save_flight(flight)
                saved_count += 1
            except Exception as e:
                logger.error(f"❌ Error guardando vuelo: {e}")
                continue
        
        logger.info(f"💾 {saved_count}/{len(flights)} vuelo(s) guardado(s) en la base de datos")
        
    except ImportError:
        logger.warning("⚠️ Módulo de base de datos no implementado aún. No se guardaron vuelos.")
    except Exception as e:
        logger.error(f"❌ Error con la base de datos: {e}", exc_info=True)


async def check_and_send_alerts(flights: list[dict]):
    """
    Revisa los vuelos y envía alertas por Telegram según los umbrales configurados.
    
    Niveles de alerta:
    - 🔴 CRÍTICA: Precio < USD $450 o < $850.000 ARS, disponibilidad <3, caída >15%
    - 🟡 IMPORTANTE: Precio < USD $550 o < $950.000 ARS, ahorro >$100k por fecha
    - 🟢 INFO: Precios estables, nuevas opciones
    
    Args:
        flights: Lista de vuelos analizados (con scores)
    """
    if not flights:
        return
    
    try:
        from src.notifier.telegram_bot import TelegramNotifier
        notifier = TelegramNotifier()
        
        alerts_sent = 0
        
        for flight in flights:
            price_usd = flight.get("price_usd")
            price_ars = flight.get("price_ars")
            availability = flight.get("availability")
            
            # Si tenemos USD pero no ARS, convertir
            if price_usd and not price_ars:
                price_ars = usd_to_ars(price_usd)
                flight["price_ars"] = price_ars
            
            alert_type = _determine_alert_type(flight)
            
            if alert_type == "critical":
                logger.info(f"🔴 ALERTA CRÍTICA detectada: {flight_summary_line(flight)}")
                await notifier.send_critical_alert(flight)
                alerts_sent += 1
                
            elif alert_type == "important":
                logger.info(f"🟡 Alerta importante detectada: {flight_summary_line(flight)}")
                await notifier.send_important_alert(flight)
                alerts_sent += 1
                
            # Las alertas info solo se logean, no se envían por Telegram
            elif alert_type == "info":
                logger.debug(f"🟢 Info: {flight_summary_line(flight)}")
        
        if alerts_sent > 0:
            logger.info(f"📱 {alerts_sent} alerta(s) enviada(s) por Telegram")
        else:
            logger.info("📱 Sin alertas que enviar en este ciclo")
            
    except ImportError:
        logger.warning("⚠️ Módulo de Telegram no implementado aún. No se enviaron alertas.")
    except Exception as e:
        logger.error(f"❌ Error enviando alertas: {e}", exc_info=True)


def _determine_alert_type(flight: dict) -> str:
    """
    Determina el tipo de alerta para un vuelo según los umbrales configurados.
    
    Args:
        flight: Diccionario con datos del vuelo
    
    Returns:
        str: "critical", "important", "info" o "none"
    """
    price_usd = flight.get("price_usd", 999999)
    price_ars = flight.get("price_ars", 999999999)
    availability = flight.get("availability")
    
    # --- ALERTA CRÍTICA 🔴 ---
    # Precio por debajo del umbral crítico
    if price_usd and price_usd < CRITICAL_PRICE_USD:
        return "critical"
    if price_ars and price_ars < CRITICAL_PRICE_ARS:
        return "critical"
    
    # Disponibilidad crítica (últimos X asientos)
    if availability is not None:
        try:
            seats = int(str(availability).split()[0]) if isinstance(availability, str) else int(availability)
            if seats <= CRITICAL_AVAILABILITY_THRESHOLD:
                return "critical"
        except (ValueError, IndexError):
            pass
    
    # --- ALERTA IMPORTANTE 🟡 ---
    # Precio por debajo del umbral importante
    if price_usd and price_usd < IMPORTANT_PRICE_USD:
        return "important"
    if price_ars and price_ars < IMPORTANT_PRICE_ARS:
        return "important"
    
    # --- INFO 🟢 ---
    return "info"


async def check_price_drops(flights: list[dict]):
    """
    Compara precios actuales con histórico para detectar caídas bruscas (>15%).
    
    Args:
        flights: Lista de vuelos actuales
    """
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        
        for flight in flights:
            price_usd = flight.get("price_usd")
            if not price_usd:
                continue
            
            # Buscar precio anterior para misma ruta/aerolínea/plataforma
            previous = db.get_previous_price(
                platform=flight.get("platform"),
                airlines=flight.get("airlines"),
                departure_date=flight.get("outbound_departure", "")[:10],
            )
            
            if previous and previous > 0:
                drop_percent = ((previous - price_usd) / previous) * 100
                
                if drop_percent >= PRICE_DROP_THRESHOLD_PERCENT:
                    flight["price_drop_percent"] = drop_percent
                    flight["previous_price_usd"] = previous
                    logger.info(
                        f"📉 ¡Caída de precio! {format_price_usd(previous)} → "
                        f"{format_price_usd(price_usd)} ({drop_percent:.1f}%)"
                    )
                    
    except ImportError:
        logger.debug("Base de datos no disponible para comparar precios anteriores")
    except Exception as e:
        logger.error(f"Error comprobando caídas de precio: {e}")


async def check_flexible_savings(flights: list[dict]):
    """
    Identifica si cambiar las fechas de viaje genera ahorros significativos.
    
    Si hay un vuelo con fecha alternativa que ahorra más de $100.000 ARS
    respecto a la fecha principal, se marca para notificar.
    
    Args:
        flights: Lista de vuelos (incluye fecha principal y flexibles)
    """
    # Buscar el mejor precio de la fecha principal
    primary_flights = [
        f for f in flights 
        if f.get("outbound_departure", "")[:10] == DEPARTURE_DATE
        and f.get("return_departure", "")[:10] == RETURN_DATE
    ]
    
    if not primary_flights:
        logger.debug("No hay vuelos en la fecha principal para comparar flexibilidad")
        return
    
    best_primary_usd = min(f.get("price_usd", 999999) for f in primary_flights)
    best_primary_ars = usd_to_ars(best_primary_usd)
    
    # Comparar con vuelos de fechas alternativas
    alt_flights = [f for f in flights if f not in primary_flights]
    
    for flight in alt_flights:
        alt_price_usd = flight.get("price_usd")
        if not alt_price_usd:
            continue
        
        alt_price_ars = usd_to_ars(alt_price_usd)
        savings_ars = best_primary_ars - alt_price_ars
        
        if savings_ars >= MIN_SAVINGS_FOR_SUGGESTION_ARS:
            flight["flexible_savings_ars"] = savings_ars
            flight["flexible_savings_usd"] = best_primary_usd - alt_price_usd
            
            logger.info(
                f"💡 Ahorro por flexibilidad: {format_price_ars(savings_ars)} "
                f"cambiando a {flight.get('outbound_departure', '?')[:10]} → "
                f"{flight.get('return_departure', '?')[:10]}"
            )


# ============================================================================
# MODOS DE EJECUCIÓN
# ============================================================================

async def run_single_search():
    """
    Ejecuta una única búsqueda completa (modo --test o ejecución manual).
    
    Flujo:
    1. Buscar en todas las plataformas habilitadas
    2. Analizar y calcular scores
    3. Guardar en base de datos
    4. Verificar caídas de precio
    5. Verificar ahorros por flexibilidad
    6. Enviar alertas si corresponde
    """
    start_time = now_argentina()
    logger.info(f"🚀 Iniciando búsqueda | {now_iso()}")
    
    # 1. Generar fechas a buscar (principal + flexibles)
    dates = get_flexible_dates()
    logger.info(f"📅 {len(dates)} combinación(es) de fechas generadas")
    
    # Solo buscar fecha principal en modo test
    # (las flexibles se buscan en ejecución completa)
    
    # 2. Ejecutar scrapers
    flights = await run_scrapers(dates)
    
    if not flights:
        logger.warning("⚠️ No se encontraron vuelos en ninguna plataforma")
        logger.info("   Posibles causas:")
        logger.info("   - Los scrapers aún no están implementados")
        logger.info("   - Problemas de conexión o anti-bot")
        logger.info("   - Las plataformas cambiaron su diseño")
        return
    
    # 3. Analizar vuelos (calcular scores)
    flights = await analyze_flights(flights)
    
    # 4. Guardar en base de datos
    await save_to_database(flights)
    
    # 5. Verificar caídas de precio (comparar con histórico)
    await check_price_drops(flights)
    
    # 6. Verificar ahorros por cambio de fecha
    await check_flexible_savings(flights)
    
    # 7. Enviar alertas
    await check_and_send_alerts(flights)
    
    # Resumen final
    elapsed = (now_argentina() - start_time).total_seconds()
    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Búsqueda completada en {elapsed:.1f} segundos")
    logger.info(f"📊 Vuelos encontrados: {len(flights)}")
    
    if flights:
        best = flights[0]  # Ya están ordenados por score
        logger.info(
            f"🏆 Mejor vuelo: {flight_summary_line(best)} "
            f"(Score: {best.get('score', 'N/D')}/100)"
        )
    
    logger.info(f"{'='*50}\n")


async def run_daemon():
    """
    Ejecuta el bot en modo daemon: búsqueda continua cada 6 horas.
    Se detiene limpiamente con Ctrl+C o señal SIGTERM.
    """
    global _shutdown_requested
    
    logger.info("🤖 Iniciando modo DAEMON (monitoreo continuo)")
    logger.info(f"⏰ Intervalo entre búsquedas: {MONITOR_INTERVAL_SECONDS // 3600} horas")
    logger.info(f"🛑 Presioná Ctrl+C para detener\n")
    
    cycle = 0
    
    while not _shutdown_requested:
        cycle += 1
        logger.info(f"\n{'═'*60}")
        logger.info(f"🔄 CICLO #{cycle} | {now_iso()}")
        logger.info(f"{'═'*60}")
        
        try:
            await run_single_search()
        except Exception as e:
            logger.error(f"❌ Error en ciclo #{cycle}: {e}", exc_info=True)
            
            # Intentar notificar el error por Telegram
            try:
                from src.notifier.telegram_bot import TelegramNotifier
                notifier = TelegramNotifier()
                await notifier.send_error_alert(
                    f"❌ Error en ciclo #{cycle}: {str(e)[:200]}"
                )
            except Exception:
                pass  # Si Telegram falla también, solo logear
        
        if _shutdown_requested:
            break
        
        # Calcular tiempo hasta la próxima ejecución
        next_run = now_argentina() + timedelta(seconds=MONITOR_INTERVAL_SECONDS)
        logger.info(f"⏳ Próxima búsqueda: {next_run.strftime('%d/%m/%Y %H:%M:%S')} (Argentina)")
        logger.info(f"💤 Esperando {MONITOR_INTERVAL_SECONDS // 3600} horas...")
        
        # Esperar el intervalo, verificando shutdown cada 30 segundos
        waited = 0
        while waited < MONITOR_INTERVAL_SECONDS and not _shutdown_requested:
            await asyncio.sleep(min(30, MONITOR_INTERVAL_SECONDS - waited))
            waited += 30
    
    logger.info("🛑 Daemon detenido limpiamente. ¡Hasta la próxima!")


async def run_analyze_only():
    """
    Solo analiza datos existentes en la base de datos (no hace scraping).
    Útil para generar reportes sin hacer nuevas búsquedas.
    """
    logger.info("📊 Modo ANÁLISIS (solo datos existentes, sin scraping)")
    
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        
        # Obtener últimos vuelos guardados
        flights = db.get_recent_flights(hours=24)
        
        if not flights:
            logger.info("📭 No hay vuelos en las últimas 24 horas")
            logger.info("   Ejecutá 'python src/main.py --test' primero para buscar vuelos")
            return
        
        logger.info(f"📊 Analizando {len(flights)} vuelo(s) de las últimas 24 horas...")
        
        # Re-analizar scores
        flights = await analyze_flights(flights)
        
        # Mostrar resultados
        for i, flight in enumerate(flights, 1):
            logger.info(f"  {i}. {flight_summary_line(flight)}")
        
    except ImportError:
        logger.error("❌ Módulo de base de datos no disponible. No se puede analizar.")
    except Exception as e:
        logger.error(f"❌ Error en análisis: {e}", exc_info=True)


async def run_report():
    """
    Genera un reporte detallado de precios y tendencias.
    Envía el reporte por Telegram si está configurado.
    """
    logger.info("📝 Generando reporte de precios...")
    
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        
        # Obtener datos para reporte
        flights_24h = db.get_recent_flights(hours=24)
        flights_7d = db.get_recent_flights(hours=168)  # 7 días
        
        # Estadísticas
        if flights_24h:
            prices_24h = [f.get("price_usd", 0) for f in flights_24h if f.get("price_usd")]
            if prices_24h:
                min_price = min(prices_24h)
                max_price = max(prices_24h)
                avg_price = sum(prices_24h) / len(prices_24h)
                
                logger.info(f"\n📊 REPORTE DE PRECIOS (últimas 24hs)")
                logger.info(f"  Búsquedas: {len(flights_24h)}")
                logger.info(f"  Precio mínimo: {format_price_usd(min_price)}")
                logger.info(f"  Precio máximo: {format_price_usd(max_price)}")
                logger.info(f"  Precio promedio: {format_price_usd(avg_price)}")
        else:
            logger.info("📭 No hay datos de las últimas 24 horas para reportar")
        
        # Enviar reporte por Telegram
        try:
            from src.notifier.telegram_bot import TelegramNotifier
            notifier = TelegramNotifier()
            await notifier.send_daily_report(flights_24h)
        except ImportError:
            logger.info("📱 Telegram no configurado. Reporte solo en logs.")
        
    except ImportError:
        logger.error("❌ Base de datos no disponible para generar reporte.")
    except Exception as e:
        logger.error(f"❌ Error generando reporte: {e}", exc_info=True)


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parsea los argumentos de línea de comandos.
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="🛫 Flight Monitor Bot - Monitoreo de precios BUE → FLN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python src/main.py --test           Una búsqueda de prueba
  python src/main.py --daemon         Monitoreo continuo (cada 6 horas)
  python src/main.py --analyze-only   Solo analizar datos existentes
  python src/main.py --report         Generar reporte de precios
  python src/main.py --debug          Modo verbose

⚠️ RESTRICCIÓN: Este bot SOLO monitorea precios. NUNCA compra vuelos.
        """
    )
    
    # Modos de ejecución (mutuamente excluyentes)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--test",
        action="store_true",
        help="Ejecutar una sola búsqueda de prueba"
    )
    mode_group.add_argument(
        "--daemon",
        action="store_true",
        help="Ejecutar en modo continuo (cada 6 horas)"
    )
    mode_group.add_argument(
        "--analyze-only",
        action="store_true",
        help="Solo analizar datos existentes (sin scraping)"
    )
    mode_group.add_argument(
        "--report",
        action="store_true",
        help="Generar reporte de precios"
    )
    
    # Opciones adicionales
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activar logging verbose (DEBUG)"
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Deshabilitar notificaciones de Telegram"
    )
    parser.add_argument(
        "--primary-only",
        action="store_true",
        help="Buscar solo la fecha principal (sin fechas flexibles)"
    )
    
    return parser.parse_args()


async def main():
    """
    Función principal que coordina todo el flujo del bot.
    """
    # Parsear argumentos CLI
    args = parse_arguments()
    
    # Configurar nivel de debug si se solicitó
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("🔧 Modo DEBUG activado")
    
    # Banner de inicio
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║  🛫 FLIGHT MONITOR BOT - BUE → FLN                 ║")
    print("║  Monitoreo de precios de vuelos a Florianópolis     ║")
    print("║  ⚠️  SOLO monitorea - NUNCA compra vuelos           ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    
    # Mostrar configuración
    print_config_summary()
    
    # Validar configuración
    errors = validate_config()
    if errors:
        logger.warning("⚠️ Hay advertencias en la configuración (ver arriba)")
        logger.warning("   El bot puede funcionar pero algunas features estarán limitadas")
    
    # Registrar handler de señales para apagado limpio
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    # Ejecutar según el modo seleccionado
    try:
        if args.test:
            logger.info("🧪 Modo TEST: ejecutando una búsqueda de prueba...")
            await run_single_search()
            
        elif args.daemon:
            await run_daemon()
            
        elif args.analyze_only:
            await run_analyze_only()
            
        elif args.report:
            await run_report()
            
        else:
            # Sin argumentos: ejecutar una búsqueda simple (como --test)
            logger.info("▶️ Ejecutando búsqueda única (usá --daemon para monitoreo continuo)")
            await run_single_search()
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrumpido por el usuario (Ctrl+C)")
    except Exception as e:
        logger.critical(f"💥 Error fatal: {e}", exc_info=True)
        
        # Intentar notificar error fatal por Telegram
        try:
            from src.notifier.telegram_bot import TelegramNotifier
            notifier = TelegramNotifier()
            await notifier.send_error_alert(f"💥 Error fatal del bot: {str(e)[:200]}")
        except Exception:
            pass
        
        sys.exit(1)
    
    logger.info("👋 Bot finalizado. ¡Buen viaje a Floripa! 🏖️")


if __name__ == "__main__":
    asyncio.run(main())
