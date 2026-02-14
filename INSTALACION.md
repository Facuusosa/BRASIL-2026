# 🛫 Guía de Instalación - Flight Monitor Bot

## Monitoreo automático de precios de vuelos Buenos Aires → Florianópolis

---

## 📋 ¿Qué hace este bot?

Este bot **busca automáticamente** los mejores precios de vuelos para tu viaje a Brasil.  
Cada 6 horas revisa los precios en Turismo City y Despegar, y si encuentra un buen precio te manda una **alerta por Telegram** al celular.

**⚠️ IMPORTANTE:** El bot **SOLO mira precios**. Nunca compra nada, nunca guarda datos de tarjetas, nunca hace pagos.

---

## 📦 Paso 1: Requisitos previos

Antes de empezar, necesitás tener instalados:

### 1.1 Python (versión 3.11 o superior)

1. Andá a [python.org/downloads](https://www.python.org/downloads/)
2. Descargá la última versión de Python (3.12 o 3.13)
3. Al instalar, **MUY IMPORTANTE**: marcá la casilla que dice **"Add Python to PATH"**
4. Terminá la instalación

**¿Cómo saber si ya lo tenés?**  
Abrí la terminal (CMD en Windows) y escribí:
```
python --version
```
Si dice algo como `Python 3.12.x`, ya está ✅

### 1.2 Git (opcional)

Solo si querés clonar el repositorio con Git. Si ya tenés la carpeta del proyecto, no hace falta.

### 1.3 Telegram

Tené la app de Telegram instalada en el celular (o en la computadora).

---

## 🚀 Paso 2: Ejecutar la instalación automática

### En Windows:

1. Abrí la carpeta del proyecto (`BRASIL 2026`)
2. Hacé **doble clic** en el archivo `setup.bat`
3. Esperá que termine (puede tardar 2-5 minutos)
4. Al final debería decir **"✅ INSTALACIÓN COMPLETADA"**

### En Mac/Linux:

1. Abrí una terminal
2. Navegá a la carpeta del proyecto:
   ```bash
   cd /ruta/a/BRASIL\ 2026
   ```
3. Dale permisos al script:
   ```bash
   chmod +x setup.sh
   ```
4. Ejecutá el script:
   ```bash
   ./setup.sh
   ```

**¿Qué hace el script?**
- ✅ Verifica que tengas Python instalado
- ✅ Crea un entorno virtual (una "burbuja" para las dependencias)
- ✅ Instala todas las librerías necesarias
- ✅ Instala Chromium (el navegador que usa el bot para buscar)
- ✅ Crea el archivo de configuración (.env)

---

## 🤖 Paso 3: Crear el bot de Telegram

Para que el bot te pueda mandar mensajes, necesitás crear tu propio bot de Telegram.

### 3.1 Crear el bot con @BotFather

1. Abrí Telegram en el celular o computadora
2. Buscá **@BotFather** (tiene una tilde azul de verificado)
3. Iniciá conversación y escribí: `/newbot`
4. Te va a preguntar el **nombre del bot** → Poné algo como: `Mi Monitor de Vuelos`
5. Te va a preguntar el **username del bot** → Poné algo como: `mi_vuelos_bot` (tiene que terminar en "bot")
6. Te va a dar un **token** que se ve así:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
7. **COPIÁ ESE TOKEN** — lo vas a necesitar en el paso 5

### 3.2 Obtener tu Chat ID

1. Buscá **@userinfobot** en Telegram
2. Iniciá conversación y escribí: `/start`
3. Te va a responder con tu información, incluyendo tu **ID** (un número como `987654321`)
4. **COPIÁ ESE NÚMERO** — lo vas a necesitar en el paso 5

> **Alternativa:** Si @userinfobot no funciona, probá con **@getmyid_bot**

---

## ⚙️ Paso 4: (Opcional) Iniciar el bot de Telegram

Después de crear el bot en el paso 3:

1. Buscá el bot que creaste (por el username que le pusiste)
2. Abrí la conversación y escribí: `/start`
3. Esto es necesario para que el bot pueda enviarte mensajes

---

## 📝 Paso 5: Configurar el archivo .env

El archivo `.env` contiene toda la configuración del bot. Es como un formulario que hay que llenar.

### 5.1 Abrí el archivo

1. Andá a la carpeta del proyecto (`BRASIL 2026`)
2. Buscá el archivo llamado `.env` (si no lo ves, puede estar oculto — en Windows activá "Ver archivos ocultos")
3. Abrilo con cualquier editor de texto (Bloc de notas, VS Code, etc.)

### 5.2 Completá estos datos

Buscá estas líneas y reemplazá los valores de ejemplo:

```env
# Pegá el token que te dio @BotFather (sin comillas)
TELEGRAM_BOT_TOKEN=PEGÁ-TU-TOKEN-ACÁ

# Pegá el número que te dio @userinfobot
TELEGRAM_CHAT_ID=PEGÁ-TU-ID-ACÁ
```

**Las demás variables ya están pre-configuradas:**
- Fechas: 9 al 16 de marzo 2026
- 2 pasajeros
- 20kg de equipaje
- Alertas configuradas para precios buenos

Si querés cambiar algo, el archivo tiene comentarios que explican cada variable.

### 5.3 Guardá el archivo

Simplemente guardá y cerrá.

---

## 🧪 Paso 6: Ejecutar el test de verificación

El test verifica que todo esté bien configurado antes de ejecutar el bot.

### En Windows:

1. Abrí CMD (Símbolo del sistema)
2. Navegá a la carpeta del proyecto:
   ```
   cd "C:\Users\TU_USUARIO\OneDrive\Escritorio\BRASIL 2026"
   ```
3. Activá el entorno virtual:
   ```
   venv\Scripts\activate
   ```
4. Ejecutá el test:
   ```
   python test_bot.py
   ```

### En Mac/Linux:

```bash
cd /ruta/a/BRASIL\ 2026
source venv/bin/activate
python test_bot.py
```

### ¿Qué debería pasar?

Al final del test vas a ver un reporte así:

```
📊 REPORTE FINAL DE VERIFICACIÓN

  ✅ Pasaron:      25/27
  ❌ Fallaron:     0/27
  ⚠️  Advertencias: 2/27

  🎉 TODO OK — El bot está listo para usarse
```

- **✅ PASS** = Todo bien
- **⚠️ WARN** = Advertencia (no es grave, pero conviene revisar)
- **❌ FAIL** = Error que hay que arreglar

---

## ▶️ Paso 7: Ejecutar el bot por primera vez

### Modo TEST (una sola búsqueda):

```
python src/main.py --test
```

Esto va a:
- Buscar vuelos una vez en Turismo City y Despegar
- Mostrar los resultados en pantalla
- Si encuentra un buen precio, te manda mensaje por Telegram

### Modo CONTINUO (monitoreo cada 6 horas):

```
python src/main.py --daemon
```

Esto va a:
- Buscar vuelos cada 6 horas automáticamente
- Enviarte alertas por Telegram cuando encuentre buenos precios
- Funcionar continuamente hasta que lo detengas con `Ctrl+C`

### Otros modos disponibles:

| Comando | ¿Qué hace? |
|---------|------------|
| `python src/main.py --test` | Una búsqueda de prueba |
| `python src/main.py --daemon` | Monitoreo continuo (cada 6 horas) |
| `python src/main.py --analyze-only` | Analiza datos guardados (sin buscar) |
| `python src/main.py --report` | Genera reporte de precios |
| `python src/main.py --debug` | Modo detallado (muestra más info) |

---

## 🔧 Paso 8: Solución de problemas

### "Python no se reconoce como comando"
- Reinstalá Python y asegurate de marcar **"Add Python to PATH"**
- Reiniciá la terminal después de instalar

### "No se pudo crear el entorno virtual"
- En Ubuntu/Debian: `sudo apt install python3-venv`
- En Mac: `brew install python@3.12`

### "Error al instalar dependencias"
- Verificá tu conexión a internet
- Intentá: `pip install --upgrade pip setuptools`
- Luego: `pip install -r requirements.txt`

### "Playwright no funciona"
- Ejecutá manualmente: `playwright install chromium`
- En Linux puede necesitar dependencias extra: `playwright install-deps`

### "El bot de Telegram no envía mensajes"
1. Verificá que el token sea correcto (sin espacios ni comillas extra)
2. Verificá que el Chat ID sea correcto (es un número)
3. Asegurate de haber enviado `/start` al bot en Telegram
4. Ejecutá `python test_bot.py` para verificar la conexión

### "Los scrapers no encuentran vuelos"
- Es normal que a veces no encuentren resultados
- Las páginas web cambian su diseño, lo que puede romper los selectores CSS
- Revisá los screenshots de error en la carpeta `data/cache/`

### "Error de permisos"
- En Windows: ejecutá CMD como Administrador
- En Linux/Mac: usá `sudo` solo para instalar dependencias del sistema

---

## 📊 Tipos de alertas que vas a recibir

| Tipo | Cuándo salta | Sonido |
|------|-------------|--------|
| 🔴 **CRÍTICA** | Precio < USD $450 o < $850.000 ARS | Sí (con sonido) |
| 🟡 **IMPORTANTE** | Precio < USD $550 o < $950.000 ARS | No (silenciosa) |
| 📊 **REPORTE** | Resumen diario de precios | No |
| ❌ **ERROR** | Si el bot tiene un problema | No |

---

## 🔐 Seguridad

- El archivo `.env` contiene tu token de Telegram. **NO lo compartas** con nadie.
- El archivo `.gitignore` ya está configurado para que `.env` no se suba a repositorios.
- El bot **NUNCA** compra vuelos ni accede a datos de pago.
- Solo busca precios públicos que cualquiera puede ver en las páginas web.

---

## 💡 Tips

1. **Dejá el bot corriendo** en una computadora que esté siempre encendida (o en un servidor)
2. **No cierres la terminal** mientras el bot está en modo daemon
3. **Revisá los logs** en `data/logs/bot.log` si algo no funciona
4. Los **screenshots de error** se guardan en `data/cache/` — úsalos para debuggear

---

*¿Preguntas? Revisá el archivo README.md para más detalles técnicos.*
