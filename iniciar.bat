@echo off
title LoL Translator

echo  Iniciando LoL Screen Translator...
echo.
python lol_translator.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Ocorreu um erro. Execute instalar.bat primeiro.
    pause
)
