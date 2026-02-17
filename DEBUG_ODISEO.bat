@echo off
title ODISEO | DEBUG MODE
color 0E
cd /d "%~dp0"

echo ===================================================
echo   MODO DEBUG - VERIFICANDO ERRORES
echo ===================================================
echo.

if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo [WARN] No se encontro entorno virtual (venv).
    echo        Intentando usar python global...
)

echo.
echo [INFO] Verificando instalacion de modulos...
python -c "import curl_cffi; import requests; print('OK: Modulos encontrados')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Faltan librerias. Ejecutando instalacion...
    pip install -r requirements.txt
)

echo.
echo [INFO] Iniciando Sistema Odiseo...
python -u src\ODISEO_SYSTEM.py

echo.
echo ===================================================
echo   FIN DE EJECUCION
echo ===================================================
echo   Si ves un error arriba, copialo y pasaselo al asistente.
echo.
pause
