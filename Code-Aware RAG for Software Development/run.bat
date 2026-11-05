@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  set PYTHON=py
) else (
  set PYTHON=python
)
%PYTHON% -m pip install --user -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Make sure Python 3.10+ and pip are installed.
  pause
  exit /b 1
)
echo.
echo Make sure Ollama is installed and the model is available:
echo   ollama pull qwen2.5-coder:3b
echo.
%PYTHON% app.py
pause
