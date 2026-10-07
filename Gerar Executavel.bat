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

echo Instalando as ferramentas necessarias para compilar (so da primeira vez)...
echo.
"%PYTHON_CMD%" -m pip install --user pandas openpyxl python-docx pyinstaller

echo.
echo ==========================================================
echo Compilando o programa num arquivo .exe unico.
echo Isso pode demorar alguns minutos - eh normal aparecer bastante
echo texto passando na tela.
echo ==========================================================
echo.
"%PYTHON_CMD%" -m PyInstaller --onefile --windowed --name "GeradorDeEntregas" --hidden-import=openpyxl.cell._writer app.py

echo.
if exist "dist\GeradorDeEntregas.exe" (
    echo ==========================================================
    echo PRONTO! O programa final esta aqui:
    echo   %cd%\dist\GeradorDeEntregas.exe
    echo.
    echo Copie so ESSE ARQUIVO .exe para o computador de quem for usar
    echo - nao precisa levar mais nada, nem instalar Python la.
    echo.
    echo Na primeira vez que abrir, um arquivo "config.ini" vai ser
    echo criado do lado dele - eh nele que se edita o caminho das
    echo planilhas, se precisar (com o Bloco de Notas, normalmente).
    echo ==========================================================
) else (
    echo Algo deu errado na compilacao. Role a tela para cima e veja
    echo a mensagem de erro em vermelho.
)
popd
pause
