import uuid
from django.db import models


class Line(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'lines'

    def __str__(self):
        return self.name


class Station(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    has_kiosk = models.BooleanField(default=False)
    gtfs_stop_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'stations'

    def __str__(self):
        return self.name


class Trajet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line = models.ForeignKey(Line, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='trajets_starting_here')
    end_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='trajets_ending_here')
    path_coordinates = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    gtfs_route_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'trajets'

    def __str__(self):
        return self.name


class TrajetStation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE, related_name='trajet_stations')
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    order_number = models.PositiveIntegerField()
    time_to_next_station = models.PositiveIntegerField(help_text='Minutes from this station to the next', default=5)

    class Meta:
        db_table = 'trajet_stations'
        ordering = ['order_number']
        unique_together = [('trajet', 'station'), ('trajet', 'order_number')]

    def __str__(self):
        return f"{self.trajet.name} -> {self.order_number}. {self.station.name}"


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plate_number = models.CharField(max_length=50, unique=True)
    fleet_id = models.CharField(max_length=50, unique=True)
    driver_id = models.UUIDField(null=True, blank=True)
    capacity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vehicles'

    def __str__(self):
        return self.plate_number


class Trip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trajet = models.ForeignKey(Trajet, on_delete=models.RESTRICT)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.RESTRICT)
    driver_id = models.UUIDField()
    current_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips_currently_here')
    destination_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips_destined_here')
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    last_gps_update_time = models.DateTimeField(null=True, blank=True)
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='SCHEDULED')
    gtfs_trip_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'trips'

    def __str__(self):
        return f"{self.trajet.name} - {self.status}"


class DriverSession(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('ARRIVED_AT_STATION', 'Arrived at Station'),
        ('FINISHED', 'Finished'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver_id = models.UUIDField()
    trajet = models.ForeignKey(Trajet, on_delete=models.RESTRICT)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.RESTRICT, null=True, blank=True)
    departure_station = models.ForeignKey(Station, on_delete=models.RESTRICT, related_name='sessions_departed')
    arrival_station = models.ForeignKey(Station, on_delete=models.RESTRICT, related_name='sessions_arrived')
    current_station = models.ForeignKey(Station, on_delete=models.RESTRICT, related_name='sessions_current')
    current_order = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    started_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'driver_sessions'

    def __str__(self):
        return f"Session {self.driver_id} - {self.trajet.name} ({self.status})"


class DriverIncident(models.Model):
    INCIDENT_TYPES = [
        ('DELAY', 'Delay'),
        ('BREAKDOWN', 'Breakdown'),
        ('ACCIDENT', 'Accident'),
        ('SECURITY', 'Security'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True)
    driver_id = models.UUIDField()
    type = models.CharField(max_length=20, choices=INCIDENT_TYPES, default='OTHER')
    description = models.TextField()
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'driver_incidents'

    def __str__(self):
        return f"{self.get_type_display()} - {self.driver_id}"


class GPSLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.RESTRICT)
    vehicle_id = models.UUIDField()
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    speed_kmh = models.DecimalField(max_digits=5, decimal_places=2)
    heading = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gps_logs'

    def __str__(self):
        return f"GPS {self.vehicle_id} @ {self.recorded_at}"


class ImportedStation(models.Model):
    SOURCE_CHOICES = [
        ('OSM', 'OpenStreetMap'),
        ('GOOGLE', 'Google Places'),
        ('GTFS', 'GTFS'),
        ('MANUAL', 'Manual'),
    ]
    STATION_TYPES = [
        ('BUS', 'Bus'),
        ('METRO', 'Metro'),
        ('TRAIN', 'Train'),
        ('UNKNOWN', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    formatted_address = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='OSM')
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    type = models.CharField(max_length=20, choices=STATION_TYPES, default='UNKNOWN')
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    is_approved = models.BooleanField(default=False)
    approved_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='imported_sources')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imported_stations'
        verbose_name = 'Imported Station'
        verbose_name_plural = 'Imported Stations'

    def __str__(self):
        parts = [self.name]
        if self.city:
            parts.append(f'({self.city})')
        parts.append(f'[{self.source}]')
        return ' '.join(parts)


class ImportedRoute(models.Model):
    SOURCE_CHOICES = [
        ('OSM', 'OpenStreetMap'),
        ('GOOGLE', 'Google Places'),
        ('GTFS', 'GTFS'),
        ('MANUAL', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='GTFS')
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    line_name = models.CharField(max_length=100, blank=True)
    is_approved = models.BooleanField(default=False)
    approved_trajet = models.ForeignKey(Trajet, on_delete=models.SET_NULL, null=True, blank=True, related_name='imported_sources')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imported_routes'
        verbose_name = 'Imported Route'
        verbose_name_plural = 'Imported Routes'

    def __str__(self):
        return f'{self.name} [{self.source}]'


class ImportedRouteStation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    imported_route = models.ForeignKey(ImportedRoute, on_delete=models.CASCADE, related_name='imported_stations')
    imported_station = models.ForeignKey(ImportedStation, on_delete=models.CASCADE)
    order_number = models.PositiveIntegerField()
    time_to_next_station = models.PositiveIntegerField(help_text='Minutes from this station to the next', default=5)

    class Meta:
        db_table = 'imported_route_stations'
        ordering = ['order_number']
        unique_together = [('imported_route', 'order_number')]

    def __str__(self):
        return f'{self.imported_route.name} -> {self.order_number}. {self.imported_station.name}'
