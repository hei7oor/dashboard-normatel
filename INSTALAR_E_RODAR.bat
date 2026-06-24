@echo off
echo ============================================
echo  Dashboard Planejamento - Produttivo
echo  Instalacao e inicializacao automatica
echo ============================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale em: python.org/downloads
    echo Marque "Add Python to PATH" na instalacao
    pause
    exit /b 1
)

echo [1/3] Python encontrado. Instalando dependencias...
pip install -r requirements.txt

echo.
echo [2/3] Dependencias instaladas!
echo.
echo [3/3] Iniciando o Dashboard...
echo.
echo ============================================
echo  Acesse no navegador: http://localhost:8501
echo  Para fechar: pressione Ctrl+C nesta janela
echo ============================================
echo.

python -m streamlit run app.py
pause
