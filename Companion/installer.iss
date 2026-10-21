#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{A9357282-A454-4F0D-971F-50163F559FC9}
AppName=Gustee Companion
AppVersion={#AppVersion}
AppPublisher=Gustee
SetupIconFile=gustee-icon.ico
DefaultDirName={localappdata}\Programs\Gustee
DefaultGroupName=Gustee Companion
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=dist\installer
OutputBaseFilename=Gustee-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Gustee.exe

[Tasks]
Name: "startupicon"; Description: "Start Gustee when I sign in"; GroupDescription: "Startup:"

[Files]
Source: "dist\Gustee\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Gustee Companion"; Filename: "{app}\Gustee.exe"
Name: "{userstartup}\Gustee Companion"; Filename: "{app}\Gustee.exe"; Tasks: startupicon

[Run]
Filename: "{app}\Gustee.exe"; Description: "Launch Gustee Companion"; Flags: nowait postinstall skipifsilent