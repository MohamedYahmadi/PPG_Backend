import uuid
from django.contrib.gis.db import models as gis_models
from django.db import models

class Line(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'lines'

class Route(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line = models.ForeignKey(Line, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    path_geom = gis_models.LineStringField(srid=4326)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'routes'

class Station(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    location = gis_models.PointField(srid=4326)
    has_kiosk = models.BooleanField(default=False)

    class Meta:
        db_table = 'stations'

class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plate_number = models.CharField(max_length=50, unique=True)
    fleet_id = models.CharField(max_length=50, unique=True)
    capacity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vehicles'

class Trip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.RESTRICT)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.RESTRICT)
    driver_id = models.UUIDField() # Référence vers User model
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='SCHEDULED')

    class Meta:
        db_table = 'trips'

class Schedule(models.Model):
    DAY_CHOICES = [
        ('MONDAY', 'Lundi'), ('TUESDAY', 'Mardi'), ('WEDNESDAY', 'Mercredi'),
        ('THURSDAY', 'Jeudi'), ('FRIDAY', 'Vendredi'),
        ('SATURDAY', 'Samedi'), ('SUNDAY', 'Dimanche'),
        ('WEEKDAY', 'Jour de semaine'), ('WEEKEND', 'Week-end'), ('ALL', 'Tous les jours'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    day_type = models.CharField(max_length=10, choices=DAY_CHOICES, default='ALL')
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    frequency_minutes = models.IntegerField(null=True, blank=True, help_text="Intervalle en minutes si fréquence régulière")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'schedules'
        ordering = ['route', 'day_type', 'departure_time']

    def __str__(self):
        return f"{self.route.name} - {self.departure_time} ({self.day_type})"


class LineConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='connections_from')
    to_line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='connections_to')
    from_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='connections_from_station')
    to_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='connections_to_station')
    transfer_time_minutes = models.IntegerField(default=5, help_text="Temps de correspondance estimé")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'line_connections'
        unique_together = ('from_line', 'to_line', 'from_station', 'to_station')

    def __str__(self):
        return f"{self.from_line.name} -> {self.to_line.name} via {self.from_station.name}"


class GPSLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.RESTRICT)
    vehicle_id = models.UUIDField()
    location = gis_models.PointField(srid=4326) # EPSG:4326
    speed_kmh = models.DecimalField(max_digits=5, decimal_places=2)
    heading = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gps_logs'
