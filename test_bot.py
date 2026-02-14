"""
test_bot.py - Script de verificación del Flight Monitor Bot

Ejecuta una serie de tests para verificar que todo está correctamente
instalado y configurado, SIN hacer scraping real ni enviar mensajes.

Uso:
    python test_bot.py

Verifica:
    1. Dependencias Python instaladas
    2. Variables de entorno en .env
    3. Conexión a Telegram (sin enviar mensaje)
    4. Base de datos SQLite
    5. Importación de módulos del proyecto
    6. Estructura de archivos del proyecto
"""

import sys
import os
import asyncio
from pathlib import Path

# Forzar UTF-8 en Windows para que los emojis y caracteres especiales se muestren bien
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        os.system("chcp 65001 > nul 2>&1")
    except Exception:
        pass

# Agregar el directorio raíz al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Contadores globales
_passed = 0
_failed = 0
_warnings = 0
_results = []  # (nombre, estado, observación)


def test_pass(name: str, obs: str = "OK"):
    global _passed
    _passed += 1
    _results.append((name, "✅ PASS", obs))
    print(f"  ✅ {name}: {obs}")


def test_fail(name: str, obs: str):
    global _failed
    _failed += 1
    _results.append((name, "❌ FAIL", obs))
    print(f"  ❌ {name}: {obs}")


def test_warn(name: str, obs: str):
    global _warnings
    _warnings += 1
    _results.append((name, "⚠️ WARN", obs))
    print(f"  ⚠️ {name}: {obs}")


# ============================================================
# TEST 1: DEPENDENCIAS PYTHON
# ============================================================
def test_dependencies():
    print("\n" + "=" * 60)
    print("📦 TEST 1: Dependencias Python")
    print("=" * 60)

    dependencies = {
        "playwright": "playwright",
        "playwright_stealth": "playwright-stealth",
        "sqlalchemy": "sqlalchemy",
        "telegram": "python-telegram-bot",
        "dotenv": "python-dotenv",
        "aiohttp": "aiohttp",
    }

    for module_name, pip_name in dependencies.items():
        try:
            __import__(module_name)
            test_pass(f"Módulo '{pip_name}'", "Instalado")
        except ImportError:
            test_fail(f"Módulo '{pip_name}'", f"No instalado. Ejecutá: pip install {pip_name}")


# ============================================================
# TEST 2: ARCHIVO .ENV Y VARIABLES
# ============================================================
def test_env_file():
    print("\n" + "=" * 60)
    print("🔑 TEST 2: Archivo .env y variables de entorno")
    print("=" * 60)

    env_path = PROJECT_ROOT / ".env"

    if not env_path.exists():
        test_fail(".env existe", "No encontrado. Ejecutá setup.bat o copiá .env.example a .env")
        return

    test_pass(".env existe", f"Encontrado en {env_path}")

    # Cargar .env
    from dotenv import load_dotenv
    load_dotenv(env_path)

    # Variables requeridas
    required_vars = {
        "TELEGRAM_BOT_TOKEN": "Token del bot de Telegram (@BotFather)",
        "TELEGRAM_CHAT_ID": "Tu Chat ID de Telegram (@userinfobot)",
    }

    # Variables opcionales (con defaults)
    optional_vars = {
        "DEPARTURE_DATE": "Fecha de ida",
        "RETURN_DATE": "Fecha de vuelta",
        "PASSENGERS": "Cantidad de pasajeros",
    }

    for var, desc in required_vars.items():
        value = os.getenv(var, "")
        if not value or value in ("123456789:ABCdefGHIjklMNOpqrsTUVwxyz", "987654321", ""):
            test_warn(f"Variable {var}", f"No configurada o tiene valor de ejemplo. → {desc}")
        else:
            # Ocultar parte del valor por seguridad
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "****"
            test_pass(f"Variable {var}", f"Configurada ({masked})")

    for var, desc in optional_vars.items():
        value = os.getenv(var, "")
        if value:
            test_pass(f"Variable {var}", f"= {value}")
        else:
            test_warn(f"Variable {var}", f"No definida (usará default). → {desc}")


# ============================================================
# TEST 3: CONEXIÓN A TELEGRAM
# ============================================================
async def test_telegram():
    print("\n" + "=" * 60)
    print("📱 TEST 3: Conexión a Telegram (sin enviar mensaje)")
    print("=" * 60)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz":
        test_warn("Token de Telegram", "No configurado. Salteando test de conexión.")
        return

    if not chat_id or chat_id == "987654321":
        test_warn("Chat ID de Telegram", "No configurado. Salteando test de conexión.")
        return

    try:
        from telegram import Bot

        bot = Bot(token=token)
        me = await bot.get_me()

        test_pass("Conexión a Telegram", f"Bot conectado: @{me.username} ({me.first_name})")

        # Verificar que el chat_id es válido intentando obtener info
        try:
            chat = await bot.get_chat(chat_id)
            chat_title = chat.title or chat.first_name or chat.username or "?"
            test_pass("Chat ID válido", f"Chat: {chat_title}")
        except Exception as e:
            test_warn("Chat ID", f"No se pudo verificar (puede estar OK): {str(e)[:60]}")

    except ImportError:
        test_fail("Telegram Bot", "python-telegram-bot no instalado")
    except Exception as e:
        test_fail("Conexión a Telegram", f"Error: {str(e)[:80]}")


# ============================================================
# TEST 4: BASE DE DATOS SQLITE
# ============================================================
def test_database():
    print("\n" + "=" * 60)
    print("💾 TEST 4: Base de datos SQLite")
    print("=" * 60)

    try:
        from src.database.models import Base, Flight, PriceHistory, AlertSent
        test_pass("Modelos importados", "Flight, PriceHistory, AlertSent")
    except ImportError as e:
        test_fail("Importar modelos", f"Error: {e}")
        return

    try:
        from sqlalchemy import create_engine, inspect

        # Usar base de datos temporal para el test
        test_db_path = PROJECT_ROOT / "data" / "test_temp.db"
        engine = create_engine(f"sqlite:///{test_db_path}", echo=False)

        # Crear tablas
        Base.metadata.create_all(engine)

        # Verificar que las tablas se crearon
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = {"flights", "price_history", "alerts_sent"}
        found_tables = set(tables)

        if expected_tables.issubset(found_tables):
            test_pass("Creación de tablas", f"Tablas creadas: {', '.join(sorted(found_tables))}")
        else:
            missing = expected_tables - found_tables
            test_fail("Creación de tablas", f"Faltan tablas: {', '.join(missing)}")

        # Verificar columnas de la tabla flights
        columns = [c["name"] for c in inspector.get_columns("flights")]
        critical_columns = ["id", "platform", "airlines_json", "price_usd", "price_ars",
                            "outbound_departure", "score", "search_timestamp"]

        missing_cols = [c for c in critical_columns if c not in columns]
        if not missing_cols:
            test_pass("Columnas de flights", f"{len(columns)} columnas verificadas")
        else:
            test_fail("Columnas de flights", f"Faltan: {', '.join(missing_cols)}")

        # Limpiar archivo de test
        engine.dispose()
        if test_db_path.exists():
            test_db_path.unlink()

    except Exception as e:
        test_fail("Base de datos", f"Error: {e}")
        # Limpiar
        test_db_path = PROJECT_ROOT / "data" / "test_temp.db"
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass


# ============================================================
# TEST 5: IMPORTACIÓN DE MÓDULOS DEL PROYECTO
# ============================================================
def test_imports():
    print("\n" + "=" * 60)
    print("📂 TEST 5: Importación de módulos del proyecto")
    print("=" * 60)

    modules_to_test = [
        ("src.config", "Configuración"),
        ("src.utils.logger", "Logger"),
        ("src.utils.helpers", "Helpers"),
        ("src.scrapers.base_scraper", "Base Scraper"),
        ("src.scrapers.turismo_city", "Scraper Turismo City"),
        ("src.scrapers.despegar", "Scraper Despegar"),
        ("src.database.models", "Modelos de BD"),
        ("src.database.db_manager", "Gestor de BD"),
        ("src.notifier.telegram_bot", "Bot Telegram"),
        ("src.analyzer.scorer", "Scorer de vuelos"),
    ]

    for module_path, desc in modules_to_test:
        try:
            __import__(module_path)
            test_pass(f"Importar {desc}", f"'{module_path}' OK")
        except ImportError as e:
            test_fail(f"Importar {desc}", f"Error: {e}")
        except Exception as e:
            test_warn(f"Importar {desc}", f"Se importó pero con advertencia: {str(e)[:60]}")


# ============================================================
# TEST 6: ESTRUCTURA DE ARCHIVOS
# ============================================================
def test_file_structure():
    print("\n" + "=" * 60)
    print("🗂️ TEST 6: Estructura de archivos del proyecto")
    print("=" * 60)

    required_files = [
        "src/main.py",
        "src/config.py",
        "src/__init__.py",
        "src/scrapers/__init__.py",
        "src/scrapers/base_scraper.py",
        "src/scrapers/turismo_city.py",
        "src/scrapers/despegar.py",
        "src/database/__init__.py",
        "src/database/models.py",
        "src/database/db_manager.py",
        "src/notifier/__init__.py",
        "src/notifier/telegram_bot.py",
        "src/analyzer/__init__.py",
        "src/analyzer/scorer.py",
        "src/utils/__init__.py",
        "src/utils/logger.py",
        "src/utils/helpers.py",
        "requirements.txt",
        ".env.example",
    ]

    for filepath in required_files:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            size = full_path.stat().st_size
            test_pass(f"Archivo {filepath}", f"Existe ({size:,} bytes)")
        else:
            test_fail(f"Archivo {filepath}", "NO ENCONTRADO")

    # Verificar directorios de datos
    data_dirs = ["data", "data/logs", "data/cache"]
    for d in data_dirs:
        full_path = PROJECT_ROOT / d
        if full_path.exists() and full_path.is_dir():
            test_pass(f"Directorio {d}/", "Existe")
        else:
            test_warn(f"Directorio {d}/", "No existe (se creará al ejecutar)")


# ============================================================
# TEST 7: VERIFICACIÓN DE SEGURIDAD
# ============================================================
def test_security():
    print("\n" + "=" * 60)
    print("🔒 TEST 7: Verificación de seguridad")
    print("=" * 60)

    dangerous_words = ["purchase", "credit_card", "payment"]
    src_dir = PROJECT_ROOT / "src"

    for word in dangerous_words:
        found_in = []
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            # Buscar la palabra como identificador, no en comentarios de restricción
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # Ignorar comentarios y docstrings que advierten sobre restricciones
                if stripped.startswith("#") or stripped.startswith("\"\"\"") or "NUNCA" in stripped:
                    continue
                if word.lower() in stripped.lower():
                    found_in.append(f"{py_file.name}:{i}")

        if found_in:
            test_fail(f"Palabra '{word}'", f"Encontrada en código: {', '.join(found_in)}")
        else:
            test_pass(f"Sin '{word}'", "Código seguro ✅")

    # Verificar que .env no se sube al repositorio
    gitignore = PROJECT_ROOT / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8", errors="ignore")
        if ".env" in content:
            test_pass("Gitignore protege .env", ".env está en .gitignore")
        else:
            test_warn("Gitignore", ".env NO está en .gitignore — riesgo de filtrar tokens")
    else:
        test_warn(".gitignore", "No existe — se recomienda crear uno")


# ============================================================
# TEST 8: FUNCIONALIDAD BÁSICA (sin scraping real)
# ============================================================
def test_basic_functionality():
    print("\n" + "=" * 60)
    print("⚙️ TEST 8: Funcionalidad básica")
    print("=" * 60)

    # Test config
    try:
        from src.config import (
            DEPARTURE_DATE, RETURN_DATE, PASSENGERS,
            PLATFORMS, BASELINE_PRICES, get_flexible_dates,
            validate_config,
        )
        test_pass("Configuración carga", f"Viaje: {DEPARTURE_DATE} → {RETURN_DATE}, {PASSENGERS} pax")

        # Test fechas flexibles
        dates = get_flexible_dates()
        test_pass("Fechas flexibles", f"{len(dates)} combinaciones generadas")

        # Test validación
        errors = validate_config()
        if errors:
            test_warn("Validación config", f"{len(errors)} advertencia(s): {errors[0][:50]}")
        else:
            test_pass("Validación config", "Sin errores")

    except Exception as e:
        test_fail("Configuración", f"Error: {e}")

    # Test scorer
    try:
        from src.analyzer.scorer import FlightScorer
        scorer = FlightScorer()

        test_flight = {
            "price_usd": 484,
            "outbound_departure": "08:30",
            "return_departure": "15:00",
            "origin_airport": "EZE",
            "return_airport": "EZE",
            "flight_type": "direct",
        }

        score = scorer.calculate_score(test_flight)
        explanation = scorer.explain_score(test_flight)

        test_pass("Scorer funciona",
                  f"Vuelo test @ USD $484: Score {score}/100 ({explanation['label']})")

    except Exception as e:
        test_fail("Scorer", f"Error: {e}")

    # Test helpers
    try:
        from src.utils.helpers import (
            format_price_ars, format_price_usd, usd_to_ars,
            price_vs_baseline, now_iso, now_argentina,
        )

        ars = format_price_ars(850000)
        usd = format_price_usd(484)
        conv = usd_to_ars(484)
        baseline = price_vs_baseline(484)

        test_pass("Helpers funcionan",
                  f"484 USD = {ars} ARS | Baseline: {baseline['label']}")

    except Exception as e:
        test_fail("Helpers", f"Error: {e}")


# ============================================================
# REPORTE FINAL
# ============================================================
def print_report():
    global _passed, _failed, _warnings, _results

    print("\n" + "═" * 60)
    print("📊 REPORTE FINAL DE VERIFICACIÓN")
    print("═" * 60)

    total = _passed + _failed + _warnings

    print(f"\n  ✅ Pasaron:      {_passed}/{total}")
    print(f"  ❌ Fallaron:     {_failed}/{total}")
    print(f"  ⚠️  Advertencias: {_warnings}/{total}")

    if _failed == 0:
        print("\n" + "═" * 60)
        print("  🎉 TODO OK — El bot está listo para usarse")
        print("═" * 60)
        print("\n  Próximo paso:")
        print("    python src/main.py --test")
        print("")
    else:
        print("\n" + "═" * 60)
        print(f"  ⚠️  HAY {_failed} PROBLEMA(S) QUE RESOLVER:")
        print("═" * 60)
        for name, status, obs in _results:
            if "FAIL" in status:
                print(f"\n  ❌ {name}")
                print(f"     → {obs}")
        print("")

    if _warnings > 0:
        print("  ℹ️  Advertencias (no bloqueantes):")
        for name, status, obs in _results:
            if "WARN" in status:
                print(f"     ⚠️ {name}: {obs}")
        print("")


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║  🧪 FLIGHT MONITOR BOT - Test de Verificación      ║")
    print("║  Verificando que todo esté instalado y configurado  ║")
    print("╚══════════════════════════════════════════════════════╝")

    # Ejecutar tests secuenciales
    test_dependencies()
    test_env_file()
    test_file_structure()
    test_imports()
    test_database()
    test_security()
    test_basic_functionality()

    # Test async (telegram)
    try:
        asyncio.run(test_telegram())
    except Exception as e:
        test_warn("Test Telegram", f"No se pudo ejecutar: {e}")

    # Reporte
    print_report()

    # Exit code
    sys.exit(1 if _failed > 0 else 0)


if __name__ == "__main__":
    main()
