from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/transit/trip/(?P<trip_id>[^/]+)/$', consumers.TransitConsumer.as_asgi()),
    re_path(r'^ws/transit/admin/$', consumers.AdminFleetConsumer.as_asgi()),
]
