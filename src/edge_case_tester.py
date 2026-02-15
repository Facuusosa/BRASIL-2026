#!/usr/bin/env python3
"""
edge_case_tester.py — Prueba de Límites (Edge Cases) en la API de Flybondi

Envía peticiones "locas" a la API GraphQL para descubrir comportamientos
inesperados que podrían revelar oportunidades o bugs:

- 0 adultos, 99 adultos, 10 niños sin adultos
- Fechas del pasado, fechas muy lejanas (2030)
- Combinaciones inválidas de clases tarifarias
- Destinos inexistentes o swapeados
- Monedas extrañas (USD, BRL, EUR)
- PromoCode con valores especiales (vacío, null, admin, test, etc.)
- Market origins diferentes (ar, br, us, uk)

Registra cualquier respuesta inesperada (precio $0, error 500, datos sin 
sentido, status 200 donde debería haber fallo) en un archivo de errores.

Uso:
    python -m src.edge_case_tester              # Ejecutar una vez
    python -m src.edge_case_tester --daily      # Solo ejecutar si no se corrió hoy
    python -m src.edge_case_tester --no-telegram

Se ejecuta una vez por día (idealmente con un scheduler).
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, date, timedelta
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

SESSION_COOKIE = os.getenv("FLYBONDI_SESSION", "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8")

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
EDGE_DIR = DATA_DIR / "edge_cases"
EDGE_DIR.mkdir(parents=True, exist_ok=True)

ERROR_LOG = EDGE_DIR / "edge_case_errors.log"
LAST_RUN_FILE = EDGE_DIR / "last_run.txt"

BASE_HEADERS = {
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
query EdgeCaseTest(
  $input: FlightsQueryInput!
) {
  viewer {
    flights(input: $input) {
      searchUrl
      edges {
        node {
          id
          flightNo
          origin
          destination
          direction
          departureDate
          arrivalDate
          currency
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
}
""".strip()


# ============================================================================
# TELEGRAM
# ============================================================================

def send_telegram(message: str, silent: bool = False) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
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
    except Exception:
        return False


# ============================================================================
# EDGE CASES A PROBAR
# ============================================================================

def generate_edge_cases() -> list[dict]:
    """
    Genera una lista de edge cases para probar contra la API.
    Cada edge case es un dict con:
        - name: identificador del edge case
        - description: qué estamos probando
        - variables: las variables GraphQL a enviar
        - headers_override: headers extra/modificados (opcional)
        - expect: lo que esperamos que pase (para saber si es inesperado)
    """
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    far_future = "2030-12-31"
    normal_dep = "2026-03-09"
    normal_ret = "2026-03-16"

    start_ts = int(datetime(2026, 3, 1).timestamp() * 1000)
    end_ts = int(datetime(2026, 3, 31, 23, 59, 59).timestamp() * 1000)

    def make_vars(origin="BUE", destination="FLN", dep=normal_dep, ret=normal_ret,
                  currency="ARS", adults=2, children=0, infants=0,
                  promo_code=None, start=start_ts, end=end_ts):
        return {
            "input": {
                "origin": origin,
                "destination": destination,
                "departureDate": dep,
                "returnDate": ret,
                "currency": currency,
                "pax": {
                    "adults": adults,
                    "children": children,
                    "infants": infants,
                },
                "promoCode": promo_code,
            }
        }

    cases = []

    # === GRUPO 1: Pasajeros anormales ===
    cases.append({
        "name": "zero_adults",
        "description": "0 adultos — ¿acepta la API?",
        "variables": make_vars(adults=0),
        "expect": "error",
    })
    cases.append({
        "name": "many_adults",
        "description": "99 adultos — ¿overflow o precio diferente?",
        "variables": make_vars(adults=99),
        "expect": "error",
    })
    cases.append({
        "name": "one_adult",
        "description": "1 adulto — ¿precio proporcional o diferente?",
        "variables": make_vars(adults=1),
        "expect": "success_cheaper",
    })
    cases.append({
        "name": "children_no_adults",
        "description": "3 niños sin adultos",
        "variables": make_vars(adults=0, children=3),
        "expect": "error",
    })
    cases.append({
        "name": "many_infants",
        "description": "2 adultos + 10 infantes",
        "variables": make_vars(adults=2, infants=10),
        "expect": "error",
    })
    cases.append({
        "name": "negative_adults",
        "description": "-1 adultos — ¿crash?",
        "variables": make_vars(adults=-1),
        "expect": "error",
    })

    # === GRUPO 2: Fechas anormales ===
    cases.append({
        "name": "past_date",
        "description": f"Fecha del pasado ({yesterday})",
        "variables": make_vars(dep=yesterday, ret=normal_ret),
        "expect": "error",
    })
    cases.append({
        "name": "same_day",
        "description": "Ida y vuelta el mismo día",
        "variables": make_vars(dep=normal_dep, ret=normal_dep),
        "expect": "success_or_empty",
    })
    cases.append({
        "name": "inverted_dates",
        "description": "Vuelta antes de ida",
        "variables": make_vars(dep=normal_ret, ret=normal_dep),
        "expect": "error",
    })
    cases.append({
        "name": "far_future",
        "description": f"Fecha muy lejana ({far_future})",
        "variables": make_vars(dep=far_future, ret="2031-01-07"),
        "expect": "error_or_empty",
    })
    cases.append({
        "name": "today_departure",
        "description": "Salir hoy mismo",
        "variables": make_vars(dep=today, ret=normal_ret),
        "expect": "success_or_empty",
    })
    cases.append({
        "name": "no_return",
        "description": "Sin fecha de vuelta (null)",
        "variables": make_vars(ret=None),
        "expect": "one_way_or_error",
    })
    cases.append({
        "name": "invalid_date_format",
        "description": "Fecha con formato incorrecto",
        "variables": make_vars(dep="09/03/2026", ret="16/03/2026"),
        "expect": "error",
    })

    # === GRUPO 3: Rutas anormales ===
    cases.append({
        "name": "swapped_route",
        "description": "Ruta invertida: FLN → BUE",
        "variables": make_vars(origin="FLN", destination="BUE"),
        "expect": "success_different_prices",
    })
    cases.append({
        "name": "same_origin_dest",
        "description": "BUE → BUE (mismo origen y destino)",
        "variables": make_vars(origin="BUE", destination="BUE"),
        "expect": "error",
    })
    cases.append({
        "name": "nonexistent_airport",
        "description": "Aeropuerto que no existe: ZZZ",
        "variables": make_vars(origin="BUE", destination="ZZZ"),
        "expect": "error",
    })
    cases.append({
        "name": "domestic_route",
        "description": "Ruta doméstica: BUE → COR (Córdoba)",
        "variables": make_vars(origin="BUE", destination="COR"),
        "expect": "success",
    })

    # === GRUPO 4: Monedas ===
    cases.append({
        "name": "currency_usd",
        "description": "Precio en USD",
        "variables": make_vars(currency="USD"),
        "expect": "success_in_usd",
    })
    cases.append({
        "name": "currency_brl",
        "description": "Precio en BRL (reales)",
        "variables": make_vars(currency="BRL"),
        "expect": "success_or_error",
    })
    cases.append({
        "name": "currency_eur",
        "description": "Precio en EUR",
        "variables": make_vars(currency="EUR"),
        "expect": "success_or_error",
    })
    cases.append({
        "name": "currency_invalid",
        "description": "Moneda inexistente: XYZ",
        "variables": make_vars(currency="XYZ"),
        "expect": "error",
    })
    cases.append({
        "name": "currency_clp",
        "description": "Precio en CLP (pesos chilenos)",
        "variables": make_vars(currency="CLP"),
        "expect": "success_or_error",
    })

    # === GRUPO 5: Promo Codes ===
    cases.append({
        "name": "promo_empty",
        "description": "PromoCode vacío",
        "variables": make_vars(promo_code=""),
        "expect": "success_no_discount",
    })
    cases.append({
        "name": "promo_admin",
        "description": "PromoCode 'ADMIN'",
        "variables": make_vars(promo_code="ADMIN"),
        "expect": "error_or_no_discount",
    })
    cases.append({
        "name": "promo_test",
        "description": "PromoCode 'TEST'",
        "variables": make_vars(promo_code="TEST"),
        "expect": "error_or_no_discount",
    })
    cases.append({
        "name": "promo_debug",
        "description": "PromoCode 'DEBUG'",
        "variables": make_vars(promo_code="DEBUG"),
        "expect": "error_or_no_discount",
    })
    cases.append({
        "name": "promo_free",
        "description": "PromoCode 'FREE'",
        "variables": make_vars(promo_code="FREE"),
        "expect": "error_or_no_discount",
    })
    cases.append({
        "name": "promo_100off",
        "description": "PromoCode '100OFF'",
        "variables": make_vars(promo_code="100OFF"),
        "expect": "error_or_no_discount",
    })
    cases.append({
        "name": "promo_carnaval",
        "description": "PromoCode 'CARNAVAL'",
        "variables": make_vars(promo_code="CARNAVAL"),
        "expect": "possible_discount",
    })
    cases.append({
        "name": "promo_carnaval2026",
        "description": "PromoCode 'CARNAVAL2026'",
        "variables": make_vars(promo_code="CARNAVAL2026"),
        "expect": "possible_discount",
    })
    cases.append({
        "name": "promo_flybondi",
        "description": "PromoCode 'FLYBONDI'",
        "variables": make_vars(promo_code="FLYBONDI"),
        "expect": "possible_discount",
    })
    cases.append({
        "name": "promo_verano",
        "description": "PromoCode 'VERANO'",
        "variables": make_vars(promo_code="VERANO"),
        "expect": "possible_discount",
    })
    cases.append({
        "name": "promo_hotsale",
        "description": "PromoCode 'HOTSALE'",
        "variables": make_vars(promo_code="HOTSALE"),
        "expect": "possible_discount",
    })
    cases.append({
        "name": "promo_club",
        "description": "PromoCode 'CLUB'",
        "variables": make_vars(promo_code="CLUB"),
        "expect": "possible_discount",
    })
    cases.append({
        "name": "promo_sql_injection",
        "description": "PromoCode con SQL injection attempt",
        "variables": make_vars(promo_code="' OR '1'='1"),
        "expect": "error",
    })

    # === GRUPO 6: Market Origin ===
    for market in ["br", "us", "uk", "py", "uy", "cl", "co", "pe", "mx"]:
        cases.append({
            "name": f"market_{market}",
            "description": f"Market origin = {market.upper()}",
            "variables": make_vars(),
            "headers_override": {"x-fo-market-origin": market},
            "expect": "success_maybe_different_price",
        })

    return cases


# ============================================================================
# EJECUCIÓN DE EDGE CASES
# ============================================================================

def run_edge_case(case: dict) -> dict:
    """
    Ejecuta un edge case individual contra la API.
    Returns: dict con el resultado del test.
    """
    name = case["name"]
    variables = case["variables"]

    headers = BASE_HEADERS.copy()
    if "headers_override" in case:
        headers.update(case["headers_override"])

    payload = {"query": GRAPHQL_QUERY, "variables": variables}
    cookies = {"FBSessionX-ar-ibe": SESSION_COOKIE}

    result = {
        "name": name,
        "description": case["description"],
        "expected": case["expect"],
        "timestamp": datetime.now().isoformat(),
    }

    try:
        kwargs = {
            "headers": headers,
            "json": payload,
            "cookies": cookies,
            "timeout": 20,
        }
        if USE_CURL:
            kwargs["impersonate"] = "chrome"

        resp = http.post(API_URL, **kwargs)

        result["status_code"] = resp.status_code
        result["response_size"] = len(resp.text)

        # Analizar respuesta
        if resp.status_code == 500:
            result["anomaly"] = "SERVER_ERROR_500"
            result["response_snippet"] = resp.text[:500]

        elif resp.status_code == 200:
            try:
                data = resp.json()
                result["has_errors"] = "errors" in data

                if "errors" in data:
                    result["error_messages"] = [
                        e.get("message", "")[:200] for e in data["errors"][:5]
                    ]

                if "data" in data:
                    viewer = data.get("data", {}).get("viewer", {})
                    flights_data = viewer.get("flights", {})
                    edges = flights_data.get("edges", [])
                    result["flights_count"] = len(edges)

                    # Analizar precios
                    prices = []
                    for edge in edges:
                        node = edge.get("node", {})
                        for fare in node.get("fares", []):
                            p = fare.get("prices", {})
                            after_tax = p.get("afterTax", -1)
                            promo = p.get("promotionAmount", 0)
                            prices.append({
                                "afterTax": after_tax,
                                "promotionAmount": promo,
                                "type": fare.get("type", "?"),
                                "class": fare.get("class", "?"),
                            })

                    result["prices_sample"] = prices[:10]

                    # Detectar anomalías
                    anomalies = []

                    # ¿Precios $0?
                    zero_prices = [p for p in prices if p["afterTax"] == 0]
                    if zero_prices:
                        anomalies.append(f"ZERO_PRICE ({len(zero_prices)} fares)")

                    # ¿Precios negativos?
                    neg_prices = [p for p in prices if p["afterTax"] < 0]
                    if neg_prices:
                        anomalies.append(f"NEGATIVE_PRICE ({len(neg_prices)} fares)")

                    # ¿Promo activa?
                    promos = [p for p in prices if (p["promotionAmount"] or 0) > 0]
                    if promos:
                        anomalies.append(f"PROMO_ACTIVE ({len(promos)} fares)")

                    # ¿Debería haber fallado pero devolvió datos?
                    if case["expect"] == "error" and edges:
                        anomalies.append(f"UNEXPECTED_SUCCESS ({len(edges)} vuelos)")

                    # ¿Precios sospechosamente bajos? (< $1000 ARS por persona)
                    low_prices = [p for p in prices if 0 < p["afterTax"] < 1000]
                    if low_prices:
                        anomalies.append(f"SUSPICIOUSLY_LOW ({len(low_prices)} fares < $1000)")

                    result["anomalies"] = anomalies

            except Exception as e:
                result["parse_error"] = str(e)
                result["response_snippet"] = resp.text[:500]

        else:
            result["anomaly"] = f"UNEXPECTED_HTTP_{resp.status_code}"
            result["response_snippet"] = resp.text[:500]

    except Exception as e:
        result["error"] = str(e)
        result["anomaly"] = "REQUEST_FAILED"

    return result


# ============================================================================
# LOGGING
# ============================================================================

def append_error_log(results: list[dict]):
    """Registra los resultados interesantes en el log de errores."""
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        for r in results:
            anomalies = r.get("anomalies", [])
            anomaly = r.get("anomaly", "")

            if anomalies or anomaly:
                timestamp = r.get("timestamp", "?")
                name = r.get("name", "?")
                desc = r.get("description", "?")
                status = r.get("status_code", "?")

                all_anomalies = anomalies + ([anomaly] if anomaly else [])
                anomaly_str = " | ".join(all_anomalies)

                f.write(
                    f"[{timestamp}] [{name}] HTTP {status} | "
                    f"{desc} | ANOMALÍAS: {anomaly_str}\n"
                )


# ============================================================================
# FLUJO PRINCIPAL
# ============================================================================

def run_tests():
    """Ejecuta todos los edge cases."""
    now = datetime.now()
    print(f"\n{'=' * 70}")
    print(f"🧪 EDGE CASE TESTER — {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'=' * 70}")

    cases = generate_edge_cases()
    total = len(cases)
    print(f"\n📋 {total} edge cases a ejecutar\n")

    results = []
    interesting = []

    for i, case in enumerate(cases, 1):
        print(f"   [{i:2d}/{total}] {case['name']}: {case['description']}...", end=" ")

        result = run_edge_case(case)
        results.append(result)

        anomalies = result.get("anomalies", [])
        anomaly = result.get("anomaly", "")
        status = result.get("status_code", "?")
        flights = result.get("flights_count", 0)

        if anomalies or anomaly:
            all_anom = anomalies + ([anomaly] if anomaly else [])
            print(f"⚠️  HTTP {status} | {', '.join(all_anom)}")
            interesting.append(result)
        elif result.get("has_errors"):
            print(f"❌ HTTP {status} | GraphQL error (esperado)")
        else:
            print(f"✅ HTTP {status} | {flights} vuelos")

        # Pausa corta entre requests
        time.sleep(0.8)

    # ========================================================================
    # RESUMEN
    # ========================================================================

    print(f"\n{'=' * 70}")
    print(f"📊 RESUMEN DE EDGE CASES")
    print(f"{'=' * 70}")
    print(f"   Total ejecutados: {total}")
    print(f"   Con anomalías: {len(interesting)}")
    print(f"   Exitosos: {sum(1 for r in results if r.get('status_code') == 200)}")
    print(f"   Errores HTTP: {sum(1 for r in results if r.get('status_code', 200) != 200)}")

    # Detallar anomalías
    if interesting:
        print(f"\n{'─' * 70}")
        print(f"🚨 ANOMALÍAS ENCONTRADAS:")
        print(f"{'─' * 70}")

        for r in interesting:
            all_anom = r.get("anomalies", []) + ([r.get("anomaly", "")] if r.get("anomaly") else [])
            print(f"\n   🔍 [{r['name']}] {r['description']}")
            print(f"      HTTP: {r.get('status_code', '?')}")
            print(f"      Anomalías: {', '.join(all_anom)}")

            if r.get("prices_sample"):
                print(f"      Precios muestra:")
                for p in r["prices_sample"][:3]:
                    print(f"         {p['type']}({p['class']}): ${p['afterTax']:,.0f}")

            if r.get("response_snippet"):
                print(f"      Respuesta: {r['response_snippet'][:200]}")

    # Registrar errores
    append_error_log(results)
    print(f"\n   💾 Log de errores: {ERROR_LOG.name}")

    # Guardar snapshot completo
    snapshot_file = EDGE_DIR / f"edge_results_{now.strftime('%Y%m%d_%H%M%S')}.json"
    snapshot_file.write_text(
        json.dumps({
            "timestamp": now.isoformat(),
            "total_cases": total,
            "total_anomalies": len(interesting),
            "results": results,
        }, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"   💾 Snapshot: {snapshot_file.name}")

    # Alertar por Telegram si hay anomalías interesantes
    critical_anomalies = [
        r for r in interesting
        if any(kw in str(r.get("anomalies", []))
               for kw in ["ZERO_PRICE", "NEGATIVE_PRICE", "UNEXPECTED_SUCCESS",
                           "SUSPICIOUSLY_LOW", "PROMO_ACTIVE", "SERVER_ERROR_500"])
    ]

    if critical_anomalies:
        msg = f"🧪 *EDGE CASE ALERT — Flybondi*\n\n"
        msg += f"*{len(critical_anomalies)} anomalía(s) encontrada(s):*\n\n"

        for r in critical_anomalies[:8]:
            all_anom = r.get("anomalies", []) + ([r.get("anomaly", "")] if r.get("anomaly") else [])
            msg += f"🔍 `{r['name']}`\n"
            msg += f"   {r['description']}\n"
            msg += f"   HTTP {r.get('status_code', '?')} | {', '.join(all_anom)}\n"

            if "PROMO_ACTIVE" in str(all_anom):
                promos = [p for p in r.get("prices_sample", []) if (p.get("promotionAmount") or 0) > 0]
                if promos:
                    msg += f"   🏷️ Promo: ${promos[0].get('promotionAmount', 0):,.0f}\n"

            msg += "\n"

        msg += f"🕐 {now.strftime('%d/%m/%Y %H:%M')}"
        send_telegram(msg)
        print(f"   📨 Alerta enviada a Telegram")

    # Marcar última ejecución
    LAST_RUN_FILE.write_text(now.isoformat(), encoding="utf-8")

    return results


def should_run_today() -> bool:
    """Verifica si el test ya se ejecutó hoy."""
    if not LAST_RUN_FILE.exists():
        return True

    try:
        last_run_str = LAST_RUN_FILE.read_text(encoding="utf-8").strip()
        last_run = datetime.fromisoformat(last_run_str)
        return last_run.date() < date.today()
    except (ValueError, OSError):
        return True


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🧪 Tester de Edge Cases para la API GraphQL de Flybondi",
    )
    parser.add_argument(
        "--daily", action="store_true",
        help="Solo ejecutar si no se corrió hoy",
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="No enviar alertas por Telegram",
    )

    args = parser.parse_args()

    if args.no_telegram:
        global TELEGRAM_BOT_TOKEN
        TELEGRAM_BOT_TOKEN = ""

    if args.daily:
        if not should_run_today():
            print(f"ℹ️  Edge Case Tester ya se ejecutó hoy. Skipping.")
            return
        print(f"🗓️  Primera ejecución del día")

    run_tests()


if __name__ == "__main__":
    main()
