import os
import glob
import webbrowser
import sys
import time

# Asegurar que estamos en el directorio correcto (padre de src)
# Si el script está en src/, subimos un nivel.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Subir de src a raiz

LOGS_DIR = os.path.join(PROJECT_ROOT, "data", "flybondi_logs")

print("🔎 Buscando último reporte...")
print(f"📂 Carpeta: {LOGS_DIR}")

if not os.path.exists(LOGS_DIR):
    print("❌ Error: No encuentro la carpeta de logs.")
    print("   Asegúrate de haber ejecutado el monitor al menos una vez.")
    time.sleep(5)
    sys.exit(1)

# Buscar archivos HTML
patron = os.path.join(LOGS_DIR, "reporte_*.html")
archivos = glob.glob(patron)

if not archivos:
    print("❌ Error: No hay reportes HTML todavía.")
    time.sleep(5)
    sys.exit(1)

# Encontrar el más nuevo
mas_nuevo = max(archivos, key=os.path.getmtime)
nombre = os.path.basename(mas_nuevo)

print(f"✅ ¡Encontrado! Abriendo: {nombre}")
webbrowser.open(f"file://{mas_nuevo}")

# Dar tiempo a leer si algo falla, pero si abre el navegador se cerrará rapido
time.sleep(2)
