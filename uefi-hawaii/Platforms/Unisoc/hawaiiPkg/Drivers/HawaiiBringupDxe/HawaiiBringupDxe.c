/*
  Hawaii Bring-up probe DXE driver.

  Registers an EndOfDxe event callback. When DXE dispatch finishes, the
  callback prints a banner via SerialPortLib and resets the system via
  PSCI SYSTEM_RESET, so cboot rolls back to Android and the ramoops log
  is readable.

  Without this, a firmware that reaches BDS just sits there waiting for
  a key press, which is indistinguishable from a hang on a black screen.
*/

#include <Uefi.h>
#include <Library/UefiDriverEntryPoint.h>
#include <Library/DebugLib.h>
#include <Library/SerialPortLib.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/UefiRuntimeServicesTableLib.h>
#include <Guid/EventGroup.h>

STATIC EFI_EVENT  mEndOfDxeEvent;

STATIC
VOID
EFIAPI
BringupEndOfDxe (
  IN EFI_EVENT  Event,
  IN VOID       *Context
  )
{
  DEBUG ((DEBUG_INFO, "hawaii: EndOfDxe reached - resetting to Android\n"));
  SerialPortWrite ((UINT8 *)"\r\n[hawaii] EndOfDxe - resetting to Android\r\n",
                   sizeof ("\r\n[hawaii] EndOfDxe - resetting to Android\r\n") - 1);

  gRT->ResetSystem (EfiResetCold, EFI_SUCCESS, 0, NULL);
}

EFI_STATUS
EFIAPI
BringupDxeEntryPoint (
  IN EFI_HANDLE        ImageHandle,
  IN EFI_SYSTEM_TABLE  *SystemTable
  )
{
  return gBS->CreateEventEx (
    EVT_NOTIFY_SIGNAL,
    TPL_CALLBACK,
    BringupEndOfDxe,
    NULL,
    &gEfiEndOfDxeEventGroupGuid,
    &mEndOfDxeEvent
    );
}