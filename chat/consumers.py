# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer , WebsocketConsumer
from .models import Conversation, Message
from user_authentication.models import CustomUser
from django.utils import timezone
import json

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        """
        This method is called when a WebSocket connection is established. It is used to assign the user
        to a specific chat room based on their unique user ID, and adds the WebSocket connection to the
        corresponding group in the channel layer for real-time communication
        """
        user_id = self.scope['url_route']['kwargs']['id']
        chat_room = f'user_chatroom_{user_id}'
        self.chat_room = chat_room
        print(f"Connecting to {chat_room}")
        try:
            self.channel_layer.group_add(chat_room, self.channel_name)
            self.accept()
        except Exception as e:
            print(f"Error connecting: {e}")
            self.close()

    def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message')
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')

    def disconnect(self, close_code):
        pass
