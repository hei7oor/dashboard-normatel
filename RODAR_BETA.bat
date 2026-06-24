@echo off
echo ============================================
echo  Dashboard Normatel - VERSAO BETA
echo  (recursos novos em teste)
echo ============================================
echo.
echo Acesse no navegador: http://localhost:8502
echo Para fechar: pressione Ctrl+C nesta janela
echo ============================================
echo.

python -m streamlit run app_beta.py --server.port 8502
pause
