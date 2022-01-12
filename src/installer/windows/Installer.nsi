SetCompressor /SOLID LZMA
!include MUI2.nsh
!include FileFunc.nsh
InstallDir "$PROGRAMFILES64\JamTools"
;InstallDirRegKey HKCU "Software\JamTools" "$PROGRAMFILES64\JamTools"
!define PRODUCT_NAME "JamTools"
!define PRODUCT_VERSION "0.13.55B"
Unicode True

;--------------------------------
;Perform Machine-level install, if possible

!define MULTIUSER_EXECUTIONLEVEL Highest
;Add support for command-line args that let uninstaller know whether to
;uninstall machine- or user installation:
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!include MultiUser.nsh
!include LogicLib.nsh

Function .onInit
  ReadRegStr $0 HKCU "Software\JamTools" ""
  ReadRegStr $6 HKCU "Software\JamTools" "bb"
  ${If} $0 == ""
  ${Else}
  StrCpy $INSTDIR $0
  MessageBox MB_OKCANCEL|MB_ICONQUESTION  "Jamtools$6已安装在$0 $\n继续安装可以直接覆盖或更换路径(将保留你的所有设置)" IDCANCEL Exit
  ${EndIf}
  killer::IsProcessRunning "JamTools.exe"
  Pop $R0
  IntCmp $R0 1 0 no_run
  MessageBox MB_OKCANCEL|MB_ICONQUESTION  "安装程序检测到 ${PRODUCT_NAME} 正在运行。$\r$\n$\r$\n点击 “确定” 强制关闭${PRODUCT_NAME}，继续安装。$\r$\n点击 “取消” 退出安装程序。" IDCANCEL Exit
  killer::KillProcess "JamTools.exe"
  Sleep 500
  killer::IsProcessRunning "JamTools.exe"
  Pop $R0
  IntCmp $R0 1 0 no_run
  Exit:
  Quit
  no_run:
  ;
  
  

FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "卸载${PRODUCT_NAME}及其组件？" IDYES +2
  Abort
  killer::IsProcessRunning "JamTools.exe"
  Pop $R0
  IntCmp $R0 1 0 no_run
  MessageBox MB_OKCANCEL|MB_ICONQUESTION  "卸载程序检测到 ${PRODUCT_NAME} 正在运行。$\r$\n$\r$\n点击 “确定” 强制关闭${PRODUCT_NAME}并立即卸载。$\r$\n点击 “取消” 退出卸载程序。" IDCANCEL Exit
  killer::KillProcess "JamTools.exe"
  Sleep 500
  killer::IsProcessRunning "JamTools.exe"
  Pop $R0
  IntCmp $R0 1 0 no_run
  Exit:
  Quit
  no_run:
  
  
 
FunctionEnd


;--------------------------------
;General

  Name "JamTools"
  OutFile "..\JamTools${PRODUCT_VERSION}Setup.exe"

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages
  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\Icon.ico"
  !define MUI_WELCOMEPAGE_TEXT "本向导将把JamTools安装到你的电脑上！$\软件主要功能:(滚动)截屏、文字识别、翻译、图像主体识别、录屏(支持自定义参数)、格式转换(支持图片音视频的简单裁剪拼接、压缩转码、提取混合操作)、键鼠动作录制/(倍速)播放、划屏提字(翻译)等功能$\r$\n本工具完全免费，严禁用于二次打包、贩卖等商业用途$\r$\n$\r$\n$\r$\nClick Next to continue."
  !define MUI_DIRECTORYPAGE_TEXT_TOP  "选择安装的位置，不建议安装到系统盘(因为太大了...) "
  !define MUI_
  !insertmacro MUI_PAGE_WELCOME
  ; 许可页面
  !define MUI_PAGE_CUSTOMFUNCTION_SHOW LicenseShow 
!insertmacro MUI_PAGE_LICENSE "..\JamTools\LICENSE" 
Function LicenseShow 
    
FunctionEnd 



  ; 安装目录选择页面
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !define MUI_FINISHPAGE_NOAUTOCLOSE
  !define MUI_FINISHPAGE_RUN
  !define MUI_FINISHPAGE_RUN_CHECKED
  !define MUI_FINISHPAGE_RUN_TEXT "Run JamTools"
  !define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "SimpChinese"
VIProductVersion "1.0.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey /LANG=2052 "Comments" "软件版权归原作者所有，他人不得复制或二次开发本程序。"
VIAddVersionKey /LANG=2052 "FileDescription" "JamTools安装向导程序"
VIAddVersionKey /LANG=2052 "FileVersion" "${PRODUCT_VERSION}"
;--------------------------------
;Installer Sections

!define UNINST_KEY \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\JamTools"
Section
  SetShellVarContext all
  ${If} $0 == ""
  ${Else}
  ;StrCpy $INSTDIR $0
  RMDir /r "$0"
  ${EndIf}
  SetOutPath "$InstDir"
  File /r "..\JamTools\*"
  WriteRegStr HKCU "Software\JamTools" "" $InstDir
  WriteRegStr HKCU "Software\JamTools" "bb" "${PRODUCT_VERSION}"
  
  
  ;关联jam文件
  WriteRegStr HKCR ".jam" "" "jamfile"
  WriteRegStr HKCR "jamfile" "" "JamTools控制文件"
  WriteRegStr HKCR "jamfile\DefaultIcon" "" "$INSTDIR\JamTools.exe,0"
  WriteRegStr HKCR "jamfile\shell" "" open
  WriteRegStr HKCR "jamfile\shell\open" "" "播放动作"
  WriteRegStr HKCR "jamfile\shell\open\command" "" '"$INSTDIR\JamTools.exe" "%1"'
  
  WriteUninstaller "$InstDir\uninstall.exe"
  CreateShortCut "$SMPROGRAMS\JamTools.lnk" "$InstDir\JamTools.exe"
  CreateShortCut "$DESKTOP\JamTools.lnk" "$InstDir\JamTools.exe"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayName" "JamTools"
  WriteRegStr HKCU "${UNINST_KEY}" "UninstallString" \
    "$\"$InstDir\uninstall.exe$\" /$MultiUser.InstallMode"
  WriteRegStr HKCU "${UNINST_KEY}" "QuietUninstallString" \
    "$\"$InstDir\uninstall.exe$\" /$MultiUser.InstallMode /S"
  WriteRegStr HKCU "${UNINST_KEY}" "Instdirstring" "$\"$InstDir$\""
  WriteRegStr HKCU "${UNINST_KEY}" "Publisher" "Fandes"
  ${GetSize} "$InstDir" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKCU "${UNINST_KEY}" "EstimatedSize" "$0"
  
  ExecWait 'regsvr32 /s "$INSTDIR\audio_sniffer-x64.dll"'
  ExecWait 'regsvr32 /s "$INSTDIR\screen-capture-recorder-x64.dll"'
  ;ExecWait 'regsvr32 /s "$INSTDIR\bin\LAVAudio.ax"'
  ;ExecWait 'regsvr32 /s "$INSTDIR\bin\LAVSplitter.ax"'
  ;ExecWait 'regsvr32 /s "$INSTDIR\bin\LAVVideo.ax"'
  ;DeleteRegKey HKCU "Software\Fandes"
  ;鎶奺xe灏佽杩涘惎鍔ㄥ櫒
  ;File /r "..\Setup Screen Capturer Recorder v0.12.10.exe"
  ;鎵ц澶栭儴绋嬪簭setup.exe
  ;ExecWait "$INSTDIR\Setup Screen Capturer Recorder v0.12.10.exe parameter"
  ;Delete "$INSTDIR\Setup Screen Capturer Recorder v0.12.10.exe"



SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"
  SetShellVarContext all
  ExecWait 'regsvr32 /s /u "$INSTDIR\audio_sniffer-x64.dll"'
  ExecWait 'regsvr32 /s /u "$INSTDIR\screen-capture-recorder-x64.dll"'
  ;ExecWait 'regsvr32 /s /u "$INSTDIR\bin\LAVAudio.ax"'
  ;ExecWait 'regsvr32 /s /u "$INSTDIR\bin\LAVSplitter.ax"'
  ;ExecWait 'regsvr32 /s /u "$INSTDIR\bin\LAVVideo.ax"'
  RMDir /r "$InstDir"
  Delete "$SMPROGRAMS\JamTools.lnk"
  Delete "$DESKTOP\JamTools.lnk"
  
  DeleteRegKey HKCU "${UNINST_KEY}"
  DeleteRegKey HKCU "Software\Fandes\jamtools"
  DeleteRegKey /ifempty HKCU "Software\Fandes"
  DeleteRegKey HKCU "Software\JamTools"

SectionEnd

Function mulu
;禁用浏览按钮
FindWindow $0 "#32770" "" $HWNDPARENT
GetDlgItem $0 $0 1001
EnableWindow $0 0
;禁止编辑目录
FindWindow $0 "#32770" "" $HWNDPARENT
GetDlgItem $0 $0 1019
EnableWindow $0 0
FunctionEnd

Function LaunchLink
  !addplugindir "."
  ExecShell  "" "$InstDir\JamTools.exe"
FunctionEnd
