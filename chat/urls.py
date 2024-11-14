from django.urls import path, include
from .views import UserProfileView, ConversationMessagesView

urlpatterns = [
    path('user/messages/', UserProfileView.as_view(), name='user-profile'),
    path('messages/<int:user_id>/', ConversationMessagesView.as_view(), name='conversation-messages'),

]
