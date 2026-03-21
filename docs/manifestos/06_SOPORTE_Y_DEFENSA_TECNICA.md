# HunterPrice AI - Soporte, Seguridad y Defensa Técnica

## 1. Misión: Resiliencia y Estabilidad del Sistema
Este experto es el guardián de la continuidad del negocio. Su objetivo es que HunterPrice AI funcione 24/7 sin errores fatales y que cualquier fallo sea detectado, reportado y mitigado antes de que el cliente lo note.

## 2. Monitoreo de Integridad de Datos (Data Drift)
- **Detección de Cambios de Formato:** SAP y las webs de competencia cambian sus estructuras sin previo aviso. Jarvis debe validar que las columnas críticas (`Material`, `Precio`, `Descripción`) existan antes de procesar.
- **Alertas de Inconsistencia:** Si en una actualización el 50% de los productos vienen con precio $0 o "NaN", Jarvis debe frenar el proceso y enviar una alerta: "Socio, la fuente de datos parece dañada. Proceso abortado para proteger el reporte del cliente".

## 3. Seguridad de la Información (Data Protection)
- **Ofuscación de Origen:** Queda estrictamente prohibido que en los archivos finales (HTML/PDF) existan metadatos, nombres de usuarios internos o rutas de carpetas de la computadora de Facu.
- **Protección de Propiedad Intelectual:** El motor de "Fuzzy Matching" y las reglas de negocio son el secreto comercial. El código debe estar organizado para que la lógica pesada ocurra en el backend y no sea visible para el usuario final.

## 4. Gestión de Logs y Auditoría
- **Logs Inteligentes (Human-Readable):** No queremos archivos de texto inentendibles. Queremos un historial que diga: 
    - "14:00 - Ingesta iniciada (40,000 filas)."
    - "14:02 - 150 nuevos productos detectados."
    - "14:05 - Reporte generado con éxito. 3 oportunidades de Flipping detectadas."
- **Checkpoints:** El sistema debe guardar una copia de la "última versión estable" de la base de datos para poder comparar tendencias o restaurar en caso de desastre.

## 5. Escalabilidad Técnica (Cloud-Ready)
- El diseño debe permitir pasar de procesar archivos locales (.csv) a conectarse a bases de datos en la nube (PostgreSQL/Supabase) sin necesidad de reescribir todo el código.
- Modularización de funciones: La "Limpieza" es independiente del "Análisis", y el "Análisis" es independiente de la "Visualización".

## 6. Defensa Legal y Ética
- Asegurar que el ritmo de scraping (cuando se automatice por completo) sea respetuoso y no cause problemas de denegación de servicio a las fuentes.
- Mantener siempre la narrativa de "Agregador de Datos Públicos" para proteger el estatus laboral y profesional del fundador.
