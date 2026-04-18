# Rules: Security

## Credenciales — regla absoluta
- NUNCA hardcodear credenciales en el código
- SIEMPRE usar `.env` + `python-dotenv` (`load_dotenv()` al inicio)
- Variables en `.env`:
  ```
  YAGUAR_USERNAME=...
  YAGUAR_PASSWORD=...
  CARREFOUR_PHPSESSID=...
  CARREFOUR_CF_CLEARANCE=...
  ```
- Acceder con `os.getenv("VAR", "fallback_seguro")`

## Git
- `.env` está en `.gitignore` — verificar antes de cada commit
- Si accidentalmente se commitea una credencial → rotar la credencial inmediatamente
- No commitear archivos con cookies, tokens o passwords en ningún formato

## Scrapers
- Cookies de MaxiCarrefour expiran cada ~30 días — proceso de renovación en `.claude/docs/operaciones.md`
- Si el scraper devuelve 0 productos → sospechar cookies expiradas antes de tocar el código
- Nunca loguear cookies completas en archivos de log (truncar si hace falta)

## Frontend
- No exponer datos sensibles en `console.log` en producción
- localStorage para MVP — no guardar datos de pago ni credenciales reales ahí
- Auth dummy para MVP: la auth real va en Tier2, con backend propio

## Validación de inputs
- Validar solo en límites del sistema: input de usuario, respuestas de APIs externas
- Confiar en el código interno y garantías del framework — no sobre-validar
