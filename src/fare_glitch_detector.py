#!/usr/bin/env python3
"""
fare_glitch_detector.py — Detección de Glitches en Clases Tarifarias

Analiza todas las tarifas (fare classes) de cada vuelo y detecta anomalías:
- Clase más cara con precio menor que una clase más barata (inversión tarifaria)
- Precios $0 o negativos
- PromotionAmount activo sin reflejo en el precio
- Disponibilidad inconsistente entre clases

Cada anomalía se registra en un archivo de log y se alerta por Telegram.

Uso:
    python -m src.fare_glitch_detector              # Check único
    python -m src.fare_glitch_detector --loop       # Cada 60 minutos
    python -m src.fare_glitch_detector --loop 30    # Cada 30 minutos

Se ejecuta en segundo plano sin intervención del usuario.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta
from itertools import product as itertools_product
from pathlib import Path

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

API_URL = "https://flybondi.com/graphql"
API_KEY = os.getenv(
    "FLYBONDI_API_KEY",
    "b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa"
)

ORIGIN = "BUE"
DESTINATION = "FLN"
ADULTS = 2

DEPARTURE_DATES = ["2026-03-08", "2026-03-09", "2026-03-10", "2026-03-11"]
RETURN_DATES = ["2026-03-15", "2026-03-16", "2026-03-17", "2026-03-18"]

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
GLITCH_DIR = DATA_DIR / "glitch_logs"
GLITCH_DIR.mkdir(parents=True, exist_ok=True)

GLITCH_LOG = GLITCH_DIR / "fare_glitches.log"
GLITCH_HISTORY = GLITCH_DIR / "glitch_history.json"

SESSION_COOKIE = os.getenv("FLYBONDI_SESSION", "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8")

# Jerarquía normal de clases tarifarias (de más barata a más cara)
# Flybondi usa: ECONOMY / PLUS / PREMIUM
# Fare types: "economy" < "promo" < "plus" < "premium" < "business"
FARE_HIERARCHY = {
    "economy": 1,
    "light": 1,
    "basic": 1,
    "promo": 2,
    "standard": 3,
    "plus": 4,
    "classic": 4,
    "flex": 5,
    "premium": 6,
    "business": 7,
    "first": 8,
}

# Las fare classes de Flybondi por código
# B=Economy, M=Promo?, J=Plus, etc.
FARE_CLASS_HIERARCHY = {
    "B": 1,  # Economy básica
    "M": 2,  # Mid / Promo
    "Y": 3,  # Economy full
    "W": 4,  # Premium Economy
    "J": 5,  # Business/Plus
    "C": 6,  # Business full
    "F": 7,  # First
}

HEADERS = {
    "accept": "application/json",
    "accept-language": "es-ES,es;q=0.9",
    "authorization": f"Key {API_KEY}",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/ar/search/dates",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Mobile Safari/537.36"
    ),
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
    "x-fo-ui-version": "2.209.0",
}


GRAPHQL_QUERY = """
query FareGlitchDetector(
  $input: FlightsQueryInput!
  $origin: String!
  $destination: String!
  $currency: String!
  $start: Timestamp!
  $end: Timestamp!
) {
  viewer {
    flights(input: $input) {
      edges {
        node {
          id
          flightNo
          segmentFlightNo
          origin
          destination
          direction
          departureDate
          arrivalDate
          carrier
          equipmentId
          fares {
            fareRef
            passengerType
            class
            type
            availability
            prices {
              afterTax
              beforeTax
              baseBeforeTax
              promotionAmount
            }
          }
        }
      }
    }
    id
  }
  departures: fares(origin: $origin, destination: $destination, currency: $currency, start: $start, end: $end, sort: "departure") {
    id
    departure
    fares {
      price
      fCCode
      fBCode
    }
    lowestPrice
  }
}
""".strip()


# ============================================================================
# TELEGRAM
# ============================================================================

def send_telegram(message: str, silent: bool = False) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"   ⚠️  Telegram no configurado")
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
        return resp.status_code == 200
    except Exception as e:
        print(f"   ❌ Error Telegram: {e}")
        return False


# ============================================================================
# QUERY A LA API
# ============================================================================

def query_flights(departure_date: str, return_date: str) -> dict | None:
    """Hace la query GraphQL para obtener todos los fares de una combinación."""
    start_ts = int(datetime(2026, 3, 1).timestamp() * 1000)
    end_ts = int(datetime(2026, 3, 31, 23, 59, 59).timestamp() * 1000)

    variables = {
        "input": {
            "origin": ORIGIN,
            "destination": DESTINATION,
            "departureDate": departure_date,
            "returnDate": return_date,
            "currency": "ARS",
            "pax": {"adults": ADULTS, "children": 0, "infants": 0},
            "promoCode": None,
        },
        "origin": ORIGIN,
        "destination": DESTINATION,
        "currency": "ARS",
        "start": start_ts,
        "end": end_ts,
    }

    payload = {"query": GRAPHQL_QUERY, "variables": variables}
    cookies = {"FBSessionX-ar-ibe": SESSION_COOKIE}

    try:
        kwargs = {
            "headers": HEADERS,
            "json": payload,
            "cookies": cookies,
            "timeout": 30,
        }
        if USE_CURL:
            kwargs["impersonate"] = "chrome"

        resp = http.post(API_URL, **kwargs)

        if resp.status_code != 200:
            print(f"   ❌ HTTP {resp.status_code}")
            return None

        data = resp.json()
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {json.dumps(data['errors'])[:200]}")
            return None

        return data

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


# ============================================================================
# ANÁLISIS DE GLITCHES
# ============================================================================

def analyze_fares_for_glitches(data: dict, dep_date: str, ret_date: str) -> list[dict]:
    """
    Analiza los fares de cada vuelo y busca anomalías.
    
    Returns:
        Lista de glitches encontrados.
    """
    glitches = []

    try:
        edges = data.get("data", {}).get("viewer", {}).get("flights", {}).get("edges", [])
    except (AttributeError, TypeError):
        return []

    for edge in edges:
        node = edge.get("node", {})
        if not node:
            continue

        flight_no = node.get("flightNo", "???")
        direction = node.get("direction", "?")
        departure = node.get("departureDate", "")[:10]
        fares = node.get("fares", [])

        if not fares:
            continue

        # Filtrar solo fares de adultos
        adt_fares = [f for f in fares if f.get("passengerType") in ("ADT", "ADULT")]

        if not adt_fares:
            continue

        # === GLITCH 1: Inversión tarifaria (clase más cara, precio menor) ===
        fare_prices = []
        for fare in adt_fares:
            fare_type = (fare.get("type") or "").lower()
            fare_class = fare.get("class", "")
            after_tax = fare.get("prices", {}).get("afterTax", 0) or 0
            before_tax = fare.get("prices", {}).get("beforeTax", 0) or 0
            availability = fare.get("availability", 0) or 0

            # Determinar rango jerárquico
            hierarchy_rank = FARE_HIERARCHY.get(fare_type, 0)
            class_rank = FARE_CLASS_HIERARCHY.get(fare_class, 0)
            rank = max(hierarchy_rank, class_rank)

            fare_prices.append({
                "type": fare_type,
                "class": fare_class,
                "rank": rank,
                "afterTax": after_tax,
                "beforeTax": before_tax,
                "availability": availability,
                "basis": fare.get("basis", ""),
                "fareRef": fare.get("fareRef", ""),
            })

        # Comparar todas las combinaciones de fares
        for i, f1 in enumerate(fare_prices):
            for f2 in fare_prices[i+1:]:
                # f1 debería ser más barata si tiene menor rango
                if f1["rank"] > f2["rank"] and f1["afterTax"] < f2["afterTax"] and f1["afterTax"] > 0:
                    # ¡Clase más cara es más barata! GLITCH
                    savings = f2["afterTax"] - f1["afterTax"]
                    glitch = {
                        "type": "FARE_INVERSION",
                        "severity": "HIGH",
                        "flight_no": flight_no,
                        "direction": direction,
                        "departure": departure,
                        "dates": f"{dep_date} → {ret_date}",
                        "expensive_class": {
                            "type": f1["type"],
                            "class": f1["class"],
                            "rank": f1["rank"],
                            "price": f1["afterTax"],
                        },
                        "cheap_class": {
                            "type": f2["type"],
                            "class": f2["class"],
                            "rank": f2["rank"],
                            "price": f2["afterTax"],
                        },
                        "savings_per_person": savings,
                        "savings_total": savings * ADULTS,
                        "timestamp": datetime.now().isoformat(),
                    }
                    glitches.append(glitch)

                # Inversión inversa
                if f2["rank"] > f1["rank"] and f2["afterTax"] < f1["afterTax"] and f2["afterTax"] > 0:
                    savings = f1["afterTax"] - f2["afterTax"]
                    glitch = {
                        "type": "FARE_INVERSION",
                        "severity": "HIGH",
                        "flight_no": flight_no,
                        "direction": direction,
                        "departure": departure,
                        "dates": f"{dep_date} → {ret_date}",
                        "expensive_class": {
                            "type": f2["type"],
                            "class": f2["class"],
                            "rank": f2["rank"],
                            "price": f2["afterTax"],
                        },
                        "cheap_class": {
                            "type": f1["type"],
                            "class": f1["class"],
                            "rank": f1["rank"],
                            "price": f1["afterTax"],
                        },
                        "savings_per_person": savings,
                        "savings_total": savings * ADULTS,
                        "timestamp": datetime.now().isoformat(),
                    }
                    glitches.append(glitch)

        # === GLITCH 2: Precio $0 o negativo ===
        for fp in fare_prices:
            if fp["afterTax"] == 0 and fp["availability"] > 0:
                glitches.append({
                    "type": "ZERO_PRICE",
                    "severity": "CRITICAL",
                    "flight_no": flight_no,
                    "direction": direction,
                    "departure": departure,
                    "dates": f"{dep_date} → {ret_date}",
                    "fare": fp,
                    "timestamp": datetime.now().isoformat(),
                })

            if fp["afterTax"] < 0:
                glitches.append({
                    "type": "NEGATIVE_PRICE",
                    "severity": "CRITICAL",
                    "flight_no": flight_no,
                    "direction": direction,
                    "departure": departure,
                    "dates": f"{dep_date} → {ret_date}",
                    "fare": fp,
                    "timestamp": datetime.now().isoformat(),
                })

        # === GLITCH 3: PromotionAmount activo pero precio no reducido ===
        for fare in adt_fares:
            prices = fare.get("prices", {})
            promo_amount = prices.get("promotionAmount", 0) or 0
            after_tax = prices.get("afterTax", 0) or 0
            before_tax = prices.get("beforeTax", 0) or 0

            if promo_amount > 0:
                # Hay una promo activa — verificar si está aplicada
                if after_tax >= before_tax and before_tax > 0:
                    # La promo no parece estar reduciendo el precio
                    glitches.append({
                        "type": "PROMO_NOT_APPLIED",
                        "severity": "MEDIUM",
                        "flight_no": flight_no,
                        "direction": direction,
                        "departure": departure,
                        "dates": f"{dep_date} → {ret_date}",
                        "promo_amount": promo_amount,
                        "after_tax": after_tax,
                        "before_tax": before_tax,
                        "fare_type": fare.get("type", ""),
                        "timestamp": datetime.now().isoformat(),
                    })
                else:
                    # La promo SÍ está aplicada — registrar como info
                    glitches.append({
                        "type": "PROMO_DETECTED",
                        "severity": "INFO",
                        "flight_no": flight_no,
                        "direction": direction,
                        "departure": departure,
                        "dates": f"{dep_date} → {ret_date}",
                        "promo_amount": promo_amount,
                        "after_tax": after_tax,
                        "before_tax": before_tax,
                        "discount_pct": round((1 - after_tax / before_tax) * 100, 1) if before_tax > 0 else 0,
                        "fare_type": fare.get("type", ""),
                        "timestamp": datetime.now().isoformat(),
                    })

        # === GLITCH 4: Disponibilidad inconsistente ===
        avail_values = [fp["availability"] for fp in fare_prices if fp["availability"] > 0]
        if avail_values:
            max_avail = max(avail_values)
            min_avail = min(avail_values)
            if max_avail > 0 and min_avail == 0:
                # Hay clases con disponibilidad 0 y otras con stock — ¿error de inventario?
                sold_out = [fp for fp in fare_prices if fp["availability"] == 0]
                available = [fp for fp in fare_prices if fp["availability"] > 0]
                # Solo es interesante si la clase barata está agotada pero la cara tiene stock
                for s in sold_out:
                    for a in available:
                        if s["rank"] < a["rank"] and a["afterTax"] < s["afterTax"] * 1.5:
                            glitches.append({
                                "type": "AVAILABILITY_GLITCH",
                                "severity": "LOW",
                                "flight_no": flight_no,
                                "direction": direction,
                                "departure": departure,
                                "dates": f"{dep_date} → {ret_date}",
                                "sold_out_class": s,
                                "available_class": a,
                                "timestamp": datetime.now().isoformat(),
                            })

    return glitches


# ============================================================================
# LOGGING Y PERSISTENCIA
# ============================================================================

def append_glitch_log(glitches: list[dict]):
    """Registra los glitches en el archivo de log."""
    with open(GLITCH_LOG, "a", encoding="utf-8") as f:
        for g in glitches:
            severity = g.get("severity", "?")
            gtype = g.get("type", "?")
            flight = g.get("flight_no", "?")
            timestamp = g.get("timestamp", "?")

            line = f"[{timestamp}] [{severity}] {gtype} — Vuelo {flight}"

            if gtype == "FARE_INVERSION":
                exp = g.get("expensive_class", {})
                chp = g.get("cheap_class", {})
                line += (
                    f" | {exp['type']}({exp['class']}) ${exp['price']:,.0f} < "
                    f"{chp['type']}({chp['class']}) ${chp['price']:,.0f} | "
                    f"Ahorro: ${g['savings_total']:,.0f}"
                )
            elif gtype == "ZERO_PRICE":
                line += f" | Precio $0 en clase {g.get('fare', {}).get('type', '?')}"
            elif gtype == "PROMO_DETECTED":
                line += (
                    f" | Promo: ${g.get('promo_amount', 0):,.0f} | "
                    f"Descuento: {g.get('discount_pct', 0)}%"
                )
            elif gtype == "PROMO_NOT_APPLIED":
                line += f" | Promo ${g.get('promo_amount', 0):,.0f} NO APLICADA"

            f.write(line + "\n")


def load_glitch_history() -> list:
    if GLITCH_HISTORY.exists():
        try:
            return json.loads(GLITCH_HISTORY.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_glitch_history(history: list):
    # Mantener solo los últimos 500 glitches
    GLITCH_HISTORY.write_text(
        json.dumps(history[-500:], indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def is_duplicate_glitch(glitch: dict, history: list) -> bool:
    """Verifica si un glitch ya fue reportado recientemente (última hora)."""
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

    for h in history:
        if (
            h.get("type") == glitch.get("type")
            and h.get("flight_no") == glitch.get("flight_no")
            and h.get("dates") == glitch.get("dates")
            and h.get("timestamp", "") > one_hour_ago
        ):
            return True
    return False


# ============================================================================
# FLUJO PRINCIPAL
# ============================================================================

def run_check():
    """Ejecuta un análisis completo de glitches en fares."""
    now = datetime.now()
    print(f"\n{'=' * 70}")
    print(f"🔍 FARE GLITCH DETECTOR — {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Ruta: {ORIGIN} → {DESTINATION} | 👥 {ADULTS} adultos")
    print(f"{'=' * 70}")

    all_glitches = []
    date_combos = list(itertools_product(DEPARTURE_DATES, RETURN_DATES))
    total = len(date_combos)

    for i, (dep, ret) in enumerate(date_combos, 1):
        print(f"\n📅 [{i}/{total}] {dep} → {ret}")

        data = query_flights(dep, ret)
        if data is None:
            continue

        glitches = analyze_fares_for_glitches(data, dep, ret)

        if glitches:
            critical = [g for g in glitches if g["severity"] in ("CRITICAL", "HIGH")]
            info = [g for g in glitches if g["severity"] == "INFO"]
            other = [g for g in glitches if g["severity"] not in ("CRITICAL", "HIGH", "INFO")]

            if critical:
                print(f"   🚨 {len(critical)} glitches CRÍTICOS encontrados!")
            if other:
                print(f"   ⚠️  {len(other)} anomalías detectadas")
            if info:
                print(f"   ℹ️  {len(info)} promos activas detectadas")

            all_glitches.extend(glitches)
        else:
            print(f"   ✅ Sin anomalías")

        # Pausa entre requests
        if i < total:
            time.sleep(1.5)

    # ========================================================================
    # RESUMEN Y ALERTAS
    # ========================================================================

    if not all_glitches:
        print(f"\n✅ Sin glitches detectados en {total} combinaciones de fechas.")
        return

    # Clasificar
    critical = [g for g in all_glitches if g["severity"] in ("CRITICAL", "HIGH")]
    medium = [g for g in all_glitches if g["severity"] == "MEDIUM"]
    info = [g for g in all_glitches if g["severity"] == "INFO"]
    low = [g for g in all_glitches if g["severity"] == "LOW"]

    print(f"\n{'=' * 70}")
    print(f"📊 RESUMEN DE GLITCHES")
    print(f"{'=' * 70}")
    print(f"   🚨 Críticos/Altos: {len(critical)}")
    print(f"   ⚠️  Medios: {len(medium)}")
    print(f"   ℹ️  Info (promos): {len(info)}")
    print(f"   📋 Bajos: {len(low)}")

    # Registrar en log
    append_glitch_log(all_glitches)
    print(f"\n   💾 Glitches registrados en: {GLITCH_LOG.name}")

    # Cargar historial para evitar duplicados en alertas
    history = load_glitch_history()

    # Alertar por Telegram si hay glitches críticos nuevos
    new_critical = [g for g in critical if not is_duplicate_glitch(g, history)]

    if new_critical:
        msg = f"🚨 *FARE GLITCH ALERT — Flybondi*\n\n"
        msg += f"*{len(new_critical)} glitch(es) nuevo(s) detectado(s):*\n\n"

        for g in new_critical[:5]:
            if g["type"] == "FARE_INVERSION":
                exp = g.get("expensive_class", {})
                chp = g.get("cheap_class", {})
                msg += (
                    f"🔄 *Inversión tarifaria* — Vuelo {g['flight_no']}\n"
                    f"   `{exp['type']}` (rango {exp['rank']}) → ${exp['price']:,.0f}\n"
                    f"   `{chp['type']}` (rango {chp['rank']}) → ${chp['price']:,.0f}\n"
                    f"   💰 Ahorro potencial: *${g['savings_total']:,.0f} ARS*\n"
                    f"   📅 {g['dates']}\n\n"
                )
            elif g["type"] == "ZERO_PRICE":
                msg += (
                    f"💥 *Precio $0* — Vuelo {g['flight_no']}\n"
                    f"   📅 {g['dates']}\n\n"
                )
            elif g["type"] == "NEGATIVE_PRICE":
                msg += (
                    f"💥 *Precio negativo* — Vuelo {g['flight_no']}\n"
                    f"   📅 {g['dates']}\n\n"
                )

        msg += f"🕐 {now.strftime('%d/%m/%Y %H:%M')}"
        send_telegram(msg)
        print(f"   📨 Alerta enviada a Telegram ({len(new_critical)} glitches)")

    # Alertar si hay promos nuevas
    new_promos = [g for g in info if g["type"] == "PROMO_DETECTED" and not is_duplicate_glitch(g, history)]
    if new_promos:
        msg = f"🏷️ *PROMO DETECTADA — Flybondi*\n\n"
        for p in new_promos[:5]:
            msg += (
                f"✈️ Vuelo {p['flight_no']} ({p['direction']})\n"
                f"   Descuento: *{p.get('discount_pct', 0)}%*\n"
                f"   Promo: ${p.get('promo_amount', 0):,.0f}\n"
                f"   Precio final: ${p.get('after_tax', 0):,.0f}\n"
                f"   📅 {p['dates']}\n\n"
            )
        msg += f"🕐 {now.strftime('%d/%m/%Y %H:%M')}"
        send_telegram(msg, silent=True)
        print(f"   📨 Alerta de promo enviada ({len(new_promos)} promos)")

    # Actualizar historial
    history.extend(all_glitches)
    save_glitch_history(history)

    # Guardar snapshot detallado
    snapshot_file = GLITCH_DIR / f"glitch_snapshot_{now.strftime('%Y%m%d_%H%M%S')}.json"
    snapshot_file.write_text(
        json.dumps({
            "timestamp": now.isoformat(),
            "total_glitches": len(all_glitches),
            "critical": len(critical),
            "medium": len(medium),
            "info": len(info),
            "low": len(low),
            "glitches": all_glitches,
        }, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"   💾 Snapshot: {snapshot_file.name}")


def run_loop(interval_minutes: int = 60):
    """Ejecuta el detector en loop continuo."""
    print(f"\n🔄 MODO DAEMON — Escaneando glitches cada {interval_minutes} min")
    print(f"   Presioná Ctrl+C para detener\n")

    send_telegram(
        f"🔍 *Fare Glitch Detector activado*\n\n"
        f"Intervalo: cada {interval_minutes} min\n"
        f"Buscando inversiones tarifarias, precios $0 y promos ocultas.",
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

            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            print(f"\n⏳ Próximo scan: {next_run.strftime('%H:%M:%S')}")
            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n🛑 Fare Glitch Detector detenido.")
            send_telegram("🛑 Fare Glitch Detector detenido.", silent=True)
            break


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🔍 Detector de Glitches en Clases Tarifarias de Flybondi",
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
