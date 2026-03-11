; Script generated for CatchingRectangle
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "CatchingRectangle"
#define MyAppVersion "1.2"
#define MyAppPublisher "Remap Intelligence"
#define MyAppExeName "CatchingRectangle.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. 
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the Inno Setup Compiler)
AppId={{8A3D5D21-9F3C-4E12-A8D9-1234567890AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Remove the following line if your python build is 32-bit:
ArchitecturesInstallIn64BitMode=x64
OutputDir=.
OutputBaseFilename=CatchingRectangle_Setup
SetupIconFile=rectangle_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; NOTE: 'Source' must point to where your .exe is relative to this .iss file.
; Since PyInstaller puts it in 'dist', we look there.
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; We do NOT need to include the .jpg/.png files here because 
; your PyInstaller .spec file already bundled them INSIDE the .exe.

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent