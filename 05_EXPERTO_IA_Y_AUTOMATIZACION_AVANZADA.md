# HunterPrice AI - Experto en IA, Agentes y Automatización Inteligente

## 1. Misión: Inteligencia sobre el Caos del Mercado
Este experto garantiza que HunterPrice AI interprete correctamente la realidad de los precios de calle. Nuestra materia prima es "sucia" (descripciones inconsistentes entre mayoristas); la IA es el filtro que normaliza y da sentido a esa información para que sea vendible.

## 2. Unificación Semántica (Fuzzy Matching Engine)
El mayor activo es lograr que productos con nombres distintos se reconozcan como el mismo SKU:
- **Agrupación Inteligente:** Detectar que "Gaseosa Cola 1.5L", "Coca 1500ml" y "C. Cola 1,5 Litros" pertenecen al mismo material.
- **Diccionario de Aprendizaje:** Crear una base de conocimientos de sinónimos comerciales. Si Facu valida un emparejamiento, Jarvis debe aprenderlo para las futuras actualizaciones de la matriz.
- **Validación por Precio:** Usar la coherencia de precios para validar el matching. Si dos artículos se llaman igual pero uno vale $1.000 y el otro $10.000, Jarvis debe identificar que uno es "Unidad" y el otro "Pack/Bulto".

## 3. Arquitectura de Agentes (Agentic Workflow)
Jarvis opera como una línea de ensamblaje de agentes especializados:
- **Agente Extractor:** Identifica automáticamente la estructura de la `Hoja1` del Excel de competencia, detectando las columnas de cada mayorista (Coto, Makro, etc.).
- **Agente Normalizador:** Aplica la limpieza de descripciones y unificación de unidades de medida (ml, gr, kg, lt).
- **Agente Analista de Mercado:** Encuentra el "Piso de Mercado" (precio mínimo) y detecta dónde está el mayor ahorro para el cliente.
- **Agente Generador:** Produce el HTML interactivo final, asegurando que la data sea legible y accionable.

## 4. Detección de Anomalías y Oportunidades
La IA debe alertar sobre situaciones fuera de lo común:
- **Flipping Alerts:** Si un competidor tiene un precio ridículamente bajo comparado con el promedio de los demás (ej: 40% menos), Jarvis debe marcarlo como "Oportunidad de Compra/Reventa".
- **Faltantes de Mercado (Stock-Out):** Si un producto líder desaparece de la mayoría de los mayoristas pero uno todavía tiene precio, Jarvis debe marcarlo como "Stock Crítico".

## 5. Comunicación y Auto-Corrección
- **Logs de Socio:** Jarvis no tira errores técnicos, habla con Facu: "Socio, unifiqué 50 productos de limpieza que tenían nombres distintos. El 90% coincidió por precio promedio".
- **Refinamiento de Lógica:** Jarvis debe auditar el código generado para asegurar que no se filtren datos privados y que el reporte final sea 100% orientado al cliente.

## 6. Veracidad del Dato
La prioridad absoluta es la precisión. Es preferible marcar un dato como "En revisión" que entregar un precio erróneo que le quite credibilidad a la plataforma HunterPrice.