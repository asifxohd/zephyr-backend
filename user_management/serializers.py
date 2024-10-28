from rest_framework import serializers
from user_authentication.models import Industry, Location, InvestorPreferences, CustomUser
from .models import *
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class LocationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Location model.
    
    Includes the 'id' and 'name' fields.
    """

    class Meta:
        model = Location
        fields = ['id', 'name']


class IndustrySerializer(serializers.ModelSerializer):
    """
    Serializer for the Industry model.
    
    Includes the 'id' and 'name' fields.
    """

    class Meta:
        model = Industry
        fields = ['id', 'name']


class CombinedIndustryLocationSerializer(serializers.Serializer):
    """
    Serializer for combining locations and industries.

    This serializer is used to represent a combined response of locations and industries.
    
    Fields:
        locations (List[LocationSerializer]): A list of location objects.
        industries (List[IndustrySerializer]): A list of industry objects.
    """
    locations = serializers.ListSerializer(child=LocationSerializer())
    industries = serializers.ListSerializer(child=IndustrySerializer())



class InvestorPreferencesSerializer(serializers.ModelSerializer):
    preferred_locations = LocationSerializer(many=True, read_only=True)
    preferred_industries = IndustrySerializer(many=True, read_only=True)
    full_name = serializers.CharField(source='user.full_name', required=False)
    phone_number = serializers.CharField(source='user.phone_number', required=False)
    
    class Meta:
        model = InvestorPreferences
        fields = [
            'cover_image', 
            'avatar_image', 
            'preferred_locations', 
            'preferred_industries', 
            'description',
            'full_name',
            'phone_number'
        ]
    def update(self, instance, validated_data):
        # Extract user data if present
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
        
        # Update user fields if they exist
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        # Update preference fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model.

    This serializer is used to represent a custom user, including their investor preferences
    if applicable.

    Fields:
        full_name (str): The full name of the user.
        phone_number (str): The phone number of the user.
        email (str): The email address of the user.
        investor_preferences (InvestorPreferencesSerializer): The investor preferences associated with the user.
    """
    investor_preferences = InvestorPreferencesSerializer()

    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone_number', 'email', 'investor_preferences']
        
class DocumentsBusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentsBusiness
        fields = ['document_title', 'document_description', 'document_file']

class VideoPitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoPitch
        fields = ['video_title', 'video_description', 'video_file']



class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['phone_number']
        

class BusinessPreferencesSerializer(serializers.ModelSerializer):
    industry = serializers.SlugRelatedField(slug_field='name', queryset=Industry.objects.all())
    location = serializers.SlugRelatedField(slug_field='name', queryset=Location.objects.all())
    user = BusinessProfileSerializer()

    class Meta:
        model = BusinessPreferences
        fields = [
            'company_name',
            'industry',
            'location',
            'user',  
            'business_type',
            'company_stage',
            'company_description',
            'seeking_amount',
            'website',
            'product_type',
            'annual_revenue',
            'employee_count',
            'linkedIn',
            'facebook',
            'twitter',
            'avatar_image',
            'cover_image'
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)

        if user_data:
            phone_number = user_data.get('phone_number')
            if phone_number:
                current_phone_number = instance.user.phone_number
                if phone_number != current_phone_number:
                    if CustomUser.objects.filter(phone_number=phone_number).exclude(id=instance.user.id).exists():
                        raise serializers.ValidationError({"phone_number": "This phone number is already in use."})
                instance.user.phone_number = phone_number
                instance.user.save()

        if 'avatar_image' in validated_data:
            instance.avatar_image = validated_data.pop('avatar_image')
        if 'cover_image' in validated_data:
            instance.cover_image = validated_data.pop('cover_image')

        return super().update(instance, validated_data)