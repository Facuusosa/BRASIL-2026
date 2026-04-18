# Reglas: Protocolo de trabajo

## Bucle verificador
Ver `testing.md` — aplica a TODA tarea, no solo código ni scrapers.

## Cuando Claude repite el mismo error → agregar regla YA
Si el mismo error ocurre dos veces, crear/actualizar la regla en `.claude/rules/` antes de continuar.
No esperar al final de la sesión. Regla nueva = problema resuelto para siempre.

## Actualizar al final de sesiones importantes
Correr `/cerrar-sesion` — el skill hace todo el proceso.

Manual si no está disponible:
1. Regla permanente → `.claude/rules/` o `.claude/docs/`
2. Estado operativo → memoria en `~/.claude/projects/.../memory/`
3. Guardar decisiones y el por qué — lo que NO está en el código ni en git
4. Podar reglas viejas — los rules/ son código vivo, no un archivo histórico

## Auditoría profunda
Correr el agente `auditor` cuando hay dudas de calidad o antes de release:
"Actúa como el agente definido en `.claude/agents/auditor.md` y auditá el proyecto completo"
