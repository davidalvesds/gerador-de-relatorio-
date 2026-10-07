@echo off
pushd "%~dp0" 2>nul
if errorlevel 1 (
    echo Nao consegui acessar esta pasta.
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=py"
    ) else (
        set "PYTHON_CMD="
        for /f "delims=" %%i in ('dir /b /s "%LocalAppData%\Programs\Python\python.exe" 2^>nul') do set "PYTHON_CMD=%%i"
    )
)

if not defined PYTHON_CMD (
    echo Nao encontrei o Python instalado neste computador.
    echo Instale o Python em: https://www.python.org/downloads/
    echo IMPORTANTE: marque a caixinha "Add python.exe to PATH" na primeira tela da instalacao.
    echo Depois rode novamente este arquivo.
    popd
    pause
    exit /b 1
)

"%PYTHON_CMD%" app.py
popd
pause
