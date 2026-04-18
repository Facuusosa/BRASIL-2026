# INSIGHTS: Curso Definitivo Claude Code (~250 min)
> Procesado de timedtext YouTube. Transcript completo en `video_claude_transcript.txt`.
> Instructor: Nick (LeftClick.ai) — $4M/año de beneficios usando Claude Code a diario.

---

## 1. CLAUDE.MD — El arma más importante

**Qué hace:** Se inyecta como primer mensaje en CADA sesión, antes que cualquier prompt tuyo.

**Analogía del barco:** Una desviación mínima al salir del puerto = destino completamente errado después de 10.000 km. El Claude.md fija el rumbo inicial y reduce el espacio de posibilidades de la IA.

**Reglas clave:**
- Máximo 200-500 líneas. Más = peor calidad + más costo.
- Solo viñetas y títulos cortos. Alta densidad de información.
- Las cosas más importantes arriba (sesgo de primacía — recuerda el inicio y el final, casi nada del medio).
- NO incluir guías de API completas, documentación masiva ni reglas vagas ("sé inteligente" = inútil).
- Tratar como código vivo: podar regularmente.
- Si Claude repite el mismo error → actualizar Claude.md YA.

**Comando clave:** `/init` en una carpeta nueva → genera un Claude.md automático analizando el código existente.

**Includes:** En el Claude.md se puede referenciar otros archivos con `@archivo.md` para importarlos.

---

## 2. ESTRUCTURA .CLAUDE/ — 3 niveles de jerarquía

```
~/.claude/           # Global — aplica a TODOS los proyectos
  claude.md          # Reglas globales
  memory.md          # Memoria persistente entre sesiones

[proyecto]/.claude/  # Local — solo este proyecto
  claude.md
  rules/             # Reglas divididas por tema (todas auto-cargan)
  agents/            # Subagentes definidos en .md
  skills/            # Habilidades (slash commands personalizados)
  settings.json      # Permisos, hooks, configuración
  settings.local.json  # Config local (NO sube a GitHub)
```

**Cómo usar las 3 capas:**
- Global: reglas que aplican a todos los proyectos (estilo, seguridad)
- Local: reglas específicas del proyecto
- Empresa (licencia Enterprise): tercer nivel, no relevante para MVP

---

## 3. MODOS DE PERMISOS — Los 4 modos

| Modo | Qué permite | Cuándo usar |
|------|-------------|-------------|
| `Ask before edit` | Pide confirmación antes de cambiar archivos | Código crítico de alto riesgo |
| `Auto-edit` | Edita archivos existentes sin pedir. Crea nuevos: pide permiso | Desarrollo normal |
| `Plan mode` | Solo lectura + investigación → genera plan sin ejecutar | Proyectos complejos antes de construir |
| `Bypass permissions` | Hace cualquier cosa sin pedir | Máxima velocidad — RIESGO: puede borrar archivos |

**Activar bypass:** En VSCode → Extensions → Claude Code → Settings → "dangerously allow bypass". No viene activado por defecto.

**Regla práctica del instructor:** Usa bypass para todo. El riesgo real es acumulación de archivos temporales, no la catástrofe.

---

## 4. PLAN MODE — Antes de construir algo complejo

**Filosofía:** 1 minuto de planificación = 10 minutos de construcción ahorrados.

**Cómo funciona:** Claude investiga la carpeta, busca en la web, razona desde primeros principios → genera documento de especificación → LUEGO construye.

**Flujo recomendado para proyectos grandes:**
1. Cambiar a Plan Mode
2. Dump de voz (hablas ~3x más rápido que escribís) → transcribir → pegar
3. Claude hace preguntas → respondés
4. Aprobás el plan
5. Cambiar a Bypass Permissions → construir

**El bucle fundamental:**
```
Tarea → Hacer → Verificar resultado → (repetir hasta óptimo)
```
Si no hay verificación (screenshot loop, tests, logs), perdés el 80% del valor.

---

## 5. DISEÑO WEB — Las 3 estrategias

**Estrategia 1: Screenshot loop (más efectiva)**
1. Ir a godly.website, dribble o similar → encontrar diseño de referencia
2. Chrome → F12 → Cmd+Shift+P → "screenshot" → captura pantalla completa
3. Reducir a <4MB (ilovimg.com resize 50%)
4. Pegar imagen + HTML body styles en Claude
5. Claude construye → screenshot → compara → itera hasta 99%

**Estrategia 2: Voice dump**
Hablar todo el contenido (3x más rápido que escribir) → transcribir → pegar → Claude construye

**Estrategia 3: Componentes de 21st.dev**
Copiar prompt de componente → pegar → Claude instala y adapta

**Tip de deployment:** Netlify para sitios estáticos. Vercel o Railway para full-stack. Modal para APIs/backends serverless.

---

## 6. GESTIÓN DE CONTEXTO — Lo más subestimado

**Ver consumo actual:** `/context` en terminal → muestra breakdown completo de tokens.

**Qué consume tokens (en orden):**
1. Herramientas del sistema (~17.000 tokens fijos — no controlable)
2. Claude.md global + local
3. MCPs instalados
4. Memory.md
5. Skills
6. Tus mensajes

**Estrategias para no degradar el contexto:**
- Usar alta densidad de información (comprimir voz → modelo barato → resumen → Claude principal)
- `/compact` manual cuando la sesión se alarga → Claude comprime historial conservando lo esencial
- Auto-compactación: Claude lo hace solo cuando quedan ~33k tokens libres
- Empezar nueva sesión cuando el contexto llega a 70-80% (no esperar)
- NO dejar documentación completa de API en Claude.md (solo los endpoints que necesitás)

**Sesgo de primacía/actualidad:** Claude recuerda bien el inicio y el final de la conversación, casi nada del medio → poner guardrails importantes al principio.

---

## 7. SKILLS — Automatizar flujos de trabajo repetitivos

**Qué son:** Archivos .md en `.claude/skills/` que definen un "script" con instrucciones de alto nivel + herramientas a usar. Se activan con `/nombre-skill`.

**Diferencia skills vs subagents:** Skills = instrucciones que ejecuta el agente principal. Subagentes = instancias Claude separadas con su propio contexto.

**Cómo crear una skill:**
1. Describir en bullets lo que querés que haga (voice → transcript → pegar)
2. Claude formatea según el patrón de skill
3. Claude genera la skill en `.claude/skills/nombre.md`
4. Probar → dar feedback → iterar hasta 90%+ de fiabilidad

**Ejemplos reales del instructor:**
- `shop-amazon.md`: navega Amazon, compara productos, pide aprobación antes de comprar
- `gmail-label.md`: recupera 100 emails, clasifica y etiqueta (36 seg → API directa más rápido que MCP)
- `design-website.md`: dado un lead, genera sitio personalizado en 30 seg
- `research.md`: busca en bases de datos específicas, ejecuta queries en paralelo

**Clave:** Skills >> MCP para tareas repetitivas. Las skills usan API directa (mucho más rápido y barato que MCP).

---

## 8. SUBAGENTES

**Cuándo usarlos:**
- Tareas paralelizables (investigación, clasificación masiva, revisión de código)
- Cuando contaminarían el contexto del agente principal
- 3 agentes útiles: Researcher (sin contexto previo), Code Reviewer (mirada fresca), QA/Tests

**Cómo funciona:** Agente padre crea "Task" → subagente corre con su propio contexto → devuelve resultado al padre.

**Costo:** ~7x el uso de tokens vs un agente solo. Usar donde justifica.

**Consejo del instructor:** Subagentes para paralelizar. Para 100 emails: 36s → 10 subagentes → 19s. Para 1000 emails: la diferencia se hace evidente.

**Problema frecuente:** El agente padre se queda sin contexto si los subagentes devuelven texto masivo. Solución: subagentes escriben a archivo en lugar de devolver texto.

---

## 9. MCP (Model Context Protocol) — Herramientas externas

**Qué es:** Como skills, pero desarrolladas por terceros. Extienden Claude con capacidades de servicios externos.

**Cómo instalar:** Pegar el JSON de configuración y decirle "instala esto en mi workspace local".

**MCP más valioso según el instructor:** `Chrome DevTools MCP` — controla el browser de Chrome directamente (mucho más rápido que Puppeteer/Playwright).

**Dónde encontrarlos:** mcpservers.org, marketplace.mcp.so, Claude plugins directory.

**Advertencia:** MCPs de terceros pueden consumir mucho contexto. Ser selectivo. Revisar cuántos tokens agrega cada uno con `/context`.

**Skills vs MCP:**
- MCP: lo desarrollaron otros, fácil de instalar, puede ser ineficiente
- Skills: lo desarrollás vos, usa API directa, mucho más rápido

---

## 10. HOOKS — Automatización del entorno

**Qué son:** Scripts que se ejecutan automáticamente antes/después de cada tool call de Claude.

**Configuración:** En `.claude/settings.json`

**Ejemplo del instructor:** Hook que suena una campanilla cuando Claude termina una tarea → saber cuándo parar la pestaña y dar más instrucciones.

**Casos de uso:**
- Notificaciones de sonido por ventana (identificar qué pestaña terminó)
- Logs automáticos
- Validaciones antes de que Claude ejecute algo

---

## 11. AGENT TEAMS — Paralelización extrema

**Qué son:** Múltiples instancias Claude completamente independientes que comparten un "tablón de anuncios" y pueden comunicarse entre sí.

**Diferencia con subagentes:**
- Subagentes: devuelven resultado al padre
- Agent Teams: cada uno tiene ventana de contexto propia + pueden comunicarse peer-to-peer

**Activar (feature experimental):**
```json
// .claude/settings.json
{"env": {"CLAUDE_CODE_AGENT_TEAMS_EXPERIMENTAL": "1"}}
```

**Costo:** MUY ALTO. El instructor gastó ~$80 en 15 minutos en un análisis de seguridad masivo. "Como una bomba nuclear apuntada a tu billetera."

**Cuándo tiene sentido:** Proyectos grandes donde múltiples features son independientes entre sí + tiempo vale más que dinero.

**Patrón antagónico:** Dos agentes con posturas opuestas debaten un hallazgo → el resultado final es de mayor calidad (similar a GANs en ML).

---

## 12. GIT WORKTREES — Desarrollo paralelo sin conflictos

**Qué son:** Ramas Git separadas en carpetas separadas → múltiples agentes trabajan en paralelo sin pisarse.

**Cuándo usar:** Cuando tenés múltiples features independientes y no querés que los agentes modifiquen los mismos archivos.

**Flujo:**
```
main/          ← rama principal intacta
feature-A/     ← agente 1 trabajando aquí
feature-B/     ← agente 2 trabajando aquí
hotfix/        ← agente 3 trabajando aquí
```
Al terminar → merge a main.

**Ventaja sobre Agent Teams:** Sin costo extra de tokens. Solo múltiples terminales/pestañas.

---

## 13. MEMORIA AUTOMÁTICA

**Cómo funciona:** Decirle "recuerda que X" → Claude escribe en `~/.claude/memory.md` → disponible en TODAS las sesiones futuras.

**Es independiente de Claude.md** — es el scratchpad de Claude, no el conjunto de instrucciones tuyo.

**Consume:** ~88 tokens (mínimo). No preocuparse por el tamaño.

---

## 14. GESTIÓN DE MÚLTIPLES PESTAÑAS

**Límite personal del instructor:** 3-4 pestañas simultáneas máximo.

**Señal de que tenés demasiadas:** Claude esperando tus instrucciones por más de 10-20 minutos.

**Regla:** Si Claude no está ejecutando algo activamente → estás dejando productividad en la mesa.

**Con hooks de sonido:** Cada pestaña tiene su propio tono → sabés cuál terminó sin mirar.

---

## 15. COMANDOS DE BARRA ESENCIALES

| Comando | Qué hace |
|---------|----------|
| `/init` | Genera Claude.md para la carpeta actual |
| `/context` | Muestra breakdown de tokens actuales |
| `/compact` | Comprime historial de conversación manualmente |
| `/permissions` | Abre panel de permisos de herramientas |

---

## 16. TIPS NO OBVIOS

- **Transcripción de voz:** Hablar 3x más rápido que escribir. En Mac: mantener FN. Usar para prompts largos.
- **Deployment rápido:** Netlify para HTML estático es instantáneo. Modal para APIs Python serverless.
- **Pausa durante ejecución:** El botón de pausa permite cambiar instrucciones mid-task sin reiniciar.
- **Thinking tab:** La "pestaña de pensamiento" no se incluye en los mensajes del historial, pero sí se cobra.
- **Auto-compactación:** Ocurre automáticamente. Pedir después: "¿qué está disponible en tu contexto?" para verificar qué retuvo.
- **Fuente de tips avanzados:** Buscar en Twitter/X "Claude Code" + pedir a Grok que resuma las mejores prácticas del último mes.
- **No mockear:** Usar datos reales siempre. Los tests con mocks pasan y el prod falla.
- **SuperBase para MVPs:** Auth + DB sin fricción, gratis para empezar.
