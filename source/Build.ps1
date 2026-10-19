param([Parameter(Mandatory=$true)][string]$EditingKit)
$ErrorActionPreference = 'Stop'
$kitRoot = (Resolve-Path -LiteralPath $EditingKit).Path
$packageRoot = Split-Path -Parent $PSScriptRoot
$managedBlam = Join-Path $kitRoot 'bin\ManagedBlam.dll'
if (!(Test-Path -LiteralPath $managedBlam)) { throw 'Select the extracted Halo 3 Editing Kit folder.' }
dotnet build (Join-Path $PSScriptRoot 'Extractor\Extractor.csproj') -c Release -o (Join-Path $packageRoot 'halo_bridge\bin\extractor') -p:LangVersion=13.0 --nologo
if ($LASTEXITCODE) { throw 'Extraction helper build failed.' }
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$destination = Join-Path $packageRoot 'halo_bridge\bin\tags'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
& $compiler /nologo /target:exe /platform:x64 /highentropyva- /r:System.Web.Extensions.dll "/r:$managedBlam" "/out:$destination\HaloBridge.Tags.exe" (Join-Path $PSScriptRoot 'TagBridge\Program.cs')
if ($LASTEXITCODE) { throw 'Tag helper build failed.' }
Write-Output 'Both HaloBridge helpers built successfully.'
