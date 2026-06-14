# Résumé du Développement Backend — Projet PPG (SITP)

## Date : 14 Juin 2026

---

## 1. Travail Effectué

### Correctifs Bugs
- **Bug `json.stringify`** → `json.dumps` dans `websockets/consumers.py` (2 occurrences)
- **API Transit non montée** : Ajout de `api/v1/transit/` dans `config/urls.py`

### Module M1 — Authentification & Comptes
- **User model enrichi** : `email`, `full_name`, `avatar_url`, `preferences` (JSON), `language`
- **Rôles étendus** : `SUPER_ADMIN` ajouté aux choix
- **Réinitialisation mot de passe** : 
  - `PasswordResetToken` model (dans `auth_identity/models.py`)
  - `POST /api/v1/auth/password-reset/request/` — génère token SHA256
  - `POST /api/v1/auth/password-reset/confirm/` — valide token + change mdp + blacklist JWT
- **Gestion de profil** : `GET/PATCH /api/v1/auth/me/` (ProfileAPIView)
- **Inscription étendue** : accepte `email`, `full_name`

### Module M2 — Données Statiques du Réseau
- **Lignes** : `LineViewSet` (CRUD complet)
- **Stations** : `StationViewSet` (CRUD avec géolocalisation PostGIS)
- **Routes** : `RouteViewSet` (CRUD complet)
- **Véhicules** : `VehicleViewSet` (CRUD — immatriculation, capacité, flotte)
- **Horaires** : Nouveau `Schedule` model (route, jour, heure départ/arrivée, fréquence)
- **Correspondances** : Nouveau `LineConnection` model (lignes, stations, temps transfert)
- **Trajets** : `TripViewSet` + endpoints dédiés :
  - `POST /api/v1/transit/trips/create/` — création
  - `POST /api/v1/transit/trips/{id}/start/` — démarrage (conducteur)
  - `POST /api/v1/transit/trips/{id}/end/` — fin (conducteur)

### Module M3 — Suivi Temps Réel
- **WebSockets** : `TransitConsumer` et `AdminFleetConsumer` (corrigés)
- **GPS Push REST** : `POST /api/v1/transit/gps/push/` (pour conducteurs)
- **Live Vehicles** : `GET /api/v1/transit/live-vehicles/` (lecture cache Redis)
- **ETA** : Nouveau `ETAService` :
  - `GET /api/v1/transit/eta/{trip_id}/station/{station_id}/`
  - `GET /api/v1/transit/eta/{trip_id}/all/`
- **Mode simulation** : `POST /api/v1/transit/simulation/start/` (Celery task)
  - Génère des points GPS simulés le long d'une route

### Module M4 — Paiement et Billetterie
- **Abonnements** : `SubscriptionType` + `Subscription` models
  - `GET /api/v1/tickets/subscriptions/types/`
  - `POST /api/v1/tickets/subscriptions/purchase/`
  - `GET /api/v1/tickets/subscriptions/history/`
- **Grille tarifaire** : `Fare` model (catégorie, zone, prix, réduction)
  - `FareViewSet` (CRUD admin)
  - `POST /api/v1/tickets/fares/calculate/`
- **Achat multi-passagers** : `MultiPassengerTicket` model
  - `POST /api/v1/tickets/multi-passenger/purchase/`
- **Factures** : `Invoice` model avec numéro unique
  - `GET /api/v1/tickets/invoices/`

### Module M5 — Vérification des Tickets
- **Marquage "utilisé"** : `POST /api/v1/tickets/validate/mark-used/`
  - Vérifie validité temporelle + statut ACTIVE
- **Sync offline** : `POST /api/v1/tickets/validate/sync/` (existait déjà)
- **Fraude** : Moteur Celery `fraud_detection_engine` (anti-replay géospatial)

### Module M6 — Tableau de Bord Admin
- **Métriques étendues** : 17 indicateurs BI (tickets, revenus, fraudes, passagers, conducteurs, véhicules, lignes, infractions, incidents, abonnements, factures)
- **Historique des revenus** : agrégation par jour sur 30 jours
- **Export analytique** : `GET /api/v1/admin/analytics/export/?type=revenue|tickets|fines`
- **Santé système** : `GET /api/v1/admin/health/` — check DB, Redis, Celery + CPU/Memory/Disk
- **Alertes fraude** : `GET /api/v1/admin/fraud/alerts/`
- **Wallets admin** : `GET /api/v1/admin/wallets/list/`
- **Infractions admin** : `GET /api/v1/admin/fines/all/`
- **Résolution litiges** : `POST /api/v1/admin/disputes/{id}/resolve/`
- **Settings** : `GET/PATCH /api/v1/admin/settings/`

### Module M7 — Notifications
- **Nouveau domaine complet** `domains/notifications/` :
  - `Notification` model (types, push/SMS/email, is_read)
  - `NotificationTemplate` model
  - `IncidentReport` model (signalement conducteurs/contôleurs)
- **Endpoints** :
  - `GET /api/v1/notifications/` — liste notifications
  - `POST /api/v1/notifications/{id}/read/` — marquer lue
  - `POST /api/v1/notifications/mark-all-read/`
  - `POST /api/v1/notifications/broadcast/` — diffusion admin
  - `GET/POST /api/v1/notifications/incidents/` — lister/signaler
  - `POST /api/v1/notifications/incidents/{id}/resolve/` — résoudre
- **FCM Push** : `tasks.py` avec `firebase-admin` (configurable)
- **Notification service** : `notify_delay()`, `notify_ticket_expiring()`, `report_incident()`

### Autres
- **`wallet_payments/tasks.py`** : `process_payment_webhook()` + `refund_wallet()` (queue `critical_payments`)
- **Compatibilité frontend** : 4 redirections d'URL ajoutées dans `config/urls.py`
- **Dépendances** : `firebase-admin`, `psutil`, `reportlab`, `openpyxl` ajoutées

---

## 2. Nouvelles Tables/Modèles

| Domaine | Modèle | Table |
|---------|--------|-------|
| auth_identity | PasswordResetToken | password_reset_tokens |
| notifications | Notification | notifications |
| notifications | NotificationTemplate | notification_templates |
| notifications | IncidentReport | incident_reports |
| transit_tracking | Schedule | schedules |
| transit_tracking | LineConnection | line_connections |
| ticketing_validation | SubscriptionType | subscription_types |
| ticketing_validation | Subscription | subscriptions |
| ticketing_validation | Fare | fares |
| ticketing_validation | Invoice | invoices |
| ticketing_validation | MultiPassengerTicket | multi_passenger_tickets |

---

## 3. Nouveaux Endpoints API

### Auth (`/api/v1/auth/`)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | `/password-reset/request/` | Demander réinitialisation |
| POST | `/password-reset/confirm/` | Confirmer réinitialisation |
| GET | `/me/` | Profil utilisateur |
| PATCH | `/me/` | Modifier profil |

### Transit (`/api/v1/transit/`)
| Méthode | Path | Description |
|---------|------|-------------|
| CRUD | `/lines/` | Lignes |
| CRUD | `/vehicles/` | Véhicules |
| CRUD | `/trips/` | Trajets |
| CRUD | `/schedules/` | Horaires |
| CRUD | `/connections/` | Correspondances |
| POST | `/trips/create/` | Créer trajet |
| POST | `/trips/{id}/start/` | Démarrer trajet |
| POST | `/trips/{id}/end/` | Terminer trajet |
| POST | `/gps/push/` | Envoyer position GPS |
| POST | `/simulation/start/` | Lancer simulation |
| GET | `/eta/{trip_id}/station/{station_id}/` | ETA vers station |
| GET | `/eta/{trip_id}/all/` | ETA toutes stations |

### Tickets (`/api/v1/tickets/`)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | `/validate/mark-used/` | Marquer ticket utilisé |
| GET | `/subscriptions/types/` | Types abonnements |
| POST | `/subscriptions/purchase/` | Acheter abonnement |
| GET | `/subscriptions/history/` | Historique abonnements |
| CRUD | `/fares/` | Grille tarifaire |
| POST | `/fares/calculate/` | Calculer tarif |
| GET | `/invoices/` | Factures |
| POST | `/multi-passenger/purchase/` | Achat multi-passagers |

### Notifications (`/api/v1/notifications/`)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | `/` | Liste notifications |
| POST | `/{id}/read/` | Marquer lue |
| POST | `/mark-all-read/` | Tout marquer lu |
| POST | `/broadcast/` | Diffusion admin |
| GET | `/incidents/` | Lister incidents |
| POST | `/incidents/report/` | Signaler incident |
| POST | `/incidents/{id}/resolve/` | Résoudre incident |

### Admin (`/api/v1/admin/`)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | `/analytics/export/` | Export analytics |
| GET | `/health/` | Santé système |
| GET | `/fraud/alerts/` | Alertes fraude |
| GET | `/wallets/list/` | Liste wallets |
| GET | `/fines/all/` | Liste infractions |
| POST | `/disputes/{id}/resolve/` | Résoudre litige |
| GET | `/settings/` | Settings |
| PATCH | `/settings/{id}/` | Modifier setting |

---

## 4. Points d'Attention/À Faire

1. **Migrations** : Exécuter `python manage.py makemigrations && python manage.py migrate` après mise à jour des modèles (User enrichi + 11 nouveaux modèles)
2. **Firebase Admin** : Configurer `GOOGLE_APPLICATION_CREDENTIALS` dans `.env` pour FCM
3. **Redis** : S'assurer que Redis est en cours d'exécution (WebSockets + Celery + Cache)
4. **Tests** : Aucun test écrit pour les nouveaux endpoints
5. **Sécurité** : Vérifier que les permissions `IsAdmin` sont bien appliquées partout
6. **Frontend** : Les URLs suivantes ont changé — mettre à jour le frontend ou garder les redirections :
   - `/wallet/admin/list/` → `/admin/wallets/list/`
   - `/fines/all/` → `/admin/fines/all/`
   - `/transit/live-fleet/` → `/transit/live-vehicles/`
   - `/transit/fraud/alerts/` → `/admin/fraud/alerts/`
7. **Logging** : Configurer les niveaux de log dans `local.py` pour les nouveaux domaines
8. **Seed data** : Mettre à jour `scripts/seed_db.py` avec les nouveaux modèles (subscriptions, fares, schedules)

---

## 5. Stats

- **Fichiers créés/modifiés** : ~45 fichiers
- **Nouvelles tables** : 11
- **Nouveaux endpoints** : ~35
- **Dépendances ajoutées** : 4
- **Bugs corrigés** : 2 (json.stringify, API non montée)
