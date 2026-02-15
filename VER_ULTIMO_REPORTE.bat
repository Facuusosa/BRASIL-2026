@echo off
setlocal
cd /d "%~dp0"
echo Buscando reporte HTML mas reciente...
for /f "delims=" %%I in ('dir "data\flybondi_logs\reporte_*.html" /b /o:-d /t:c') do (
    echo Abriendo: %%I
    start "" "data\flybondi_logs\%%I"
    goto :fin
)
echo No se encontraron reportes.
pause
:fin
endlocal
