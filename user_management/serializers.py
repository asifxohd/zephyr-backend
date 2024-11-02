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
    user = BusinessProfileSerializer(read_only=True)

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
        if 'avatar_image' in validated_data:
            instance.avatar_image = validated_data.pop('avatar_image')
        if 'cover_image' in validated_data:
            instance.cover_image = validated_data.pop('cover_image')

        return super().update(instance, validated_data)
    

class VideoPitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoPitch
        fields = ['id', 'video_title', 'video_description', 'video_file']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)
    
class DocumentsBusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentsBusiness
        fields = ['id','document_title', 'document_description', 'document_file']
        
        

class CombinedDataBusinessProfileSerializer(serializers.ModelSerializer):
    business_preferences = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    video_pitch = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'role', 'full_name', 'email', 'status',
                  'business_preferences', 'documents', 'video_pitch']

    def get_business_preferences(self, obj):
        try:
            preferences = BusinessPreferences.objects.get(user=obj)
            return {
                'cover_image': preferences.cover_image.url if preferences.cover_image else None,
                'avatar_image': preferences.avatar_image.url if preferences.avatar_image else None,
                'company_name': preferences.company_name,
                'industry': preferences.industry.name if preferences.industry else None,
                'location': preferences.location.name if preferences.location else None,
                'business_type': preferences.business_type,
                'company_stage': preferences.company_stage,
                'listed_status': preferences.listed_status,
                'company_description': preferences.company_description,
                'seeking_amount': str(preferences.seeking_amount),
                'website': preferences.website,
                'product_type': preferences.product_type,
                'annual_revenue': str(preferences.annual_revenue),
                'employee_count': preferences.employee_count,
                'linkedIn': preferences.linkedIn,
                'facebook': preferences.facebook,
                'twitter': preferences.twitter,
            }
        except BusinessPreferences.DoesNotExist:
            return None

    def get_documents(self, obj):
        documents = DocumentsBusiness.objects.filter(user=obj)
        return [
            {
                'id':doc.id,
                'document_title': doc.document_title,
                'document_description': doc.document_description,
                'document_file': doc.document_file.url if doc.document_file else None
            }
            for doc in documents
        ]

    def get_video_pitch(self, obj):
        try:
            video = VideoPitch.objects.get(user=obj)
            return {
                'video_title': video.video_title,
                'video_description': video.video_description,
                'video_file': video.video_file.url if video.video_file else None
            }
        except VideoPitch.DoesNotExist:
            return None
        


class InvestorSerializer(serializers.ModelSerializer):
    """
    Serializer to represent investor users along with their preferences.

    Fields:
        avatar_image (str): URL of the user's avatar image.
        full_name (str): Full name of the user.
        email (str): Email address of the user.
        phone_number (str): Phone number of the user.
        status (bool): Status indicating if the user's account is active.
    """

    avatar_image = serializers.ImageField(source='investor_preferences.avatar_image', required=False)
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    status = serializers.BooleanField()

    class Meta:
        model = CustomUser
        fields = ['id','avatar_image', 'full_name', 'email', 'phone_number', 'status']


class CustomInvestorUserSerializer(serializers.ModelSerializer):
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
        fields = ['id','status','full_name','date_joined', 'phone_number', 'email', 'investor_preferences']
        
    
class AdminBusinessSerializer(serializers.ModelSerializer):
    """
    Serializer to represent business users with specific fields.

    Fields:
        id (int): Unique identifier for the user.
        avatar_image (str): URL of the business's avatar image.
        full_name (str): Full name of the business user.
        email (str): Email address of the business user.
        phone_number (str): Phone number of the business user.
        status (bool): Status indicating if the business user's account is active.
        company_name (str): Name of the company associated with the business user.
    """

    avatar_image = serializers.ImageField(source='business_preferences.avatar_image', required=False)
    company_name = serializers.CharField(source='business_preferences.company_name', required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'avatar_image', 'full_name', 'email', 'phone_number', 'status', 'company_name']
        
        
        
class DetailedInformationForSpecificUserBusinessProfileSerializer(serializers.ModelSerializer):
    business_preferences = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    video_pitch = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'role', 'full_name', 'email', 'status',
                  'business_preferences', 'documents', 'video_pitch']

    def get_business_preferences(self, obj):
        try:
            preferences = BusinessPreferences.objects.get(user=obj)
            return {
                'cover_image': preferences.cover_image.url if preferences.cover_image else None,
                'avatar_image': preferences.avatar_image.url if preferences.avatar_image else None,
                'company_name': preferences.company_name,
                'industry': preferences.industry.name if preferences.industry else None,
                'location': preferences.location.name if preferences.location else None,
                'business_type': preferences.business_type,
                'company_stage': preferences.company_stage,
                'listed_status': preferences.listed_status,
                'company_description': preferences.company_description,
                'seeking_amount': str(preferences.seeking_amount),
                'website': preferences.website,
                'product_type': preferences.product_type,
                'annual_revenue': str(preferences.annual_revenue),
                'employee_count': preferences.employee_count,
                'linkedIn': preferences.linkedIn,
                'facebook': preferences.facebook,
                'twitter': preferences.twitter,
            }
        except BusinessPreferences.DoesNotExist:
            return None

    def get_documents(self, obj):
        documents = DocumentsBusiness.objects.filter(user=obj)
        return [
            {
                'id': doc.id,
                'document_title': doc.document_title,
                'document_description': doc.document_description,
                'document_file': doc.document_file.url if doc.document_file else None
            }
            for doc in documents
        ]

    def get_video_pitch(self, obj):
        try:
            video = VideoPitch.objects.get(user=obj)
            return {
                'video_title': video.video_title,
                'video_description': video.video_description,
                'video_file': video.video_file.url if video.video_file else None
            }
        except VideoPitch.DoesNotExist:
            return None
