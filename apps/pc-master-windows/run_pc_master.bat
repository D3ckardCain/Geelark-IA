@echo off
setlocal
pushd "%~dp0"
set "VENV_PYW=%~dp0..\..\.venv\Scripts\pythonw.exe"
if exist "%VENV_PYW%" goto launch_venv
where pyw >nul 2>nul
if errorlevel 1 goto missing_python
start "" pyw -3 "%~dp0pc_master.py"
goto check_start

:launch_venv
start "" "%VENV_PYW%" "%~dp0pc_master.py"

:check_start
if errorlevel 1 goto launch_failed
popd
exit /b 0

:missing_python
echo No se encontro Python para ventanas. Instala Python 3.11 o posterior con el lanzador pyw.
goto failure

:launch_failed
echo No se pudo abrir PC-MASTER. Revisa la instalacion de Python.

:failure
popd
pause
exit /b 1
