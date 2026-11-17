Vendor Hardware Reference — Moto E32 (hawaii / UMS9230 / T606)
===========================================================

Source: dts/vendor_ref/moto_sc2730.dtsi (vendor PMIC dtsi)
Source: dts/proc_device_tree_root/ (live device tree capture)
Source: dts/vendor_ref/moto_m170-overlay.dts (vendor board overlay)

----------------------------------------------------------------
SC2730 PMIC Regulators (power-controller@1800)
----------------------------------------------------------------
Regulator        | Type   | Min uV      | Max uV      | Always-on
-----------------|--------|-------------|-------------|----------
vddcpu           | DCDC   | 200,000     | 1,596,875   | yes
vddgpu           | DCDC   | 200,000     | 1,596,875   | yes
vddcore          | DCDC   | 200,000     | 1,596,875   | yes
vddmodem         | DCDC   | 200,000     | 1,596,875   | yes
vddmem           | DCDC   | 400,000     | 1,593,750   | yes
vddmemq          | DCDC   | 400,000     | 1,596,875   | yes
vddgen0          | DCDC   | 1,220,000   | 2,410,625   | yes
vddgen1          | DCDC   | 850,000     | 1,643,750   | yes
vddsram          | DCDC   | 200,000     | 1,596,875   | yes
avdd18           | LDO    | 1,175,000   | 1,805,000   | yes
vddrf18          | LDO    | 1,175,000   | 1,805,000   | yes
vddcamio         | LDO    | 1,200,000   | 1,830,000   | no
vddwcn           | LDO    | 900,000     | 1,845,000   | no
vddcamd1         | LDO    | 900,000     | 1,365,000   | no
vddcamd0         | LDO    | 900,000     | 1,365,000   | no
vddrf1v25        | LDO    | 900,000     | 1,365,000   | yes
avdd12           | LDO    | 900,000     | 1,365,000   | yes
vddcama0         | LDO    | 1,200,000   | 3,750,000   | no
vddcama1         | LDO    | 1,200,000   | 3,750,000   | no
vddcammot        | LDO    | 1,200,000   | 3,750,000   | no
vddsim2          | LDO    | 1,200,000   | 3,750,000   | no
vddemmccore      | LDO    | 1,200,000   | 3,750,000   | no
vddsdcore        | LDO    | 1,200,000   | 3,750,000   | no
vddsdio          | LDO    | 1,200,000   | 3,750,000   | no
vdd28            | LDO    | 1,200,000   | 3,750,000   | yes
vddwifipa        | LDO    | 1,200,000   | 3,750,000   | no
vdd18_dcxo       | LDO    | 1,200,000   | 3,750,000   | yes
vddusb33         | LDO    | 1,200,000   | 3,750,000   | no
vddldo0          | LDO    | 1,200,000   | 3,750,000   | no
vddldo1          | LDO    | 1,200,000   | 3,750,000   | no
vddldo2          | LDO    | 1,200,000   | 3,750,000   | no
vddkpled         | LDO    | 1,200,000   | 3,750,000   | no

----------------------------------------------------------------
SC2730 PMIC Sub-devices
----------------------------------------------------------------
pmic_wdt         | watchdog@40      | sprd,sc2730-wdt
led-controller   | led-controller@180 | sprd,sc2730-bltc (red, green, blue LEDs)
rtc              | rtc@200          | sprd,sc2731-rtc (irq 1)
pmic_eic         | gpio@280         | sprd,sc2731-eic (GPIO controller, #gpio-cells=2)
efuse            | efuse@300        | sprd,sc2730-efuse (calibration data)
pmic_typec       | typec@380        | sprd,sc2730-typec
pmic_fchg        | fchg@400         | sprd,sc2730-fast-charger (status=disabled)
pmic_adc         | adc@504          | sprd,sc2730-adc
pmic_fgu         | fgu@c00          | sprd,sc2730-fgu (fuel-gauge, irq 3)
pmic_pd          | pd@e00           | sprd,sc27xx-pd (status=disabled)
sprd_audio_codec_ana | audio-codec@1000 | unisoc,sc2730-audio-codec (status=disabled)
syscon           | syscon@1800      | sprd,sc2731-syscon
refout           | refout@1800      | sprd,sc27xx-refout (refnum=5)
pmic_smpl        | smpl@1800        | sprd,sc27xx-smpl
poweroff         | poweroff@1820    | sprd,sc27xx-poweroff
pmic_tsensor     | tsensor@1b34     | sprd,sc27xx-tsensor
vibrator         | vibrator@1b90    | sprd,sc2730-vibrator
hw-reset         | hw-reset@1bc0    | sprd,sc27xx-7sreset

----------------------------------------------------------------
GPIO Keys (from live DT proc_device_tree_root/gpio-keys/)
----------------------------------------------------------------
Key            | GPIO[0] | GPIO[1] | GPIO[2] | linux,code | Name
---------------|---------|---------|---------|------------|------------
key-power      | 73      | 1       | 1       | 116        | Power Key (wakeup-source)
key-volumedown | 122     | 124     | 1       | 114        | Volume Down Key (wakeup-source)
key-volumeup   | 73      | 4       | 0       | 115        | Volume Up Key
key-google     | 122     | 126     | 1       | 249        | Google Key (wakeup-source)

----------------------------------------------------------------
Audio (from live DT)
----------------------------------------------------------------
sound@0        | compatible = "sprd,vbc-v4-codec-sc2730" (voice codec)
sound@1        | compatible = "sprd,i2s-null-codec" (I2S null codec)
audio-dsp-dump@0 | compatible = "sprd,audio-dsp-log" (mailbox, rxblocksize=0x2000)
audio-sipc     | compatible = "sprd,audio_sipc" (mailbox-core=5)
Vendor DTS: sprd_audio_codec_ana compatible="unisoc,sc2730-audio-codec" (reg=0x1000, status=disabled)

----------------------------------------------------------------
Display Panel (from live DT proc_device_tree_root/lcds/lcd_nt36525c_boe_mipi_fhd/)
----------------------------------------------------------------
Panel          | lcd_nt36525c_boe_mipi_fhd
Resolution     | 720 x 1600
Format         | rgb888
DSI lanes      | 4
DSI mode       | video mode (work-mode=1)
Clock          | 140,666,000 Hz
lcd_base       | 0x9e000000 (logobuffer)
Size           | 68 x 111 mm
DPI clk div    | 6
ESD check      | disabled
Timing0 (active): hfp=40, hbp=40, hsync=4, vfp=10, vbp=326, vsync=2
Timing1:         hfp=40, hbp=40, hsync=4, vfp=986, vbp=326, vsync=2

----------------------------------------------------------------
Wi-Fi (from live DT proc_device_tree_root/sprd-wlan/)
----------------------------------------------------------------
Chip           | sprd,sc2355-wifi (Unisoc SC2355 combo over SDIO)

----------------------------------------------------------------
GPU (from live DT proc_device_tree_root/sprd-marlin3/)
----------------------------------------------------------------
Chip           | sprd,marlin3 (Mali-G57 Valhall JM)
Reg            | 0x23100000 / 0x100000
IRQs           | GIC_SPI 60 x3 (JOB/MMU/GPU)
DVFS           | 1500-3300 MHz

----------------------------------------------------------------
Battery / Charger (from live DT proc_device_tree_root/battery/ + charger-manager/)
----------------------------------------------------------------
Battery        | NH50 5000mAh (Sunwoda/ATL)
Charger        | bq2597x + sc2730_fast_charger
Fuel gauge     | sc27xx-fgu


----------------------------------------------------------------
Touch Panel (from vendor overlay moto_m170-overlay.dts)
----------------------------------------------------------------
Touch driver include: tp/ums9230-spi3-gpio144-145-tp.dtsi
Bus: SPI3 (not I2C), GPIO reset/irq: 144/145
Touch disabled in bootargs: cit_tp=0x00
Vendor overlay does NOT enable a specific touch controller chip - uses generic SPI3 TP

----------------------------------------------------------------
I2C Bus Devices (from vendor overlay)
----------------------------------------------------------------
I2C3: status=okay
  aw9610x_sar@12: compatible=awinic,aw9610x_sar (SAR ADC), reg=0x12, irq-gpio=ap_gpio 176
I2C4: status=okay
  ucp1301_spk@58: compatible=sprd,ucp1301-spk (speaker), reg=0x58, reset-gpio=ap_gpio 167
  stm_vl53l0@52: compatible=st,stmvl53l0 (ToF sensor), reg=0x52, reset_gpio=168, irq_gpio=169
AON_I2C0: status=okay, clock-frequency=1000000

----------------------------------------------------------------
WCN / Wi-Fi / Bluetooth (from vendor overlay)
----------------------------------------------------------------
WCN reserved memory: wcn-mem@87000000, size=0x00800000 (8MB)
Wi-Fi chip: sprd,sc2355-wifi (Unisoc SC2355 combo over SDIO)
Firmware: /dev/block/by-name/wcnmodem (btwf), /dev/block/by-name/gnssmodem (gnss)

----------------------------------------------------------------
Backlight / Display Power (from vendor overlay)
----------------------------------------------------------------
Backlight: sprd_backlight (PWM)
  PWM: &pwms channel 2, period 40000Hz
  max-brightness-level: 924
  default-brightness-level: 262
  brightness-scale: 1023
  Note: m170 uses cabc_pwm, not pwm_backlight (commented out compatible)

----------------------------------------------------------------
Fingerprint (from vendor overlay)
----------------------------------------------------------------
Fingerprint: compatible=microarray,afs121
  fpint-gpios: &eic_async 29 0

----------------------------------------------------------------
Regulators forced always-on (from vendor overlay)
----------------------------------------------------------------
vddldo0: regulator-always-on
vddldo1: regulator-always-on
pmic_fgu: monitored-battery=&bat &bat2, sprd,calib-resistance-micro-ohms=5000, sprd,comp-resistance-mohm=15, fgu-capacity-track

----------------------------------------------------------------
Thermal (from vendor overlay)
----------------------------------------------------------------
board-thmzone: polling-delay-passive=0, polling-delay=0, thermal-sensors=&tboard_thermistor

----------------------------------------------------------------
Reserved Memory Map (from vendor overlay)
----------------------------------------------------------------
wcn-mem@87000000: size=0x00800000 (8MB) - Wi-Fi firmware
logobuffer@9e000000: size=0x00ab0000 - Framebuffer/logo
faceid-mem@ffa70000: size=0x00500000 - Face ID memory

----------------------------------------------------------------
GPIO Key Details (decoded from live DT)
----------------------------------------------------------------
key-power:      gpio=73 (0x49), flags=1, wakeup=1, linux,code=116 (KEY_POWER)
key-volumedown: gpio=122 (0x7a), flags=124 (0x7c), wakeup=1, linux,code=114 (KEY_VOLUMEDOWN)
key-volumeup:   gpio=73 (0x49), flags=4 (0x4), wakeup=0, linux,code=115 (KEY_VOLUMEUP)
key-google:     gpio=122 (0x7a), flags=126 (0x7e), wakeup=1, linux,code=249 (KEY_GOOGLE)
