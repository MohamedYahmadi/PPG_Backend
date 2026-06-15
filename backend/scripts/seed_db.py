import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import transaction
from django.contrib.auth.hashers import make_password
from domains.auth_identity.models import User
from domains.transit_tracking.models import Line, Trajet, Station, Vehicle, TrajetStation
from domains.wallet_payments.models import Wallet

@transaction.atomic
def run_seeders():
    """
    DÉCISION CTO : Script d'amorçage "Idempotent".
    Peut être lancé plusieurs fois sans casser l'intégrité de la DB.
    Idéal pour l'onboarding de développeurs sur la stack locale.
    """
    print("🚀 Démarrage du Seeding de la base de données (transport_db)...")

    # 1. Création Admin
    admin_phone = "+21650000000"
    if not User.objects.filter(phone_number=admin_phone).exists():
        User.objects.create(
            phone_number=admin_phone,
            password=make_password("AdminSecure123!"),
            role="SUPER_ADMIN"
        )
        print(f"✅ Administrateur créé : {admin_phone}")
        
    # 2. Création Controller
    controller_phone = "+21670000000"
    if not User.objects.filter(phone_number=controller_phone).exists():
        User.objects.create(
            phone_number=controller_phone,
            password=make_password("Controller123!"),
            role="CONTROLLER"
        )
        print(f"✅ Contrôleur créé : {controller_phone}")

    # 3. Création Passenger
    test_phone = "+21699000000"
    if not User.objects.filter(phone_number=test_phone).exists():
        passenger = User.objects.create(
            phone_number=test_phone,
            password=make_password("Passenger123!"),
            role="PASSENGER"
        )
        Wallet.objects.create(passenger=passenger, balance=50.000)
        print(f"✅ Passager créé avec 50 TND : {test_phone}")

    # 4. Création Driver
    driver_phone = "+21620000000"
    if not User.objects.filter(phone_number=driver_phone).exists():
        User.objects.create(
            phone_number=driver_phone,
            password=make_password("Driver123!"),
            role="DRIVER"
        )
        print(f"✅ Chauffeur créé : {driver_phone}")

    # 5. Création Géographique
    if not Line.objects.exists():
        line = Line.objects.create(name="TGM", color_code="#0000FF")
        station1 = Station.objects.create(name="Tunis Marine", location_lat=36.8065, location_lng=10.1815, has_kiosk=True)
        station2 = Station.objects.create(name="Marsa Plage", location_lat=36.8833, location_lng=10.3293, has_kiosk=True)
        trajet = Trajet.objects.create(
            line=line,
            name="Tunis -> Marsa",
            start_station=station1,
            end_station=station2,
            path_coordinates="36.8065,10.1815;36.8833,10.3293"
        )
        TrajetStation.objects.create(trajet=trajet, station=station1, order_number=1, time_to_next_station=15)
        TrajetStation.objects.create(trajet=trajet, station=station2, order_number=2, time_to_next_station=0)
        Vehicle.objects.create(plate_number="123-TU-4567", fleet_id="TGM-001", capacity=300)
        print("✅ Données géographiques (Lignes, Trajets, Stations) créées.")

    print("🎉 Base de données initialisée avec succès.")

if __name__ == '__main__':
    run_seeders()
