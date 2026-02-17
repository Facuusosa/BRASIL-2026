import os

# Archivos a incluir en el contexto maestro
FILES_TO_INCLUDE = [
    "LEEME.md",
    "DOCUMENTACION_PROYECTO.md",
    "smart_monitor.py",
    "monitor_flybondi.py",
    "src/edge_case_tester.py",
    "src/feature_flag_monitor.py",
    "src/source_analyzer.py",
    "src/fare_glitch_detector.py"
]

OUTPUT_FILE = "CONTEXTO_IA_MASTER.md"

def create_master_context():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        # 1. Header
        outfile.write("# 🧠 BRASIL 2026 - CONTEXTO MAESTRO PARA IA\n\n")
        outfile.write("Este archivo contiene TODO el contexto técnico, de negocio y de código del proyecto 'BRASIL 2026'.\n")
        outfile.write("Úsalo para entender la arquitectura, la lógica de evasión y el estado actual del sistema.\n\n")
        outfile.write(f"Generado automáticamente el: {os.popen('date /t').read().strip()}\n\n")
        
        # 2. Iterar archivos
        for filename in FILES_TO_INCLUDE:
            if not os.path.exists(filename):
                print(f"⚠️ Archivo no encontrado: {filename}")
                continue
                
            print(f"📄 Procesando: {filename}...")
            
            outfile.write(f"\n{'='*80}\n")
            outfile.write(f"## ARCHIVO: {filename}\n")
            outfile.write(f"{'='*80}\n\n")
            
            ext = filename.split('.')[-1]
            lang = "python" if ext == "py" else "markdown"
            
            outfile.write(f"```{lang}\n")
            
            try:
                with open(filename, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
            except Exception as e:
                outfile.write(f"Error leyendo archivo: {e}")
                
            outfile.write("\n```\n\n")
            
    print(f"\n✅ Archivo maestro generado: {OUTPUT_FILE}")

if __name__ == "__main__":
    create_master_context()
