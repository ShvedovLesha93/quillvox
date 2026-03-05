#define MyAppName "My Program"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "My Company, Inc."
#define MyAppURL "https://github.com/ShvedovLesha93/quillvox"
#define MyAppExeName "QuillVox.exe"

[Setup]
AppId={{895D37A7-EDFD-4E9C-A43A-1F31DB452A81}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=release
OutputBaseFilename=mysetup
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Launcher exe
Source: "dist\MyApp.exe"; DestDir: "{app}"; Flags: ignoreversion

; App source files
Source: "dist\QuillVox.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\uv.lock"; DestDir: "{app}"; Flags: ignoreversion

; App folder (translator, etc.)
Source: "dist\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

