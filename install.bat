@echo off
echo Creando entorno virtual...
python -m venv venv

echo Instalando dependencias...
:: El comando /c cierra el proceso al terminar, permitiendo que el script siga
cmd /c "venv\Scripts\activate && pip install -r requirements.txt"

echo.
echo Proceso finalizado.
pause