# 🎯 RESUMEN EJECUTIVO - Flight Monitor Bot

**Para:** Facu  
**Fecha:** 12 febrero 2026  
**Estado:** ✅ Estructura del proyecto COMPLETA - Listo para programar

---

## ✨ ¿Qué tenemos?

Acabamos de crear la **estructura completa** de tu bot de monitoreo de vuelos a Florianópolis. Todo está documentado y listo para que Gemini (o cualquier IA) programe el código.

---

## 📁 Lo que se creó

### 1. **README.md** (El cerebro del proyecto)
- Especificaciones técnicas completas
- Restricciones claras (NO puede comprar, solo monitorear)
- Sistema de scoring detallado
- Configuración de alertas
- Roadmap de desarrollo en fases

### 2. **docs/01-research.md** (Tu investigación manual)
- Todos los precios que encontraste
- Comparación Flybondi vs JetSmart vs GOL
- Data de Turismo City, Despegar, Perplexity
- Conclusiones clave: Turismo City es 30-40% más barato
- Insight de oro: cambiar 1 día las fechas ahorra $128k

### 3. **docs/04-ai-prompts.md** (Instrucciones para la IA)
- 7 prompts específicos para que Gemini programe cada parte
- PROMPT MAESTRO para generar el bot completo
- Prompts individuales para: scrapers, scoring, notificaciones, BD, etc.
- Incluye ejemplos de código y estructura esperada

### 4. **Archivos de configuración:**
- `requirements.txt` → Todas las librerías Python necesarias
- `.env.example` → Template de variables de entorno
- `.gitignore` → Para no commitear datos sensibles

---

## 🎯 Datos Clave de Tu Investigación

### Mejor precio encontrado:
- **USD $484** (2 personas con equipaje) en Turismo City
- Flybondi ida y vuelta, horarios de madrugada

### Mejor relación calidad-precio:
- **USD $537** (2 personas con equipaje) en Turismo City
- Flybondi + JetSmart, horarios mixtos

### Insight crítico:
- **Cambiar fechas 1 día ahorra ~$128.000 ARS**
- Salir martes 10 en vez de lunes 9: -$86k
- Volver martes 17 en vez de lunes 16: -$42k

### Plataformas a monitorear (por prioridad):
1. 🔴 **Turismo City** (más barato, 30-40% menos que otros)
2. 🔴 **Despegar** (validación, más aerolíneas)
3. 🟢 **Webs directas** (backup, generalmente más caros)

---

## 🚀 Próximos Pasos (Para que Gemini Programe)

### OPCIÓN A - Un solo prompt (más rápido):
1. Abrí Gemini
2. Subí estos archivos:
   - `README.md`
   - `docs/01-research.md`
   - `docs/04-ai-prompts.md`
3. Usa el **PROMPT MAESTRO** (está en 04-ai-prompts.md)
4. Gemini generará todo el código de una

### OPCIÓN B - Paso a paso (más control):
1. Empezá con el PROMPT MAESTRO (arquitectura)
2. Seguí con los prompts específicos (#1 a #5) en orden
3. Vas revisando cada parte antes de continuar

**Mi recomendación:** Opción B si querés entender todo, Opción A si querés rapidez.

---

## ⚙️ Cómo Va a Funcionar el Bot (Una Vez Programado)

### Configuración inicial:
```bash
# 1. Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# 2. Configurar Telegram Bot
# - Crear bot en @BotFather
# - Copiar token a .env

# 3. Configurar variables (.env)
TELEGRAM_BOT_TOKEN=tu_token
CRITICAL_PRICE_ARS=850000
DEPARTURE_DATE=2026-03-09
RETURN_DATE=2026-03-16
```

### Ejecución:
```bash
# Test (una búsqueda)
python src/main.py --test

# Monitoreo continuo (cada 6 horas)
python src/main.py --daemon
```

### Qué hace el bot:
1. **Cada 6 horas** busca vuelos en Turismo City y Despegar
2. **Guarda** precios en base de datos SQLite
3. **Calcula score** de cada vuelo (0-100 según precio/horario)
4. **Te avisa por Telegram** cuando:
   - Precio < $850k (ALERTA CRÍTICA 🔴)
   - Precio < $950k con buenos horarios (ALERTA IMPORTANTE 🟡)
   - Ahorro >$100k cambiando fechas
   - Nueva opción aparece
5. **Genera reportes** diarios con tendencias

---

## 🔐 Restricciones de Seguridad (MUY IMPORTANTE)

El bot **NUNCA** va a poder:
- ❌ Comprar vuelos automáticamente
- ❌ Guardar datos de tarjetas
- ❌ Hacer checkout
- ❌ Acceder a tus cuentas

Solo va a:
- ✅ Buscar precios
- ✅ Guardarte el histórico
- ✅ Avisarte cuando encuentra ofertas

**VOS decidís cuándo comprar.**

---

## 💰 Potencial de Ahorro

Basado en tu research:

| Escenario | Precio sin bot | Precio con bot | Ahorro |
|-----------|----------------|----------------|--------|
| Compra inmediata (hoy) | ~$1.200.000 | ~$850.000 | **$350.000** |
| + Cambio de fechas | ~$1.200.000 | ~$722.000 | **$478.000** |
| + Esperar caída de precio (10%) | ~$1.200.000 | ~$650.000 | **$550.000** |

**Objetivo realista:** Ahorrar $300k-500k encontrando el momento óptimo.

---

## 📊 Fases del Desarrollo

### ✅ Fase 0: Research (COMPLETADO)
- Investigación manual de precios
- Validación con Perplexity
- Definición de arquitectura
- Documentación completa

### 🟡 Fase 1: MVP (Siguiente, 2-3 días)
- Scraper de Turismo City
- Base de datos SQLite
- Notificaciones Telegram básicas
- Ejecución manual

### 🔵 Fase 2: Avanzado (1-2 días)
- Scraper de Despegar
- Fechas flexibles (±2 días)
- Sistema de scoring
- Análisis de tendencias

### 🟣 Fase 3: Automatización (1 día)
- Cron job para ejecutar cada 6 horas
- Reportes diarios
- Dashboard simple

### 🟠 Fase 4: Opcional (futuro)
- VPN integration
- Más plataformas (Google Flights, etc.)
- Dashboard web interactivo

---

## 🎓 Lo que Aprendiste

Durante el research descubriste que:

1. **Los metabuscadores son mejores** que comprar directo
2. **Turismo City >> Despegar** (30-40% más barato)
3. **La flexibilidad vale oro** (+1 día = -$128k)
4. **Flybondi es la más barata** pero horarios jodidos
5. **JetSmart tiene quirks** (no funciona en incógnito)
6. **Los precios varían MUCHO** entre plataformas (hasta 40%)

Esto justifica 100% tener un bot monitoreando 24/7.

---

## ❓ FAQ Anticipadas

**P: ¿Cuánto tarda Gemini en programar esto?**  
R: Con los prompts que armamos, 2-4 horas de "conversación" con Gemini. Capaz 1-2 días si vas revisando y testeando cada parte.

**P: ¿Necesito saber programar?**  
R: No para usar el bot. Sí para modificarlo o debuggear si algo falla. Los prompts están hechos para que Gemini explique todo.

**P: ¿Dónde corro el bot?**  
R: Opciones:
1. Tu compu (gratis, pero tiene que estar prendida)
2. Raspberry Pi (ideal, consume poca energía)
3. VPS en la nube (DigitalOcean $6/mes, siempre online)

**P: ¿Y si cambian los diseños de Turismo City/Despegar?**  
R: Los scrapers se rompen. Hay que actualizarlos (pasa cada 3-6 meses típicamente). El bot loguea warnings cuando algo falla.

**P: ¿Es legal esto?**  
R: Sí, siempre que:
- Respetes robots.txt
- No hagas scraping agresivo (por eso delays de 5-15 seg)
- Solo uses la data para vos (no la revendas)

**P: ¿Cuándo compro?**  
R: El bot te avisa, vos decidís. Regla general:
- Si ves < $650k y horarios decentes → comprar YA
- Si ves $650k-850k → esperar 1-2 días más
- Si ves > $850k → esperar, probablemente baje

---

## 🎁 Bonus: Comandos del Bot de Telegram

Una vez programado, vas a poder hacer:

```
/start - Info del bot
/status - ¿Está monitoreando?
/lastprice - Último precio encontrado
/history - Histórico últimas 24hs
/report - Generar reporte con gráficos
/stop - Pausar alertas
/resume - Reanudar alertas
```

---

## 🚀 Listo para Empezar

Tenés TODO lo necesario para que Gemini te programe el bot:

1. ✅ README con specs completas
2. ✅ Research con datos reales
3. ✅ Prompts optimizados para la IA
4. ✅ Estructura del proyecto definida
5. ✅ Requirements y configuración lista

**Siguiente paso:** Abrí Gemini y dale el PROMPT MAESTRO.

---

## 📞 Si Necesitás Ayuda

Durante el desarrollo con Gemini:

1. **Si Gemini no entiende algo:**  
   → Mostrá el README.md y research.md completos

2. **Si el código no funciona:**  
   → Pedí que agregue más logging  
   → Compartí el error con Gemini

3. **Si querés agregar features:**  
   → Volvé a este documento  
   → Usá los prompts específicos

4. **Si el bot no encuentra precios:**  
   → Puede que los selectores CSS cambiaron  
   → Pedí a Gemini que tome un screenshot y analice

---

## 🎯 Objetivo Final

**Viajar a Floripa ahorrando $300k-500k** gracias a:
- Monitoreo 24/7 automatizado
- Alertas cuando bajan los precios
- Flexibilidad de fechas
- Comparación de múltiples plataformas

Y de paso, aprender sobre automation, scraping y bots 🤓

---

**¿Alguna duda antes de empezar con Gemini?**

Si no, dale nomás con el PROMPT MAESTRO y dejá que la magia suceda ✨

---

**Archivos principales que vas a usar:**
- `docs/04-ai-prompts.md` → PROMPT MAESTRO (empezá por acá)
- `README.md` → Referencia técnica completa
- `docs/01-research.md` → Tus datos de investigación

**Todo está en:** `/mnt/user-data/outputs/flight-monitor-bot/`

¡Éxitos con el proyecto! 🛫🏖️
