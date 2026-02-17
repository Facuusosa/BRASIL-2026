
import requests
import time
import sys

urls = [
    "https://flybondi.com/static/js/bundle.18bfad73.js",
    "https://flybondi.com/static/js/flight-search.574dc118.chunk.js", 
    "https://flybondi.com/static/js/Club~Passes~club-confirmation~club-subscription~dates~extras~extras-summary~flight-search~flight-sta~76ae0596.cd69c325.chunk.js"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36'
}

def download_file(url, retries=5):
    filename = url.split("/")[-1]
    print(f"⬇️ Intentando descargar: {filename[:20]}...")
    
    for i in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(f"✅ ÉXITO: {filename}")
                return True
            else:
                print(f"⚠️ Error HTTP {r.status_code}. Reintentando ({i+1}/{retries})...")
        except Exception as e:
            print(f"⚠️ Error de Conexión: {e}. Reintentando en 3s ({i+1}/{retries})...")
            time.sleep(3)
    
    print(f"❌ FALLÓ DEFINITIVAMENTE: {filename}")
    return False

print("📡 INICIANDO SECUENCIA DE DESCARGA RESILIENTE...")
print("    (Asegurate de tener internet activos)")
time.sleep(1)

success_count = 0
for url in urls:
    if download_file(url):
        success_count += 1

print(f"\n📊 Resultado: {success_count}/{len(urls)} archivos descargados.")
if success_count > 0:
    print("🚀 LISTO PARA ANÁLISIS.")
else:
    print("💀 SIN CONEXIÓN. REVISA TU INTERNET.")
