from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as status_code
from django.db.models import Max
from .models import Conversation, Message,OnlineChatStatus
from user_authentication.models import CustomUser, InvestorPreferences
from user_management.models import BusinessPreferences
from connections.models import Connections
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from .serializers import MessageSerializer
from django_redis import get_redis_connection


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status_code.HTTP_404_NOT_FOUND)

        # Fetch all conversations where the authenticated user is a participant
        conversations = Conversation.objects.filter(
            Q(user_one=user) | Q(user_two=user)
        ).order_by('-last_updated')  # Optionally order by the last updated timestamp

        user_profiles = []

        for conversation in conversations:
            # Determine the other user in the conversation
            other_user = conversation.user_two if conversation.user_one == user else conversation.user_one

            # Fetch user name based on role
            if other_user.role == 'business':
                business_pref = BusinessPreferences.objects.filter(user=other_user).first()
                user_name = business_pref.company_name if business_pref and business_pref.company_name else other_user.full_name
            else:
                user_name = other_user.full_name

            # Fetch avatar image based on role
            if other_user.role == 'investor':
                avatar = InvestorPreferences.objects.filter(user=other_user).first()
                avatar_image = avatar.avatar_image.url if avatar else None
            elif other_user.role == 'business':
                avatar = BusinessPreferences.objects.filter(user=other_user).first()
                avatar_image = avatar.avatar_image.url if avatar else None
            else:
                avatar_image = None

            # Fetch the last message for the conversation
            last_message = None
            last_seen_time = None
            last_msg = Message.objects.filter(conversation=conversation).order_by('-timestamp').first()
            if last_msg:
                last_message = last_msg.get_content()
                last_seen_time = last_msg.timestamp
            else:
                last_message = "No messages"
                last_seen_time = None

            # Fetch status (assuming an online/offline tracking mechanism is in place)
            # status = "Offline"  # Placeholder (replace with actual logic if available)
            # key = f"user:{other_user.pk}:status"
            try:
                status_obj = OnlineChatStatus.objects.get(user__id=other_user.pk)
                status = status_obj.status
                print(status_obj.user.email,status)
            except:
                # OnlineChatStatus.objects.create(user__id=other_user.pk,stat)
                status = 'offline'
            # redis_connection = get_redis_connection("default")

            # # Get the value for the key
            # try:
            #     status = redis_connection.get(key)
            #     status = status.decode('utf-8')
            #     print(status)
            # except:
            #     status='offline'
            #     print('offline')

        # 

            # Prepare the profile data for the other user in the conversation
            profile_data = {
                "user_id": other_user.id,
                "user_name": user_name,
                "status": status,
                "avatar_image": avatar_image,
                "last_message": last_message,
                "last_seen_time": last_seen_time,
                "conversation_id": conversation.id,  
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