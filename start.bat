@echo off
cd /d "%~dp0"
echo === SimCity Control Panel ===
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% -m pip install -r requirements.txt
%PY% app.py
pause
