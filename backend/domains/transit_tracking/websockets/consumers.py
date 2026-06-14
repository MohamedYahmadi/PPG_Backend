import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TransitConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.room_group_name = f'trip_{self.trip_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # On broadcast à tout le monde dans la room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'gps_update',
                'payload': data.get('payload', {})
            }
        )

    async def gps_update(self, event):
        payload = event['payload']
        await self.send(text_data=json.dumps({
            'type': 'gps_update',
            'payload': payload
        }))

class AdminFleetConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'admin_fleet'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def fleet_update(self, event):
        payload = event['payload']
        await self.send(text_data=json.dumps({
            'type': 'fleet_update',
            'payload': payload
        }))
