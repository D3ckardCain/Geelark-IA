@echo off
cd /d "%~dp0"
where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw -3 "%~dp0control_android_lab.py"
  exit /b
)
where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "%~dp0control_android_lab.py"
  exit /b
)
echo No se encuentra Python para Windows. Se necesita Python 3.11 o posterior con Tkinter.
pause
