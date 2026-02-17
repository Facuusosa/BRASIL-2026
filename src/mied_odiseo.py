
import json
import requests
import re
from datetime import datetime, timedelta, timezone
import time
import sys

# --- CONFIGURACIÓN ---
IDENTITY_FILE = 'identity.txt'
LOG_FILE = 'alertas.log'
TARGET_PRICE = 800000 

TARGET_DATES = [
    "2026-03-08",
    "2026-03-09",
    "2026-03-10",
    "2026-03-11"
]

class SessionCloner:
    def __init__(self, curl_command):
        self.url = ""
        self.headers = {}
        self.data = None
        self.method = "GET"
        self._parse_curl(curl_command)

    def _parse_curl(self, curl_command):
        # ESTRATEGIA BRUTA v3.0 (COOKIES SUPPORT)
        
        # 1. URL
        if 'flybondi.com/graphql' in curl_command:
            self.url = 'https://flybondi.com/graphql'
        else:
            matches = re.search(r"'(https?://[^']+)'", curl_command)
            if matches:
                self.url = matches.group(1)
            else:
                start = curl_command.find('http')
                if start != -1:
                    end = curl_command.find("'", start)
                    if end == -1: end = curl_command.find(' ', start)
                    self.url = curl_command[start:end]

        # 2. Headers (CON LIMPIEZA AGRESIVA)
        # Regex más permisiva para valores vacíos: ([^'\"]*)
        headers_matches = re.findall(r"-H\s+['\"]([^:]+):\s*([^'\"]*)['\"]", curl_command)
        
        for key, val in headers_matches:
            k = key.strip()
            v = val.strip()
            
            # FILTRO: Ignorar headers rotos, con saltos de línea o caracteres prohibidos en el nombre
            if not k or '\n' in k or ';' in k or ' ' in k:
                continue
                
            self.headers[k] = v

        # 2.5 COOKIES (CRITICO PARA WAF)
        # Buscar -b "cookie=value" o --cookie "cookie=value"
        cookie_matches = re.findall(r"(?:-b|--cookie)\s+['\"]([^'\"]+)['\"]", curl_command)
        if cookie_matches:
            cookie_str = "; ".join(cookie_matches) # Unir multiples si las hay
            # Si ya existe cookie header, appendeamos
            if 'cookie' in self.headers or 'Cookie' in self.headers:
                c_key = 'Cookie' if 'Cookie' in self.headers else 'cookie'
                self.headers[c_key] += f"; {cookie_str}"
            else:
                self.headers['Cookie'] = cookie_str

        # 3. Data
        data_match = re.search(r"--data-raw\s+\$?'({.*})'", curl_command, re.DOTALL)
        if not data_match:
             data_match = re.search(r"--data\s+\$?'({.*})'", curl_command, re.DOTALL)
        
        if data_match:
            self.data = data_match.group(1)
            if "\\n" in self.data:
                 self.data = self.data.replace("\\n", " ")
            self.method = "POST"
        else:
            start = curl_command.find('{')
            end = curl_command.rfind('}')
            if start != -1 and end != -1:
                self.data = curl_command[start:end+1]
                self.method = "POST"

    def clone_request(self, new_payload_str=None):
        try:
            # Importante: requests valida headers estrictamente.
            # Limpiamos headers antes de enviar.
            safe_headers = {k: v for k, v in self.headers.items() if k and v}
            
            data = new_payload_str if new_payload_str else self.data

            if data and self.method == "POST":
                if 'content-type' not in safe_headers:
                     safe_headers['content-type'] = 'application/json'
                # Content-Length debe ser exacto
                safe_headers['Content-Length'] = str(len(data.encode('utf-8')))
                response = requests.post(self.url, headers=safe_headers, data=data)
            else:
                response = requests.get(self.url, headers=safe_headers)
            return response
        except Exception as e:
            print(f"❌ Error en petición clonada: {e}")
            return None

class DataMiner:
    def extract_flights(self, response_json):
        flights = []
        try:
            if 'data' in response_json and 'flightSearch' in response_json['data']:
                edges = response_json['data']['flightSearch']['flights']['edges']
                for edge in edges:
                    node = edge['node']
                    origin = node.get('origin')
                    destination = node.get('destination')
                    dep_date_str = node.get('departureDate') 
                    arr_date_str = node.get('arrivalDate')
                    
                    dep_dt = datetime.fromisoformat(dep_date_str)
                    arr_dt = datetime.fromisoformat(arr_date_str)
                    
                    if dep_dt.hour < 6: continue 
                    if arr_dt.hour >= 20: continue 
                    
                    price = float('inf')
                    if 'fares' in node:
                        for fare in node['fares']:
                            if fare.get('availability', 0) > 0:
                                p = fare['prices']['afterTax']
                                if p < price: price = p
                    
                    if price != float('inf'):
                        flights.append({
                            'fecha': dep_dt.strftime('%Y-%m-%d %H:%M'),
                            'llegada': arr_dt.strftime('%H:%M'),
                            'precio': price,
                            'origen': origin,
                            'destino': destination
                        })

            elif 'data' in response_json and 'search' in response_json['data']:
                legs = response_json['data']['search']['legs']
                for leg in legs:
                    date = leg.get('date')
                    price = leg.get('price', {}).get('amount')
                    if price and date:
                        flights.append({'fecha': date, 'precio': price, 'origen': 'UNK', 'destino': 'UNK', 'llegada': 'UNK'})

        except Exception as e:
            pass
        return flights

class OdiseoCore:
    def __init__(self, curl_file_path, target_price):
        self.curl_file_path = curl_file_path
        self.target_price = target_price
        self.cloner = None
        self.miner = DataMiner()
        self.scan_dates = TARGET_DATES

    def load_identity(self):
        try:
            with open(self.curl_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                idx = content.find("curl ")
                if idx != -1: content = content[idx:]
                
                self.cloner = SessionCloner(content)
                if not self.cloner.url:
                     raise ValueError("No se pudo extraer URL válida")
                print("✅ Identidad asimilada.")
                return True
        except Exception as e:
            print(f"❌ Error cargando identidad: {e}")
            return False

    def _generate_smart_payload(self, original_json_str, target_date_str):
        try:
            clean_json = original_json_str
            if "\\n" in clean_json: clean_json = clean_json.replace("\\n", " ")
            if "\\u0021" in clean_json: clean_json = clean_json.replace("\\u0021", "!")
            
            payload_dict = json.loads(clean_json)
            
            target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
            start_ts = int(target_dt.replace(hour=0, minute=0, second=0).timestamp() * 1000)
            end_ts = int((target_dt + timedelta(days=10)).timestamp() * 1000)

            if 'variables' in payload_dict and 'input' in payload_dict['variables']:
                inp = payload_dict['variables']['input']
                inp['departureDate'] = target_date_str
                return_dt = target_dt + timedelta(days=7)
                inp['returnDate'] = return_dt.strftime("%Y-%m-%d")
                
                if 'start' in payload_dict['variables']:
                    payload_dict['variables']['start'] = start_ts
                if 'end' in payload_dict['variables']:
                    payload_dict['variables']['end'] = end_ts

            return json.dumps(payload_dict)
        except json.JSONDecodeError:
            print("⚠️ JSON complejo. Reemplazo básico.")
            return re.sub(r'"date":"\d{4}-\d{2}-\d{2}"', f'"date":"{target_date_str}"', original_json_str)

    def run_scan(self):
        if not self.load_identity():
            return

        print(f"🚀 Iniciando MIED Odiseo v2.3 (Sanitized).")
        print(f"📅 Fechas Objetivo: {self.scan_dates}")
        
        for date in self.scan_dates:
            print(f"\n📡 Escaneando {date}...", end="", flush=True)
            
            current_payload = self.cloner.data
            new_payload = None
            if current_payload:
                new_payload = self._generate_smart_payload(current_payload, date)

            time.sleep(3) 
            
            response = self.cloner.clone_request(new_payload)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    flights = self.miner.extract_flights(data)
                    
                    if flights:
                        print(f" ✅ {len(flights)} vuelos encontrados.")
                        for f in flights:
                            price = f['precio']
                            msg = f"   ✈️ {f['fecha']} -> {f['llegada']} | ${price:,.2f}"
                            print(msg)
                            self._alert(f, price)
                    else:
                        print(" ⚠️ Sin vuelos que cumplan criterio horario/precio.")
                        
                except json.JSONDecodeError:
                    print(" ❌ Error JSON (Posible WAF Block).")
            elif response.status_code == 403:
                print("\n⛔ [CRÍTICO] 403 FORBIDDEN. El WAF detectó la inyección.")
                sys.exit(1)
            else:
                print(f" ❌ Error HTTP {response.status_code}")

    def _alert(self, flight_data, price):
        msg = f"🚨 OPORTUNIDAD: {flight_data['fecha']} - ${price:,.2f}"
        print(f"   🔥 {msg}")
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now()} - {msg}\n")

if __name__ == "__main__":
    bot = OdiseoCore(IDENTITY_FILE, TARGET_PRICE)
    bot.run_scan()
