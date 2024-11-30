from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Conversation, Message, OnlineChatStatus
from user_authentication.models import CustomUser
from django.utils import timezone
from channels.db import database_sync_to_async
from django_redis import get_redis_connection
from django.db.models import Q
import base64, os, uuid, logging, json
from django.core.files.base import ContentFile


logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Handle new WebSocket connection
        """
        try:
            # Extract user ID from the WebSocket connection URL
            user_id = self.scope['url_route']['kwargs']['id']
            
            # Retrieve the user
            self.user = await self.get_user(user_id)
            
            # Create a unique chat room for this user
            self.chat_room = f'user_{user_id}_chat'
            
            # Add the user to their personal chat room group
            await self.channel_layer.group_add(self.chat_room, self.channel_name)
            
            # Update user status
            await self.update_user_status('online')
            await self.update_user_status_db(user_id, 'online')
            
            # Broadcast status change to conversation partners
            await self.broadcast_status_change('online')
            
            # Accept the WebSocket connection
            await self.accept()
            
            logger.info(f"User {user_id} connected to WebSocket successfully")
        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        try:
            # Update user status to offline
            await self.update_user_status('offline')
            await self.update_user_status_db(self.user.pk, 'offline')
            
            # Broadcast status change
            await self.broadcast_status_change('offline')
            
            # Remove user from the chat room group
            await self.channel_layer.group_discard(self.chat_room, self.channel_name)
            
            logger.info(f"User {self.user.id} disconnected from WebSocket")
        
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {e}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages
        """
        try:
            # Parse incoming JSON data
            data = json.loads(text_data)
            message_type = data.get('content_type', 'message')

            if message_type == 'message':
                await self.handle_chat_message(data)
            elif message_type == 'status_request':
                await self.handle_status_request(data)
            elif message_type == 'audio':
                await self.handle_chat_audio(data)
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Message receive error: {e}")

    async def handle_chat_message(self, data):
        """
        Process and broadcast chat messages
        """
        try:
            # Extract message details
            message_content = data.get('message')
            sender_id = data.get('sender_id')
            receiver_id = data.get('receiver_id')
            
            # Get sender and receiver
            sender = await self.get_user(sender_id)
            receiver = await self.get_user(receiver_id)
            
            # Create chat rooms
            sender_room = f'user_{sender_id}_chat'
            receiver_room = f'user_{receiver_id}_chat'
            
            # Get or create conversation
            conversation = await self.get_or_create_conversation(sender, receiver)
            
            # Create message
            message = await self.create_message(conversation, sender, message_content)
            
            # Send message to both sender and receiver rooms
            await self.send_chat_message(message, [sender_room, receiver_room])
        
        except Exception as e:
            logger.error(f"Chat message handling error: {e}")

    async def handle_chat_audio(self, data):
        """
        Process and broadcast audio messages
        """
        try:
            audio_content = data.get('audio_data')
            sender_id = data.get('sender_id')
            receiver_id = data.get('receiver_id')
            
            sender = await self.get_user(sender_id)
            receiver = await self.get_user(receiver_id)
            
            sender_room = f'user_{sender_id}_chat'
            receiver_room = f'user_{receiver_id}_chat'
            
            conversation = await self.get_or_create_conversation(sender, receiver)
            
            message = await self.create_audio_message(conversation, sender, audio_content)
            
            await self.send_chat_message(message, [sender_room, receiver_room])
        
        except Exception as e:
            logger.error(f"Chat audio message handling error: {e}")

    async def handle_status_request(self, data):
        """
        Handle status request from client
        """
        try:
            user_id = data.get('user_id')
            if user_id:
                # Retrieve user status
                status = await self.get_user_status(user_id)
                
                # Send status response
                await self.send(text_data=json.dumps({
                    'type': 'status_response',
                    'user_id': user_id,
                    'status': status
                }))
        
        except Exception as e:
            logger.error(f"Status request error: {e}")

    async def broadcast_status_change(self, status):
        """
        Broadcast user status change to conversation partners
        """
        try:
            # Get users in conversations with current user
            conversation_users = await self.get_users_in_conversations()
            
            # Send status update to each conversation partner
            for user in conversation_users:
                user_room = f'user_{user.id}_chat'
                await self.channel_layer.group_send(
                    user_room,
                    {
                        "type": "status_update",
                        "user_id": self.user.id,
                        "status": status,
                    }
                )
        
        except Exception as e:
            logger.error(f"Status broadcast error: {e}")

    async def send_chat_message(self, message, rooms):
        """
        Send chat message to multiple rooms
        """

        try:
            # Prepare message data
            message_data = {
                'type': 'chat_message',
                'id': message.id,
                'sender': message.sender.id,
                'content_type': message.content_type,
                'content': message.content if message.content else None,
                'image': message.image.url if message.image else None,
                'voice': "media"+ "/" +message.voice.name if message.voice else None,
                'status': message.status,
                'timestamp': message.timestamp.isoformat(),
            }

            for room in rooms:
                await self.channel_layer.group_send(room, message_data)
        
        except Exception as e:
            logger.error(f"Send chat message error: {e}")

    async def chat_message(self, event):
        """
        Forward received message to WebSocket client
        """
        try:
            # Prepare event data
            event_data = event.copy()
            event_data.pop('type', None)
            
            # Send message to client
            await self.send(text_data=json.dumps(event_data))
        
        except Exception as e:
            logger.error(f"Chat message forwarding error: {e}")

    async def status_update(self, event):
        """
        Handle and forward status update messages
        """
        try:
            # Send status update to client
            await self.send(text_data=json.dumps({
                'type': 'status_update',
                'user_id': event['user_id'],
                'status': event['status']
            }))
        
        except Exception as e:
            logger.error(f"Status update sending error: {e}")

    async def update_user_status(self, status):
        """
        Update user status in Redis
        """
        try:
            # Get Redis connection
            redis_connection = get_redis_connection("default")
            
            # Set user status in Redis
            await database_sync_to_async(redis_connection.set)(
                f"user:{self.user.id}:status", status
            )
        
        except Exception as e:
            logger.error(f"Redis status update error: {e}")

    @database_sync_to_async
    def get_user(self, user_id):
        """
        Retrieve user from database
        """
        return CustomUser.objects.get(id=int(user_id))

    @database_sync_to_async
    def get_or_create_conversation(self, user_one, user_two):
        """
        Retrieve or create a conversation between two users
        """
        try:
            # Try to find existing conversation
            return Conversation.objects.get(
                (Q(user_one=user_one, user_two=user_two) | 
                 Q(user_one=user_two, user_two=user_one))
            )
        except Conversation.DoesNotExist:
            # Create new conversation if not exists
            return Conversation.objects.create(
                user_one=user_one, 
                user_two=user_two
            )

    @database_sync_to_async
    def create_message(self, conversation, sender, content):
        """
        Create and save text message to database
        """
        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            content_type='text',
            content=content,
            status='sent',
            timestamp=timezone.now()
        )
    
    @database_sync_to_async
    def create_audio_message(self, conversation, sender, content):
        """
        Create and save audio message to database
        """
        
        audio_file_name = f"{uuid.uuid4().hex}.webm"
        audio_data = base64.b64decode(content)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content_type='voice',
            status='sent',
            timestamp=timezone.now()
        )
        
        message.voice.save(audio_file_name, ContentFile(audio_data), save=True)
        
        return message

    @database_sync_to_async
    def get_user_status(self, user_id):
        """
        Retrieve user status from Redis
        """
        try:
            redis_connection = get_redis_connection("default")
            status = redis_connection.get(f"user:{user_id}:status")
            return status.decode('utf-8') if status else 'offline'
        except Exception as e:
            logger.error(f"Get user status error: {e}")
            return 'offline'
    
    @database_sync_to_async
    def update_user_status_db(self, user_id, status):
        """
        Update user status in database
        """
        try:
            # Get or create OnlineChatStatus
            online_status, created = OnlineChatStatus.objects.get_or_create(
                user_id=user_id,
                defaults={'status': status}
            )
            
            # Update status if not created
            if not created:
                online_status.status = status
                online_status.save()
            
            return online_status
        
        except Exception as e:
            logger.error(f"Database status update error: {e}")
            return None

    @database_sync_to_async
    def get_users_in_conversations(self):
        """
        Retrieve users involved in conversations with current user
        """
        try:
            # Find conversations involving the current user
            conversations = Conversation.objects.filter(
                Q(user_one=self.user) | Q(user_two=self.user)
            )
            
            # Get unique users from these conversations
            users = CustomUser.objects.filter(
                Q(conversations_as_user_one__in=conversations) | 
                Q(conversations_as_user_two__in=conversations)
            ).exclude(id=self.user.id).distinct()
            
            return list(users)
        
        except Exception as e:
            logger.error(f"Get conversation users error: {e}")
            return []