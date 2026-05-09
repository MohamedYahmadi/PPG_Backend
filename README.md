# SITP - Smart Intelligent Transit Platform

Bienvenue dans le dépôt du projet **SITP** (Système Intelligent de Suivi et Paiement du Transport Public).  
Ce projet est architecturé comme un système d'entreprise de type **Modular Monolith** (Domain-Driven Design), conçu avec une approche **Zero Trust** et **Offline-First**, prévu pour tourner nativement en local (No Docker).

---

## 🚀 INSTALLATION RAPIDE (RECOMMANDÉ)

Pour simplifier l'installation sur Windows et éviter les erreurs de configuration, utilisez le script automatique :

1.  **Cloner le projet** : `git clone <votre-url-depot>`
2.  **Lancer la configuration** :
    Ouvrez PowerShell dans le dossier du projet et tapez :
    ```powershell
    .\setup.ps1
    ```
    *(Ce script va créer les .env, installer les dépendances et initialiser la base de données).*
3.  **Lancer le projet** :
    ```powershell
    .\run_all.ps1
    ```

---

## 🛠️ Configuration Manuelle (Détails)

Si vous préférez installer chaque composant séparément ou si vous êtes sur Linux :

### 1. Backend (Django)
- **Prérequis** : Python 3.11+, PostgreSQL/PostGIS, Redis.
- **Setup** :
  ```bash
  cd backend
  python -m venv .venv
  source .venv/bin/activate # Ou .\.venv\Scripts\activate sous Windows
  pip install -r requirements.txt
  cp .env.example .env # À configurer
  python manage.py migrate
  python scripts/seed_db.py
  python manage.py runserver 0.0.0.0:8000
  ```

### 2. Admin Dashboard (React)
  ```bash
  cd admin
  npm install
  npm start
  ```

### 3. Mobile App (Expo)
  ```bash
  cd mobile
  npm install
  npm start
  ```

---

## 🚨 GUIDE DE DÉPANNAGE (Windows)

### ❌ Erreur GDAL (GeoDjango)
Si vous avez l'erreur `Could not find the GDAL library` :
1. Installez **OSGeo4W**.
2. Modifiez le fichier `backend/.env` pour pointer vers votre installation :
   ```env
   GDAL_BIN_PATH=C:\OSGeo4W\bin
   GDAL_DLL_NAME=gdal312.dll
   ```

### ❌ Erreur Connexion Mobile
Si l'application mobile ne contacte pas le serveur :
1. Vérifiez que votre téléphone et votre PC sont sur le **même réseau Wi-Fi**.
2. Dans `mobile/.env`, remplacez `localhost` par l'**IP locale de votre PC** (ex: `192.168.1.XX`).

---
*Projet architecturé pour une performance et une sécurité de niveau entreprise.*
