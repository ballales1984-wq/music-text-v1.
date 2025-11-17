# Crea collegamento desktop per Music Text Generator
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Music Text Generator.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$scriptPath\avvia_app.ps1`""
$shortcut.WorkingDirectory = $scriptPath
$shortcut.Description = "Music Text Generator - Isola voce e genera testo"
$shortcut.IconLocation = "powershell.exe"
$shortcut.Save()

Write-Host "Collegamento desktop creato: $shortcutPath" -ForegroundColor Green

