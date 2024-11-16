from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Conversation, Message
from user_authentication.models import CustomUser
from django.utils import timezone
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id = self.scope['url_route']['kwargs']['id']
        self.user = await self.get_user(user_id)
        self.chat_room = f'conversation_{self.scope["url_route"]["kwargs"]["id"]}'

        try:
            await self.channel_layer.group_add(self.chat_room, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Error connecting: {e}")
            await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message')
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')
        conversation_id = data.get('conversation_id')
        
        sender = await self.get_user(sender_id)
        receiver = await self.get_user(receiver_id)
        
        # Define chat rooms for both sender and receiver
        sender_room = f'conversation_{sender_id}'
        receiver_room = f'conversation_{receiver_id}'
        
        conversation = await self.get_conversation(conversation_id)
        message = await self.create_message(conversation, sender, message_content)

        # Send the message to both sender's and receiver's chat rooms
        await self.send_chat_message(message, [sender_room, receiver_room])

    async def send_chat_message(self, message, rooms):
        """
        Send the chat message to multiple chat rooms.
        """
        message_data = {
            'type': 'chat_message',
            'id': message.id,
            'sender': message.sender.id,
            'content_type': message.content_type,
            'content': message.content,
            'image': message.image or None,
            'voice': message.voice or None,
            'status': message.status,
            'timestamp': message.timestamp.isoformat(),
        }
        
        for room in rooms:
            await self.channel_layer.group_send(room, message_data)

    async def chat_message(self, event):
        """
        Forward the received message to the WebSocket client.
        """
        # Extract event data
        id = event['id']
        sender_id = event['sender']
        content_type = event['content_type']
        content = event['content']
        image = event.get('image')
        voice = event.get('voice')
        status = event['status']
        timestamp = event['timestamp']

        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'id': id,
            'sender': sender_id,
            'content_type': content_type,
            'content': content,
            'image': image,
            'voice': voice,
            'status': status,
            'timestamp': timestamp,
        }))

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.chat_room, self.channel_name)
        except Exception as e:
            print(f"Error disconnecting: {e}")

    @database_sync_to_async
    def get_user(self, user_id):
        return CustomUser.objects.get(id=int(user_id))

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        return Conversation.objects.get(id=int(conversation_id))

    @database_sync_to_async
    def create_message(self, conversation, sender, content):
        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            content_type='text',
            content=content,
            status='sent',
            timestamp=timezone.now()
        )