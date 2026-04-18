# Skill: Cerrar Sesión

Protocolo obligatorio de cierre para sesiones importantes. Retroalimenta el `.claude/` con lo aprendido. Usar con `/cerrar-sesion` al final de cada sesión que cambió algo relevante.

## Cuándo usar
- Se modificó código, scrapers, o el pipeline
- Se tomaron decisiones arquitectónicas o de negocio no obvias
- Se descubrió un problema nuevo (bug, bloqueo, patrón de error)
- Se probó algo que funcionó bien o que falló

## Pasos

1. **Revisar la sesión**
   - Leer el historial de la conversación actual
   - Identificar: ¿qué cambió? ¿qué se decidió? ¿qué error se resolvió?
   - Separar lo que es obvio del código (no guardar) de lo que no está documentado (guardar)

2. **Actualizar rules/ si corresponde**
   - Si Claude repitió un error → crear/actualizar la regla en `.claude/rules/` ahora
   - Si se descubrió un patrón de bloqueo nuevo (ej: nueva forma de detectar cookies expiradas) → agregar a `rules/02-scrapers.md`
   - Si cambió el scope del MVP → actualizar `rules/01-proyecto.md`
   - Si se aprendió algo sobre el comportamiento esperado de Claude → actualizar `rules/00-facu.md`

3. **Actualizar docs/ si corresponde**
   - Si cambió el proceso operativo (ej: nueva frecuencia de cookies, nuevo paso en el pipeline) → actualizar `.claude/docs/operaciones.md`
   - Si hay una decisión arquitectónica importante (ej: "decidimos no usar BD real en MVP") → actualizar `.claude/docs/arquitectura.md`

4. **Actualizar memoria persistente**
   - Escribir en `~/.claude/projects/.../memory/` lo que no está en los archivos del proyecto
   - Estado actual del proyecto: ¿qué está funcionando, qué está pendiente?
   - Decisiones de negocio: precio, canales de venta, prioridades
   - Solo lo que un Claude frío en la próxima sesión necesitaría saber para no empezar de cero

5. **Verificación final**
   - ¿Las reglas en `rules/` reflejan lo que aprendimos hoy?
   - ¿La memoria tiene el estado actual del proyecto?
   - ¿Hay archivos temporales o de debug que limpiar?

6. **Resumen de cierre**
   Reportar:
   - Qué se modificó en `.claude/`
   - Estado del proyecto en una línea
   - Próximo paso para la próxima sesión (una sola acción, concreta)
