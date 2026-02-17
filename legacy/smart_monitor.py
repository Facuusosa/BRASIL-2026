
import subprocess
import time
import requests
import sys
import os
import random
from datetime import datetime

# --- CONFIGURACIÓN ---
BOT_SCRIPT = "monitor_flybondi.py"
TELEGRAM_TOKEN = "7736636760:AAHX2p3yRjC2lBhQAxOQ_g2U8T3J91s1wBg"
CHAT_ID = "1136402434"
CHECK_INTERVAL_MIN = 45   # Intervalo normal (minutos)
CHECK_INTERVAL_MAX = 70
CRITICAL_HOURS = [2, 3, 4, 5, 6] # Hora de la madrugada (Lobo Nocturno)

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

def run_bot():
    print(f"🦅 Ejecutando {BOT_SCRIPT}...")
    try:
        # Ejecutamos el script visual y esperamos a que termine
        result = subprocess.run([sys.executable, BOT_SCRIPT], capture_output=True, text=True)
        
        # Analizamos la salida
        output = result.stdout + result.stderr
        print(output) # Mostrar en consola local también
        
        if "Ups" in output or "Error en el navegador" in output:
            send_telegram("⚠️ ALERTA: WAF detectado (Ups!). El bot entrará en reposo extendido.")
            return False
            
        if "OPORTUNIDAD" in output:
            # El script interno ya manda telegram, pero reforzamos
            return True
            
        return True
    except Exception as e:
        print(f"❌ Error ejecutando sub-bot: {e}")
        send_telegram(f"❌ Error crítico en Vigía: {e}")
        return False

def main():
    print("🛡️ SMART MONITOR FASE 3 (WOLF PACK) INICIADO")
    send_telegram("🐺 El Lobo está de guardia. Modo Nocturno Activado.")
    
    last_heartbeat = 0
    
    while True:
        now = datetime.now()
        current_hour = now.hour
        
        # 1. HEARTBEAT (Cada 4 horas aprox)
        if time.time() - last_heartbeat > 14400: 
            send_telegram(f"💓 Sigo vivo. Hora: {now.strftime('%H:%M')}. Esperando presa.")
            last_heartbeat = time.time()

        # 2. DETERMINAR INTERVALO (Dinámico)
        # Si es hora crítica (madrugada martes), somos más agresivos
        if current_hour in CRITICAL_HOURS:
            wait_time = random.randint(20 * 60, 35 * 60) # 20-35 mins
            prefix = "🌙 [MADRUGADA]"
        else:
            wait_time = random.randint(CHECK_INTERVAL_MIN * 60, CHECK_INTERVAL_MAX * 60)
            prefix = "☀️ [DÍA]"
            
        print(f"\n{prefix} Ejecutando escaneo: {now.strftime('%H:%M')}")
        
        # 3. EJECUTAR ROBOT
        success = run_bot()
        
        # 4. PENALIZACIÓN POR FALLO
        if not success:
            print("⛔ Fallo detectado. Aplicando enfriamiento extra (2 horas).")
            # Si falló (Ups!), esperamos 2 horas para que cambie la IP o se calme el WAF
            extra_wait = 7200 
            time.sleep(extra_wait)
        
        # 5. DORMIR HASTA EL PRÓXIMO TURNO
        next_run = datetime.now() + timedelta(seconds=wait_time)
        print(f"💤 Durmiendo {wait_time/60:.1f} min. Próximo: {next_run.strftime('%H:%M')}")
        time.sleep(wait_time)

if __name__ == "__main__":
    # Necesitamos importar timedelta
    from datetime import timedelta
    main()
