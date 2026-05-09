# Script pour lancer tous les services SITP
# Usage: .\run_all.ps1

Write-Host "Lancement des services SITP..." -ForegroundColor Cyan

# 1. Backend
Write-Host "Démarrage du Backend (Django) sur http://localhost:8000 (Accesible via reseau) ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\activate; python manage.py runserver localhost:8000"

# 2. Admin Dashboard
Write-Host "Démarrage du Dashboard Admin sur http://localhost:3000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd admin; npm start"

# 3. Mobile App
Write-Host "Démarrage de l'App Mobile (Expo)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd mobile; npm start -c"

Write-Host "`n[!] Tous les terminaux sont ouverts. Vérifiez les erreurs dans chaque fenêtre." -ForegroundColor Green
