# 🦅 PROYECTO MONITOR BRASIL 2026

**El Agente Odiseo:** Una inteligencia artificial autónoma diseñada para vigilar y capturar pasajes aéreos (BUE-FLN) al menor precio posible.

## 🚀 Misión y Objetivo
*   **Destino:** Florianópolis (Brasil).
*   **Fechas Objetivo:** Marzo 2026 (Del 8 al 19 aprox).
*   **Presupuesto Máximo:** $900.000 ARS (Ida y Vuelta).
*   **Meta Ideal:** < $700.000 ARS.

## 🔥 Capacidades del Sistema
1.  **Monitor Inteligente (Daemon):** Un proceso en segundo plano que vigila Flybondi 24/7.
2.  **Evasión Cloudflare:** Usa `curl_cffi` para simular navegadores reales y evitar bloqueos.
3.  **Base de Datos Propia:** Almacena historial de precios en `flybondi_monitor.db`.
4.  **Alerta Telegram "Fuego Único":** Solo te molesta si hay una oportunidad REAL (Semáforo Amarillo/Verde).
5.  **Inteligencia Competitiva:** (En desarrollo) Compara precios contra Turismocity/Despegar para validar ofertas.

## 🛠️ Instalación Rápida
Requisitos: Python 3.10+

1.  **Clonar y Entrar:**
    ```bash
    git clone ...
    cd BRASIL-2026
    ```
2.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configurar Variables de Entorno (.env):**
    ```ini
    TELEGRAM_BOT_TOKEN="tu_token"
    TELEGRAM_CHAT_ID="tu_id"
    FLYBONDI_API_KEY="" (Opcional si usa modo browserless)
    ```

## 🎮 Operación (Comandos)

**Modo Vigilante (Recomendado):**
```bash
python smart_monitor.py --daemon
```
*Este comando inicia el ciclo infinito de vigilancia.*

**Modo Manual (Sniffer):**
```bash
python monitor_flybondi.py
```
*Ejecuta una sola búsqueda y reporta.*

---
**Desarrollado por:** Facu Sosa + Agente IA Odiseo.
*Versión del Manifiesto: 2.1*
