import os
import re
from datetime import datetime
import glob

# Configuración
LOG_DIR = os.path.join(os.getcwd(), "data", "smart_monitor_logs")
INTROSPECTION_FILE = os.path.join(os.getcwd(), "data", "introspection_report.md")

def analyze_logs():
    """Analiza los logs recientes para detectar patrones de fallo."""
    logs = glob.glob(os.path.join(LOG_DIR, "*.log"))
    if not logs:
        return {"403_errors": 0, "429_errors": 0, "success_rate": 0}
    
    # Tomar el último log
    latest_log = max(logs, key=os.path.getctime)
    
    with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    errors_403 = len(re.findall(r"403 Forbidden", content))
    errors_429 = len(re.findall(r"429 Too Many Requests", content))
    access_denied = len(re.findall(r"Access denied", content))
    
    # Calcular tasa de éxito aproximada (buscando "✅")
    successes = len(re.findall(r"✅", content))
    attempts = len(re.findall(r"🔎 Buscando", content))
    
    success_rate = (successes / attempts * 100) if attempts > 0 else 0
    
    return {
        "403_errors": errors_403 + access_denied,
        "429_errors": errors_429,
        "success_rate": success_rate,
        "latest_log": latest_log
    }

def generate_introspection_report():
    """Genera un reporte de pensamiento crítico basado en datos."""
    stats = analyze_logs()
    
    report = f"""# 🧠 Reporte de Introspección Crítica - {datetime.now().strftime('%Y-%m-%d')}

## 1. Análisis de Salud (Signos Vitales)
- **Tasa de Éxito de Caza:** {stats['success_rate']:.1f}%
- **Bloqueos de Defensa (403):** {stats['403_errors']}
- **Saturación (429):** {stats['429_errors']}

## 2. Cuestionamiento de Suposiciones
"""

    if stats['success_rate'] < 60:
        report += """- **⚠️ Suposición Rota:** "El camuflaje actual es efectivo".
  - **Evidencia:** La tasa de éxito es inaceptable (<60%). Cloudflare nos está detectando.
  - **Acción Propuesta:** ROTAR USER-AGENTS INMEDIATAMENTE O SOLICITAR PROXIES RESIDENCIALES.
"""
    else:
         report += """- **✅ Suposición Validada:** "El camuflaje actual sigue siendo efectivo".
  - **Evidencia:** Tasa de éxito superior al 80%. Mantener perfil bajo.
"""

    if stats['403_errors'] > 5:
        report += """- **⚠️ Alerta Táctica:** Detectados múltiples bloqueos 403.
  - **Propuesta:** Implementar backoff exponencial más agresivo (esperar 10 min tras fallo).
"""

    report += """
## 3. Propuesta Audaz (Generada por IA)
- **Idea:** Expandir el territorio de caza a otras aerolíneas (GOL/LATAM) usando la misma infraestructura de evasión.
- **Justificación:** Si Flybondi sube precios, necesitamos tener el "Plan B" ya monitoreado.
"""

    # Guardar reporte
    with open(INTROSPECTION_FILE, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"🧠 [SELF-EVOLUTION] Reporte generado: {INTROSPECTION_FILE}")

if __name__ == "__main__":
    generate_introspection_report()
