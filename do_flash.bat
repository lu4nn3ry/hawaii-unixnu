@echo off
chcp 65001 >nul
echo ========================================
echo  Flash boot_a - Moto E32 (UMS9230)
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
echo [2/2] Fazendo flash em boot_a...
%FASTBOOT% flash boot_a %BOOT_IMG%
if errorlevel 1 (
    echo ERRO: Falha no flash da particao boot_a.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  FLASH CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo  Agora reinicie o dispositivo:
echo    fastboot reboot
echo.
pause
