; HaiBot Desktop NSIS installer. Run makensis from repo root after
; building dist/win-unpacked (see scripts/pack/build_win.ps1).
; Usage: makensis /DHAIBOT_VERSION=1.2.3 /DOUTPUT_EXE=dist\HaiBot-Setup-1.2.3.exe scripts\pack\haibot_desktop.nsi

!include "MUI2.nsh"
!define MUI_ABORTWARNING
; Use custom icon from unpacked env (copied by build_win.ps1)
!define MUI_ICON "${UNPACKED}\icon.ico"
!define MUI_UNICON "${UNPACKED}\icon.ico"

!ifndef HAIBOT_VERSION
  !define HAIBOT_VERSION "0.0.0"
!endif
!ifndef OUTPUT_EXE
  !define OUTPUT_EXE "dist\HaiBot-Setup-${HAIBOT_VERSION}.exe"
!endif

Name "HaiBot Desktop"
OutFile "${OUTPUT_EXE}"
InstallDir "$LOCALAPPDATA\HaiBot"
InstallDirRegKey HKCU "Software\HaiBot" "InstallPath"
RequestExecutionLevel user

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

; Pass /DUNPACKED=full_path from build_win.ps1 so path works when cwd != repo root
!ifndef UNPACKED
  !define UNPACKED "dist\win-unpacked"
!endif

Section "HaiBot Desktop" SEC01
  SetOutPath "$INSTDIR"
  File /r "${UNPACKED}\*.*"
  WriteRegStr HKCU "Software\HaiBot" "InstallPath" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Main shortcut - uses VBS to hide console window
  CreateShortcut "$SMPROGRAMS\HaiBot Desktop.lnk" "$INSTDIR\HaiBot Desktop.vbs" "" "$INSTDIR\icon.ico" 0
  CreateShortcut "$DESKTOP\HaiBot Desktop.lnk" "$INSTDIR\HaiBot Desktop.vbs" "" "$INSTDIR\icon.ico" 0
  
  ; Debug shortcut - shows console window for troubleshooting
  CreateShortcut "$SMPROGRAMS\HaiBot Desktop (Debug).lnk" "$INSTDIR\HaiBot Desktop (Debug).bat" "" "$INSTDIR\icon.ico" 0
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\HaiBot Desktop.lnk"
  Delete "$SMPROGRAMS\HaiBot Desktop (Debug).lnk"
  Delete "$DESKTOP\HaiBot Desktop.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\HaiBot"
SectionEnd
