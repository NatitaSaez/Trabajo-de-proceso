@echo off
setlocal

REM --- Ubica el directorio base del proyecto sin importar desde dónde se ejecute ---
set "ROOT=%~dp0"
pushd "%ROOT%"

echo [1/3] Verificando dependencias...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo Error: no se pudo ejecutar python/pip. Verifica tu instalacion.
    goto :end
)
python -m pip install -r "interfaz_usuario\requirements.txt"
if errorlevel 1 (
    echo Error al instalar dependencias de la interfaz.
    goto :end
)

echo [2/3] Compilando la aplicacion Dash...
python -m py_compile "interfaz_usuario\app.py"
if errorlevel 1 (
    echo Error durante la compilacion de interfaz_usuario\app.py.
    goto :end
)

echo [3/3] Levantando la GUI en http://127.0.0.1:8050 ...
python "interfaz_usuario\app.py"

:end
popd
endlocal
