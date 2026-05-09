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
