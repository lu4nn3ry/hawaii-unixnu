# hawaii-startup.nsh - UEFI Shell auto-run script for Moto E32 (hawaii / UMS9230)
#
# The Shell runs this from the FV (fs0:).  UniXNUDxe registers a Boot####
# option for UniXNU.efi and moves it to the front of BootOrder, so BDS
# starts the menu automatically.  This script is a fallback for when the
# boot option is not yet registered.

if not exist fs0:\EFI\UniXNU\unixnu.toml then
  echo No UniXNU payload found.
  echo Listing filesystems:
  fsmap
else
  echo UniXNU payload found, starting...
  fs0:\EFI\UniXNU\UniXNU.efi
endif