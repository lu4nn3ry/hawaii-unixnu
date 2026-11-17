@echo off
chcp 65001 >nul
echo ========================================
echo  Reboot para bootloader - Moto E32
echo ========================================
echo.

set ADB="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe"
set FASTBOOT="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\fastboot.exe"
set BOOT_IMG="D:\GitHub\unixnu-core\out\hawaii\ipados-17.7.11-21H461\hawaii\boot\boot.img"

echo [1/2] Reiniciando dispositivo em modo bootloader...
%ADB% reboot bootloader
if errorlevel 1 (
    echo ERRO: Falha ao reiniciar em bootloader.
    pause
    exit /b 1
)

echo.
echo Aguardando 10 segundos para entrar em modo fastboot...
timeout /t 10 >nul

echo.
echo [2/2] Verificando modo fastboot...
%FASTBOOT% devices
if errorlevel 1 (
    echo ERRO: Dispositivo nao detectado em modo fastboot.
    echo   Coloque manualmente: desligue, depois Volume Diminuir + Power
    pause
    exit /b 1
)

echo.
echo Dispositivo em modo fastboot detectado!
echo.
echo Agora execute o boot do XNU:
echo   %FASTBOOT% boot %BOOT_IMG%
echo.
echo Ou execute o script:
echo   D:\GitHub\hawaii-unixnu\do_boot.bat
echo.
pause
