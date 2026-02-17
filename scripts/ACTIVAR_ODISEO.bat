@echo off
title ODISEO | SISTEMA DE CAZA AUTOMATICO
color 0A
mode con: cols=100 lines=30

:inicio
cls
echo ===============================================================================
echo   ODISEO ESTA EN LINEA - BUSCANDO VUELOS (CAMPAÑA BRASIL)
echo ===============================================================================
echo.
echo   [!] Objetivo: BUE -> FLN (Marzo 8-12)
echo   [!] Sistema: ODISEO V3 (DAEMON + DASHBOARD)
echo   [!] Estado: VIGILANCIA ACTIVA (Telegram + HTML)
echo.

:: Ejecutar el Sistema Central
python ODISEO_SYSTEM.py

:: Verificar si hubo éxito (El script debe devolver codigo de error si falla)
if %ERRORLEVEL% EQU 0 (
    echo.
    echo   [OK] CICLO COMPLETADO. REPOSANDO 60 SEGUNDOS...
    timeout /t 60 >nul
    goto inicio
) else (
    echo.
    echo   [X] ERROR TACTICO DETECTADO (CRASH). REINICIANDO SISTEMA EN 10 SEGUNDOS...
    timeout /t 10
    goto inicio
)
