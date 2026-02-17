import time
import json
import os
import datetime
from curl_cffi import requests
try:
    from mied_odiseo import SessionCloner
except ImportError:
    SessionCloner = None

# ==============================================================================
# CONFIGURACIÓN DE MISIÓN (ODISEO)
# ==============================================================================

# VUELO
ORIGIN = "BUE"
DESTINATION = "FLN"
DATES_TO_MONITOR = [
    "2026-03-08", # Domingo (El deseado)
    "2026-03-09", # Lunes
    "2026-03-10", # Martes (El barato)
    "2026-03-11", # Miércoles
    "2026-03-12"  # Jueves
]

# UMBRALES (ARS)
PRECIO_GANGA = 200000    # VERDE: Comprar sin pensar (< 200k)
PRECIO_NORMAL = 250000   # AMARILLO: Analizar (< 250k)
# ROJO: > 250k

# TELEGRAM (Recuperado de memoria)
TELEGRAM_TOKEN = "7736636760:AAHX2p3yRjC2lBhQAxOQ_g2U8T3J91s1wBg"
CHAT_ID = "1136402434"

# SISTEMA
REFRESH_MINUTES = 10     # Chequear cada 10 minutos
DASHBOARD_FILE = "ODISEO_DASHBOARD.html"

# ==============================================================================
# MOTOR API (Validado en flybondi_force.py)
# ==============================================================================

URL = "https://flybondi.com/graphql"
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://flybondi.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def load_dynamic_headers():
    """Carga headers frescos desde identity.txt si es posible."""
    if SessionCloner and os.path.exists("identity.txt"):
        try:
            with open("identity.txt", "r", encoding="utf-8") as f:
                content = f.read()
                # Buscar inicio de curl si hay basura antes
                idx = content.find("curl ")
                if idx != -1: content = content[idx:]
                
            cloner = SessionCloner(content)
            
            # Filtrar headers problematicos para curl_cffi/http2
            forbidden = ['content-length', 'host', 'connection', 'accept-encoding']
            clean_headers = {k: v for k, v in cloner.headers.items() if k.lower() not in forbidden}
            
            # Asegurar content-type
            clean_headers['content-type'] = 'application/json'
            
            return clean_headers
        except Exception as e:
            print(f"⚠️ Error cargando identity.txt: {e}")
    return HEADERS

# Query Limpia (La que funcionó)
QUERY_TEMPLATE = """
query (
  $origin: String!
  $destination: String!
  $currency: String!
) {
  departures: fares(origin: $origin, destination: $destination, currency: $currency, start: {start}, end: {end}, sort: "departure") {
    departure
    lowestPrice
    fares {
      price
      availability
    }
  }
}
"""

def get_price_monitor(date_str):
    """Consulta el precio para una fecha específica."""
    try:
        # Timestamps para cubrir todo el día
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        ts_start = int(dt.timestamp() * 1000)
        # Final del día
        dt_end = dt + datetime.timedelta(hours=23, minutes=59)
        ts_end = int(dt_end.timestamp() * 1000)

        # Inyectar timestamps
        query_final = QUERY_TEMPLATE.replace("{start}", str(ts_start)).replace("{end}", str(ts_end))

        variables = {
            "origin": ORIGIN,
            "destination": DESTINATION,
            "currency": "ARS"
        }

        payload = {
            "operationName": None,
            "query": query_final,
            "variables": variables
        }

        # Cargar headers dinámicos
        current_headers = load_dynamic_headers()

        response = requests.post(
            URL,
            json=payload,
            headers=current_headers, 
            impersonate="chrome110", # La versión que funcionó
            timeout=20
        )

        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                return {"status": "ERROR", "msg": "API Error"}
            
            departures = data.get("data", {}).get("departures", [])
            
            precios = []
            for dep in departures:
                if dep.get("lowestPrice"):
                    precios.append(dep.get("lowestPrice"))
            
            if precios:
                min_price = min(precios)
                return {"status": "OK", "price": min_price, "count": len(departures)}
            else:
                return {"status": "EMPTY", "msg": "Agotado / No Disponible"}
        else:
            return {"status": "HTTP_ERROR", "msg": str(response.status_code)}

    except Exception as e:
        return {"status": "EXCEPTION", "msg": str(e)}

# ==============================================================================
# NOTIFICACIONES Y DASHBOARD
# ==============================================================================

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except:
        pass

def generate_dashboard(results):
    """Genera un HTML con estilo Hacker/Odiseo."""
    
    html_rows = ""
    for r in results:
        date_fmt = datetime.datetime.strptime(r['date'], "%Y-%m-%d").strftime("%A %d/%m")
        
        status_color = "gray"
        price_display = "---"
        action = "ESPERAR"
        row_class = ""
        
        if r['status'] == 'OK':
            price_display = f"${r['price']:,.0f}"
            if r['price'] <= PRECIO_GANGA:
                status_color = "#00ff00" # Neon Green
                action = "COMPRAR YA"
                row_class = "glow-green"
            elif r['price'] <= PRECIO_NORMAL:
                status_color = "#ffff00" # Yellow
                action = "ANALIZAR"
            else:
                status_color = "#ff0000" # Red
                action = "CARO"
        elif r['status'] == 'EMPTY':
            price_display = "AGOTADO"
            status_color = "#444"
            action = "SIN CUPO"
        else:
            price_display = "ERROR API"
            status_color = "#ff00ff" # Magenta
            action = "REINTENTANDO"

        # Link de compra
        link = f"https://flybondi.com/ar/search/results?adults=1&currency=ARS&departureDate={r['date']}&from={ORIGIN}&to={DESTINATION}"
        
        html_rows += f"""
        <tr class="{row_class}">
            <td>{date_fmt}</td>
            <td style="color: {status_color}; font-weight: bold; font-size: 1.2em;">{price_display}</td>
            <td style="color: {status_color}">{action}</td>
            <td><a href="{link}" target="_blank" class="btn">VER VUELO</a></td>
        </tr>
        """

    now = datetime.datetime.now().strftime("%H:%M:%S")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ODISEO MONITOR | {ORIGIN}-{DESTINATION}</title>
        <meta http-equiv="refresh" content="300"> <!-- Auto refresh 5 min -->
        <style>
            body {{ background-color: #0d0d0d; color: #0f0; font-family: 'Courier New', monospace; text-align: center; }}
            h1 {{ text-shadow: 0 0 10px #0f0; }}
            table {{ margin: 0 auto; border-collapse: collapse; width: 80%; }}
            th, td {{ border: 1px solid #333; padding: 15px; }}
            th {{ background-color: #111; color: #fff; }}
            .btn {{ background: #222; color: white; padding: 5px 10px; text-decoration: none; border: 1px solid #555; }}
            .btn:hover {{ background: #444; }}
            .glow-green {{ box-shadow: 0 0 15px #00ff00 inset; }}
            .log {{ color: #666; font-size: 0.8em; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>✈️ SISTEMA ODISEO ACTIVO</h1>
        <h3>Misión: {ORIGIN} -> {DESTINATION} | Marzo 2026</h3>
        <table>
            <tr>
                <th>FECHA</th>
                <th>PRECIO (ARS)</th>
                <th>ESTADO</th>
                <th>ENLACE</th>
            </tr>
            {html_rows}
        </table>
        <div class="log">Última actualización: {now} | Próximo escaneo en {REFRESH_MINUTES} min</div>
    </body>
    </html>
    """
    
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    
    return os.path.abspath(DASHBOARD_FILE)

# ==============================================================================
# BUCLE PRINCIPAL
# ==============================================================================

def main():
    print("🦅 SISTEMA ODISEO INICIADO")
    print(f"🎯 Objetivo: {ORIGIN}-{DESTINATION} | {len(DATES_TO_MONITOR)} Fechas")
    print(f"📡 Dashboard: {os.path.abspath(DASHBOARD_FILE)}")
    
    # ABRIR DASHBOARD AUTOMATICAMENTE
    import webbrowser
    webbrowser.open(os.path.abspath(DASHBOARD_FILE))
    
    print("📨 Enviando notificación de inicio a Telegram...")
    send_telegram(f"🦅 *ODISEO ACTIVO*\nMonitoreando {len(DATES_TO_MONITOR)} fechas para Marzo.\nDashboard inicializado.")
    print("✅ Notificación enviada (o intentada).")

    last_prices = {} # Para detectar cambios

    while True:
        results = []
        alert_msg = ""
        print(f"\n⚡ Escaneando... {datetime.datetime.now().strftime('%H:%M:%S')}")

        for date in DATES_TO_MONITOR:
            res = get_price_monitor(date)
            res['date'] = date
            results.append(res)
            
            # Lógica de Notificación Inteligente
            if res['status'] == 'OK':
                price = res['price']
                print(f"  > {date}: ${price:,.0f}")
                
                # 1. ES GANGA?
                if price <= PRECIO_GANGA:
                    # Avisar siempre si es ganga y no avisamos hace poco (simple debounce aqui)
                    alert_msg += f"🟢 *¡GANGA DETECTADA!* {date}\n💵 *${price:,.0f}*\n"
                
                # 2. CAMBIO DE PRECIO?
                last = last_prices.get(date)
                if last and last != price:
                    diff = price - last
                    icon = "📉" if diff < 0 else "📈"
                    alert_msg += f"{icon} *Cambio {date}:* ${last:,.0f} -> ${price:,.0f}\n"

                last_prices[date] = price

            elif res['status'] == 'EMPTY':
                print(f"  > {date}: AGOTADO")
            else:
                print(f"  > {date}: Error ({res['msg']})")
                
            time.sleep(1) # Rate limit suave

        # Generar HTML
        path = generate_dashboard(results)
        
        # Enviar Alerta Agrupada
        if alert_msg:
            full_msg = f"🦅 *REPORTE ODISEO*\n\n{alert_msg}\n[Ver Dashboard]({URL})" # URL del dashboard local no sirve en telegram, pero aviso
            send_telegram(full_msg)
            print("📨 Alerta enviada a Telegram.")

        print(f"💤 Durmiendo {REFRESH_MINUTES} minutos...")
        time.sleep(REFRESH_MINUTES * 60)

if __name__ == "__main__":
    main()
