@echo off
chcp 65001 >nul
set ADB="C:\Users\luann\AppData\Local\Android\Sdk\platform-tools\adb.exe"

echo ========================================
echo  Coletar dados do dispositivo (root)
echo ========================================
echo.

echo [1/6] Capturando cmdline...
%ADB% shell su -c "cat /proc/cmdline > /data/local/tmp/cmdline.txt"

echo [2/6] Capturando iomem...
%ADB% shell su -c "cat /proc/iomem > /data/local/tmp/iomem.txt"

echo [3/6] Capturando DTB...
%ADB% shell su -c "cat /sys/firmware/fdt > /data/local/tmp/hawaii-live.dtb"

echo [4/6] Capturando boot_b...
%ADB% shell su -c "cat /dev/block/by-name/boot_b > /data/local/tmp/boot_b-original.img"

echo [5/6] Capturando uboot_b...
%ADB% shell su -c "cat /dev/block/by-name/uboot_b > /data/local/tmp/uboot_b.img"

echo [6/6] Verificando arquivos...
%ADB% shell su -c "ls -la /data/local/tmp/"

echo.
echo Puxando arquivos para o host...
%ADB% pull /data/local/tmp/cmdline.txt D:\GitHub\hawaii-unixnu\extracted\cmdline.txt
%ADB% pull /data/local/tmp/iomem.txt D:\GitHub\hawaii-unixnu\extracted\iomem.txt
%ADB% pull /data/local/tmp/hawaii-live.dtb D:\GitHub\hawaii-unixnu\extracted\hawaii-live.dtb
%ADB% pull /data/local/tmp/boot_b-original.img D:\GitHub\hawaii-unixnu\extracted\boot_b-original.img
%ADB% pull /data/local/tmp/uboot_b.img D:\GitHub\hawaii-unixnu\extracted\uboot_b.img

echo.
echo Concluido!
