# Skill: Enviar Outreach

Redacta y envía emails de prospección a comercios para ofrecerles Brújula de Precios. Usar con `/enviar-outreach [archivo-comercios]`.

## Input esperado
- Archivo JSON con comercios (output de `/buscar-comercios`) o lista manual
- Si no se especifica → usar el archivo más reciente en `data/outreach/`

## Pasos

1. **Leer lista de comercios**
   - Cargar el archivo de comercios especificado
   - Filtrar: solo los que tienen email O teléfono (WhatsApp)
   - Excluir los que ya tienen `contactado: true`

2. **Personalizar mensaje por tipo**
   - Template para kiosco: énfasis en bebidas, snacks, lácteos
   - Template para almacén: énfasis en secos, limpieza, lácteos
   - Template para minimercado: énfasis en volumen, margen, múltiples categorías
   - Variables a personalizar: nombre del negocio, tipo de comercio, zona

3. **Redactar emails**
   - Asunto: "¿Sabés cuánto te cobraron de más en tu última compra al mayorista?"
   - Cuerpo: corto (5 líneas máx), propuesta de valor clara, link a la app, CTA específico
   - Tono: directo, comerciante a comerciante, sin corporativo
   - NO usar palabras: "solución", "plataforma", "ecosistema", "sinergias"

4. **Mostrar preview**
   - Mostrar los primeros 3 emails redactados
   - Pedir confirmación antes de enviar cualquiera
   - "¿Aprobás este template o querés ajustar algo?"

5. **Enviar (solo si Facu aprueba)**
   - Usar Gmail MCP si está disponible
   - Si no → generar archivo `emails_draft_[fecha].txt` con todos los emails listos para copiar-pegar
   - Marcar cada comercio enviado como `contactado: true` en el JSON

6. **Reporte**
   - Cuántos emails enviados vs redactados
   - Cuántos quedan pendientes (sin email, solo teléfono)
   - Para los de WhatsApp → generar mensajes cortos separados (120 chars máx)
