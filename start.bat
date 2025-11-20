@echo off
echo ========================================
echo   Tax Gold - Sistema de Notas Fiscais
echo ========================================
echo.

REM Ativa o ambiente virtual
if exist venv\Scripts\activate.bat (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
) else (
    echo AVISO: Ambiente virtual nao encontrado!
    echo Execute: python -m venv venv
    echo.
)

REM Verifica se as dependências estão instaladas
echo Verificando dependencias...
python -c "import django" 2>nul
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

REM Executa migrações se necessário
echo.
echo Verificando banco de dados...
python manage.py migrate --check 2>nul
if errorlevel 1 (
    echo Executando migracoes...
    python manage.py migrate
)

REM Inicia o servidor
echo.
echo ========================================
echo   Iniciando servidor de desenvolvimento
echo ========================================
echo.
echo Acesse: http://localhost:8000/
echo Admin: http://localhost:8000/admin/
echo.
echo Pressione CTRL+C para parar o servidor
echo.

python manage.py runserver
