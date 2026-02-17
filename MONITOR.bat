@echo off
cd /d "%~dp0"
title ODISEO | MONITOR BRASIL
color 0A

echo ===============================================================================
echo   INICIANDO MONITOR ODISEO...
echo ===============================================================================
echo.
echo   [!] Si ves errores, avisa al Operador.
echo   [!] Para detener: Cierra esta ventana.
echo.

:: Detectar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo   [!] Activando entorno virtual...
    call venv\Scripts\activate.bat
)

:: Ejecutar Python asegurando que la ventana no se cierre
python -u src\ODISEO_SYSTEM.py

:: Si python falla o termina, esperamos
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   [ERROR CRITICO] Python se cerro inesperadamente.
    echo   Posibles causas:
    echo     1. No tienes libreria curl_cffi instalada? (pip install curl_cffi)
    echo     2. Error de sintaxis en el script.
    echo.
    pause
)

pause
