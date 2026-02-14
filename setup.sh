#!/bin/bash

# ============================================================
# Flight Monitor Bot - Script de Instalación Automática
# Para Mac/Linux
# ============================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  🛫 FLIGHT MONITOR BOT - Instalación Automática    ║"
echo "║  Monitoreo de precios de vuelos BUE → FLN          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# PASO 1: Verificar Python 3.11+
# ============================================================
echo "[1/6] Verificando Python..."

# Intentar con python3 primero, luego python
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ ERROR: Python no está instalado."
    echo ""
    echo "   Instalalo con:"
    echo "   - Mac:   brew install python@3.12"
    echo "   - Ubuntu: sudo apt install python3.12 python3.12-venv"
    echo "   - Fedora: sudo dnf install python3.12"
    echo ""
    exit 1
fi

PYVER=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
MAJOR=$(echo "$PYVER" | cut -d. -f1)
MINOR=$(echo "$PYVER" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "⚠️  ADVERTENCIA: Se recomienda Python 3.11+. Tenés Python $PYVER."
    echo "   Puede funcionar, pero no está garantizado."
    echo ""
fi

echo "✅ Python $PYVER detectado (usando: $PYTHON_CMD)."
echo ""

# ============================================================
# PASO 2: Crear entorno virtual
# ============================================================
echo "[2/6] Creando entorno virtual..."

if [ -d "venv" ]; then
    echo "   ℹ️  El entorno virtual ya existe. Usando el existente."
else
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: No se pudo crear el entorno virtual."
        echo "   En Ubuntu/Debian, intentá: sudo apt install python3-venv"
        exit 1
    fi
    echo "✅ Entorno virtual creado en ./venv"
fi
echo ""

# ============================================================
# PASO 3: Activar entorno virtual e instalar dependencias
# ============================================================
echo "[3/6] Instalando dependencias..."

source venv/bin/activate

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Fallo la instalación de dependencias."
    echo "   Verificá tu conexión a internet y el archivo requirements.txt"
    exit 1
fi

echo "✅ Dependencias instaladas correctamente."
echo ""

# ============================================================
# PASO 4: Instalar navegadores de Playwright
# ============================================================
echo "[4/6] Instalando navegadores de Playwright (Chromium)..."
echo "   Esto puede tardar unos minutos..."
echo ""

playwright install chromium
if [ $? -ne 0 ]; then
    echo "⚠️  ADVERTENCIA: No se pudo instalar Chromium automáticamente."
    echo "   Intentá manualmente: playwright install chromium"
    echo ""
else
    echo "✅ Chromium instalado para Playwright."
fi
echo ""

# ============================================================
# PASO 5: Crear archivo .env
# ============================================================
echo "[5/6] Configurando archivo .env..."

if [ -f ".env" ]; then
    echo "   ℹ️  El archivo .env ya existe. No se sobreescribe."
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Archivo .env creado desde .env.example"
    else
        echo "❌ ERROR: No se encontró .env.example"
    fi
fi
echo ""

# ============================================================
# PASO 6: Crear carpetas de datos
# ============================================================
echo "[6/6] Creando estructura de carpetas..."

mkdir -p data/logs
mkdir -p data/cache

echo "✅ Carpetas creadas: data/, data/logs/, data/cache/"
echo ""

# ============================================================
# RESUMEN FINAL
# ============================================================
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅ INSTALACIÓN COMPLETADA                         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "┌──────────────────────────────────────────────────────┐"
echo "│  SIGUIENTE PASO: Configurar el archivo .env         │"
echo "│                                                      │"
echo "│  Abrí el archivo .env con un editor de texto y      │"
echo "│  completá estos datos:                               │"
echo "│                                                      │"
echo "│  1. TELEGRAM_BOT_TOKEN                               │"
echo "│     → Creá un bot en Telegram con @BotFather         │"
echo "│     → Copiá el token que te da                       │"
echo "│                                                      │"
echo "│  2. TELEGRAM_CHAT_ID                                 │"
echo "│     → Habla con @userinfobot en Telegram             │"
echo "│     → Copiá tu chat ID                               │"
echo "│                                                      │"
echo "│  3. Las fechas y precios ya están pre-configurados   │"
echo "│     pero podés modificarlos si querés.               │"
echo "│                                                      │"
echo "│  PARA PROBAR:                                        │"
echo "│     source venv/bin/activate                         │"
echo "│     python test_bot.py                               │"
echo "│                                                      │"
echo "│  PARA EJECUTAR:                                      │"
echo "│     source venv/bin/activate                         │"
echo "│     python src/main.py --test                        │"
echo "└──────────────────────────────────────────────────────┘"
echo ""
