@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo No se encontro el lanzador py de Python.
  echo Instala Python 3.11 o posterior desde python.org y activa la opcion Add Python to PATH.
  pause
  exit /b 1
)
py -3 pc_master.py
if errorlevel 1 (
  echo PC-MASTER se cerro con un error. Revisa el manual README.md.
  pause
)
endlocal
