# -*- coding: utf-8 -*-
import sys
import json
from curl_cffi import requests

# Configurar salida UTF-8 para evitar errores en Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

URLS = ["https://flybondi.com/api/graphql", "https://api.flybondi.com/graphql"]

QUERY = """
query IntrospectSchema {
  __schema {
    mutationType {
      fields {
        name
        args {
          name
          type {
            name
            kind
            inputFields { name type { name } }
            ofType {
              name
              kind
              inputFields { name type { name } }
              ofType {
                name
                kind
                inputFields { name type { name } }
              }
            }
          }
        }
      }
    }
  }
}
"""

def get_real_type(t_obj):
    name = None
    fields = []
    curr = t_obj
    while curr:
        if curr.get('name'):
            name = curr['name']
        if curr.get('inputFields'):
            fields = curr['inputFields']
        curr = curr.get('ofType')
    return name, fields

print("🕵️  ESPIONAJE DE ESQUEMA FLYBONDI...")

for url in URLS:
    print(f"👉 Objetivo: {url}")
    try:
        r = requests.post(url, json={"query": QUERY}, headers={"Content-Type": "application/json"}, impersonate="chrome110", timeout=15)
        if r.status_code != 200:
            print(f"   ❌ HTTP {r.status_code}")
            continue
            
        data = r.json()
        if not data.get("data"):
            print("   ❌ Datos vacíos")
            continue
            
        fields = data["data"]["__schema"]["mutationType"]["fields"]
        print(f"   ✅ Esquema adquirido. Escaneando {len(fields)} mutaciones...")
        
        targets = ["addUBADiscount", "addBankDiscount", "addPromoCode", "changeAlternativeFlightFares", "addClubDiscount"]
        keywords = ["UBA", "Bank", "Discount"]
        
        matches = []
        for f in fields:
            fname = f["name"]
            if any(t.lower() == fname.lower() for t in targets) or \
               any(k.lower() in fname.lower() for k in keywords):
                matches.append(f)
        
        if matches:
            print(f"\n🔐 ENCONTRADAS {len(matches)} MUTACIONES CLAVE:")
            for m in matches:
                print(f"\n[MUTATION] {m['name']}")
                for arg in m['args']:
                    tname, tfields = get_real_type(arg['type'])
                    print(f"   ► Argumento: {arg['name']} (Tipo: {tname})")
                    if tfields:
                        print("     📝 Estructura del Input:")
                        for fld in tfields:
                             ftname, _ = get_real_type(fld['type'])
                             print(f"       • {fld['name']} ({ftname})")
            break
        else:
            print("   ⚠️  No se encontraron mutaciones interesantes en este endpoint.")

    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\nEscaneo completado.")
