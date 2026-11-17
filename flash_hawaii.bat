@echo off
chcp 65001 >nul
title Flash Hawaii - Moto E32 (UMS9230)

echo ========================================
echo  Port Hawaii - Flash boot.img
echo ========================================
echo.

set ADB="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe"
set FASTBOOT="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\fastboot.exe"
set BOOT_IMG="D:\GitHub\unixnu-core\out\hawaii\ipados-17.7.11-21H461\hawaii\boot\boot.img"

:: Usar porta 5038 para evitar conflito com WSL
set ANDROID_ADB_SERVER_PORT=5038

echo [1/4] Verificando adb...
%ADB% -P 5038 devices
if errorlevel 1 (
    echo ERRO: adb nao encontrado.
    pause
    exit /b 1
)

echo.
echo [2/4] Reiniciando dispositivo em modo bootloader...
%ADB% -P 5038 reboot bootloader
timeout /t 10 >nul

echo.
echo [3/4] Verificando modo fastboot...
%FASTBOOT% devices
if errorlevel 1 (
    echo ERRO: Dispositivo nao detectado em modo fastboot.
    echo.
    echo   Coloque o dispositivo em modo fastboot manualmente:
    echo   - Desligue o aparelho
    echo   - Pressione Volume Diminuir + Power simultaneamente
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Fazendo flash em boot_a...
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
echo  Ou deixe em modo fastboot e monitore UART1 (115200n8)
echo  para capturar logs de boot do kernel XNU.
echo.
pause
%FASTBOOT% reboot
