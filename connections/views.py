from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Connections
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .serializers import FollowSerializer, UserProfileSerializer
from user_authentication.models import CustomUser
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from chat.models import Conversation

User = get_user_model()

class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        followed = get_object_or_404(User, id=user_id)
        follower = request.user

        if Connections.objects.filter(follower=follower, followed=followed).exists():
            return Response({"detail": "Already following this user."}, status=status.HTTP_400_BAD_REQUEST)

        Connections.objects.create(follower=follower, followed=followed)
        Conversation.objects.create(user_one=follower, user_two=followed)
        return Response({"detail": "User followed successfully."}, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        followed = get_object_or_404(User, id=user_id)
        follower = request.user

        connection = Connections.objects.filter(follower=follower, followed=followed).first()
        chat = Conversation.objects.filter(user_one=follower, user_two=followed).first()

        if not connection:
            return Response({"detail": "Not following this user."}, status=status.HTTP_400_BAD_REQUEST)

        connection.delete()
        chat.delete()
        return Response({"detail": "User unfollowed successfully."}, status=status.HTTP_204_NO_CONTENT)

class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        followers = user.followers.all()
        serializer = FollowSerializer(followers, many=True)
        return Response(serializer.data)

class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        following = user.following.all()
        serializer = FollowSerializer(following, many=True)
        return Response(serializer.data)


class CheckFollowStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_id):
        """
        Checks if the logged-in user is following the given business (business_id).
        """
        user = request.user 
        is_following = Connections.objects.filter(follower=user, followed_id=business_id).exists()
        return Response({'is_following': is_following})
    

class UserConnectionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        followers = CustomUser.objects.filter(following__followed=user)
        following = CustomUser.objects.filter(followers__follower=user)

        followers_data = UserProfileSerializer(followers, many=True).data
        following_data = UserProfileSerializer(following, many=True).data

        return Response({
            'followers': followers_data,
            'following': following_data
        })
        
class UserFollowersFollowingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None, *args, **kwargs):
        target_user = get_object_or_404(CustomUser, id=user_id)
        followers = CustomUser.objects.filter(following__followed=target_user)
        following = CustomUser.objects.filter(followers__follower=target_user)
        followers_data = UserProfileSerializer(followers, many=True).data
        following_data = UserProfileSerializer(following, many=True).data
        
        return Response({
            'followers': followers_data,
            'following': following_data
        })
        
class SuggestedUsersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        suggested_users = self.get_suggested_users(request)
        serializer = UserProfileSerializer(suggested_users, many=True)
        return Response(serializer.data)
    
    def get_suggested_users(self, request):
        current_user = request.user

        # Step 1: Base Query - Exclude current user, 'admin' role, and already-followed users
        followed_user_ids = Connections.objects.filter(follower=current_user).values_list('followed_id', flat=True)
        base_users = CustomUser.objects.filter(
            ~Q(role='admin'),
            ~Q(id=current_user.id),
            ~Q(id__in=followed_user_ids)
        )

        # Step 2: Mutual Connection Scoring - annotate users with mutual followers count
        mutual_connections = Connections.objects.filter(
            follower__in=base_users, 
            followed=current_user
        ).values('follower_id').annotate(mutual_count=Count('follower_id'))

        # Build a user list with mutual connections prioritized
        suggested_users = base_users.annotate(
            mutual_count=Count('followers__follower_id', filter=Q(followers__follower=current_user))
        ).order_by('-mutual_count')

        # Step 3: Additional Sorting and Randomization
        # Order users by mutual connection count, then by recent activity, finally randomize a few for diversity
        recently_active_time = timezone.now() - timedelta(days=7)
        active_users = suggested_users.filter(last_login__gte=recently_active_time).order_by('?')[:5]  # Top 5 active users
        diverse_users = suggested_users.order_by('?')[:7]  # Add randomness for variety

        # Combine active and diverse users
        final_suggestions = list(active_users) + list(diverse_users)

        return final_suggestions[:7]  