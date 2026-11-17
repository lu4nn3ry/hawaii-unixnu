@echo off
chcp 65001 >nul
echo ========================================
echo  Preparar boot.img com padding para dd
echo ========================================
echo.

set BOOT_IMG="D:\GitHub\unixnu-core\out\hawaii\ipados-17.7.11-21H461\hawaii\boot\boot.img"
set PADDED_IMG="D:\GitHub\hawaii-unixnu\boot_padded.img"

:: Verificar tamanho atual
for %%F in (%BOOT_IMG%) do set SIZE=%%~zF
echo Tamanho atual: %SIZE% bytes

:: Calcular padding para múltiplo de 4096
set /a BLOCK=4096
set /a PADDED=(%SIZE% + %BLOCK% - 1) / %BLOCK% * %BLOCK%
set /a PADDING=%PADDED% - %SIZE%
echo Tamanho com padding: %PADDED% bytes
echo Padding necessario: %PADDING% bytes

:: Fazer padding com zeros
copy %BOOT_IMG% %PADDED_IMG% >nul
if %PADDING% gtr 0 (
    echo Adicionando padding de zeros...
    >> %PADDED_IMG% (
        for /L %%i in (1,1,%PADDING%) do set /p "=0" <nul
    )
)

for %%F in (%PADDED_IMG%) do set PADSIZE=%%~zF
echo Tamanho final: %PADSIZE% bytes
echo.

:: Fazer push para o device
echo Fazendo push para /data/local/tmp/boot_custom.img...
"C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe" push %PADDED_IMG% /data/local/tmp/boot_custom.img
if errorlevel 1 (
    echo ERRO: Falha no push.
    pause
    exit /b 1
)

echo.
echo Push concluido!
echo.
echo Agora execute no device (ja tem root):
echo   sh /data/local/tmp/flash_boot_a.sh /data/local/tmp/boot_custom.img
echo.
echo Depois troque de slot:
echo   fastboot set_active a
echo   fastboot reboot
echo.
pause
