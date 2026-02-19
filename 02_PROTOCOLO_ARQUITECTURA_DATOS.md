# HunterPrice AI - Protocolo de Arquitectura y Procesamiento de Datos

## 1. Definición de Fuente de Datos (La Materia Prima)
Para que el sistema sea el más potente del mercado, Jarvis debe procesar la matriz integral de competencia:
- **Master Competencia (Matriz Horizontal):** Archivo `Precios competidores.xlsx - Hoja1.csv`. 
- **Estructura:** Contiene los productos en filas (Material, Descripción) y los competidores en columnas (Carrefour, Coto, Diarco, Makro, Maxiconsumo, Nini, Vital, Yaguar, etc.). 
- **Nota de Socio:** Vital aquí es tratado como un competidor más para comparar, no como un costo interno confidencial.

## 2. Pipeline de Limpieza Profunda (Data Sanitization)
Jarvis debe asegurar que el output sea profesional y "limpio" de rastros corporativos:
- **Eliminación de Basura de SAP:** Suprimir filas de encabezado innecesarias (ej. filas 1 a 4 del CSV que contienen filtros de SAP) y columnas que no sirven al cliente final (GCp, Usuario, Status, etc.).
- **Integridad de SKU (Material):** El campo `Material` debe ser **String**. Es prohibido transformarlo a número para no perder los ceros iniciales que permiten el cruce de datos.
- **Normalización de Texto (Fuzzy Matching):** - Convertir todas las descripciones a Mayúsculas.
    - Estandarizar unidades (ej: "1.5LT", "1500ML", "1,5 LITROS" -> "1.5L") para unificar la base de datos y evitar duplicados visuales.

## 3. Lógica de Inteligencia de Mercado (Business Logic)
El valor agregado que vendemos surge de procesar la fila de cada producto:
- **Detección del "Piso de Mercado":** Identificar el valor mínimo de la fila entre todos los competidores (ignorando ceros y celdas vacías). Este es el "Precio de Compra Óptimo" para el cliente.
- **Identificación del Proveedor Ganador:** Determinar el nombre del mayorista/competidor que ofrece ese precio mínimo.
- **Precio Promedio y Disparidad:** Calcular el promedio de mercado para mostrarle al cliente cuánto dinero está perdiendo si no compra en el lugar indicado por HunterPrice.

## 4. Gestión de Contingencias y Calidad
- **Detección de Outliers (Flipping):** Si un precio es un 40% menor al promedio del mercado, marcar como "ALERTA DE OPORTUNIDAD/ERROR" para que Facu decida si es una oportunidad de reventa (Flipping).
- **Consistencia:** Si un producto no tiene precios en al menos 2 competidores, marcar como "Baja Referencia".

## 5. Formatos de Salida (Productos Entregables)
El sistema debe exportar la inteligencia en formatos que el cliente perciba como Premium:
1. **JSON:** Para la base de datos del Dashboard.
2. **HTML Interactivo (Single File):** El archivo que se envía por WhatsApp. Debe incluir el buscador, filtros por rubro y resaltar en Verde Esmeralda la mejor opción de compra.
3. **CSV de Oportunidades:** Un resumen para Facu con los productos donde la brecha de ahorro es mayor al 20%.