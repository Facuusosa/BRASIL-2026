# 🦅 MASTER BLUEPRINT: GENERADOR DE MONITORES DE PRECIOS (V2.0)

> **Propósito**: Guía unificada de Producto + Tecnología para replicar bots de monitoreo exitosos.
> **Basado en**: Metodología "Creación de Producto desde Cero" (Notion) + Caso de Éxito Flybondi.

---

## 1. FASE DE PRODUCTO (Thinking like a PM) 🧠

Antes de escribir una línea de código, define esto para el nuevo proyecto:

### 1.1. Tabla de Hipótesis y Validación (Template)

| Paso | Elemento | Definición para el Nuevo Proyecto |
| :--- | :--- | :--- |
| **1** | **Producto digital** | *Bot monitor de [SITIO/PRODUCTO] 24/7.* |
| **2** | **Hipótesis** | *Si monitoreamos [VARIABLE CLAVE: Precio/Stock] en tiempo real, detectaremos [OPORTUNIDAD] antes que el usuario común.* |
| **3** | **Métricas de éxito** | 1. Precio objetivo logrado: [MONTO].<br>2. Tiempo de detección: < [MINUTOS].<br>3. Falsos positivos: 0. |
| **4** | **Ciclo corto (MVP)** | Paso 1: Script manual.<br>Paso 2: Bypass de seguridad.<br>Paso 3: Bot en modo Demonio (v0). |
| **5** | **Aprendizaje** | *¿El sitio muestra datos reales o cacheados? ¿Hay patrones de actualización?* |

### 1.2. Roles y Entregables (Checklist)

Para este proyecto, la IA (o vos) asumirá 3 roles. Verifica que cumplas cada uno:

*   **🕵️‍♂️ Product Manager**: Definir URL objetivo, Presupuesto Máximo y Reglas de Alerta (¿Cuándo comprar?).
*   **🎨 UX Designer**: Diseñar el mensaje de Telegram. Que sea limpio, con emojis y enlaces directos al carrito.
*   **💻 Developer**: Implementar la **Arquitectura Técnica** (ver sección 2).

---

## 2. FASE TÉCNICA (Execution like a Dev) 🛠️

Una vez definido el producto, esta es la "Receta Secreta" técnica que la IA debe seguir.

### 2.1. Arquitectura de Datos y Módulos
La IA debe replicar esta estructura modular probada:

1.  **Core Monitor (Orquestador)**: Loop infinito inteligente (`while True`). No usar Cronjobs simples, usar delays aleatorios.
2.  **API Sniffer (El Sabueso)**:
    *   *Objetivo*: Encontrar `api/graphql`, `v1/products` o JSONs ocultos en `<script id="__NEXT_DATA__">`.
    *   *Regla*: **Nunca** scrapear HTML si existe un JSON.
3.  **Source Analyzer (El Espía - Opcional)**:
    *   Descargar JS principales, hacer hash MD5 y comparar para detectar "Deploys" o "Feature Flags" activados.
4.  **Glitch/Anomaly Detector**:
    *   Comparar Precio Actual vs. Promedio Histórico (SQLite).
    *   Si baja > 30% de golpe -> **ALERTA CRÍTICA 🚨**.

### 2.2. Stack Tecnológico (Estándar de Oro)
*   **Lenguaje**: Python 3.10+.
*   **Request Engine**: 
    *   Opción A (Preferida): `curl_cffi` (Imita Chrome/Safari real). Bypassea Cloudflare.
    *   Opción B (Fallback): `Playwright` + `stealth` (Solo si hay mucha interacción JS).
*   **Base de Datos**: SQLite (`price_history.db`).
*   **Notificaciones**: Telegram Bot API.

---

## 3. EL "MEGA PROMPT" DE INICIALIZACIÓN 🤖

Copia y pega esto para iniciar un nuevo proyecto con cualquier IA, garantizando que siga esta metodología:

```text
Actúa como un Senior Product Engineer experto en Automation y Scraping ético.

Vamos a iniciar el Proyecto: [NOMBRE DEL PROYECTO]
Objetivo: Monitorear [URL] para encontrar [OBJETIVO: Precio/Stock].

Sigue estrictamente el Framework "MASTER BLUEPRINT V2":

1. FASE DE PRODUCTO (PM):
   - Confirma que entiendes la Hipótesis: "Detectar oportunidades ocultas mediante monitoreo de alta frecuencia".
   - Define qué métrica vamos a traquear (Precio, Stock, Disponibilidad).

2. FASE TÉCNICA (DEV) - ARQUITECTURA:
   - Stack Obligatorio: Python + curl_cffi (para evadir WAF/Cloudflare) + SQLite.
   - Estrategia: "API First". Prioriza encontrar endpoints JSON ocultos antes que scrapear HTML.
   - Módulos a crear: 
     a) Orquestador (Daemon).
     b) Analizador de Precios.
     c) Notificador Telegram (con diseño UX limpio: Emojis, Links de compra).

3. PRIMER PASO (RECONOCIMIENTO):
   - No escribas código final todavía.
   - Tu primera tarea es analizar la URL [INSERTAR URL].
   - Dime: ¿Usa GraphQL? ¿Tiene protección Cloudflare? ¿Dónde están los datos interesantes?

¡Manos a la obra!
```
