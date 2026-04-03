# 🔱 BRÚJULA DE PRECIOS – SCRAPING MASTER PLAN 2026

## 🛡️ CAPA 1: INVISIBILIDAD Y EVASIÓN (Hardened Layer)

### TLS Fingerprinting (JA4+)
- **Estrategia**: No usar `requests` estándar. Implementar **`curl_cffi`** en Python o **`nodriver`** / **`camoufox`** en Node/Python.
- **Configuración**: El "apretón de manos" TLS debe coincidir exactamente con el `User-Agent`. 
- **Herramienta Recomendada**: `requests.get("URL", impersonate="chrome120")`.

### Infraestructura de Red
- **Proxies**: Priorizar **Proxies Residenciales o Móviles (IPv6)**. Evitar Datacenters (AWS/GCP) que están bloqueados de entrada.
- **Sesiones**: Implementar **Sticky Sessions** (Mantener la misma IP durante 5-10 minutos) para no disparar alertas de anomalías.

---

### 🧬 CAPA 2: EXTRACCIÓN QUIRÚRGICA (Low-Level Extraction)

### Mobile API Sniffing
- **Punto de Oro**: No scrapear HTML. Buscar las **APIs de la App Móvil** (`api.mayorista.com`).
- **SSL Pinning**: Usar **Frida** para saltar la validación de certificados en emuladores Android.
  - *Script Base*: Sobrescribir `TrustManagerImpl.checkTrustedRecursive`.
- **Inyección de Sucursales (Store ID)**: Inyectar el `StoreId` o `SucursalId` directamente en los Headers/Payloads para saltar de Carrefour Normal a **MaxiCarrefour** sin navegar por el selector web.

---

### 🧠 CAPA 3: UNIFICACIÓN INTELIGENTE (IA-Native Parsing)

### Formato TOON (Token-Oriented Object Notation)
- **Estrategia**: Convertir los JSONs anidados a un formato similar a CSV antes de mandarlos a la IA.
- **Ahorro**: Reduce entre un **40% y 50%** el costo de tokens en DeepSeek/Gemini.
- **Aplanamiento**: Ejecutar *Hierarchical Flattening* (eliminar capas redundantes) para reducir el contexto un **69%**.

### Modelos de Procesamiento
- **Costos Locales/Bajos**: Usar **DeepSeek V3** o **Gemini Flash** para procesos masivos (hasta 18 veces más barato que GPT-4o).
- **Traductor Universal**: Definir un *Prompt Seed* único con *Few-Shot Learning* para que la IA unifique cualquier formato al esquema de la Brújula de Precios.

---

### 🚨 CAPA 4: GESTIÓN DE INCIDENTES

- **Error 403**: Cambiar perfil de `impersonate` y rotar Proxy Residencial.
- **Error 429**: Aplicar *Exponential Backoff con Jitter* (retrasos aleatorios crecientes).
- **Error 1020 (Cloudflare)**: Simular comportamientos humanos (timings aleatorios, trayectorias de mouse) e incrementar la consistencia de sesión.
