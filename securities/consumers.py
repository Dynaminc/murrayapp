import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = "stock-update"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        data = data["data"]
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "stock_update_data", "data": data}
        )

    def stock_update_data(self, event, type="stock_update_data"):
        data = event["data"]
        self.send(text_data=json.dumps({"type": type, "data": data}))
