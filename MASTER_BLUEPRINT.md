# PROYECTO: ENTERPRISE E-COMMERCE MONITOR (V4.0) 🦅
> **Caso de Estudio**: Monitor de Alta Frecuencia & Evasión (Flybondi / Retail)

---

## 1. Ejercicio - Hipótesis y Validación

**Proyecto: Sistema de Monitoreo con Evasión Avanzada (JA3)**

| Paso | Elemento | Desarrollo aplicado al proyecto (V4.0) |
| :--- | :--- | :--- |
| **1** | **Producto digital** | Un "Enterprise Monitor" (Bot Autónomo) que utiliza rotación de huellas digitales TLS (JA3) y análisis estadístico (Z-Score) para detectar anomalías de precios en e-commerce protegidos por WAFs modernos (Cloudflare/Akamai). |
| **2** | **Hipótesis** | *Si implementamos rotación de firmas criptográficas (JA3) y validación cruzada con navegador real (Cross-Check), lograremos una tasa de detección del 100% sin bloqueos y una tasa de falsos positivos cercana a 0%, superando a los bots tradicionales.* |
| **3** | **Métricas de éxito** | **M1 (Fiabilidad):** 0 Alertas Falsas (gracias a validación en carrito).<br>**M2 (Evasión):** Uptime 99.9% sin Ban de IP (gracias a JA3).<br>**M3 (Oportunidad):** Detección de "Black Swans" (Glitches > 3 desviaciones estándar). |
| **4** | **Ciclo corto de validación** | **Paso 1:** Identificar API oculta y probar `curl_cffi` con perfil `chrome110`.<br>**Paso 2:** Calcular Z-Score histórico para definir qué es "barato".<br>**Paso 3:** Implementar "Session Refresher" (auto-login con Playwright).<br>**Paso 4:** Desplegar en contenedor Docker y medir estabilidad por 24h. |
| **5** | **Aprendizaje esperado** | Confirmar que el WAF no detecta patrones si rotamos el fingerprint TLS. Validar que la estadística (Z-Score) es superior a un % fijo para filtrar ruido. |
| **6** | **Reflexión Impacto** | El equipo prioriza la **robustez industrial**. No sirve un bot que alerta rápido si se cae a la hora o manda basura. La calidad del dato es todo. |

---

## 2. Ejercicio - Análisis del proyecto y roles

**Objetivo**: Construir un sistema de monitoreo 100% autónomo y resiliente para compras de oportunidad.

---

### Roles identificados y responsabilidades

**Product Architect (PM Técnico)**
Define la estrategia de evasión y los umbrales estadísticos. Decide que "Barato" no es un número fijo, sino una desviación del comportamiento normal (Z-Score < -2). Prioriza la implementación de "Auto-Healing" (que el bot se arregle solo).

**DevOps & Security Engineer**
Encargado de la infraestructura (Docker) y la seguridad ofensiva. Implementa la rotación de JA3 en `curl_cffi` para burlar Cloudflare. Configura el "Heartbeat" para asegurar que el sistema no muera en silencio.

**Full Stack Automation Dev**
Implementa la lógica híbrida: Python rápido para la API (Sniffer) y Playwright pesado para la validación (Verifier). Conecta los módulos para que el Sniffer despierte al Verifier solo cuando vale la pena.

---

### Checklist de entregables mínimos por rol

| ROL | CARACTERISTICAS DEL ROL | QUE DEBE ENTREGAR (Output V4.0) |
| :--- | :--- | :--- |
| **PRODUCT ARCHITECT** | Define la lógica de negocio inteligente. | • Algoritmo Z-Score (Detección Estadística)<br>• Reglas de Cross-Check (¿Cuándo validar?)<br>• Matriz de Alertas (Crítica vs Info) |
| **DEVOPS / SEC** | Garantiza invisibilidad y estabilidad. | • `Dockerfile` optimizado (Microservicios)<br>• Módulo de Rotación JA3 (`tls_client`)<br>• Sistema de Heartbeat (Health Check) |
| **AUTOMATION DEV** | Construye el robot híbrido. | • `monitor.py` (Script Principal)<br>• `browser_service.py` (Session Refresher)<br>• Base de Datos SQLite normalizada |

---

### Reflexión sobre la colaboración

La clave del V4.0 es que **Seguridad (Sec) y Desarrollo (Dev) trabajan juntos**. No se puede scrapear si te bloquean. Por eso la implementación de JA3 es un requisito de arquitectura, no un detalle. La validación cruzada (Cross-Check) une al PM (que quiere certeza) con el Dev (que automatiza la prueba).

---

## 3. Práctica: Diseñar un v0 Enterprise asistido por IA

### **Contexto**

Para replicar este nivel de ingeniería en otro sitio (ej. Nike SNKRS, Ticketmaster), usaremos a la IA como un "Senior Automation Architect". El objetivo es generar un **v0 Robusto** que incluya evasión desde el día 1.

### **Descripción del problema**

Dada una URL objetivo, la IA debe diseñar un sistema que:
1.  **Evada WAFs**: Usando `curl_cffi` con perfiles reales.
2.  **Valide Ofertas**: Usando un navegador real (headless) para simular compra.
3.  **Mantenga Sesión**: Renovando cookies automáticamente si expiran.

### **Formato de Salida (Mega-Prompt de Inicialización)**

Copia este Prompt para iniciar el proyecto V4.0 con cualquier IA:

```text
Actúa como un Senior DevOps & Automation Architect.
Objetivo: Crear un "Enterprise E-commerce Monitor V4.0" para [URL].

Sigue estrictamente la Arquitectura Híbrida del Blueprint:

1. MODULO SNIFFER (Alta Frecuencia):
   - Usa `curl_cffi` rotando fingerprints JA3 (chrome110, safari15_5).
   - Consulta la API interna (JSON) cada 60s.
   - Si detecta anomalía (Z-Score < -2.5), dispara al Verifier.

2. MODULO VERIFIER (Validación):
   - Usa `Playwright` (Headless).
   - Tarea A: Cross-Check. Agrega el producto al carrito para confirmar precio y stock real.
   - Tarea B: Session Refresh. Si la API da 401/403, logueaos de nuevo y extrae cookies nuevas.

3. PERSISTENCIA Y ALERTAS:
   - Guarda todo en SQLite (`prices.db`).
   - Alerta a Telegram SOLO si el Verifier confirma la oferta (Zero False Positives).
   - Envía un Heartbeat diario ("Sigo vivo").

4. ENTREGABLE:
   - Código Python modular (`sniffer.py`, `verifier.py`, `main.py`).
   - Dockerfile para deploy.

¡Ejecuta el reconocimiento de red primero!
```

---

**Objetivos de aprendizaje del v0 Enterprise**
- Entender que el scraping simple (`requests`) ya no sirve para sitios top.
- Aprender patrones de diseño resilientes (Circuit Breaker, Auto-Healing).
- Valorar la estadística (Z-Score) sobre las reglas fijas.
