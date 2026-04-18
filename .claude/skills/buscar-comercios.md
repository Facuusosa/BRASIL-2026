# Skill: Buscar Comercios

Busca comercios potenciales (kioscos, almacenes, minimercados) en una zona específica para outreach. Usar con `/buscar-comercios [zona]`.

## Input esperado
- Zona a buscar (ej: "Villa Pueyrredón", "Villa del Parque", "Agronomía")
- Si no se especifica zona → usar Villa Pueyrredón por defecto

## Pasos

1. **Leer base existente**
   - Verificar si existe `Comercios_Villa_Pueyrredon.xlsx` en la raíz
   - Si existe → leerlo, ver cuántos contactos ya hay y cuáles tienen email/teléfono
   - Evitar duplicados en la nueva búsqueda

2. **Buscar en Google Maps** (via WebSearch o browser)
   - Queries: `"almacén" [zona] Buenos Aires`, `"kiosco" [zona] Buenos Aires`, `"minimercado" [zona] Buenos Aires`
   - Objetivo: encontrar nombre del local, dirección, teléfono, Google Maps URL

3. **Estructurar resultados**
   - Formato: nombre, tipo (kiosco/almacén/minimercado), dirección, teléfono, tiene_whatsapp (bool), fuente
   - Agrupar por tipo de comercio
   - Marcar los que ya estaban en la base como "ya contactado"

4. **Guardar resultados**
   - Agregar nuevos comercios a `data/outreach/comercios_[zona]_[fecha].json`
   - Si el directorio no existe → crearlo
   - Reportar: cuántos nuevos, cuántos ya existían, cuántos tienen teléfono

5. **Reporte**
   - Total de comercios encontrados (nuevos vs ya en base)
   - Breakdown por tipo
   - Próximo paso sugerido: `/enviar-outreach` con estos comercios
