@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║  🛫 FLIGHT MONITOR BOT - Instalación Automática    ║
echo ║  Monitoreo de precios de vuelos BUE → FLN          ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: ============================================================
:: PASO 1: Verificar Python 3.11+
:: ============================================================
echo [1/6] Verificando Python...

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH.
    echo.
    echo    Descargalo desde: https://www.python.org/downloads/
    echo    IMPORTANTE: Marcá "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo ❌ ERROR: Se requiere Python 3.11 o superior. Tenés Python %PYVER%.
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 11 (
    echo ⚠️  ADVERTENCIA: Se recomienda Python 3.11+. Tenés Python %PYVER%.
    echo    Puede funcionar, pero no está garantizado.
    echo.
)

echo ✅ Python %PYVER% detectado.
echo.

:: ============================================================
:: PASO 2: Crear entorno virtual
:: ============================================================
echo [2/6] Creando entorno virtual...

if exist "venv" (
    echo    ℹ️  El entorno virtual ya existe. Usando el existente.
) else (
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ ERROR: No se pudo crear el entorno virtual.
        echo    Intentá: python -m pip install --upgrade pip setuptools
        pause
        exit /b 1
    )
    echo ✅ Entorno virtual creado en ./venv
)
echo.

:: ============================================================
:: PASO 3: Activar entorno virtual e instalar dependencias
:: ============================================================
echo [3/6] Instalando dependencias...

call venv\Scripts\activate.bat

python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Fallo la instalación de dependencias.
    echo    Verificá tu conexión a internet y el archivo requirements.txt
    pause
    exit /b 1
)

echo ✅ Dependencias instaladas correctamente.
echo.

:: ============================================================
:: PASO 4: Instalar navegadores de Playwright
:: ============================================================
echo [4/6] Instalando navegadores de Playwright (Chromium)...
echo    Esto puede tardar unos minutos...
echo.

playwright install chromium
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  ADVERTENCIA: No se pudo instalar Chromium automáticamente.
    echo    Intentá manualmente: playwright install chromium
    echo.
) else (
    echo ✅ Chromium instalado para Playwright.
)
echo.

:: ============================================================
:: PASO 5: Crear archivo .env
:: ============================================================
echo [5/6] Configurando archivo .env...

if exist ".env" (
    echo    ℹ️  El archivo .env ya existe. No se sobreescribe.
) else (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo ✅ Archivo .env creado desde .env.example
    ) else (
        echo ❌ ERROR: No se encontró .env.example
        echo    El archivo .env.example debería estar en la raíz del proyecto.
    )
)
echo.

:: ============================================================
:: PASO 6: Crear carpetas de datos
:: ============================================================
echo [6/6] Creando estructura de carpetas...

if not exist "data" mkdir data
if not exist "data\logs" mkdir data\logs
if not exist "data\cache" mkdir data\cache

echo ✅ Carpetas creadas: data/, data/logs/, data/cache/
echo.

:: ============================================================
:: RESUMEN FINAL
:: ============================================================
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║  ✅ INSTALACIÓN COMPLETADA                         ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo ┌──────────────────────────────────────────────────────┐
echo │  SIGUIENTE PASO: Configurar el archivo .env         │
echo │                                                      │
echo │  Abrí el archivo .env con un editor de texto y      │
echo │  completá estos datos:                               │
echo │                                                      │
echo │  1. TELEGRAM_BOT_TOKEN                               │
echo │     → Creá un bot en Telegram con @BotFather         │
echo │     → Copiá el token que te da                       │
echo │                                                      │
echo │  2. TELEGRAM_CHAT_ID                                 │
echo │     → Habla con @userinfobot en Telegram             │
echo │     → Copiá tu chat ID                               │
echo │                                                      │
echo │  3. Las fechas y precios ya están pre-configurados   │
echo │     pero podés modificarlos si querés.               │
echo │                                                      │
echo │  PARA PROBAR:                                        │
echo │     venv\Scripts\activate                            │
echo │     python test_bot.py                               │
echo │                                                      │
echo │  PARA EJECUTAR:                                      │
echo │     venv\Scripts\activate                            │
echo │     python src/main.py --test                        │
echo └──────────────────────────────────────────────────────┘
echo.

pause
