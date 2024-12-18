from django.db import models
from user_authentication.models import CustomUser
from django.db.models import Q

TEXT = 'text'
IMAGE = 'image'
VOICE = 'voice'

CONTENT_TYPE_CHOICES = [
    (TEXT, 'Text'),
    (IMAGE, 'Image'),
    (VOICE, 'Voice'),
]

SENT = 'sent'
DELIVERED = 'delivered'
READ = 'read'

STATUS_CHOICES = [
    (SENT, 'Sent'),
    (DELIVERED, 'Delivered'),
    (READ, 'Read'),
]

class ConversationManager(models.Manager):
    def by_user(self, user):
        """Retrieve all conversations that the user is a participant in."""
        lookup = Q(user_one=user) | Q(user_two=user)
        return self.get_queryset().filter(lookup).distinct()

class Conversation(models.Model):
    user_one = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations_as_user_one')
    user_two = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations_as_user_two')
    last_updated = models.DateTimeField(auto_now=True)  # Timestamp of the last update (e.g., last message)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the conversation was created

    objects = ConversationManager()  
    
    class Meta:
        unique_together = ['user_one', 'user_two']

    def __str__(self):
        return f"Conversation between {self.user_one} and {self.user_two}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, null=True, blank=True, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sent_messages")  # User who sent the message
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, default=TEXT)  # Type of content (text, image, or voice)
    content = models.TextField(blank=True, null=True)  # Text content (for text messages)
    image = models.ImageField(upload_to='message_images/', null=True, blank=True)  # For image messages
    voice = models.FileField(upload_to='message_voices/', null=True, blank=True)  # For voice messages
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=SENT)  # Message status (sent, delivered, read)
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp when the message was sent

    class Meta:
        ordering = ['timestamp']  

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

    def get_content(self):
        """Returns the appropriate content based on message type."""
        if self.content_type == TEXT:
            return self.content
        elif self.content_type == IMAGE:
            return self.image.url if self.image else None
        elif self.content_type == VOICE:
            return self.voice.url if self.voice else None
        return None

    def mark_as_delivered(self):
        """Mark the message as delivered."""
        self.status = DELIVERED
        self.save()

    def mark_as_read(self):
        """Mark the message as read."""
        self.status = READ
        self.save()

class OnlineChatStatus(models.Model):
    # STATUS_CHOICES = [
    #     ('offline', 'Offline'),
    #     ('online', 'Online'),
    # ]
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    status=models.CharField(max_length=20,default='offline')

    def __str__(self) -> str:
        return f"user:{self.user}-status:{self.status}"