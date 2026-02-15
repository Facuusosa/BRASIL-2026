#!/usr/bin/env python3
"""
smart_monitor.py — Orquestador Inteligente de todos los módulos de monitoreo

Ejecuta en un solo proceso:
  1. Feature Flag Monitor       (cada 1 hora)
  2. Fare Glitch Detector       (cada 1 hora)
  3. Edge Case Tester           (1 vez por día)
  4. Source Analyzer             (cada 6 horas)
  5. Monitor de Precios normal  (cada 1 hora)

Uso:
    python smart_monitor.py                # Ejecutar todo una vez
    python smart_monitor.py --daemon       # Modo daemon (se queda en background)
    python smart_monitor.py --module flags # Solo un módulo específico
    python smart_monitor.py --module glitch
    python smart_monitor.py --module edge
    python smart_monitor.py --module source
    python smart_monitor.py --module prices
    python smart_monitor.py --no-telegram  # Sin alertas

Puede dejarse corriendo con: pythonw smart_monitor.py --daemon
O con Task Scheduler de Windows para ejecución automática.
"""

import os
import sys
import time
import argparse
import traceback
from datetime import datetime, date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

PROJECT_DIR = Path(__file__).parent
LOG_DIR = PROJECT_DIR / "data" / "smart_monitor_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MASTER_LOG = LOG_DIR / "smart_monitor.log"

# Intervalos de ejecución (en minutos)
SCHEDULES = {
    "prices": 60,       # Precios cada 1 hora
    "flags": 60,        # Feature flags cada 1 hora
    "glitch": 60,       # Glitches cada 1 hora
    "source": 360,      # Source analysis cada 6 horas
    "edge": 1440,       # Edge cases 1 vez por día
}


# ============================================================================
# LOGGING
# ============================================================================

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}"
    print(entry)
    with open(MASTER_LOG, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def send_telegram(message: str, silent: bool = True) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        try:
            from curl_cffi import requests as http
        except ImportError:
            import requests as http

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_notification": silent,
        }
        resp = http.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


# ============================================================================
# EJECUCIÓN DE MÓDULOS
# ============================================================================

def run_prices():
    """Ejecuta el monitor de precios principal."""
    log("🛫 Ejecutando monitor de precios...")
    try:
        from monitor_flybondi import run_search
        results = run_search(send_telegram_alerts=True, json_output=False)
        log(f"🛫 Precios: {len(results)} resultados encontrados")
        return True
    except Exception as e:
        log(f"❌ Error en monitor de precios: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


def run_flags():
    """Ejecuta el monitor de feature flags."""
    log("🔬 Ejecutando feature flag monitor...")
    try:
        from src.feature_flag_monitor import run_check
        run_check()
        log("🔬 Feature flags: Check completado")
        return True
    except Exception as e:
        log(f"❌ Error en feature flags: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


def run_glitch():
    """Ejecuta el detector de glitches."""
    log("🔍 Ejecutando fare glitch detector...")
    try:
        from src.fare_glitch_detector import run_check
        run_check()
        log("🔍 Glitch detector: Check completado")
        return True
    except Exception as e:
        log(f"❌ Error en glitch detector: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


def run_edge():
    """Ejecuta el tester de edge cases."""
    log("🧪 Ejecutando edge case tester...")
    try:
        from src.edge_case_tester import run_tests, should_run_today
        if should_run_today():
            run_tests()
            log("🧪 Edge cases: Tests completados")
        else:
            log("🧪 Edge cases: Ya se ejecutó hoy, saltando")
        return True
    except Exception as e:
        log(f"❌ Error en edge case tester: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


def run_source():
    """Ejecuta el analizador de código fuente."""
    log("🔬 Ejecutando source analyzer...")
    try:
        from src.source_analyzer import run_analysis
        run_analysis(compare=True)
        log("🔬 Source analyzer: Análisis completado")
        return True
    except Exception as e:
        log(f"❌ Error en source analyzer: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


MODULES = {
    "prices": run_prices,
    "flags": run_flags,
    "glitch": run_glitch,
    "edge": run_edge,
    "source": run_source,
}


# ============================================================================
# MODO DAEMON
# ============================================================================

def run_all_once():
    """Ejecuta todos los módulos una vez."""
    now = datetime.now()
    log(f"{'=' * 70}")
    log(f"🤖 SMART MONITOR — Ejecución completa {now.strftime('%d/%m/%Y %H:%M:%S')}")
    log(f"{'=' * 70}")

    results = {}
    for name, func in MODULES.items():
        try:
            success = func()
            results[name] = "✅" if success else "❌"
        except Exception as e:
            results[name] = f"❌ {e}"
            log(f"Error fatal en módulo {name}: {e}", "CRITICAL")

        # Pausa entre módulos
        time.sleep(3)

    log(f"\n📊 Resumen: {' | '.join(f'{k}: {v}' for k, v in results.items())}")
    return results


def run_daemon():
    """Ejecuta todos los módulos según su schedule."""
    log(f"{'=' * 70}")
    log(f"🤖 SMART MONITOR — Modo DAEMON activado")
    log(f"{'=' * 70}")

    send_telegram(
        f"🤖 *Smart Monitor activado*\n\n"
        f"Módulos:\n"
        f"  • 🛫 Precios: cada {SCHEDULES['prices']} min\n"
        f"  • 🔬 Feature Flags: cada {SCHEDULES['flags']} min\n"
        f"  • 🔍 Fare Glitches: cada {SCHEDULES['glitch']} min\n"
        f"  • 📄 Source Analysis: cada {SCHEDULES['source']} min\n"
        f"  • 🧪 Edge Cases: 1x/día\n\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )

    # Track de última ejecución de cada módulo
    last_run: dict[str, datetime] = {}
    iteration = 0

    while True:
        try:
            iteration += 1
            now = datetime.now()

            log(f"\n{'#' * 70}")
            log(f"# TICK #{iteration} — {now.strftime('%H:%M:%S')}")
            log(f"{'#' * 70}")

            modules_run = []

            for name, func in MODULES.items():
                interval = SCHEDULES.get(name, 60)
                last = last_run.get(name)

                # ¿Es hora de ejecutar este módulo?
                should_run = (
                    last is None
                    or (now - last).total_seconds() >= interval * 60
                )

                if should_run:
                    try:
                        success = func()
                        last_run[name] = now
                        modules_run.append(f"{name}: {'✅' if success else '⚠️'}")
                    except Exception as e:
                        log(f"Error en módulo {name}: {e}", "ERROR")
                        modules_run.append(f"{name}: ❌")
                        last_run[name] = now  # No reintentar inmediatamente

                    # Pausa entre módulos
                    time.sleep(5)

            if modules_run:
                log(f"Ejecutados: {' | '.join(modules_run)}")

            # Calcular próximo módulo a ejecutar
            next_runs = {}
            for name in MODULES:
                interval = SCHEDULES.get(name, 60)
                last = last_run.get(name, now)
                next_time = last + timedelta(minutes=interval)
                next_runs[name] = next_time

            # Dormir hasta el próximo módulo (mínimo 1 min, máximo 10 min)
            next_module = min(next_runs, key=next_runs.get)
            sleep_seconds = max(
                60,
                min(600, (next_runs[next_module] - now).total_seconds())
            )

            log(
                f"⏳ Próximo: {next_module} a las "
                f"{next_runs[next_module].strftime('%H:%M:%S')} "
                f"(durmiendo {sleep_seconds/60:.0f} min)"
            )

            time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            log("\n🛑 Smart Monitor detenido por el usuario.")
            send_telegram("🛑 *Smart Monitor detenido*", silent=True)
            break
        except Exception as e:
            log(f"Error inesperado en daemon loop: {e}", "CRITICAL")
            log(traceback.format_exc(), "CRITICAL")
            time.sleep(60)  # Esperar 1 min y reintentar


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🤖 Orquestador Inteligente de Monitoreo Flybondi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python smart_monitor.py                 # Todo una vez
  python smart_monitor.py --daemon        # Modo daemon (background)
  python smart_monitor.py --module flags  # Solo feature flags
  python smart_monitor.py --module glitch # Solo glitch detector
  python smart_monitor.py --module edge   # Solo edge cases
  python smart_monitor.py --module source # Solo source analyzer
  python smart_monitor.py --module prices # Solo precios

Para ejecutar en background (Windows):
  start /B pythonw smart_monitor.py --daemon

Para ejecutar con Task Scheduler:
  1. Abrir Task Scheduler
  2. Create Basic Task
  3. Trigger: "When the computer starts"
  4. Action: Start a program
  5. Program: python
  6. Arguments: smart_monitor.py --daemon
  7. Start in: <directorio del proyecto>
        """,
    )

    parser.add_argument(
        "--daemon", action="store_true",
        help="Modo daemon (se queda corriendo en background)",
    )
    parser.add_argument(
        "--module", type=str, choices=list(MODULES.keys()),
        help="Ejecutar solo un módulo específico",
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="No enviar alertas por Telegram",
    )

    args = parser.parse_args()

    if args.no_telegram:
        global TELEGRAM_BOT_TOKEN
        TELEGRAM_BOT_TOKEN = ""

    if args.module:
        log(f"Ejecutando módulo: {args.module}")
        func = MODULES[args.module]
        func()
    elif args.daemon:
        run_daemon()
    else:
        run_all_once()


if __name__ == "__main__":
    main()
