from rest_framework import serializers
from .models import Connections
from django.contrib.auth import get_user_model
from user_authentication.models import InvestorPreferences
from user_management.models import BusinessPreferences
from user_authentication.models import CustomUser

User = get_user_model()

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connections
        fields = ['follower', 'followed', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'followers_count', 'following_count']

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id','name', 'role', 'email', 'avatar_image']

    def get_avatar_image(self, obj):
        # Handle investor role
        if obj.role == 'investor':
            investor_pref = getattr(obj, 'investor_preferences', None)
            return investor_pref.avatar_image.url if investor_pref and investor_pref.avatar_image else None
        
        # Handle business role, with error handling if 'business_preferences' doesn't exist
        elif obj.role == 'business':
            business_pref = getattr(obj, 'business_preferences', None)
            return business_pref.avatar_image.url if business_pref and business_pref.avatar_image else None
        
        # Default case
        return None

    def get_name(self, obj):
        # Handle business role, with error handling if 'business_preferences' doesn't exist
        if obj.role == 'business':
            business_pref = getattr(obj, 'business_preferences', None)
            return business_pref.company_name if business_pref else obj.full_name
        
        # Default case for other roles
        return obj.full_name
