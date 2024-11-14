# serializers.py
from rest_framework import serializers
from .models import Post, Comment, Like, Share
from user_authentication.models import CustomUser, InvestorPreferences
from user_management.models import BusinessPreferences


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = serializers.ImageField()

    def to_representation(self, instance):
        """
        This method will customize the way user information is serialized 
        based on the user role (Investor or Business).
        """
        user_data = {
            'id': instance.id,
        }

        if instance.role == 'investor':
            # Fetch Investor-related data
            try:
                investor_profile = instance.investor_preferences
                user_data['name'] = instance.full_name
                user_data['image'] = investor_profile.avatar_image.url if investor_profile.avatar_image else None
            except InvestorPreferences.DoesNotExist:
                user_data['name'] = instance.full_name
                user_data['image'] = None  # If no investor preferences exist, set image to None
        elif instance.role == 'business':
            # Fetch Business-related data
            try:
                business_profile = instance.business_preferences
                user_data['name'] = business_profile.company_name
                user_data['image'] = business_profile.avatar_image.url if business_profile.avatar_image else None
            except BusinessPreferences.DoesNotExist:
                user_data['name'] = "Business Profile"  # Default name if no business preferences
                user_data['image'] = None  # Default to None if no business preferences exist
        else:
            # For other roles, return basic info
            user_data['name'] = instance.full_name
            user_data['image'] = None  # No image if role is not recognized

        return user_data

class PostSerializer(serializers.ModelSerializer):
    total_likes = serializers.ReadOnlyField()
    total_comments = serializers.ReadOnlyField()
    total_shares = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'user', 'caption', 'location', 'image', 'created_at', 'total_likes', 'total_comments', 'total_shares', 'is_liked']
    def get_is_liked(self, obj):
            # Retrieve the authenticated user from the request
            user = self.context.get('request').user
            return obj.is_liked_by_user(user)

class CommentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'text', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'created_at']


class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = ['id', 'post', 'user', 'created_at']
