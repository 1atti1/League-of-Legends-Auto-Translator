@echo off
title LoL Translator - Instalacao

echo.
echo  =========================================
echo   LoL Screen Translator - Instalacao
echo  =========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Python nao encontrado!
    echo  Baixe em: https://www.python.org/downloads/
    echo  IMPORTANTE: Marque "Add Python to PATH" na instalacao!
    pause
    exit /b 1
)
echo  [OK] Python encontrado!

echo.
echo  Atualizando pip...
python -m pip install --upgrade pip --quiet

echo.
echo  Instalando dependencias...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo  [ERRO] Falha ao instalar dependencias!
    pause
    exit /b 1
)
echo  [OK] Dependencias instaladas!

echo.
echo  Verificando Tesseract OCR...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  =========================================
    echo   ATENCAO: Tesseract nao encontrado!
    echo  =========================================
    echo.
    echo  1. Baixe o instalador em:
    echo     https://github.com/UB-Mannheim/tesseract/wiki
    echo     arquivo: tesseract-ocr-w64-setup-xxx.exe
    echo.
    echo  2. Durante a instalacao marque: Add to PATH
    echo.
    echo  3. Reinicie este instalador apos instalar.
    echo.
    echo  Abrindo o link no navegador...
    start https://github.com/UB-Mannheim/tesseract/wiki
    pause
    exit /b 1
)
echo  [OK] Tesseract encontrado!

echo.
echo  =========================================
echo   Instalacao concluida com sucesso!
echo   Execute iniciar.bat para comecar.
echo  =========================================
echo.
pause
