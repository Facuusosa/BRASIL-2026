#!/usr/bin/env python3
"""
monitor_flybondi.py - Monitor de precios Flybondi via API GraphQL

🚀 Consulta DIRECTAMENTE la API interna de Flybondi.
   Sin browser, sin Playwright, sin stealth — solo HTTP requests.

Ruta: Buenos Aires (BUE) → Florianópolis (FLN)
Fechas: 8-11 marzo ida, 15-18 marzo vuelta (todas las combinaciones)

Umbrales de alerta:
  🟢 VERDE  (Compra Inmediata): Total < $600.000 ARS
  🟡 AMARILLA (Oportunidad):    Total < $800.000 ARS  
  🔴 TECHO:                     Total > $1.000.000 ARS → NO comprar

Uso:
    python monitor_flybondi.py                # Una búsqueda + alerta
    python monitor_flybondi.py --loop         # Modo daemon (cada hora)
    python monitor_flybondi.py --loop 30      # Daemon cada 30 minutos
    python monitor_flybondi.py --no-telegram  # Sin enviar a Telegram
    python monitor_flybondi.py --json         # Output en JSON
"""

import os
import sys
import json
import time
import argparse

# curl_cffi imita la "huella digital" TLS de Chrome para pasar Cloudflare
try:
    from curl_cffi import requests as curl_requests
    USE_CURL_CFFI = True
except ImportError:
    import requests as curl_requests
    USE_CURL_CFFI = False
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Si no tiene dotenv, lee directo de env vars


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# --- Financiero ---
DOLAR_MEP = float(os.getenv("DOLAR_MEP", "1440"))
DOLARES_AHORRADOS = float(os.getenv("DOLARES_AHORRADOS", "725"))

# --- Umbrales de alerta (ARS total para 2 personas, ida y vuelta) ---
ALERTA_VERDE = int(os.getenv("ALERTA_VERDE", "600000"))       # 🟢 Compra YA
ALERTA_AMARILLA = int(os.getenv("ALERTA_AMARILLA", "800000"))  # 🟡 Oportunidad
TECHO_MAXIMO = int(os.getenv("TECHO_MAXIMO", "1000000"))       # 🔴 No comprar

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- API Flybondi ---
API_URL = "https://flybondi.com/graphql"
API_KEY = os.getenv(
    "FLYBONDI_API_KEY",
    "b64ead64fb26d64668838ac2ef8c0c3222c3d285cf5a2fd1ce49281c140bcdaa"
)

# --- Ruta ---
ORIGIN = "BUE"
DESTINATION = "FLN"
ADULTS = 2

# --- Equipaje (estimado para 2 personas, ida y vuelta, 20kg c/u) ---
# Basado en precio real de Flybondi al 13/02/2026
EQUIPAJE_ESTIMADO = float(os.getenv("EQUIPAJE_ESTIMADO", "75033"))

# --- Rangos de fecha ---
DEPARTURE_DATES = ["2026-03-08", "2026-03-09", "2026-03-10", "2026-03-11"]
RETURN_DATES = ["2026-03-15", "2026-03-16", "2026-03-17", "2026-03-18"]

# --- Intervalo de monitoreo ---
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))

# --- Directorios ---
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = DATA_DIR / "flybondi_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# HEADERS HTTP (copiados exactos del cURL original del browser)
# ============================================================================

HEADERS = {
    "accept": "application/json",
    "accept-language": "es-ES,es;q=0.9",
    "authorization": f"Key {API_KEY}",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "referer": "https://flybondi.com/ar/search/dates?adults=2&children=0&currency=ARS&fromCityCode=BUE&infants=0&toCityCode=FLN&utm_origin=search_bar",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Mobile Safari/537.36"
    ),
    "x-fo-flow": "ibe",
    "x-fo-market-origin": "ar",
    "x-fo-ui-version": "2.209.0",
}

# Cookie de sesión (se puede actualizar si expira)
SESSION_COOKIE = os.getenv(
    "FLYBONDI_SESSION",
    "SFO-bfac89a4-129e-4741-a22e-b1875eaf52f8"
)


# ============================================================================
# QUERY GraphQL (simplificada — solo lo que necesitamos)
# ============================================================================

GRAPHQL_QUERY = """
query FlightSearchContainerQuery(
  $input: FlightsQueryInput!
  $origin: String!
  $destination: String!
  $currency: String!
  $start: Timestamp!
  $end: Timestamp!
) {
  viewer {
    flights(input: $input) {
      searchUrl
      edges {
        node {
          id
          lfId
          sfId
          origin
          destination
          direction
          carrier
          departureDate
          arrivalDate
          flightTimeMinutes
          international
          flightNo
          segmentFlightNo
          currency
          stops
          connections {
            waitingTimeMinutes
            connectingAirport
            connectionType
          }
          legs {
            arrivalDate
            carrier
            departureDate
            destination
            flightNo
            flightTimeMinutes
            id
            origin
          }
          fares {
            fareRef
            passengerType
            class
            basis
            type
            availability
            taxes {
              taxRef
              taxCode
              codeType
              amount
              description
            }
            prices {
              afterTax
              beforeTax
              baseBeforeTax
              promotionAmount
            }
          }
          equipmentId
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
      roundtrip
      advancedDays
      minDays
      maxDays
      hasRestrictions
    }
    lowestPrice
  }
  arrivals: fares(origin: $destination, destination: $origin, currency: $currency, start: $start, end: $end, sort: "departure") {
    id
    departure
    fares {
      price
      fCCode
      fBCode
      roundtrip
      advancedDays
      minDays
      maxDays
      hasRestrictions
    }
    lowestPrice
  }
}
""".strip()


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def build_variables(departure_date: str, return_date: str) -> dict:
    """Construye las variables GraphQL para una combinación de fechas."""
    # Timestamps para el rango del calendario (cubrir todo marzo 2026)
    start_dt = datetime(2026, 3, 1)
    end_dt = datetime(2026, 3, 31, 23, 59, 59)
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    return {
        "input": {
            "origin": ORIGIN,
            "destination": DESTINATION,
            "departureDate": departure_date,
            "returnDate": return_date,
            "currency": "ARS",
            "pax": {
                "adults": ADULTS,
                "children": 0,
                "infants": 0,
            },
            "promoCode": None,
        },
        "origin": ORIGIN,
        "destination": DESTINATION,
        "currency": "ARS",
        "start": start_ts,
        "end": end_ts,
    }


def query_flybondi(departure_date: str, return_date: str) -> dict | None:
    """
    Hace la query GraphQL a Flybondi para una combinación de fechas.
    
    Returns:
        dict con la respuesta JSON completa, o None si falla
    """
    variables = build_variables(departure_date, return_date)
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": variables,
    }

    cookies = {"FBSessionX-ar-ibe": SESSION_COOKIE}

    try:
        if USE_CURL_CFFI:
            response = curl_requests.post(
                API_URL,
                headers=HEADERS,
                json=payload,
                cookies=cookies,
                timeout=30,
                impersonate="chrome",
            )
        else:
            response = curl_requests.post(
                API_URL,
                headers=HEADERS,
                json=payload,
                cookies=cookies,
                timeout=30,
            )

        if response.status_code != 200:
            print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
            return None

        data = response.json()

        if "errors" in data:
            print(f"   ❌ GraphQL errors: {json.dumps(data['errors'], indent=2)[:300]}")
            return None

        return data

    except Exception as e:
        if "timeout" in str(e).lower() or "Timeout" in type(e).__name__:
            print("   ❌ Timeout — La API no respondió en 30s")
            return None
        if "connection" in str(e).lower() or "Connection" in type(e).__name__:
            print(f"   ❌ Error de conexión: {e}")
            return None
        print(f"   ❌ Error inesperado: {e}")
        return None



def parse_flights(data: dict, departure_date: str, return_date: str) -> list[dict]:
    """
    Parsea la respuesta de la API y extrae los vuelos con sus precios.
    
    El response contiene vuelos de ida y vuelta mezclados.
    Separamos por direction y calculamos combinaciones.
    """
    results = []
    
    try:
        edges = data.get("data", {}).get("viewer", {}).get("flights", {}).get("edges", [])
    except (AttributeError, TypeError):
        print("   ⚠️ Estructura de respuesta inesperada")
        return []

    if not edges:
        print("   📭 No se encontraron vuelos para estas fechas")
        return []

    # Separar vuelos por dirección
    outbound_flights = []  # ida
    inbound_flights = []   # vuelta

    for edge in edges:
        node = edge.get("node", {})
        if not node:
            continue

        direction = node.get("direction", "")
        flight_info = extract_flight_info(node)

        if direction == "outbound":
            outbound_flights.append(flight_info)
        elif direction == "inbound":
            inbound_flights.append(flight_info)

    # Si no hay separación por direction, intentar por fecha
    if not outbound_flights and not inbound_flights:
        for edge in edges:
            node = edge.get("node", {})
            dep_date = node.get("departureDate", "")[:10]
            flight_info = extract_flight_info(node)
            
            if dep_date == departure_date:
                outbound_flights.append(flight_info)
            elif dep_date == return_date:
                inbound_flights.append(flight_info)

    # Generar combinaciones (ida + vuelta)
    for ob in outbound_flights:
        for ib in inbound_flights:
            total_price = ob["total_price"] + ib["total_price"]
            total_usd = total_price / DOLAR_MEP

            combo = {
                "departure_date": departure_date,
                "return_date": return_date,
                "outbound": ob,
                "inbound": ib,
                "total_ars": round(total_price, 2),
                "total_usd": round(total_usd, 2),
                "total_per_person_ars": round(total_price / ADULTS, 2),
                "availability_min": min(
                    ob.get("availability", 99),
                    ib.get("availability", 99)
                ),
                "search_url": data.get("data", {}).get("viewer", {})
                              .get("flights", {}).get("searchUrl", ""),
            }
            results.append(combo)

    # También agregar info de vuelos sueltos si no hay combos
    if not results:
        all_flights = outbound_flights + inbound_flights
        for f in all_flights:
            results.append({
                "departure_date": departure_date,
                "return_date": return_date,
                "single_flight": f,
                "total_ars": f["total_price"],
                "total_usd": round(f["total_price"] / DOLAR_MEP, 2),
                "note": "Vuelo suelto (sin combinación ida+vuelta)",
            })

    return results


def extract_flight_info(node: dict) -> dict:
    """Extrae la info relevante de un nodo de vuelo."""
    # Calcular precio total (sumando todas las tarifas de todos los pasajeros)
    total_price = 0.0
    cheapest_fare_type = None
    availability = 99
    fare_details = []

    for fare in node.get("fares", []):
        prices = fare.get("prices", {})
        after_tax = prices.get("afterTax", 0) or 0
        fare_type = fare.get("type", "unknown")
        fare_avail = fare.get("availability", 99) or 99
        pax_type = fare.get("passengerType", "ADT")

        fare_details.append({
            "type": fare_type,
            "pax": pax_type,
            "afterTax": after_tax,
            "beforeTax": prices.get("beforeTax", 0),
            "availability": fare_avail,
            "class": fare.get("class", ""),
        })

        # Usar la tarifa más barata disponible (tipo "Economy" o similar)
        if pax_type == "ADT" and fare_avail > 0:
            if cheapest_fare_type is None or after_tax < total_price / max(ADULTS, 1):
                pass  # Tracking

        availability = min(availability, fare_avail)

    # Precio total = sumar afterTax de todas las fares para este vuelo
    # afterTax de la API es POR PERSONA → multiplicamos por ADULTS
    # Tomamos el tipo más barato y multiplicamos por cantidad de adultos
    adt_fares = [f for f in fare_details if f["pax"] in ("ADT", "ADULT") and f["availability"] > 0]
    
    if adt_fares:
        # Agrupar por tipo y tomar el más barato
        by_type = {}
        for f in adt_fares:
            ft = f["type"]
            if ft not in by_type or f["afterTax"] < by_type[ft]["afterTax"]:
                by_type[ft] = f
        
        cheapest = min(by_type.values(), key=lambda x: x["afterTax"])
        total_price = cheapest["afterTax"] * ADULTS
        cheapest_fare_type = cheapest["type"]
        availability = cheapest["availability"]
    else:
        # Fallback: sumar todas las fares
        total_price = sum(f["afterTax"] for f in fare_details)

    # Formatear horarios
    dep_date_raw = node.get("departureDate", "")
    arr_date_raw = node.get("arrivalDate", "")

    try:
        dep_dt = datetime.fromisoformat(dep_date_raw.replace("Z", "+00:00"))
        arr_dt = datetime.fromisoformat(arr_date_raw.replace("Z", "+00:00"))
        dep_time = dep_dt.strftime("%H:%M")
        arr_time = arr_dt.strftime("%H:%M")
        dep_date_str = dep_dt.strftime("%d/%m")
    except (ValueError, AttributeError):
        dep_time = "??:??"
        arr_time = "??:??"
        dep_date_str = "??/??"

    flight_minutes = node.get("flightTimeMinutes", 0) or 0
    hours = flight_minutes // 60
    minutes = flight_minutes % 60

    # Legs info
    legs = node.get("legs", [])
    leg_details = []
    for leg in legs:
        leg_details.append({
            "origin": leg.get("origin", ""),
            "destination": leg.get("destination", ""),
            "flightNo": leg.get("flightNo", ""),
            "carrier": leg.get("carrier", ""),
        })

    return {
        "flight_no": node.get("flightNo", ""),
        "segment_flight_no": node.get("segmentFlightNo", ""),
        "carrier": node.get("carrier", "FO"),
        "origin": node.get("origin", ""),
        "destination": node.get("destination", ""),
        "departure_time": dep_time,
        "arrival_time": arr_time,
        "departure_date_str": dep_date_str,
        "duration": f"{hours}h {minutes:02d}min",
        "duration_minutes": flight_minutes,
        "stops": node.get("stops", 0),
        "connections": node.get("connections", []),
        "legs": leg_details,
        "total_price": total_price,
        "fare_type": cheapest_fare_type or "unknown",
        "availability": availability,
        "currency": node.get("currency", "ARS"),
        "fare_details": fare_details,
    }


def parse_calendar_fares(data: dict) -> dict:
    """
    Extrae los precios del calendario de tarifas (todas las fechas disponibles).
    Útil para identificar los días más baratos.
    """
    calendar = {"departures": {}, "arrivals": {}}

    for key in ["departures", "arrivals"]:
        fares_list = data.get("data", {}).get(key, [])
        if not fares_list:
            continue
        for entry in fares_list:
            date = entry.get("departure", "")[:10]
            lowest = entry.get("lowestPrice", None)
            fares = entry.get("fares", [])
            prices = [f.get("price", 0) for f in fares if f.get("price")]
            
            calendar[key][date] = {
                "lowest": lowest,
                "prices": prices,
                "min_price": min(prices) if prices else None,
            }

    return calendar


# ============================================================================
# ALERTAS Y NOTIFICACIONES
# ============================================================================

def classify_alert(total_ars: float) -> tuple[str, str]:
    """
    Clasifica el precio según los umbrales.
    Returns: (nivel, emoji)
    """
    if total_ars <= ALERTA_VERDE:
        return "VERDE", "🟢"
    elif total_ars <= ALERTA_AMARILLA:
        return "AMARILLA", "🟡"
    elif total_ars <= TECHO_MAXIMO:
        return "NORMAL", "⚪"
    else:
        return "TECHO", "🔴"


def format_price_ars(price: float) -> str:
    """Formatea precio en ARS con separador de miles y estima USD con margen."""
    ars_price = price
    usd_price = (ars_price / DOLAR_MEP) + 50 # Sumamos 50 USD estimados de tasas
    return f"${ars_price:,.0f} (US$ {usd_price:.0f})".replace(",", ".")


def format_flight_line(flight: dict, label: str) -> str:
    """Formatea una línea de vuelo para display."""
    f = flight
    stops_icon = "✈️" if f["stops"] == 0 else f"🔄 {f['stops']} escala(s)"
    avail_warn = ""
    if f["availability"] <= 5:
        avail_warn = f"  ⚠️ ¡Últimos {f['availability']} asientos!"
    
    return (
        f"  {label}: {f['origin']}→{f['destination']}  "
        f"{f['departure_time']}-{f['arrival_time']}  "
        f"({f['duration']})  {stops_icon}  "
        f"Vuelo {f['flight_no']}  "
        f"{format_price_ars(f['total_price'])} ({f['fare_type']})"
        f"{avail_warn}"
    )


def build_buy_link(departure_date: str, return_date: str) -> str:
    """Genera el link directo de compra en Flybondi con fechas precargadas."""
    return (
        f"https://flybondi.com/ar/search/results?"
        f"adults={ADULTS}&children=0&currency=ARS"
        f"&departureDate={departure_date}"
        f"&returnDate={return_date}"
        f"&fromCityCode={ORIGIN}&infants=0"
        f"&toCityCode={DESTINATION}"
    )


def send_telegram(message: str, silent: bool = False) -> bool:
    """Envía un mensaje a Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("   ⚠️ Telegram no configurado (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_notification": silent,
        }
        resp = curl_requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("   📨 Mensaje enviado a Telegram ✅")
            return True
        else:
            print(f"   ❌ Error Telegram: {resp.status_code} - {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"   ❌ Error enviando a Telegram: {e}")
        return False


def build_telegram_alert(combo: dict, alert_level: str, emoji: str) -> str:
    """Construye el mensaje de alerta para Telegram."""
    ob = combo["outbound"]
    ib = combo["inbound"]
    total = combo["total_ars"]
    total_usd = combo["total_usd"]

    # Calcular ahorro vs techo
    ahorro_vs_techo = TECHO_MAXIMO - total
    
    # Calcular si alcanza con los dólares ahorrados
    costo_usd = total / DOLAR_MEP
    sobra_usd = DOLARES_AHORRADOS - costo_usd
    
    avail_outbound = ob.get("availability", "?")
    avail_inbound = ib.get("availability", "?")
    
    buy_link = build_buy_link(combo["departure_date"], combo["return_date"])

    msg = f"""{emoji} *ALERTA {alert_level}* — Flybondi BUE→FLN

💰 *TOTAL: {format_price_ars(total)}* (US$ {total_usd:.0f})
📊 Dólar MEP: ${DOLAR_MEP:.0f}

✈️ *IDA* ({combo['departure_date']}):
   {ob['origin']}→{ob['destination']} | {ob['departure_time']}-{ob['arrival_time']}
   Vuelo {ob['flight_no']} | {ob['duration']} | {format_price_ars(ob['total_price'])}
   🪑 {avail_outbound} asientos

✈️ *VUELTA* ({combo['return_date']}):
   {ib['origin']}→{ib['destination']} | {ib['departure_time']}-{ib['arrival_time']}
   Vuelo {ib['flight_no']} | {ib['duration']} | {format_price_ars(ib['total_price'])}
   🪑 {avail_inbound} asientos
"""

    if alert_level == "VERDE":
        msg += f"""
🏆 *¡COMPRA YA!* Ahorro vs techo: {format_price_ars(ahorro_vs_techo)}
"""
        if sobra_usd > 0:
            msg += f"💵 Con tus US$ {DOLARES_AHORRADOS:.0f}, te sobran *US$ {sobra_usd:.0f}* para caipirinhas 🍹\n"
        else:
            msg += f"💵 Necesitás US$ {costo_usd:.0f} (tenés US$ {DOLARES_AHORRADOS:.0f})\n"

    elif alert_level == "AMARILLA":
        msg += f"\n💡 *Oportunidad* — Ahorro vs techo: {format_price_ars(ahorro_vs_techo)}\n"

    msg += f"\n🔗 [Comprar ahora]({buy_link})"
    msg += f"\n\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    return msg


# ============================================================================
# TRACKING DE DISPONIBILIDAD (Anti-Scareware)
# ============================================================================

def load_availability_history() -> dict:
    """Carga el historial de disponibilidad."""
    path = LOG_DIR / "availability_history.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_availability_history(history: dict):
    """Guarda el historial de disponibilidad."""
    path = LOG_DIR / "availability_history.json"
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def track_availability(combo: dict, history: dict) -> str | None:
    """
    Trackea la disponibilidad para detectar "scareware".
    Si un vuelo dice "¡Últimos 3!" hace días, es mentira.
    
    Returns: warning message si detecta scareware, None si no
    """
    ob = combo.get("outbound", {})
    ib = combo.get("inbound", {})

    for flight, label in [(ob, "ida"), (ib, "vuelta")]:
        key = f"{flight.get('flight_no', '?')}_{combo['departure_date']}_{combo['return_date']}"
        avail = flight.get("availability", 99)
        now_str = datetime.now().isoformat()

        if key not in history:
            history[key] = []

        history[key].append({
            "timestamp": now_str,
            "availability": avail,
            "price": flight.get("total_price", 0),
        })

        # Detectar scareware: si la disponibilidad estuvo <= 5 por más de 3 días
        if avail <= 5 and len(history[key]) >= 3:
            first_low = None
            for entry in history[key]:
                if entry["availability"] <= 5:
                    if first_low is None:
                        first_low = entry["timestamp"]

            if first_low:
                try:
                    first_dt = datetime.fromisoformat(first_low)
                    days_low = (datetime.now() - first_dt).days
                    if days_low >= 3:
                        return (
                            f"⚠️ SCAREWARE DETECTADO en vuelo {flight.get('flight_no', '?')} ({label}): "
                            f"Dice '{avail} asientos' hace {days_low} días. Probablemente es mentira."
                        )
                except (ValueError, TypeError):
                    pass

    return None


# ============================================================================
# LOGGING DE RESULTADOS
# ============================================================================

def save_search_log(all_results: list[dict], calendar: dict | None = None):
    """Guarda los resultados de la búsqueda en un archivo JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"search_{timestamp}.json"

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "origin": ORIGIN,
            "destination": DESTINATION,
            "adults": ADULTS,
            "dolar_mep": DOLAR_MEP,
            "alerta_verde": ALERTA_VERDE,
            "alerta_amarilla": ALERTA_AMARILLA,
            "techo_maximo": TECHO_MAXIMO,
        },
        "results": all_results,
        "best_price_ars": min((r["total_ars"] for r in all_results), default=None),
        "calendar_fares": calendar,
    }

    log_file.write_text(
        json.dumps(log_data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"   💾 Log guardado: {log_file.name}")
    return log_file


def generate_html_report(all_results: list[dict], calendar: dict | None = None):
    """
    Genera un reporte HTML completo con TODOS los vuelos.
    Incluye precio con equipaje estimado en todas las opciones.
    Se abre automáticamente en el navegador.
    """
    import webbrowser

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = LOG_DIR / f"reporte_{timestamp}.html"

    # Separar vuelos únicos de ida y vuelta
    outbound_set = {}
    inbound_set = {}

    for combo in all_results:
        ob = combo.get("outbound", {})
        ib = combo.get("inbound", {})
        if ob:
            key = f"{ob.get('flight_no','')}_{combo['departure_date']}"
            if key not in outbound_set or ob["total_price"] < outbound_set[key]["total_price"]:
                outbound_set[key] = {**ob, "date": combo["departure_date"]}
        if ib:
            key = f"{ib.get('flight_no','')}_{combo['return_date']}"
            if key not in inbound_set or ib["total_price"] < inbound_set[key]["total_price"]:
                inbound_set[key] = {**ib, "date": combo["return_date"]}

    outbound_list = sorted(outbound_set.values(), key=lambda x: x["total_price"])
    inbound_list = sorted(inbound_set.values(), key=lambda x: x["total_price"])

    best = all_results[0] if all_results else None
    best_total_equip = (best["total_ars"] + EQUIPAJE_ESTIMADO) if best else 0
    best_usd_equip = best_total_equip / DOLAR_MEP if best else 0
    sobra_usd = DOLARES_AHORRADOS - best_usd_equip if best else 0

    # Equipaje proporcional: mitad ida, mitad vuelta
    equip_medio = EQUIPAJE_ESTIMADO / 2

    # === GENERAR COMBOS HTML (TODOS) ===
    combos_html = ""
    for i, combo in enumerate(all_results, 1):
        ob = combo.get("outbound", {})
        ib = combo.get("inbound", {})
        total_con_equip = combo["total_ars"] + EQUIPAJE_ESTIMADO
        usd_con_equip = total_con_equip / DOLAR_MEP
        level, _ = classify_alert(total_con_equip)
        badge_class = "badge-green" if level == "VERDE" else "badge-yellow" if level == "AMARILLA" else "badge-red" if level == "TECHO" else "badge-normal"
        buy_url = build_buy_link(combo["departure_date"], combo["return_date"])
        avail_min = combo.get("availability_min", 99)
        avail_warn = f'<span class="avail-low">⚠️ {avail_min} asientos</span>' if avail_min <= 5 else ""

        combos_html += f"""
        <div class="combo-card{' hidden-item combos-extra' if i > 10 else ''}">
            <div class="combo-header">
                <span class="rank">#{i}</span>
                <span class="combo-price-final">{format_price_ars(total_con_equip)}</span>
                <span class="combo-usd">US$ {usd_con_equip:.0f}</span>
                <span class="badge {badge_class}">{level}</span>
                {avail_warn}
            </div>
            <div class="combo-sub-price">Sin equipaje: {format_price_ars(combo['total_ars'])} · Equipaje: +{format_price_ars(EQUIPAJE_ESTIMADO)}</div>
            <div class="combo-dates">📅 {combo['departure_date']} → {combo['return_date']}</div>
            <table class="flight-table">
                <tr class="ida-row">
                    <td>✈️ <strong>IDA</strong></td>
                    <td>{ob.get('origin','?')} → {ob.get('destination','?')}</td>
                    <td>{ob.get('departure_time','?')} - {ob.get('arrival_time','?')}</td>
                    <td>{ob.get('duration','?')}</td>
                    <td>FO {ob.get('flight_no','?')}</td>
                    <td class="price">{format_price_ars(ob['total_price'])}</td>
                </tr>
                <tr class="vuelta-row">
                    <td>🔙 <strong>VUELTA</strong></td>
                    <td>{ib.get('origin','?')} → {ib.get('destination','?')}</td>
                    <td>{ib.get('departure_time','?')} - {ib.get('arrival_time','?')}</td>
                    <td>{ib.get('duration','?')}</td>
                    <td>FO {ib.get('flight_no','?')}</td>
                    <td class="price">{format_price_ars(ib['total_price'])}</td>
                </tr>
            </table>
            <a href="{buy_url}" target="_blank" class="buy-btn">🛒 COMPRAR EN FLYBONDI</a>
        </div>"""

    if len(all_results) > 10:
        combos_html += f"""<button class="toggle-btn" onclick="toggleSection('combos-extra', this)">
            📋 Ver las {len(all_results) - 10} combinaciones restantes
        </button>"""

    # === COMPARACIÓN: COMBO vs COMPRANDO POR SEPARADO ===
    if outbound_list and inbound_list:
        mejor_ida = outbound_list[0]
        mejor_vuelta = inbound_list[0]
        total_separado = mejor_ida['total_price'] + mejor_vuelta['total_price'] + EQUIPAJE_ESTIMADO
        mejor_combo_total = all_results[0]["total_ars"] + EQUIPAJE_ESTIMADO if all_results else 0
        ahorro = total_separado - mejor_combo_total
        comparacion_html = f"""
    <div class="compare-box">
        <div class="compare-title">💡 ¿Conviene comprar por separado?</div>
        <div class="compare-row">
            <div class="compare-item">
                <div class="compare-label">Mejor combo (ida+vuelta)</div>
                <div class="compare-price">{format_price_ars(mejor_combo_total)}</div>
                <div class="compare-detail">US$ {mejor_combo_total/DOLAR_MEP:.0f}</div>
            </div>
            <div class="compare-vs">VS</div>
            <div class="compare-item">
                <div class="compare-label">Ida + vuelta más baratas</div>
                <div class="compare-price">{format_price_ars(total_separado)}</div>
                <div class="compare-detail">
                    Ida: {format_price_ars(mejor_ida['total_price'])} ({mejor_ida.get('date','?')})<br>
                    Vuelta: {format_price_ars(mejor_vuelta['total_price'])} ({mejor_vuelta.get('date','?')})
                </div>
            </div>
        </div>
        <div class="compare-result">
            {"✅ El combo es <strong>" + format_price_ars(abs(ahorro)) + " más barato</strong> que comprar separado" if ahorro > 0 else "🔥 <strong>Comprar separado te ahorra " + format_price_ars(abs(ahorro)) + "!</strong>" if ahorro < 0 else "Mismo precio"}
        </div>
    </div>"""
    else:
        comparacion_html = ""

    # === GENERAR TABLA IDA (TOP 10 + OCULTAS) ===
    ida_html = ""
    for i, f in enumerate(outbound_list, 1):
        con_equip = f['total_price'] + equip_medio
        avail = f.get("availability", 99)
        avail_cls = "avail-low" if avail <= 5 else ""
        avail_txt = f"⚠️ {avail}" if avail <= 5 else str(avail)
        hidden = " hidden-item ida-extra" if i > 10 else ""
        ida_html += f"""
        <tr class="{hidden}">
            <td>#{i}</td>
            <td>{f.get('date','?')}</td>
            <td>{f.get('origin','?')} → {f.get('destination','?')}</td>
            <td>{f.get('departure_time','?')} - {f.get('arrival_time','?')}</td>
            <td>{f.get('duration','?')}</td>
            <td>FO {f.get('flight_no','?')}</td>
            <td class="{avail_cls}">{avail_txt}</td>
            <td class="price">{format_price_ars(f['total_price'])}</td>
            <td class="price-final">{format_price_ars(con_equip)}<br><small>US$ {con_equip/DOLAR_MEP:.0f}</small></td>
        </tr>"""

    ida_toggle = ""
    if len(outbound_list) > 10:
        ida_toggle = f"""<button class="toggle-btn" onclick="toggleSection('ida-extra', this)">
            📋 Ver los {len(outbound_list) - 10} vuelos restantes
        </button>"""

    # === GENERAR TABLA VUELTA (TOP 10 + OCULTAS) ===
    vuelta_html = ""
    for i, f in enumerate(inbound_list, 1):
        con_equip = f['total_price'] + equip_medio
        avail = f.get("availability", 99)
        avail_cls = "avail-low" if avail <= 5 else ""
        avail_txt = f"⚠️ {avail}" if avail <= 5 else str(avail)
        hidden = " hidden-item vuelta-extra" if i > 10 else ""
        vuelta_html += f"""
        <tr class="{hidden}">
            <td>#{i}</td>
            <td>{f.get('date','?')}</td>
            <td>{f.get('origin','?')} → {f.get('destination','?')}</td>
            <td>{f.get('departure_time','?')} - {f.get('arrival_time','?')}</td>
            <td>{f.get('duration','?')}</td>
            <td>FO {f.get('flight_no','?')}</td>
            <td class="{avail_cls}">{avail_txt}</td>
            <td class="price">{format_price_ars(f['total_price'])}</td>
            <td class="price-final">{format_price_ars(con_equip)}<br><small>US$ {con_equip/DOLAR_MEP:.0f}</small></td>
        </tr>"""

    vuelta_toggle = ""
    if len(inbound_list) > 10:
        vuelta_toggle = f"""<button class="toggle-btn" onclick="toggleSection('vuelta-extra', this)">
            📋 Ver los {len(inbound_list) - 10} vuelos restantes
        </button>"""

    # === CALENDARIO HTML ===
    cal_html = ""
    if calendar:
        for direction, label in [("departures", "✈️ IDA (BUE → FLN)"), ("arrivals", "🔙 VUELTA (FLN → BUE)")]:
            dates = calendar.get(direction, {})
            if dates:
                prices_valid = [
                    (d.get("lowest") or d.get("min_price", float("inf")))
                    for d in dates.values()
                    if (d.get("lowest") or d.get("min_price"))
                ]
                min_price = min(prices_valid) if prices_valid else 0
                cal_html += f"<h3>{label}</h3><div class='cal-grid'>"
                for date in sorted(dates.keys()):
                    info = dates[date]
                    lowest = info.get("lowest") or info.get("min_price")
                    if lowest:
                        is_cheap = lowest == min_price
                        cls = "cal-cheap" if is_cheap else "cal-normal"
                        day = date.split("-")[2]
                        month = date.split("-")[1]
                        cal_html += f"""
                        <div class="cal-day {cls}">
                            <div class="cal-date">{day}/{month}</div>
                            <div class="cal-price">{format_price_ars(lowest)}</div>
                            {"<div class='cal-badge'>💰 MÁS BARATO</div>" if is_cheap else ""}
                        </div>"""
                cal_html += "</div>"

    # === LEER INTELIGENCIA DE CÓDIGO ===
    codigo_section = ""
    resumen_path = DATA_DIR / "resumen_codigo.txt"
    if resumen_path.exists():
        try:
            contenido_codigo = resumen_path.read_text(encoding="utf-8")
            if contenido_codigo.strip():
                codigo_section = f"""
                <div class="section" id="codigo">
                    <div class="section-title">🕵️ Inteligencia de Código Fuente</div>
                    <div style="background:rgba(0,0,0,0.3); padding:15px; border-radius:10px; font-family:monospace; font-size:0.9em; border:1px solid #444;">
                        {contenido_codigo}
                    </div>
                </div>
                """
        except Exception:
            pass

    # === HTML COMPLETO ===
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✈️ Flybondi Monitor — {datetime.now().strftime('%d/%m/%Y %H:%M')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 2.2em;
            margin-bottom: 5px;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 25px; font-size: 0.95em; }}

        /* HERO */
        .hero {{
            background: linear-gradient(135deg, #1a472a, #2d6a4f);
            border-radius: 16px;
            padding: 25px 30px;
            text-align: center;
            margin-bottom: 30px;
            border: 2px solid #40916c;
        }}
        .hero-label {{ font-size: 0.95em; color: #b7e4c7; }}
        .hero-price {{ font-size: 3em; font-weight: 800; color: #52b788; margin: 5px 0; }}
        .hero-detail {{ font-size: 1em; color: #95d5b2; }}
        .hero-detail .small {{ font-size: 0.85em; color: #7bba9e; }}
        .hero-savings {{ font-size: 1.1em; color: #b7e4c7; margin-top: 8px; }}
        .hero-savings strong {{ color: #ffdd57; }}

        /* NAVEGACIÓN */
        .nav {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; justify-content: center; }}
        .nav a {{
            padding: 8px 18px;
            background: rgba(58,123,213,0.2);
            color: #a0c4ff;
            border-radius: 20px;
            text-decoration: none;
            font-size: 0.9em;
            border: 1px solid rgba(58,123,213,0.3);
            transition: background 0.2s;
        }}
        .nav a:hover {{ background: rgba(58,123,213,0.4); }}

        /* SECCIONES */
        .section {{ margin-bottom: 35px; }}
        .section-title {{
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #3a7bd5;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section-count {{ font-size: 0.8em; color: #888; font-weight: 400; }}

        /* COMBO CARDS */
        .combo-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
            border: 1px solid rgba(255,255,255,0.08);
            transition: transform 0.2s, border-color 0.2s;
        }}
        .combo-card:hover {{ transform: translateY(-2px); border-color: #3a7bd5; }}
        .combo-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }}
        .rank {{ font-size: 1.4em; font-weight: 800; color: #3a7bd5; min-width: 40px; }}
        .combo-price-final {{ font-size: 1.6em; font-weight: 700; color: #52b788; }}
        .combo-usd {{ font-size: 1em; color: #95d5b2; }}
        .combo-sub-price {{ font-size: 0.8em; color: #777; margin-bottom: 6px; }}
        .combo-dates {{ color: #aaa; margin-bottom: 10px; font-size: 0.9em; }}

        .badge {{
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 700;
        }}
        .badge-green {{ background: #2d6a4f; color: #b7e4c7; }}
        .badge-yellow {{ background: #7c6f00; color: #ffdd57; }}
        .badge-red {{ background: #6a2d2d; color: #ffaaaa; }}
        .badge-normal {{ background: #444; color: #ccc; }}

        /* TABLAS DE VUELOS */
        .flight-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }}
        .flight-table td {{
            padding: 7px 8px;
            font-size: 0.85em;
        }}
        .ida-row {{ background: rgba(58, 123, 213, 0.12); }}
        .vuelta-row {{ background: rgba(213, 58, 157, 0.12); }}

        .buy-btn {{
            display: inline-block;
            background: linear-gradient(90deg, #ff6b35, #f7c948);
            color: #1a1a2e;
            padding: 8px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.85em;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .buy-btn:hover {{ transform: scale(1.05); box-shadow: 0 4px 15px rgba(255,107,53,0.4); }}

        /* TABLAS DE DATOS */
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            overflow: hidden;
        }}
        .data-table th {{
            background: rgba(58,123,213,0.25);
            padding: 8px 10px;
            text-align: left;
            font-size: 0.8em;
            color: #a0c4ff;
            position: sticky;
            top: 0;
        }}
        .data-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            font-size: 0.85em;
        }}
        .data-table tr:hover {{ background: rgba(255,255,255,0.05); }}
        .data-table tbody tr:nth-child(-n+5) {{ background: rgba(45,106,79,0.1); }}
        .price {{ color: #52b788; font-weight: 600; }}
        .price-final {{ color: #ffdd57; font-weight: 700; }}
        .avail-low {{ color: #ff6b6b; font-weight: 600; }}

        /* CALENDARIO */
        .cal-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(95px, 1fr));
            gap: 6px;
            margin-bottom: 15px;
        }}
        .cal-day {{
            background: rgba(255,255,255,0.04);
            border-radius: 8px;
            padding: 8px;
            text-align: center;
        }}
        .cal-cheap {{
            background: rgba(45,106,79,0.35);
            border: 2px solid #52b788;
        }}
        .cal-date {{ font-size: 0.8em; color: #aaa; }}
        .cal-price {{ font-size: 0.85em; font-weight: 600; color: #e0e0e0; margin-top: 3px; }}
        .cal-badge {{
            background: #52b788;
            color: #1a1a2e;
            font-size: 0.6em;
            padding: 2px 5px;
            border-radius: 10px;
            margin-top: 3px;
            font-weight: 700;
            display: inline-block;
        }}

        .equip-note {{
            background: rgba(255,221,87,0.1);
            border: 1px solid rgba(255,221,87,0.3);
            border-radius: 10px;
            padding: 12px 18px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #ffdd57;
        }}
        .equip-note strong {{ color: #fff; }}

        .hidden-item {{ display: none; }}
        .toggle-btn {{
            display: block;
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(58,123,213,0.15);
            color: #a0c4ff;
            border: 1px dashed rgba(58,123,213,0.4);
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.2s;
        }}
        .toggle-btn:hover {{ background: rgba(58,123,213,0.3); }}

        .compare-box {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,221,87,0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .compare-title {{ font-size: 1.1em; font-weight: 700; margin-bottom: 15px; color: #ffdd57; }}
        .compare-row {{ display: flex; align-items: center; gap: 20px; flex-wrap: wrap; justify-content: center; }}
        .compare-item {{
            flex: 1;
            min-width: 200px;
            background: rgba(255,255,255,0.04);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }}
        .compare-label {{ font-size: 0.85em; color: #aaa; margin-bottom: 5px; }}
        .compare-price {{ font-size: 1.4em; font-weight: 700; color: #52b788; }}
        .compare-detail {{ font-size: 0.8em; color: #888; margin-top: 5px; }}
        .compare-vs {{ font-size: 1.2em; font-weight: 800; color: #666; }}
        .compare-result {{
            text-align: center;
            margin-top: 15px;
            padding: 10px;
            background: rgba(82,183,136,0.1);
            border-radius: 8px;
            font-size: 0.95em;
        }}

        .footer {{
            text-align: center;
            color: #555;
            margin-top: 40px;
            padding: 20px;
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
<div class="container">

    <h1>✈️ Monitor de Vuelos Flybondi</h1>
    <p class="subtitle">Buenos Aires (BUE) → Florianópolis (FLN) · {ADULTS} adultos · {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>

    <div class="nav">
        <a href="#combos">🎯 Ida+Vuelta</a>
        <a href="#ida">✈️ Solo Ida</a>
        <a href="#vuelta">🔙 Solo Vuelta</a>
        <a href="#calendario">📅 Calendario</a>
        { '<a href="#codigo">🕵️ Código Fuente</a>' if codigo_section else '' }
    </div>

    <div class="hero">
        <div class="hero-label">🏆 MEJOR PRECIO ENCONTRADO (con equipaje)</div>
        <div class="hero-price">{format_price_ars(best_total_equip) if best else 'N/A'}</div>
        <div class="hero-detail">
            US$ {best_usd_equip:.0f} al dólar MEP ${DOLAR_MEP:.0f}
            <br><span class="small">Pasajes: {format_price_ars(best['total_ars']) if best else 'N/A'} + Equipaje: ~{format_price_ars(EQUIPAJE_ESTIMADO)}</span>
        </div>
        <div class="hero-savings">
            {"💵 Con tus <strong>US$ " + f"{DOLARES_AHORRADOS:.0f}" + "</strong> ahorrados → te sobran <strong>US$ " + f"{sobra_usd:.0f}" + "</strong> 🍹" if sobra_usd > 0 else "⚠️ Necesitás <strong>US$ " + f"{best_usd_equip:.0f}" + "</strong> (tenés US$ " + f"{DOLARES_AHORRADOS:.0f}" + ", faltan US$ " + f"{abs(sobra_usd):.0f}" + ")" if best else ""}
        </div>
    </div>

    <div class="equip-note">
        🧳 <strong>Equipaje estimado:</strong> {format_price_ars(EQUIPAJE_ESTIMADO)} para {ADULTS} personas ida y vuelta (20kg c/u).
        Los precios en <span style="color:#ffdd57">amarillo</span> incluyen este estimado.
        Podés ajustarlo con la variable <code>EQUIPAJE_ESTIMADO</code>.
    </div>

    <!-- COMBOS IDA + VUELTA -->
    <div class="section" id="combos">
        <div class="section-title">🎯 Ida + Vuelta — precio total {ADULTS} personas <span class="section-count">({len(all_results)} combinaciones)</span></div>
        {combos_html}
    </div>

    {comparacion_html}

    <!-- SOLO IDA -->
    <div class="section" id="ida">
        <div class="section-title">✈️ Solo IDA (BUE → FLN) — {ADULTS} personas <span class="section-count">({len(outbound_list)} vuelos)</span></div>
        <table class="data-table">
            <thead><tr>
                <th>#</th><th>Fecha</th><th>Ruta</th><th>Horario</th><th>Duración</th><th>Vuelo</th><th>Asientos</th><th>Precio</th><th>Con equipaje</th>
            </tr></thead>
            <tbody>{ida_html}</tbody>
        </table>
        {ida_toggle}
    </div>

    <!-- SOLO VUELTA -->
    <div class="section" id="vuelta">
        <div class="section-title">🔙 Solo VUELTA (FLN → BUE) — {ADULTS} personas <span class="section-count">({len(inbound_list)} vuelos)</span></div>
        <table class="data-table">
            <thead><tr>
                <th>#</th><th>Fecha</th><th>Ruta</th><th>Horario</th><th>Duración</th><th>Vuelo</th><th>Asientos</th><th>Precio</th><th>Con equipaje</th>
            </tr></thead>
            <tbody>{vuelta_html}</tbody>
        </table>
        {vuelta_toggle}
    </div>

    <!-- CALENDARIO -->
    <div class="section" id="calendario">
        <div class="section-title">📅 Calendario de Tarifas (precio por persona, sin equipaje)</div>
        {cal_html}
    </div>

    {codigo_section}

    <div class="footer">
        Monitor Flybondi v1.0 · Datos de la API de Flybondi en tiempo real<br>
        Precios incluyen impuestos y tasas · Equipaje es estimado<br>
        {len(all_results)} combinaciones · {len(outbound_list)} vuelos ida · {len(inbound_list)} vuelos vuelta
    </div>

</div>
<script>
function toggleSection(className, btn) {{
    const items = document.querySelectorAll('.' + className);
    const isHidden = items[0] && items[0].style.display !== 'table-row' && items[0].style.display !== 'block';
    items.forEach(el => {{
        if (el.tagName === 'TR') {{
            el.style.display = isHidden ? 'table-row' : 'none';
        }} else {{
            el.style.display = isHidden ? 'block' : 'none';
        }}
        el.classList.toggle('hidden-item');
    }});
    btn.textContent = isHidden ? '🔼 Ocultar' : btn.getAttribute('data-original') || btn.textContent;
    if (!btn.getAttribute('data-original')) btn.setAttribute('data-original', btn.textContent);
}}
</script>
</body>
</html>"""

    report_file.write_text(html, encoding="utf-8")
    print(f"   📊 Reporte HTML guardado: {report_file.name}")

    # Abrir en el navegador automáticamente
    try:
        webbrowser.open(str(report_file.resolve()))
        print(f"   🌐 Abriendo reporte en el navegador...")
    except Exception:
        print(f"   ℹ️ Abrí manualmente: {report_file.resolve()}")

    return report_file


# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

def run_search(send_telegram_alerts: bool = True, json_output: bool = False) -> list[dict]:
    """
    Ejecuta una búsqueda completa en todas las combinaciones de fechas.
    
    Returns:
        Lista de todos los resultados encontrados, ordenados por precio
    """
    now = datetime.now()
    print("\n" + "=" * 70)
    print(f"🛫 FLYBONDI MONITOR — {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Ruta: {ORIGIN} → {DESTINATION} | 👥 {ADULTS} adultos")
    print(f"   Dólar MEP: ${DOLAR_MEP:,.0f}")
    print(f"   Umbrales: 🟢 <{format_price_ars(ALERTA_VERDE)} | "
          f"🟡 <{format_price_ars(ALERTA_AMARILLA)} | "
          f"🔴 >{format_price_ars(TECHO_MAXIMO)}")
    print("=" * 70)

    all_results = []
    calendar_data = None
    date_combos = list(product(DEPARTURE_DATES, RETURN_DATES))
    total_combos = len(date_combos)
    errors = 0

    for i, (dep, ret) in enumerate(date_combos, 1):
        print(f"\n📅 [{i}/{total_combos}] {dep} → {ret}")

        data = query_flybondi(dep, ret)
        if data is None:
            errors += 1
            continue

        # Parsear vuelos
        combos = parse_flights(data, dep, ret)
        all_results.extend(combos)

        # Parsear calendario (solo la primera vez)
        if calendar_data is None:
            calendar_data = parse_calendar_fares(data)

        # Mostrar resultados parciales
        for combo in combos:
            level, emoji = classify_alert(combo["total_ars"])
            ob = combo.get("outbound", combo.get("single_flight", {}))
            ib = combo.get("inbound", {})
            
            if ib:
                print(f"   {emoji} TOTAL: {format_price_ars(combo['total_ars'])} "
                      f"(US$ {combo['total_usd']:.0f}) "
                      f"| {ob.get('flight_no', '?')} + {ib.get('flight_no', '?')}")
            else:
                print(f"   ℹ️ Vuelo suelto: {format_price_ars(combo['total_ars'])}")

        # Pequeña pausa entre requests para no saturar la API
        if i < total_combos:
            time.sleep(1.5)

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    
    if not all_results:
        print("\n❌ No se encontraron vuelos en ninguna combinación de fechas.")
        if errors > 0:
            print(f"   ({errors} errores de API — ¿expiró la API key?)")
        return []

    # Ordenar por precio
    all_results.sort(key=lambda x: x.get("total_ars", float("inf")))

    print("\n" + "=" * 70)
    print(f"📊 TODOS LOS VUELOS — {len(all_results)} combinaciones (más barato → más caro)")
    print("=" * 70)

    for i, combo in enumerate(all_results, 1):
        level, emoji = classify_alert(combo["total_ars"])
        ob = combo.get("outbound", {})
        ib = combo.get("inbound", {})

        print(f"\n{emoji} #{i}  {format_price_ars(combo['total_ars'])} "
              f"(US$ {combo.get('total_usd', 0):.0f}) "
              f"— [{level}]  📅 {combo['departure_date']} → {combo['return_date']}")
        
        if ob:
            print(format_flight_line(ob, "IDA"))
        if ib:
            print(format_flight_line(ib, "VTA"))

    # Mejor precio
    best = all_results[0]
    best_level, best_emoji = classify_alert(best["total_ars"])

    print(f"\n{'=' * 70}")
    print(f"🏆 MEJOR PRECIO: {best_emoji} {format_price_ars(best['total_ars'])} "
          f"(US$ {best.get('total_usd', 0):.0f}) — [{best_level}]")
    
    costo_usd = best["total_ars"] / DOLAR_MEP
    sobra = DOLARES_AHORRADOS - costo_usd
    if sobra > 0:
        print(f"   💵 Con US$ {DOLARES_AHORRADOS:.0f} ahorrados → "
              f"te sobran US$ {sobra:.0f}")
    else:
        print(f"   💵 Necesitás US$ {costo_usd:.0f} "
              f"(tenés US$ {DOLARES_AHORRADOS:.0f}, "
              f"faltan US$ {abs(sobra):.0f})")

    # ========================================================================
    # CALENDARIO DE TARIFAS
    # ========================================================================

    if calendar_data:
        print(f"\n{'=' * 70}")
        print("📅 CALENDARIO DE TARIFAS (precio más bajo por día)")
        print("=" * 70)
        
        for direction, label in [("departures", "IDA"), ("arrivals", "VUELTA")]:
            dates = calendar_data.get(direction, {})
            if dates:
                print(f"\n  {label}:")
                for date in sorted(dates.keys()):
                    info = dates[date]
                    lowest = info.get("lowest") or info.get("min_price")
                    if lowest:
                        marker = " ← BARATO" if lowest == min(
                            (d.get("lowest") or d.get("min_price", float("inf")))
                            for d in dates.values()
                            if (d.get("lowest") or d.get("min_price"))
                        ) else ""
                        print(f"    {date}: {format_price_ars(lowest)}{marker}")

    # ========================================================================
    # TRACKING DE DISPONIBILIDAD (Anti-Scareware)
    # ========================================================================

    history = load_availability_history()
    scareware_warnings = []

    for combo in all_results:
        if "outbound" in combo and "inbound" in combo:
            warning = track_availability(combo, history)
            if warning:
                scareware_warnings.append(warning)

    save_availability_history(history)

    if scareware_warnings:
        print(f"\n{'=' * 70}")
        print("🚨 ALERTAS DE SCAREWARE")
        print("=" * 70)
        for w in scareware_warnings:
            print(f"  {w}")

    # ========================================================================
    # ENVIAR ALERTAS TELEGRAM
    # ========================================================================

    if send_telegram_alerts and best_level in ("VERDE", "AMARILLA"):
        print(f"\n📨 Enviando alerta {best_level} a Telegram...")
        msg = build_telegram_alert(best, best_level, best_emoji)
        send_telegram(msg, silent=(best_level == "AMARILLA"))

        # Agregar observaciones de scareware si hay
        if scareware_warnings:
            scareware_msg = "🚨 *ALERTA SCAREWARE*\n\n" + "\n".join(scareware_warnings)
            send_telegram(scareware_msg, silent=True)

    # ========================================================================
    # GUARDAR LOG
    # ========================================================================

    save_search_log(all_results, calendar_data)
    generate_html_report(all_results, calendar_data)

    # JSON output si se pidió
    if json_output:
        print("\n" + json.dumps(all_results, indent=2, ensure_ascii=False, default=str))

    return all_results


def run_loop(interval_minutes: int, send_telegram_alerts: bool = True):
    """Ejecuta el monitor en modo daemon (loop infinito)."""
    print(f"\n🔄 MODO DAEMON — Chequeando cada {interval_minutes} minutos")
    print(f"   Presioná Ctrl+C para detener\n")

    # Notificar inicio por Telegram
    if send_telegram_alerts:
        send_telegram(
            f"🤖 *Monitor Flybondi activado*\n\n"
            f"Ruta: {ORIGIN}→{DESTINATION}\n"
            f"Intervalo: cada {interval_minutes} min\n"
            f"Umbrales: 🟢<{format_price_ars(ALERTA_VERDE)} "
            f"🟡<{format_price_ars(ALERTA_AMARILLA)}",
            silent=True,
        )

    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"\n{'#' * 70}")
            print(f"# ITERACIÓN #{iteration}")
            print(f"{'#' * 70}")

            run_search(send_telegram_alerts=send_telegram_alerts)

            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            print(f"\n⏳ Próxima búsqueda: {next_run.strftime('%H:%M:%S')}")
            print(f"   (durmiendo {interval_minutes} minutos...)")

            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n🛑 Monitor detenido por el usuario.")
            if send_telegram_alerts:
                send_telegram("🛑 Monitor Flybondi detenido.", silent=True)
            break


# ============================================================================
# CLI
# ============================================================================

def main():
    global DOLAR_MEP, API_KEY, HEADERS

    parser = argparse.ArgumentParser(
        description="🛫 Monitor de precios Flybondi (API GraphQL directa)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python monitor_flybondi.py                 # Búsqueda única
  python monitor_flybondi.py --loop          # Daemon cada 60 min
  python monitor_flybondi.py --loop 30       # Daemon cada 30 min
  python monitor_flybondi.py --no-telegram   # Sin alertas Telegram
  python monitor_flybondi.py --json          # Output JSON
  python monitor_flybondi.py --mep 1500      # Dólar MEP custom
  
🔑 Cómo actualizar la API key si expira:
  1. Abrí https://flybondi.com/ar/search/dates en Chrome
  2. Abrí DevTools (F12) → Network → Fetch/XHR
  3. Buscá "Buenos Aires" → "Florianópolis" → Buscar
  4. Buscá la request "graphql" en la lista
  5. Click derecho → Copy → Copy as cURL
  6. Del cURL, copiá el valor de "authorization: Key XXXXX"
  7. Poné la key nueva en la variable FLYBONDI_API_KEY en .env
     o pasala con --key XXXXX
        """,
    )

    parser.add_argument("--loop", nargs="?", const=CHECK_INTERVAL_MINUTES,
                        type=int, metavar="MIN",
                        help=f"Modo daemon, chequea cada N minutos (default: {CHECK_INTERVAL_MINUTES})")
    parser.add_argument("--no-telegram", action="store_true",
                        help="No enviar alertas por Telegram")
    parser.add_argument("--json", action="store_true",
                        help="Output en JSON")
    parser.add_argument("--mep", type=float, default=None,
                        help="Dólar MEP manual (default: 1440)")
    parser.add_argument("--key", type=str, default=None,
                        help="API key de Flybondi (override)")

    args = parser.parse_args()

    # Overrides
    if args.mep:
        DOLAR_MEP = args.mep
    if args.key:
        API_KEY = args.key
        HEADERS["authorization"] = f"Key {API_KEY}"

    send_tg = not args.no_telegram

    # Ejecutar
    if args.loop is not None:
        run_loop(args.loop, send_telegram_alerts=send_tg)
    else:
        results = run_search(send_telegram_alerts=send_tg, json_output=args.json)
        
        if not results:
            sys.exit(1)
        
        best_level, _ = classify_alert(results[0]["total_ars"])
        if best_level == "VERDE":
            sys.exit(0)   # 🟢 ¡A comprar!
        elif best_level == "AMARILLA":
            sys.exit(0)   # 🟡 Oportunidad
        else:
            sys.exit(2)   # ⚪ Normal / 🔴 Caro


if __name__ == "__main__":
    main()
