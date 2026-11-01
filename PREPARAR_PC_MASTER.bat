@echo off
setlocal
pushd "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Se necesita Python 3.11 o posterior con Tkinter y el lanzador py.
  popd
  pause
  exit /b 1
)
echo Preparando el entorno local desde esta descarga de GitHub...
py -3 "apps\pc-master-windows\setup_pc_master.py"
if errorlevel 1 (
  echo La preparacion se detuvo. Revisa el mensaje anterior.
  pause
  popd
  exit /b 1
)
popd
endlocal
