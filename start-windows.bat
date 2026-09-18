@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:usepython
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:run
".venv\Scripts\python.exe" -c "import flask, waitress" >nul 2>nul
if errorlevel 1 goto install
".venv\Scripts\python.exe" run.py
goto end
:failed
echo Setup failed. Install Python 3.12+ and JDK 17+, then restart VS Code.
:end
pause
