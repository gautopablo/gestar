# PowerShell script to update deploy.zip for Azure App Service
$zipPath = "deploy.zip"

Write-Host "--- Actualizando $zipPath ---" -ForegroundColor Cyan

# Eliminar el zip anterior si existe
if (Test-Path $zipPath) {
    Write-Host "Eliminando $zipPath anterior..."
    Remove-Item $zipPath
}

# Lista de archivos y carpetas a incluir
$includeList = @(
    "app.py",
    "app_v2.py",
    "db.py",
    "models.py",
    "requirements.txt",
    ".streamlit",
    ".deployment",
    "marca - Isologo Taranto.png",
    "*.md"
)

Write-Host "Comprimiendo archivos seleccionados..."
try {
    Compress-Archive -Path $includeList -DestinationPath $zipPath -ErrorAction Stop
    Write-Host "¡Éxito! $zipPath actualizado correctamente." -ForegroundColor Green
}
catch {
    Write-Host "Error al crear el archivo zip: $_" -ForegroundColor Red
    exit 1
}

Read-Host "Presione Enter para salir..."
