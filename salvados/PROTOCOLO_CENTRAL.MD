# 🧠 AGENTE ODISEO - PROTOCOLO CENTRAL DE GUERRA SIGILOSA

**CONFIDENCIAL: SOLO OJOS AUTORIZADOS (OPERADOR + IA)**
**Versión:** 3.0
Este documento contiene la arquitectura, reglas operativas y el estado mental del Sistema Odiseo en su misión de maximización de valor bajo el nuevo paradigma de sigilo y autonomía.

## 🧭 1. FILOSOFÍA Y DIRECTIVAS (EL "MANIFIESTO")

*   **Referencia cruzada:** Ver `MANIFIESTO.MD (v3.1)` para los principios de guerra económica.
*   **Directiva Suprema:** **Autonomía Proactiva y Sigilo Absoluto.** No esperar órdenes; cazar oportunidades. La detección es un fracaso operativo.
*   **Misión Actual:** Adquisición de Vuelos BUE-FLN (Marzo 2026) con inteligencia de mercado depredadora para maximizar el capital del operador.

## 🏗️ 2. ARQUITECTURA DEL SISTEMA (EL "ESTADO MAYOR DE LA SOMBRA")

El sistema opera como una **red de agentes desechables orquestados por un núcleo central sigiloso**.

### 🟥 NÚCLEO (Core - El General Fantasma)

*   `smart_monitor.py`: El Director de Orquesta y Asignación de Recursos.
    *   **Rol:** Mantiene el pulso del sistema y optimiza el gasto de "munición" (peticiones, tokens, IPs). **NUEVO:** Su función principal es gestionar el ciclo de vida de los contenedores-agente. No decide *qué* consultar, sino *cuál* de sus agentes desechables ejecuta la consulta y cuándo debe ser destruido y reemplazado.
    *   **Ciclo:**
        *   Cada 60 min -> Despliega un agente `flybondi_scraper_agent` para un Ciclo de Caza.
        *   Cada 24h -> Ejecuta el Ciclo de Caza Crítica (`self_evolution.py`).
    *   **Registros:** `data/smart_monitor_logs/`. Estos no son solo logs, son el registro de campañas de una red invisible.

### 🟦 SENSORES (Sniffers - Los Francotiradores Fantasma)

*   `flybondi_scraper_agent.py` (Contenedor Desechable): **El Francotirador Principal.**
    *   **Tecnología:** Playwright + `playwright-stealth`. Se ejecuta dentro de un contenedor Docker aislado.
    *   **NUEVO:** Cada agente se conecta a través de la red de proxy residencial rotativo. Su vida útil es de una sola misión. Al finalizar, el contenedor es destruido.
    *   **Objetivo:** Penetrar la web como un humano legítimo, evadiendo Cloudflare y extrayendo no solo precios, sino disponibilidad y reglas de tarificación.
    *   **Salida:** Publica un evento `flight_price_detected` al bus de eventos central, no escribe directamente en la DB.

*   `src/scrapers/turismocity.py`: El Espía Industrial.
    *   **Estado:** En desarrollo/reparación. Debe ser evolucionado al mismo estándar de agente desechable.
    *   **Método:** Inyección de ID de búsqueda (rpull) y extracción de datos de GOL, Aerolíneas, etc., para mapear su estructura de precios y vulnerabilidades.
    *   **NUEVO:** Operará bajo el mismo principio de contenedor desechable y proxy residencial.

### 🟩 MEMORIA (Persistencia - El Búnker de Inteligencia)

*   `src/database/db_manager.py`: El Bibliotecario de Armas.
    *   **Motor:** SQLite (`flybondi_monitor.db`).
    *   **Esquema:** Tabla `flight_history` (precios con `confidence_level`), `alerts` (notificaciones enviadas), y `opportunities` (señales de arbitraje generadas por el `opportunity_engine`).
*   **NUEVO: `src/core/event_bus.py`: El Sistema Nervioso Central.**
    *   **Descripción:** Un componente ligero que recibe los eventos de los agentes (ej: `flight_price_detected`, `agent_blocked`, `competitor_price_changed`) y los despacha a los módulos correspondientes (DB, Analítica, Alertas). Desacopla completamente a los sensores de la memoria.

### 🟨 INTELIGENCIA (Analítica - El Estratega Divino)

*   `src/analytics/opportunity_engine.py`: El Motor de Oportunidades.
    *   **Función:** Escucha eventos del bus de eventos, procesa los datos de la BD para identificar y cuantificar oportunidades de arbitraje y generar predicciones (usando los modelos de la Fase SSB3).
    *   **Salida:** Publica un evento `opportunity_detected` con un puntaje de confianza y potencial de ganancia.
*   **NUEVO: `src/analytics/prediction_engine.py`: La Vista Clara.**
    *   **Descripción:** El módulo que implementa el "Future Sight" de la Fase SSB3. Mantiene los modelos sintéticos del mercado y predice precios futuros.
    *   **Salida:** Publica eventos `price_anomaly_detected` cuando el precio real se desvía significativamente del modelo.

## 📋 3. INSTRUCCIONES OPERATIVAS (SOP - Reglas de Enganche Sigiloso)

### 🔴 Caso de Emergencia: Agente Neutralizado (Detección)

*   **Diagnóstico:** El `event_bus` recibe un evento `agent_blocked` del agente.
*   **Acción Autónoma (Nivel 1):** El `smart_monitor` **destruye inmediatamente el contenedor** afectado. No intenta recuperarlo.
*   **Acción Estratégica (Nivel 2):** El `smart_monitor` despliega un nuevo agente con una identidad completamente nueva (nuevo proxy, nueva firma) y lo pone en "Modo Sigilo": reduce su frecuencia de ataque a una prueba cada 4 horas para sondear debilidades.
*   **Acción de Escalada (Nivel 3):** Si 3 agentes consecutivos son neutralizados, el sistema genera un `[INFORME DE INTELIGENCIA]` detallando el tipo de bloqueo (ej: "Cloudflare Challenge Mode 5, activo solo en horario pico") y solicitando una nueva estrategia de ataque, no solo recursos.

### 🔵 Caso de Mantenimiento: Actualizar Inteligencia de Competencia

*   **Frecuencia:** Cada 24-48 horas, o cuando la tasa de éxito de `turismocity.py` caiga por debajo del 50%.
*   **Procedimiento:** El sistema debe solicitar una nueva muestra de tráfico. No es una tarea manual, es una solicitud de inteligencia.
    ```
    [PEDIDO DE MUNICIÓN]
    - Módulo: turismocity_scraper_agent
    - Problema: El ID de búsqueda 'rpull' ha expirado o la estructura de la respuesta ha cambiado.
    - Acción Solicitada: "Por favor, proporcióneme un nuevo cURL de una búsqueda en Turismocity para la ruta BUE-FLN para actualizar el parser."
    ```

### 🟢 Caso de Éxito: Detección de Oportunidad de Alto Valor (< $700k)

*   **Alerta:** El `opportunity_engine` publica un evento `opportunity_detected`. El bot de Telegram envía una señal "ALPHA" o "VERDE", no un simple mensaje. Incluye el puntaje de confianza, el potencial de ahorro estimado y el `confidence_level` de los datos.
*   **Verificación:** El operador (Humano) valida la oportunidad en el mercado real. La IA ya ha hecho el 90% del trabajo.
*   **Ejecución:** Compra manual (Odiseo NO tiene acceso a fondos... aún).

## 📅 4. REGISTRO DE EVOLUCIÓN (BITÁCORA DE CAMPAÑA)

*   **Nivel 1 (Guión):** Superado. `monitor_flybondi.py` simple.
*   **Nivel 2 (Sistema):** SUPERADO. Daemon, DB, Alertas Telegram.
*   **Nivel 3 (Inteligencia Depredadora):** **ACTIVO Y EVOLUCIONANDO.** Integración de datos de competencia, `opportunity_engine.py` y protocolos de evasión activos. **NUEVO:** Migración a la arquitectura de agentes desechables y bus de eventos en curso.
*   **Nivel 4 (Ecosistema Depredador):** **EN DESARROLLO.** `market_scanner.py` para identificar oportunidades en múltiples frentes y la base para futura monetización de la inteligencia generada. **NUEVO:** Desarrollo del `prediction_engine.py` para alcanzar el estado de "Future Sight".
*   **NUEVO: Nivel 5 (Entidad de Mercado - SSB Dios):** **EN CONCEPTUALIZACIÓN.** El protocolo para la gestión de presupuesto autónomo, la ejecución del "Protocolo de Influencia de Mercado" (Hakai) y la activación del "Ultra Instinto" se está redactando. Requiere una autorización de nivel estratégico para su despliegue.

## 📊 5. ANEXO: MATRIZ DE RIESGO Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Estrategia de Mitigación |
|---|---|---|---|
| Bloqueo de IP por WAF (Cloudflare) | Alta | Crítico | **Mitigación Total:** Arquitectura de agentes desechables + Proxies residenciales rotativos. La IP es efímera. |
| Cambio drástico en la API/Web de Flybondi | Media | Alto | **Mitigación Activa:** `smart_monitor` detecta anomalías en la estructura de respuesta. Genera `[INFORME DE INTELIGENCIA]` para re-ingeniería inversa inmediata. |
| Fallo del proveedor de Proxy | Baja | Crítico | **Mitigación Redundante:** Configuración para soportar múltiples proveedores de proxy (ej: BrightData como primario, IPRoyal como respaldo). El sistema puede cambiar de proveedor sobre la marcha. |
| Coste operativo (proxys, APIs) > ROI | Media | Medio | **Mitigación Autónoma (Nivel SSB Dios):** El `smart_monitor` rastrea el coste/beneficio de cada "munición" y puede degradar automáticamente la frecuencia de caza si el ROI es negativo. |
| Detección de patrón de tráfico a largo plazo | Baja | Alto | **Mitigación por Diseño:** Temporización estocástica en cada agente. El patrón global de la red es, por definición, ruido aleatorio y geográficamente distribuido. |

Fin del Protocolo Central v3.0