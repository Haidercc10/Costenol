# Construir desde un Python de Windows con Tcl/Tk y PyInstaller instalados.
$ErrorActionPreference = 'Stop'
$baseProyecto = Split-Path -Parent $PSScriptRoot
python -m PyInstaller --noconfirm --distpath (Join-Path $baseProyecto 'dist') --workpath (Join-Path $baseProyecto 'build') (Join-Path $PSScriptRoot 'Costenol.spec')
if ($LASTEXITCODE -ne 0) { throw 'Falló la construcción del ejecutable.' }
Copy-Item -LiteralPath (Join-Path $baseProyecto 'ejemplos') -Destination (Join-Path $baseProyecto 'dist/Costenol/ejemplos') -Recurse -Force
Write-Host 'Portable disponible en dist/Costenol. Copia toda la carpeta.'
