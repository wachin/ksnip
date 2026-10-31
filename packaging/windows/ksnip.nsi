; NSIS installer for ksnip-pyqt6.
;
; Structure follows the Lucio IVA Calculator installer: MUI v1 pages with a
; components page, header and welcome bitmaps, XPStyle, four sections and ZLIB
; compression. That installer measured 0/68 on VirusTotal.
;
; Run this script from the directory that contains the payload folder
; (ksnip-pyqt6), LICENSE, ksnip.ico and the two .bmp files. The workflow stages
; all of them before calling makensis. VERSION must be a four-part numeric
; version (for example 0.1.1.0).

Unicode true
!include "MUI.nsh"

!ifndef VERSION
  !define VERSION "0.1.1.0"
!endif
!ifndef INSTALLER_NAME
  !define INSTALLER_NAME "ksnip-pyqt6-setup.exe"
!endif
!ifndef PAYLOAD_DIR
  !define PAYLOAD_DIR "ksnip-pyqt6"
!endif

!define APP_NAME "ksnip-pyqt6"
!define APP_DIR "ksnip-pyqt6"
!define APP_EXE "ksnip-pyqt6.exe"
!define COMPANY_NAME "ksnip"
!define COPYRIGHT "Copyright (c) 2026 ksnip contributors"
!define DESCRIPTION "Screenshot and annotation tool"
!define LICENSE_TXT "LICENSE"
!define WEB_SITE "https://github.com/ksnip/ksnip"

VIFileVersion "${VERSION}"
VIProductVersion "${VERSION}"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${COMPANY_NAME}"
VIAddVersionKey "LegalCopyright" "${COPYRIGHT}"
VIAddVersionKey "FileDescription" "${DESCRIPTION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "InternalName" "${APP_NAME} Installer"
VIAddVersionKey "OriginalFilename" "${INSTALLER_NAME}"

SetCompressor ZLIB
Name "${APP_NAME}"
Caption "${APP_NAME}"
OutFile "${INSTALLER_NAME}"
BrandingText "${APP_NAME}"
XPStyle on
RequestExecutionLevel user
InstallDir "$LOCALAPPDATA\Programs\${APP_DIR}"
InstallDirRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation"
Icon "ksnip.ico"
UninstallIcon "ksnip.ico"

!define MUI_ABORTWARNING
!define MUI_ICON "ksnip.ico"
!define MUI_UNICON "ksnip.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "nsis-header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "nsis-welcome.bmp"
!define MUI_WELCOMEPAGE_TITLE "$(WelcomeTitle)"
!define MUI_WELCOMEPAGE_TEXT "$(WelcomeText)"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LICENSE_TXT}"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "$(RunApp)"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "English"

LangString WelcomeTitle ${LANG_SPANISH} "Bienvenido a ksnip-pyqt6"
LangString WelcomeTitle ${LANG_ENGLISH} "Welcome to ksnip-pyqt6"
LangString WelcomeText ${LANG_SPANISH} "Este asistente instalara ksnip-pyqt6, una herramienta de captura de pantalla y anotacion.$\r$\n$\r$\nPuedes elegir los accesos directos que deseas crear antes de instalar.$\r$\n$\r$\nPresiona Siguiente para continuar."
LangString WelcomeText ${LANG_ENGLISH} "This wizard will install ksnip-pyqt6, a screenshot and annotation tool.$\r$\n$\r$\nYou can choose which shortcuts to create before installing.$\r$\n$\r$\nClick Next to continue."
LangString RunApp ${LANG_SPANISH} "Iniciar ksnip-pyqt6"
LangString RunApp ${LANG_ENGLISH} "Start ksnip-pyqt6"
LangString SectionMain ${LANG_SPANISH} "Programa principal"
LangString SectionMain ${LANG_ENGLISH} "Main program"
LangString SectionStartMenu ${LANG_SPANISH} "Accesos en el menu Inicio"
LangString SectionStartMenu ${LANG_ENGLISH} "Start Menu shortcuts"
LangString SectionDesktop ${LANG_SPANISH} "Acceso directo en el Escritorio"
LangString SectionDesktop ${LANG_ENGLISH} "Desktop shortcut"
LangString SectionWebsite ${LANG_SPANISH} "Enlace al sitio web"
LangString SectionWebsite ${LANG_ENGLISH} "Website link"

Function .onInit
  System::Call "kernel32::GetUserDefaultUILanguage() i .r0"
  IntOp $1 $0 & 0x3ff
  IntCmp $1 9 0 +2 +2
    StrCpy $LANGUAGE ${LANG_ENGLISH}
  IntCmp $1 10 0 +2 +2
    StrCpy $LANGUAGE ${LANG_SPANISH}
FunctionEnd

Function un.onInit
  System::Call "kernel32::GetUserDefaultUILanguage() i .r0"
  IntOp $1 $0 & 0x3ff
  IntCmp $1 9 0 +2 +2
    StrCpy $LANGUAGE ${LANG_ENGLISH}
  IntCmp $1 10 0 +2 +2
    StrCpy $LANGUAGE ${LANG_SPANISH}
FunctionEnd

Section "$(SectionMain)" SecMain
SectionIn RO
SetOverwrite ifnewer
SetOutPath "$INSTDIR"
File /r "${PAYLOAD_DIR}\*.*"
WriteUninstaller "$INSTDIR\uninstall.exe"
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${VERSION}"
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${COMPANY_NAME}"
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation" "$INSTDIR"
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${WEB_SITE}"
WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
SectionEnd

Section "$(SectionStartMenu)" SecStartMenu
SetOutPath "$INSTDIR"
CreateDirectory "$SMPROGRAMS\${APP_NAME}"
CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}"
CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe"
SectionEnd

Section "$(SectionDesktop)" SecDesktop
SetOutPath "$INSTDIR"
CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "$(SectionWebsite)" SecWebsite
SetOutPath "$INSTDIR"
CreateDirectory "$SMPROGRAMS\${APP_NAME}"
WriteIniStr "$INSTDIR\${APP_NAME} website.url" "InternetShortcut" "URL" "${WEB_SITE}"
CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME} Website.lnk" "$INSTDIR\${APP_NAME} website.url"
SectionEnd

Section Uninstall
RmDir /r "$INSTDIR"
Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
Delete "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk"
Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME} Website.lnk"
Delete "$DESKTOP\${APP_NAME}.lnk"
RmDir "$SMPROGRAMS\${APP_NAME}"
DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
