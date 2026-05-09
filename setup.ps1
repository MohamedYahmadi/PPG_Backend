# Script de Configuration Automatique pour le projet SITP
# Usage: .\setup.ps1

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   SITP - Système de Transport Intelligent     " -ForegroundColor Cyan
Write-Host "        Configuration Automatique              " -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# 1. Vérification des prérequis
Write-Host "`n[1/5] Vérification des prérequis..." -ForegroundColor Yellow

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[-] Python n'est pas installé. Veuillez l'installer sur https://python.org" -ForegroundColor Red
    exit
}
Write-Host "[+] Python détecté." -ForegroundColor Green

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "[-] Node.js n'est pas installé. Veuillez l'installer sur https://nodejs.org" -ForegroundColor Red
    exit
}
Write-Host "[+] Node.js détecté." -ForegroundColor Green

# 2. Configuration des fichiers .env
Write-Host "`n[2/5] Configuration des variables d'environnement (.env)..." -ForegroundColor Yellow

function Create-Env($path, $example) {
    if (-not (Test-Path "$path\.env")) {
        Copy-Item "$path\$example" "$path\.env"
        Write-Host "[+] Créé : $path\.env (à partir de $example)" -ForegroundColor Green
    } else {
        Write-Host "[!] $path\.env existe déjà. Ignoré." -ForegroundColor Gray
    }
}

Create-Env "backend" ".env.example"
Create-Env "admin" ".env.example"
Create-Env "mobile" ".env.example"

# 2.5 Vérification spécifique GDAL
Write-Host "`n[2.5/5] Vérification de GDAL (GeoDjango)..." -ForegroundColor Yellow
$gdalPaths = @(
    "C:\OSGeo4W\bin",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\OSGeo4W\bin",
    "C:\Program Files\OSGeo4W\bin"
)
$foundGdal = $false
foreach ($p in $gdalPaths) {
    if (Test-Path "$p\gdal*.dll") {
        Write-Host "[+] GDAL trouvé dans $p" -ForegroundColor Green
        $foundGdal = $true
        break
    }
}
if (-not $foundGdal) {
    Write-Host "[!] GDAL non trouvé. L'installation de OSGeo4W est recommandée pour les fonctions GPS." -ForegroundColor Magenta
}

# 3. Installation des dépendances Backend
Write-Host "`n[3/5] Installation du Backend (Django)..." -ForegroundColor Yellow
Set-Location backend
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
Write-Host "[+] Dépendances Backend installées." -ForegroundColor Green

# 4. Installation des dépendances Frontend
Write-Host "`n[4/5] Installation du Dashboard Admin & Mobile (npm)..." -ForegroundColor Yellow
Set-Location ..\admin
Write-Host "Installing Admin dependencies (this may take a few minutes)..."
npm install
Write-Host "[+] Dépendances Admin installées." -ForegroundColor Green

Set-Location ..\mobile
Write-Host "Installing Mobile dependencies..."
npm install
Write-Host "[+] Dépendances Mobile installées." -ForegroundColor Green

# 5. Base de données
Write-Host "`n[5/5] Initialisation de la base de données..." -ForegroundColor Yellow
Set-Location ..\backend
& ".\.venv\Scripts\Activate.ps1"
Write-Host "Application des migrations..."
python manage.py migrate
Write-Host "Injection des données de test (seed)..."
python scripts/seed_db.py

Set-Location ..
Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "   CONFIGURATION TERMINÉE AVEC SUCCÈS !        " -ForegroundColor Green
Write-Host "   Utilisez .\run_all.ps1 pour tout lancer.    " -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
