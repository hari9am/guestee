#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{A9357282-A454-4F0D-971F-50163F559FC9}
AppName=Gestuee Companion
AppVersion={#AppVersion}
AppPublisher=Gestuee
SetupIconFile=gestuee-icon.ico
DefaultDirName={localappdata}\Programs\Gestuee
DefaultGroupName=Gestuee Companion
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=dist\installer
OutputBaseFilename=Gestuee-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Gestuee.exe

[Tasks]
Name: "startupicon"; Description: "Start Gestuee when I sign in"; GroupDescription: "Startup:"

[Files]
Source: "dist\Gestuee\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Gestuee Companion"; Filename: "{app}\Gestuee.exe"
Name: "{userstartup}\Gestuee Companion"; Filename: "{app}\Gestuee.exe"; Tasks: startupicon

[Run]
Filename: "{app}\Gestuee.exe"; Description: "Launch Gestuee Companion"; Flags: nowait postinstall skipifsilent