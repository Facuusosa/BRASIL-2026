#!/usr/bin/env python3
"""
feature_flag_monitor.py — Monitoreo de Feature Flags de Flybondi

Consulta el endpoint de experimentación (experimentation-beta.sts.flybondi.com)
y los JavaScript bundles de flybondi.com para detectar cambios en feature flags.

Si una flag clave cambia (ej: enable_usd_payment, enable_uba_discount,
enable_promo, etc.), envía una alerta por Telegram.

Uso:
    python -m src.feature_flag_monitor              # Check único
    python -m src.feature_flag_monitor --loop       # Cada 60 minutos
    python -m src.feature_flag_monitor --loop 30    # Cada 30 minutos

Se ejecuta en segundo plano sin intervención del usuario.
"""

import os
import sys
import json
import time
import re
import argparse
from datetime import datetime
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from curl_cffi import requests as http
    USE_CURL = True
except ImportError:
    import requests as http
    USE_CURL = False

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

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
FLAGS_DIR = DATA_DIR / "feature_flags"
FLAGS_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = FLAGS_DIR / "flag_state.json"
LOG_FILE = FLAGS_DIR / "flag_changes.log"

# Endpoints a consultar para detectar feature flags
EXPERIMENTATION_ENDPOINTS = [
    "https://experimentation-beta.sts.flybondi.com/flags",
    "https://experimentation-beta.sts.flybondi.com/api/flags",
    "https://experimentation-beta.sts.flybondi.com/v1/flags",
    "https://experimentation-beta.sts.flybondi.com/experiments",
    "https://experimentation-beta.sts.flybondi.com/api/experiments",
    "https://experimentation-beta.sts.flybondi.com/config",
]

# URLs de assets JS de Flybondi que podrían contener feature flags inline
JS_BUNDLE_URLS = [
    "https://flybondi.com/ar/search/dates",
    "https://flybondi.com/ar/search/results",
    "https://flybondi.com/ar",
]

# Keywords que indican feature flags relevantes para descuentos/precios
FLAG_KEYWORDS = [
    "enable_usd", "enable_uba", "enable_promo", "enable_discount",
    "enable_club", "enable_flex", "enable_bundle", "enable_loyalty",
    "enable_credit", "enable_voucher", "enable_gift", "enable_refer",
    "enable_special", "enable_cheap", "enable_low", "enable_flash",
    "enable_sale", "enable_offer", "enable_dynamic", "enable_surge",
    "show_promo", "show_discount", "show_banner", "show_offer",
    "ab_test", "experiment", "feature_flag", "feature_toggle",
    "price_strategy", "pricing_rule", "fare_rule", "commission",
    "payment_method", "currency_switch", "market_origin",
    "carnival", "carnaval", "hot_sale", "black_friday", "cyber",
    "FO_ENABLE", "FO_FEATURE", "FO_EXPERIMENT", "FO_AB",
    "ff_", "flag_", "toggle_", "experiment_",
]

HEADERS = {
    "accept": "application/json, text/html, */*",
    "accept-language": "es-ES,es;q=0.9,en;q=0.8",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Safari/537.36"
    ),
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
}


# ============================================================================
# TELEGRAM
# ============================================================================

def send_telegram(message: str, silent: bool = False) -> bool:
    """Envía un mensaje a Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"   ⚠️  Telegram no configurado. Mensaje: {message[:200]}")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_notification": silent,
        }
        resp = http.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("   📨 Alerta enviada a Telegram ✅")
            return True
        else:
            print(f"   ❌ Error Telegram: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error enviando a Telegram: {e}")
        return False


# ============================================================================
# ESTADO PERSISTENTE
# ============================================================================

def load_state() -> dict:
    """Carga el estado anterior de las feature flags."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict):
    """Guarda el estado actual de las feature flags."""
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def append_log(message: str):
    """Agrega un entry al log de cambios."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


# ============================================================================
# DETECCIÓN DE FLAGS VIA ENDPOINTS
# ============================================================================

def check_experimentation_endpoints() -> dict:
    """
    Intenta consultar los endpoints de experimentación.
    Devuelve un dict con los datos encontrados.
    """
    results = {}

    for endpoint in EXPERIMENTATION_ENDPOINTS:
        try:
            kwargs = {"headers": HEADERS, "timeout": 15}
            if USE_CURL:
                kwargs["impersonate"] = "chrome"

            resp = http.get(endpoint, **kwargs)

            result_entry = {
                "status_code": resp.status_code,
                "content_type": resp.headers.get("content-type", ""),
                "timestamp": datetime.now().isoformat(),
            }

            if resp.status_code == 200:
                # Intentar parsear JSON
                try:
                    data = resp.json()
                    result_entry["data"] = data
                    result_entry["type"] = "json"
                    print(f"   ✅ {endpoint} → JSON ({len(str(data))} chars)")
                except Exception:
                    text = resp.text[:5000]
                    result_entry["data"] = text
                    result_entry["type"] = "text"
                    print(f"   ✅ {endpoint} → TEXT ({len(text)} chars)")
            else:
                result_entry["data"] = None
                print(f"   ⚪ {endpoint} → HTTP {resp.status_code}")

            results[endpoint] = result_entry

        except Exception as e:
            print(f"   ❌ {endpoint} → Error: {e}")
            results[endpoint] = {
                "status_code": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    return results


# ============================================================================
# DETECCIÓN DE FLAGS VIA JavaScript BUNDLES
# ============================================================================

def extract_flags_from_js(html_content: str) -> dict:
    """
    Busca feature flags, configuración y variables de experimentación
    dentro del HTML/JS de las páginas de Flybondi.
    """
    flags_found = {}

    # === Patrón 1: Variables tipo window.__CONFIG__ o window.__FLAGS__ ===
    config_patterns = [
        r'window\.__CONFIG__\s*=\s*({[^;]+})',
        r'window\.__FLAGS__\s*=\s*({[^;]+})',
        r'window\.__EXPERIMENTS__\s*=\s*({[^;]+})',
        r'window\.__FEATURE_FLAGS__\s*=\s*({[^;]+})',
        r'window\.__NEXT_DATA__\s*=\s*({.+?})\s*;?\s*</script>',
        r'"featureFlags"\s*:\s*({[^}]+})',
        r'"features"\s*:\s*({[^}]+})',
        r'"experiments"\s*:\s*({[^}]+})',
        r'"flags"\s*:\s*({[^}]+})',
        r'"toggles"\s*:\s*({[^}]+})',
        r'"abTests"\s*:\s*({[^}]+})',
    ]

    for pattern in config_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict):
                    for key, value in data.items():
                        key_lower = key.lower()
                        if any(kw.lower() in key_lower for kw in FLAG_KEYWORDS):
                            flags_found[key] = value
            except (json.JSONDecodeError, TypeError):
                pass

    # === Patrón 2: Strings tipo "enable_xxx": true/false ===
    flag_pattern = r'"((?:enable|disable|show|hide|use|allow|block|ff_|flag_|toggle_|FO_)[a-zA-Z_]+)"\s*:\s*(true|false|"[^"]*"|\d+)'
    for match in re.finditer(flag_pattern, html_content, re.IGNORECASE):
        key = match.group(1)
        value = match.group(2)
        if value == "true":
            value = True
        elif value == "false":
            value = False
        elif value.startswith('"'):
            value = value.strip('"')
        else:
            try:
                value = int(value)
            except ValueError:
                pass
        flags_found[key] = value

    # === Patrón 3: Buscar en <script> tags con JSON embebido ===
    script_pattern = r'<script[^>]*>\s*({[^<]+})\s*</script>'
    for match in re.finditer(script_pattern, html_content):
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                _extract_nested_flags(data, flags_found)
        except (json.JSONDecodeError, TypeError):
            pass

    # === Patrón 4: Environment/Config variables en el bundle ===
    env_pattern = r'(?:process\.env\.)(NEXT_PUBLIC_[A-Z_]+|REACT_APP_[A-Z_]+|FO_[A-Z_]+)'
    for match in re.finditer(env_pattern, html_content):
        key = match.group(1)
        flags_found[f"env:{key}"] = "referenced"

    return flags_found


def _extract_nested_flags(data: dict, output: dict, prefix: str = ""):
    """Extrae flags recursivamente de un dict anidado."""
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        key_lower = key.lower()

        if any(kw.lower() in key_lower for kw in FLAG_KEYWORDS):
            output[full_key] = value

        if isinstance(value, dict) and len(str(value)) < 10000:
            _extract_nested_flags(value, output, full_key)


def check_js_bundles() -> dict:
    """
    Descarga las páginas de Flybondi y extrae feature flags de su JavaScript.
    """
    all_flags = {}

    for url in JS_BUNDLE_URLS:
        try:
            kwargs = {"headers": HEADERS, "timeout": 20}
            if USE_CURL:
                kwargs["impersonate"] = "chrome"

            resp = http.get(url, **kwargs)

            if resp.status_code == 200:
                flags = extract_flags_from_js(resp.text)
                if flags:
                    print(f"   🔍 {url} → {len(flags)} flags encontradas")
                    for key, val in flags.items():
                        all_flags[f"{url}|{key}"] = val
                else:
                    print(f"   ⚪ {url} → Sin flags detectadas")
            else:
                print(f"   ⚠️  {url} → HTTP {resp.status_code}")

        except Exception as e:
            print(f"   ❌ {url} → Error: {e}")

    return all_flags


# ============================================================================
# DETECCIÓN DE CAMBIOS
# ============================================================================

def detect_changes(old_state: dict, new_state: dict) -> list[dict]:
    """
    Compara dos estados de feature flags y detecta cambios.
    Returns: lista de cambios detectados
    """
    changes = []

    # Flags nuevas
    for key in new_state:
        if key not in old_state:
            changes.append({
                "type": "NEW",
                "key": key,
                "old_value": None,
                "new_value": new_state[key],
            })

    # Flags que cambiaron de valor
    for key in new_state:
        if key in old_state and str(new_state[key]) != str(old_state.get(key)):
            changes.append({
                "type": "CHANGED",
                "key": key,
                "old_value": old_state[key],
                "new_value": new_state[key],
            })

    # Flags que desaparecieron
    for key in old_state:
        if key not in new_state:
            changes.append({
                "type": "REMOVED",
                "key": key,
                "old_value": old_state[key],
                "new_value": None,
            })

    return changes


# ============================================================================
# FLUJO PRINCIPAL
# ============================================================================

def run_check():
    """Ejecuta un check completo de feature flags."""
    now = datetime.now()
    print(f"\n{'=' * 70}")
    print(f"🔬 FEATURE FLAG MONITOR — {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'=' * 70}")

    # 1. Cargar estado anterior
    old_state = load_state()
    is_first_run = not bool(old_state)

    # 2. Consultar endpoints de experimentación
    print("\n📡 Consultando endpoints de experimentación...")
    endpoint_flags = check_experimentation_endpoints()

    # 3. Extraer flags de JavaScript bundles
    print("\n🔍 Analizando JavaScript bundles...")
    js_flags = check_js_bundles()

    # 4. Consolidar nuevo estado
    new_state = {}

    # Agregar flags de endpoints (con prefijo)
    for endpoint, data in endpoint_flags.items():
        if data.get("data") and data.get("type") == "json":
            if isinstance(data["data"], dict):
                for key, val in data["data"].items():
                    new_state[f"endpoint:{key}"] = val
        # También guardar el status code como indicador
        new_state[f"status:{endpoint}"] = data.get("status_code")

    # Agregar flags de JS
    for key, val in js_flags.items():
        new_state[f"js:{key}"] = val

    # 5. Detectar cambios
    if is_first_run:
        print(f"\n📦 Primera ejecución — guardando {len(new_state)} flags como baseline")
        append_log(f"BASELINE: {len(new_state)} flags iniciales guardadas")
    else:
        changes = detect_changes(old_state, new_state)

        if changes:
            print(f"\n🚨 ¡{len(changes)} CAMBIOS DETECTADOS!")
            print("-" * 50)

            # Clasificar cambios por importancia
            critical_changes = []
            info_changes = []

            for ch in changes:
                key_lower = ch["key"].lower()
                # Determinar si es un cambio "crítico" (relacionado con precios/descuentos)
                is_critical = any(kw in key_lower for kw in [
                    "price", "promo", "discount", "usd", "uba", "club",
                    "loyalty", "sale", "offer", "flash", "carnival", "carnaval",
                    "commission", "fare", "payment", "currency", "special",
                ])

                if is_critical:
                    critical_changes.append(ch)
                else:
                    info_changes.append(ch)

                emoji = {"NEW": "🆕", "CHANGED": "🔄", "REMOVED": "🗑️"}.get(ch["type"], "❓")
                print(f"   {emoji} [{ch['type']}] {ch['key']}")
                print(f"      Antes: {ch['old_value']}")
                print(f"      Ahora: {ch['new_value']}")
                print()

                append_log(
                    f"{ch['type']}: {ch['key']} | "
                    f"old={ch['old_value']} → new={ch['new_value']}"
                )

            # Enviar alerta Telegram si hay cambios críticos
            if critical_changes:
                msg = f"🚨 *FEATURE FLAG ALERT — Flybondi*\n\n"
                msg += f"Se detectaron *{len(critical_changes)} cambio(s) crítico(s)*:\n\n"

                for ch in critical_changes[:10]:  # Limitar a 10 para Telegram
                    emoji = {"NEW": "🆕", "CHANGED": "🔄", "REMOVED": "🗑️"}.get(ch["type"], "❓")
                    msg += f"{emoji} `{ch['key']}`\n"
                    msg += f"   Antes: `{ch['old_value']}`\n"
                    msg += f"   Ahora: `{ch['new_value']}`\n\n"

                msg += f"🕐 {now.strftime('%d/%m/%Y %H:%M')}"
                send_telegram(msg)

            if info_changes:
                print(f"\n   ℹ️  También hay {len(info_changes)} cambios informativos (no alertados)")

        else:
            print(f"\n✅ Sin cambios detectados ({len(new_state)} flags monitoreadas)")

    # 6. Guardar nuevo estado
    save_state(new_state)

    # 7. Guardar snapshot con timestamp
    snapshot_file = FLAGS_DIR / f"snapshot_{now.strftime('%Y%m%d_%H%M%S')}.json"
    snapshot_file.write_text(
        json.dumps({
            "timestamp": now.isoformat(),
            "total_flags": len(new_state),
            "flags": new_state,
        }, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n   💾 Snapshot guardado: {snapshot_file.name}")

    return new_state


def run_loop(interval_minutes: int = 60):
    """Ejecuta el monitor en loop continuo."""
    print(f"\n🔄 MODO DAEMON — Chequeando flags cada {interval_minutes} min")
    print(f"   Presioná Ctrl+C para detener\n")

    send_telegram(
        f"🔬 *Feature Flag Monitor activado*\n\n"
        f"Intervalo: cada {interval_minutes} min\n"
        f"Monitoreando flags de precios, promos y descuentos.",
        silent=True,
    )

    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"\n{'#' * 70}")
            print(f"# ITERACIÓN #{iteration}")
            print(f"{'#' * 70}")

            run_check()

            next_run = datetime.now()
            from datetime import timedelta
            next_run += timedelta(minutes=interval_minutes)
            print(f"\n⏳ Próximo check: {next_run.strftime('%H:%M:%S')}")

            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n🛑 Feature Flag Monitor detenido.")
            send_telegram("🛑 Feature Flag Monitor detenido.", silent=True)
            break


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🔬 Monitor de Feature Flags de Flybondi",
    )
    parser.add_argument(
        "--loop", nargs="?", const=60, type=int, metavar="MIN",
        help="Modo daemon, chequea cada N minutos (default: 60)",
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="No enviar alertas por Telegram",
    )

    args = parser.parse_args()

    if args.no_telegram:
        global TELEGRAM_BOT_TOKEN
        TELEGRAM_BOT_TOKEN = ""

    if args.loop is not None:
        run_loop(args.loop)
    else:
        run_check()


if __name__ == "__main__":
    main()
