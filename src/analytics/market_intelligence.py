import json
import os
from pathlib import Path
from datetime import datetime

# Configuración básica
PROJECT_DIR = Path(__file__).parent.parent.parent
DATA_FILE = PROJECT_DIR / "turismocity_success.json"
REPORT_FILE = PROJECT_DIR / "data" / "market_intelligence_report.txt"

def analyze_market():
    """ Analiza el dump manual de Turismocity para extraer inteligencia competitiva. """
    
    if not DATA_FILE.exists():
        print(f"❌ No se encontró el archivo de datos: {DATA_FILE}")
        return

    print(f"📊 Iniciando Análisis de Inteligencia de Mercado...")
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        flights = []
        
        # Lógica robusta para detectar estructura
        if isinstance(raw_data, list):
            print(f"   Estructura detectada: LISTA ({len(raw_data)} elementos)")
            # Buscar en cada elemento si tiene 'flights'
            for item in raw_data:
                if isinstance(item, dict):
                    if "flights" in item:
                        flights.extend(item["flights"])
                    elif "bestFlights" in item:
                        # Si es un objeto de resumen, podríamos extraer info de ahí también
                        pass
        elif isinstance(raw_data, dict):
             print(f"   Estructura detectada: DICCIONARIO")
             flights = raw_data.get("flights", [])
        
        if not flights:
            print("❌ No se encontraron vuelos en la estructura analizada.")
            # Intento de debug adicional: imprimir keys del primer elemento si es lista
            if isinstance(raw_data, list) and len(raw_data) > 0:
                print(f"   Keys del primer elemento: {list(raw_data[0].keys()) if isinstance(raw_data[0], dict) else 'No es dict'}")
            return

        print(f"   Vuelos extraídos para análisis: {len(flights)}")

        # Métricas clave
        cheapest_overall = None
        cheapest_non_lowcost = None
        cheapest_with_baggage = None
        
        airlines_found = set()
        
        for flight in flights:
            price_info = flight.get("price", {})
            total_price = price_info.get("totalAmount", float('inf'))
            currency = price_info.get("currency", "ARS")
            
            # Identificar aerolínea (asumimos que está en el primer segmento)
            outbound = flight.get("outboundRoutes", [])
            airline_code = "Unknown"
            airline_name = "Unknown"
            
            if outbound:
                segments = outbound[0].get("segments", [])
                if segments:
                    airline_code = segments[0].get("marketingAirline", {}).get("code", "??")
                    airline_name = segments[0].get("marketingAirline", {}).get("name", "Unknown")
            
            airlines_found.add(airline_name)
            
            is_lowcost = airline_code in ["FO", "WJ"] # FO=Flybondi, WJ=Jetsmart
            has_baggage = False # Lógica compleja, simplificamos por ahora
            
            # Check equipaje (mockup, dependerá de la estructura real)
            # baggage_info = flight.get("baggageInformation", {}) or ...
            
            # 1. Cheapest Overall
            if cheapest_overall is None or total_price < cheapest_overall["price"]:
                cheapest_overall = {
                    "price": total_price,
                    "airline": airline_name,
                    "currency": currency,
                    "stops": len(segments) - 1 if segments else 0
                }
            
            # 2. Cheapest INCUMBENT (No Low Cost) -> GOL, Aerolíneas, Latam
            if not is_lowcost:
                if cheapest_non_lowcost is None or total_price < cheapest_non_lowcost["price"]:
                    cheapest_non_lowcost = {
                        "price": total_price,
                        "airline": airline_name,
                        "currency": currency,
                        "stops": len(segments) - 1 if segments else 0
                    }

        # Generar Reporte
        report_lines = []
        report_lines.append(f"🧠 REPORTE DE INTELIGENCIA DE MERCADO (ODISEO)")
        report_lines.append(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        report_lines.append(f"{'='*50}")
        report_lines.append(f"🔹 Aerolíneas Detectadas: {', '.join(airlines_found)}")
        
        if cheapest_overall:
            report_lines.append(f"\n🏆 MEJOR PRECIO ABSOLUTO:")
            report_lines.append(f"   ${cheapest_overall['price']:,.0f} ({cheapest_overall['currency']})")
            report_lines.append(f"   Aerolínea: {cheapest_overall['airline']}")
            report_lines.append(f"   Escalas: {cheapest_overall['stops']}")

        if cheapest_non_lowcost:
            report_lines.append(f"\n🛡️ MEJOR OPCIÓN TRADICIONAL (Referencia de Calidad):")
            report_lines.append(f"   ${cheapest_non_lowcost['price']:,.0f} ({cheapest_non_lowcost['currency']})")
            report_lines.append(f"   Aerolínea: {cheapest_non_lowcost['airline']}")
            
            # Calculamos el GAP
            if cheapest_overall:
                gap = cheapest_non_lowcost['price'] - cheapest_overall['price']
                gap_pct = (gap / cheapest_overall['price']) * 100
                report_lines.append(f"\n⚡ GAP DE MERCADO:")
                report_lines.append(f"   Diferencia: ${gap:,.0f} (+{gap_pct:.1f}%)")
                report_lines.append(f"   Conclusión: {'Flybondi conviene' if gap_pct > 20 else 'Ojo! La competencia está cerca'}")
        
        # Guardar y mostrar
        report_text = "\n".join(report_lines)
        print(report_text)
        
        # Guardar en archivo para persistencia
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report_text)
            
    except Exception as e:
        print(f"💥 Error analizando mercado: {e}")

if __name__ == "__main__":
    analyze_market()
