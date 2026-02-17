import json

def analyze_competitor_prices():
    try:
        with open("turismocity_clean.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        print("🔍 Analizando Precios de Competencia (Turismocity)...")
        
        # Estructura compleja de Turismocity (graph/diccionario)
        # Buscamos en 'flights' o 'itineraries'
        flights = []
        
        # 1. Intentar encontrar la lista de vuelos
        if isinstance(data, dict):
            if "flights" in data:
                flights = data["flights"]
            elif "data" in data and "flights" in data["data"]:
                flights = data["data"]["flights"]
                
        # 2. Si es una lista directa
        elif isinstance(data, list):
            flights = data
            
        if not flights:
            print("❌ No se pudieron extraer vuelos del JSON limpio.")
            return

        print(f"✅ Se encontraron {len(flights)} opciones de vuelo.")
        
        # 3. Extraer precios y aerolíneas
        options = []
        for f in flights:
            try:
                # Adaptar según estructura real observada
                price = f.get("price", {}).get("totalAmount")
                if not price: continue
                
                # Intentar sacar nombre aerolínea
                airline = "Desconocida"
                if "outboundRoutes" in f and len(f["outboundRoutes"]) > 0:
                    segments = f["outboundRoutes"][0].get("segments", [])
                    if segments:
                        airline = segments[0].get("marketingAirline", {}).get("name", "??")
                
                options.append({
                    "price": price,
                    "airline": airline,
                    "currency": f.get("price", {}).get("currency", "ARS")
                })
            except:
                continue
                
        # 4. Ordenar y Reportar
        options.sort(key=lambda x: x["price"])
        
        print("\n🏆 TOP 5 MEJORES OPCIONES (NO FLYBONDI SI ES POSIBLE):")
        for i, opt in enumerate(options[:5]):
            print(f"   {i+1}. {opt['airline']}: ${opt['price']:,.0f} {opt['currency']}")
            
        # Comparativa con Flybondi ($712,506)
        fb_price = 712506
        best_comp = options[0]["price"]
        
        diff = best_comp - fb_price
        pct = (diff / fb_price) * 100
        
        print(f"\n📊 ANÁLISIS FINAL:")
        print(f"   Flybondi Hoy: ${fb_price:,.0f}")
        print(f"   Mejor Competencia: ${best_comp:,.0f} ({options[0]['airline']})")
        print(f"   Diferencia: ${diff:,.0f} (+{pct:.1f}%)")
        
        if pct < 15:
            print("\n⚠️ DECISIÓN: ESPERAR. La diferencia es poca (<15%). Con valija, Flybondi podría ser más caro.")
        else:
            print("\n✅ DECISIÓN: OPORTUNIDAD. Flybondi está significativamente más barato.")

    except Exception as e:
        print(f"💥 Error crítico en análisis: {e}")

if __name__ == "__main__":
    analyze_competitor_prices()
