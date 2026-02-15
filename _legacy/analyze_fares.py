import json

data = json.load(open(r'data/flybondi_logs/search_20260213_002312.json', 'r', encoding='utf-8'))

# Analizar clases y precios
class_prices = {}
for r in data['results']:
    for side in ['outbound', 'inbound']:
        if side in r:
            for fd in r[side].get('fare_details', []):
                cls = fd.get('class', '?')
                price = fd['afterTax']
                avail = fd['availability']
                if cls not in class_prices:
                    class_prices[cls] = []
                class_prices[cls].append({'price': price, 'avail': avail})

print('=== ANALISIS POR CLASE DE TARIFA ===')
for cls in sorted(class_prices.keys()):
    prices = [p['price'] for p in class_prices[cls]]
    avails = [p['avail'] for p in class_prices[cls]]
    print(f'  Clase {cls}: ${min(prices):,.0f} - ${max(prices):,.0f} (avg ${sum(prices)/len(prices):,.0f}) | Asientos: {min(avails)}-{max(avails)} | {len(prices)} vuelos')

print()
print('=== VUELOS MAS BARATOS (afterTax por persona) ===')
all_flights = []
for r in data['results']:
    for side in ['outbound', 'inbound']:
        if side in r:
            f = r[side]
            for fd in f.get('fare_details', []):
                all_flights.append({
                    'side': 'IDA' if side == 'outbound' else 'VUELTA',
                    'flight': f"FO{f['flight_no']}",
                    'route': f"{f['origin']}->{f['destination']}",
                    'time': f"{f['departure_time']}-{f['arrival_time']}",
                    'class': fd['class'],
                    'price_pp': fd['afterTax'],
                    'price_before_tax': fd['beforeTax'],
                    'avail': fd['availability'],
                    'date': r.get('departure_date', '') if side == 'outbound' else r.get('return_date', '')
                })

# Deduplicar y mostrar top 15
seen = set()
count = 0
for f in sorted(all_flights, key=lambda x: x['price_pp']):
    key = f"{f['flight']}_{f['date']}_{f['class']}"
    if key not in seen:
        seen.add(key)
        tax = f['price_pp'] - f['price_before_tax']
        tax_pct = (tax / f['price_pp']) * 100
        print(f"  {f['side']:6s} {f['date']} {f['flight']:>7s} {f['route']:>10s} {f['time']:>12s} Clase:{f['class']} ${f['price_pp']:>10,.0f}/pp (base ${f['price_before_tax']:>8,.0f} + tax ${tax:>8,.0f} = {tax_pct:.0f}%) Asientos:{f['avail']}")
        count += 1
    if count >= 20:
        break

print()
print('=== PROPORCION IMPUESTOS vs TARIFA BASE ===')
# Ver cuánto son impuestos
for f in sorted(all_flights, key=lambda x: x['price_pp'])[:5]:
    tax = f['price_pp'] - f['price_before_tax']
    print(f"  {f['flight']} {f['date']}: Base ${f['price_before_tax']:,.0f} + Impuestos ${tax:,.0f} = ${f['price_pp']:,.0f}")
    print(f"    -> Impuestos son el {(tax/f['price_pp'])*100:.0f}% del precio total")

print()
print('=== ANALISIS DE BEFORETAX UNICO (tarifa pura de la aerolinea) ===')
base_prices = set()
for f in all_flights:
    base_prices.add(f['price_before_tax'])
print(f'  Tarifas base unicas encontradas: {len(base_prices)}')
for bp in sorted(base_prices):
    matching = [f for f in all_flights if f['price_before_tax'] == bp]
    print(f"  Base ${bp:>10,.0f} -> con tax ${matching[0]['price_pp']:>10,.0f} | {len(matching)} vuelos | Clases: {set(f['class'] for f in matching)}")
