from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"notifications_{self.user_id}"
        print(f"User {self.user_id} is connecting. Group name: {self.group_name}")

        # Join the notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        print(f"User {self.user_id} joined group: {self.group_name}")
        await self.accept()
        print(f"WebSocket connection accepted for user {self.user_id}")

    async def disconnect(self, close_code):
        print(f"User {self.user_id} is disconnecting. Close code: {close_code}")

        # Leave the notification group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"User {self.user_id} left group: {self.group_name}")

    # Send notification to the WebSocket
    async def send_notification(self, event):
        message = event["message"]
        created_at = event["created_at"]
        print(f"Sending notification to user {self.user_id}: {message}")
        await self.send(text_data=json.dumps({
            "message": message,
            "created_at": created_at
        }))
        print(f"Notification sent to user {self.user_id}")
