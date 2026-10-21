@echo off
setlocal
pushd "%~dp0"
set "VENV_PY=%~dp0..\..\.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
  "%VENV_PY%" pc_master.py
  set "APP_EXIT=%ERRORLEVEL%"
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    echo No se encontro Python. Instala Python 3.11 o posterior desde python.org.
    popd
    pause
    exit /b 1
  )
  py -3 pc_master.py
  set "APP_EXIT=%ERRORLEVEL%"
)
if not "%APP_EXIT%"=="0" (
  echo PC-MASTER se cerro con un error. Revisa README.md.
  pause
)
popd
endlocal
