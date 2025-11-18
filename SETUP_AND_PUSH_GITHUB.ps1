# Script PowerShell per setup completo GitHub
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup e Push GitHub - Music Text Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica autenticazione GitHub
Write-Host "🔐 Verifica autenticazione GitHub..." -ForegroundColor Yellow
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Non autenticato su GitHub CLI" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 Per autenticarti:" -ForegroundColor Yellow
    Write-Host "   1. Esegui: gh auth login" -ForegroundColor White
    Write-Host "   2. Segui le istruzioni nel browser" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Oppure usa un token GitHub:" -ForegroundColor Yellow
    Write-Host "   git remote set-url origin https://TOKEN@github.com/USERNAME/repo.git" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ Autenticato su GitHub" -ForegroundColor Green
Write-Host ""

# Ottieni username GitHub
$username = gh api user --jq .login
if (-not $username) {
    Write-Host "❌ Impossibile ottenere username GitHub" -ForegroundColor Red
    exit 1
}

Write-Host "👤 Username GitHub: $username" -ForegroundColor Cyan
Write-Host ""

# Nome repository
$repoName = "music-text-generator"
$repoUrl = "https://github.com/$username/$repoName.git"

# Verifica se remote esiste
Write-Host "🔍 Verifica remote GitHub..." -ForegroundColor Yellow
$remoteExists = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Remote già configurato: $remoteExists" -ForegroundColor Green
    $currentRemote = $remoteExists
} else {
    Write-Host "📝 Creazione repository su GitHub..." -ForegroundColor Yellow
    
    # Crea repository (privato)
    $createRepo = gh repo create $repoName --private --source=. --remote=origin --push 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Repository creato e push completato!" -ForegroundColor Green
        Write-Host "🌐 URL: https://github.com/$username/$repoName" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "⚠️  Repository potrebbe già esistere o errore nella creazione" -ForegroundColor Yellow
        Write-Host "📝 Aggiungo remote manualmente..." -ForegroundColor Yellow
        git remote add origin $repoUrl
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Remote aggiunto: $repoUrl" -ForegroundColor Green
        } else {
            Write-Host "❌ Errore nell'aggiunta del remote" -ForegroundColor Red
            exit 1
        }
    }
}

# Push
Write-Host ""
Write-Host "🚀 Eseguo push su GitHub..." -ForegroundColor Yellow
git push -u origin master

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Push completato con successo!" -ForegroundColor Green
    Write-Host "🌐 Repository: https://github.com/$username/$repoName" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Errore nel push" -ForegroundColor Red
    Write-Host "💡 Verifica:" -ForegroundColor Yellow
    Write-Host "   - Autenticazione GitHub" -ForegroundColor White
    Write-Host "   - Repository esiste su GitHub" -ForegroundColor White
    Write-Host "   - Permessi sul repository" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "🎉 Completato!" -ForegroundColor Green

