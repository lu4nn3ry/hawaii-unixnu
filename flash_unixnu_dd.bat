@echo off
chcp 65001 >nul
set ADB="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe"
set FASTBOOT="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\fastboot.exe"

echo ========================================
echo  Gravar boot.img do UniXNU no boot_a
echo ========================================
echo.

echo [1/3] Gravando imagem via cat > /dev/block/by-name/boot_a...
%ADB% shell su -c "cat /data/local/tmp/boot_unixnu.img > /dev/block/by-name/boot_a"
if errorlevel 1 (
    echo ERRO: Falha ao gravar em boot_a.
    pause
    exit /b 1
)

echo.
echo [2/3] Verificando hash de read-back do boot_a...
%ADB% shell su -c "cat /dev/block/by-name/boot_a > /data/local/tmp/boot_a_readback.img"
%ADB% pull /data/local/tmp/boot_a_readback.img D:\GitHub\hawaii-unixnu\extracted\boot_a_readback.img

echo.
echo [3/3] Comparando hashes...
for /f "tokens=1 delims= " %%a in ('%ADB% shell su -c "sha256sum /data/local/tmp/boot_a_readback.img"') do set ADB_HASH=%%a
for /f "tokens=1 delims= " %%a in ('sha256sum D:\GitHub\hawaii-unixnu\out\hawaii\boot\boot_unixnu_signed.img') do set HOST_HASH=%%a

echo Hash do device: %ADB_HASH%
echo Hash do host:   %HOST_HASH%

if "%ADB_HASH%"=="%HOST_HASH%" (
    echo.
    echo VERIFY OK - Hashes correspondem!
) else (
    echo.
    echo AVISO - Hashes diferem!
)

echo.
echo [4/4] Trocando slot para 'a' via fastboot...
%FASTBOOT% set_active a
if errorlevel 1 (
    echo AVISO: Nao foi possivel trocar slot via fastboot.
    echo   Coloque o device em modo fastboot e execute manualmente:
    echo   fastboot set_active a
    echo   fastboot reboot
    pause
    exit /b 0
)

%FASTBOOT% reboot
echo.
echo ========================================
echo  Gravacao concluida!
echo ========================================
echo.
echo MONITORE A TELA do dispositivo para ver:
echo   - Barra verde (DarwinBoot handoff)
echo   - Diagnostic page (estagios de boot)
echo   - build-tag=hawaii-001
echo   - Panic screen (se houver erro)
echo.
pause
