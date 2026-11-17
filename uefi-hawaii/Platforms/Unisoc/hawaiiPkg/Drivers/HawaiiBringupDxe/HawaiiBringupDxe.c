/*
  Hawaii Bring-up probe DXE driver.

  At EndOfDxe, prints a banner via SerialPortLib (UART1 + framebuffer),
  then resets the system via PSCI SYSTEM_RESET so cboot rolls back to
  Android and the ramoops log can be read.

  Without this, a firmware that reaches BDS just sits there waiting for
  a key press, which is indistinguishable from a hang on a black screen.
*/

#include <Uefi.h>
#include <Library/UefiDriverEntryPoint.h>
#include <Library/DebugLib.h>
#include <Library/SerialPortLib.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Protocol/LoadedImage.h>

EFI_STATUS
EFIAPI
BringupDxeEntryPoint (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  return EFI_SUCCESS;
}

EFI_STATUS
EFIAPI
BringupEndOfDxe (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  DEBUG ((DEBUG_INFO, "hawaii: EndOfDxe reached - resetting to Android\n"));
  SerialPortWrite ((UINT8 *)"\r\n[hawaii] EndOfDxe - resetting to Android\r\n",
                   sizeof ("\r\n[hawaii] EndOfDxe - resetting to Android\r\n") - 1);

  //
  // PSCI SYSTEM_RESET via ArmPkg.  Resets the SoC, cboot loads Android from slot b.
  //
  SystemTable->RuntimeServices->ResetSystem (EfiResetCold, EFI_SUCCESS, 0, NULL);

  return EFI_SUCCESS;
}