##
#  APRIORI DXE dependency list for the Moto E32 (hawaii / UMS9230).
#
#  Everything listed here is generic EDK2 or SiliciumPkg.
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
##
APRIORI DXE {
  INF MdeModulePkg/Core/Dxe/DxeMain.inf
  INF MdeModulePkg/Universal/PCD/Dxe/Pcd.inf

  INF MdeModulePkg/Universal/ReportStatusCodeRouter/RuntimeDxe/ReportStatusCodeRouterRuntimeDxe.inf
  INF MdeModulePkg/Universal/StatusCodeHandler/RuntimeDxe/StatusCodeHandlerRuntimeDxe.inf
  INF MdeModulePkg/Core/RuntimeDxe/RuntimeDxe.inf
  INF ArmPkg/Drivers/CpuDxe/CpuDxe.inf
  INF ArmPkg/Drivers/ArmGicDxe/ArmGicDxe.inf
  INF EmbeddedPkg/MetronomeDxe/MetronomeDxe.inf
  INF ArmPkg/Drivers/TimerDxe/TimerDxe.inf

  INF MdeModulePkg/Universal/Variable/RuntimeDxe/VariableRuntimeDxe.inf
  INF MdeModulePkg/Universal/ResetSystemRuntimeDxe/ResetSystemRuntimeDxe.inf
  INF MdeModulePkg/Universal/WatchdogTimerDxe/WatchdogTimer.inf
  INF EmbeddedPkg/EmbeddedMonotonicCounter/EmbeddedMonotonicCounter.inf
  INF EmbeddedPkg/RealTimeClockRuntimeDxe/RealTimeClockRuntimeDxe.inf
  INF MdeModulePkg/Universal/PrintDxe/PrintDxe.inf
  INF MdeModulePkg/Universal/DevicePathDxe/DevicePathDxe.inf
  INF MdeModulePkg/Universal/CapsuleRuntimeDxe/CapsuleRuntimeDxe.inf
  INF MdeModulePkg/Universal/HiiDatabaseDxe/HiiDatabaseDxe.inf
  INF MdeModulePkg/Universal/BdsDxe/BdsDxe.inf

  INF SiliciumPkg/Drivers/SimpleFbDxe/SimpleFbDxe.inf

  INF EmbeddedPkg/SimpleTextInOutSerial/SimpleTextInOutSerial.inf
  INF MdeModulePkg/Universal/Console/ConPlatformDxe/ConPlatformDxe.inf
  INF MdeModulePkg/Universal/Console/ConSplitterDxe/ConSplitterDxe.inf
  INF MdeModulePkg/Universal/Console/GraphicsConsoleDxe/GraphicsConsoleDxe.inf
}