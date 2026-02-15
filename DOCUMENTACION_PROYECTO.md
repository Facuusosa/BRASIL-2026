# 🚀 Documentación de Producto: BRASIL 2026

**Basado en Framework de Validación de Producto**
> **Proyecto**: Monitor de Vuelos Inteligente (Flybondi)
> **Estado**: v0 Validado y en Producción

---

## 1. Hipótesis y Validación 🧪

Tabla de definición estratégica del producto basada en el modelo de validación rápida.

| Paso | Elemento | Desarrollo aplicado al Proyecto BRASIL 2026 |
| :--- | :--- | :--- |
| **1** | **Producto digital** | Bot autónomo ("Smart Monitor") que audita la API de Flybondi 24/7, salta protecciones de seguridad (Cloudflare) y alerta en Telegram sobre precios bajos y cambios ocultos en la web (Feature Flags). |
| **2** | **Hipótesis** | *Si monitoreamos la API interna ocultando la identidad del bot y analizamos los cambios de código fuente, entonces podemos detectar precios bajos y errores de tarifa antes que el público general, logrando comprar pasajes a Brasil por debajo del mercado (<$800k).* |
| **3** | **Métricas de éxito** | **Métrica 1:** Encontrar un vuelo Ida/Vuelta por debajo de $800.000 ARS. (Logrado: $668k).<br>**Métrica 2:** Tiempo de detección de ofertas < 1 min desde el deploy.<br>**Métrica 3:** Uptime del bot sin ser bloqueado (Anti-bot evasion). |
| **4** | **Ciclo corto de validación** | **Paso 1:** Script simple (`monitor_flybondi.py`) para consultar API GraphQL.<br>**Paso 2:** Prueba de bypass de Cloudflare con `curl_cffi`.<br>**Paso 3:** Ejecución continua (Daemon) y recepción de primera alerta en Telegram.<br>**Paso 4:** Comparación de precios detectados vs. web pública. |
| **5** | **Aprendizaje esperado** | Confirmar si existen "precios ocultos" o si la disponibilidad mostrada es real. (Aprendizaje: Detectamos "Scareware" en cupos y patrones de actualización los domingos antes de ofertas). |
| **6** | **Reflexión sobre el impacto** | El equipo priorizó la **funcionalidad (backend)** sobre la interfaz visual. Se construyó una herramienta que resuelve el problema de "incertidumbre de precios" con datos duros. |

---

## 2. Análisis del Proyecto y Roles 👥

**Objetivo del Proyecto**: Reducir el costo del viaje a Florianópolis mediante inteligencia de datos, centralizando la búsqueda en un sistema automático que no duerme.

### Roles Identificados y Responsabilidades (Simulación)

Como "Solo Entrepreneur" asistido por IA, en este proyecto cumplimos todos los roles:

#### **Product Manager (Tú)**
Se encargó de definir el presupuesto (Techo $1M, Objetivo $800k), las fechas (8-17 Marzo) y la estrategia de riesgo ("Esperar al martes"). Priorizó qué funcionalidades eran críticas (alerta Telegram) y cuáles no (interfaz web bonita).

#### **UX/UI Designer (Telegram Interface)**
Diseñó la experiencia de las alertas. Se aseguró de que el mensaje de Telegram fuera legible en 1 segundo: uso de semáforos (🟢/🟡/🔴), cálculo automático a Dólar MEP y enlace directo de "Comprar Ahora" para reducir fricción.

#### **Desarrollador Full Stack (IA + Tú)**
Implementó la lógica compleja: ingeniería inversa de la API de Flybondi, sistema de evasión de bloqueos (`curl_cffi`), base de datos SQLite y el orquestador Daemon (`smart_monitor.py`).

---

### Checklist de Entregables Mínimos (MVP)

| ROL | CARACTERISTICAS DEL ROL | LO QUE SE ENTREGÓ (DONE ✅) |
| :--- | :--- | :--- |
| **PRODUCT MANAGER** | Define el problema y valida que el producto tenga sentido. | • Problema: "Vuelos caros y precios volátiles".<br>• Hipótesis: "Automation beats manual search".<br>• Reglas de Negocio: Umbrales de alerta ($600k/$800k). |
| **UX/UI** | Diseña cómo se siente usar el producto (Alertas). | • Formato de Mensaje Telegram optimizado.<br>• Emojis indicadores de estado.<br>• Link deep-link prearmado al checkout. |
| **DESARROLLO** | Convierte ideas en código funcional y seguro. | • `smart_monitor.py` (Script funcional 24/7).<br>• Persistence: Logs JSON y SQLite.<br>• Deploy: Ejecución local en Windows modo servicio. |

---

## 3. Práctica: Diseño del v0 (MVP) �️

### Contexto
Utilizamos IA para generar el **v0** (Versión Cero) del monitor. El objetivo no fue una app perfecta, sino un script funcional para validar la hipótesis de precios.

### Estructura de Flujos del v0 (Validada)

El sistema se compone de flujos de procesos autónomos (Daemon), validados para no chocar entre sí.

**Input (Estructura de Flujos):**
```
3
prices Monitor de Precios (Consulta GraphQL periódica)
flags Detector de Feature Flags (Cambios en configuración web)
source Analizador de Código Fuente (Detección de Deploys)
```

**Validación:**
- **VALID**: Los flujos son únicos, tienen objetivos claros y cubren la necesidad del negocio.
    - `prices`: Ataca la métrica principal (precio).
    - `flags`: Ataca la oportunidad oculta (descuentos nuevos).
    - `source`: Ataca la anticipación (saber cuándo actualizan).

---

## 4. Stack Tecnológico & Datos 💾

Similar a la filosofía **Supabase** (Backend listo para usar), construimos nuestro propio mini-backend local.

- **Base de Datos**: SQLite + JSON Files (En lugar de Postgres/Supabase, para simplicidad local).
- **Auth & Seguridad**: Gestión de Cookies de Sesión (`SESSION_COOKIE`) y Tokens de Telegram en `.env`.
- **API (Backend)**: Scripts Python actuando como clientes de la API de Flybondi.

### Framework RICE (Priorización aplicada)
¿Por qué construimos esto así?
- **Reach (Alcance)**: 100% de los vuelos de Flybondi a FLN.
- **Impact (Impacto)**: Alto. Ahorro potencial de >$300.000 ARS.
- **Confidence (Confianza)**: Alta. La API es la fuente de verdad.
- **Effort (Esfuerzo)**: Bajo. Script en Python vs App Web compleja.

---

> **Conclusión**: El proyecto BRASIL 2026 sigue la metodología de Producto Digital, validando una hipótesis de alto valor mediante un MVP técnico (v0) ejecutado con roles definidos y métricas claras.
