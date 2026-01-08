@echo off
echo Ejecutando main.py desde el entorno virtual...

:: Accedemos directamente al ejecutable de python dentro del venv
venv\Scripts\python.exe ./core/effects.py

echo.
echo Ejecucion terminada.
pause