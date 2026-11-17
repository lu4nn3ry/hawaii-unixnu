@echo off
chcp 65001 >nul
echo ========================================
echo  Fastboot boot - Moto E32 (UMS9230)
echo ========================================
echo.

set FASTBOOT="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\fastboot.exe"
set BOOT_IMG="D:\GitHub\unixnu-core\out\hawaii\ipados-17.7.11-21H461\hawaii\boot\boot.img"

echo [1/2] Verificando dispositivo em fastboot...
%FASTBOOT% devices
if errorlevel 1 (
    echo ERRO: Dispositivo nao detectado em modo fastboot.
    pause
    exit /b 1
)

echo.
echo [2/2] Carregando boot.img via fastboot boot (temporario, nao grava na flash)...
%FASTBOOT% boot %BOOT_IMG%
if errorlevel 1 (
    echo ERRO: Falha ao carregar boot.img.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  BOOT IMG CARREGADO COM SUCESSO!
echo ========================================
echo.
echo  O dispositivo esta rodando o kernel XNU.
echo  Monitore UART1 (115200n8) para logs de boot.
echo.
pause
