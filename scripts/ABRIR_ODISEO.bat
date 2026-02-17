@echo off
title ODISEO | SISTEMA DE CONTROL
color 0A
mode con: cols=100 lines=30

:inicio
cls
echo ===============================================================================
echo   SISTEMA ODISEO | VUELOS BRASIL MARZO 2026
echo ===============================================================================
echo.
echo   [!] Objetivo: BUE - FLN (8-12 Marzo)
echo   [!] Iniciando Motores (Python)...
echo.

:: Asegurar directorio correcto
cd /d "%~dp0"

:: Ejecutar Sistema
python -u ODISEO_SYSTEM.py

:: Si llega aqui es que el script terminó o crasheó
echo.
echo   [!] CRASH DETECTADO O FIN DE EJECUCION.
echo   [!] Presiona una tecla para reiniciar o Cierra esta ventana.
pause
goto inicio
