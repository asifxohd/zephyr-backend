from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as status_code
from django.db.models import Max
from .models import Conversation, Message
from user_authentication.models import CustomUser, InvestorPreferences
from user_management.models import BusinessPreferences
from connections.models import Connections
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from .serializers import MessageSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status_code.HTTP_404_NOT_FOUND)

        # Fetch connections where the authenticated user is the follower (following other users)
        following_users = Connections.objects.filter(
            follower=user
        ).exclude(followed__role='admin')

        # List to store profile data of followed users
        user_profiles = []

        for connection in following_users:
            # Get the followed user
            followed_user = connection.followed

            # Fetch user name based on role
            if followed_user.role == 'business':
                business_pref = BusinessPreferences.objects.filter(user=followed_user).first()
                user_name = business_pref.company_name if business_pref and business_pref.company_name else followed_user.full_name
            else:
                user_name = followed_user.full_name

            # Fetch avatar image based on role
            if followed_user.role == 'investor':
                avatar = InvestorPreferences.objects.filter(user=followed_user).first()
                avatar_image = avatar.avatar_image.url if avatar else None
            elif followed_user.role == 'business':
                avatar = BusinessPreferences.objects.filter(user=followed_user).first()
                avatar_image = avatar.avatar_image.url if avatar else None
            else:
                avatar_image = None

            # Fetch status (assuming an online/offline tracking mechanism is in place)
            status = "Offline"  # Placeholder (replace with actual logic if available)

            # Fetch the last message for the conversation with the followed user
            conversation = Conversation.objects.filter(
                Q(user_one=followed_user, user_two=user) | Q(user_one=user, user_two=followed_user)
            ).first()
            
            last_message = None
            last_seen_time = None
            if conversation:
                last_msg = Message.objects.filter(conversation=conversation).order_by('-timestamp').first()
                if last_msg:
                    last_message = last_msg.get_content()
                    last_seen_time = last_msg.timestamp
                else:
                    last_message = "No messages"
                    last_seen_time = None
            else:
                last_message = "No messages"
                last_seen_time = None

            # Prepare the profile data for each followed user
            profile_data = {
                "user_id": followed_user.id,
                "user_name": user_name,
                "status": status,
                "avatar_image": avatar_image,
                "last_message": last_message,
                "last_seen_time": last_seen_time,
            }

            user_profiles.append(profile_data)

        return Response(user_profiles, status=status_code.HTTP_200_OK)



class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = request.user
        conversation = Conversation.objects.filter(
            (Q(user_one=user) & Q(user_two__id=user_id)) |
            (Q(user_one__id=user_id) & Q(user_two=user))
        ).first()
        if not conversation:
            return Response({"messages": []})

        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        
        return Response({"messages": serializer.data})