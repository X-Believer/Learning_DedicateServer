param(
    [string]$ArchiveDirectory = (Join-Path $PSScriptRoot 'Build\Build_1')
)

$project = Join-Path $PSScriptRoot 'FPSTemplate.uproject'
$engine = 'E:\UE_5_4'
$uat = Join-Path $engine 'Engine\Build\BatchFiles\RunUAT.bat'
$editor = Join-Path $engine 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'

& $uat BuildCookRun -nop4 -utf8output -nocompileeditor -skipbuildeditor -cook "-project=$project" -target=FPSTemplateServer "-unrealexe=$editor" -platform=Win64 -stage -archive -package -build -pak -iostore -compressed -prereqs "-archivedirectory=$ArchiveDirectory" -server -noclient -serverconfig=Development '-AdditionalCookerOptions=-DisablePlugins=RiderLink' -nocompile -nocompileuat
exit $LASTEXITCODE