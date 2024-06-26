"""Imports"""
import random
import json
from datetime import datetime
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
from django.core.exceptions import PermissionDenied



class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User objects.
    """

    class Meta:
        """
        Handling model information while registering users.
        """
        model = CustomUser
        fields = ['username', 'email', 'password', 'phone_number', 'role', 'full_name']
        extra_kwargs = {'password': {'write_only': True}}

    def save(self, **kwargs):
        """
        Custom method to save user data in Redis.
        """
        from .views import MessageHandler
        
        redis_connection = get_redis_connection("default")
        validated_data = dict(self.validated_data)
        otp = random.randint(100000, 999999)
        print(otp)
        validated_data['otp'] = otp
        current_time = datetime.now()
        validated_data['otp_generated_time'] = current_time.strftime("%H:%M:%S")
        validated_data_json = json.dumps(validated_data)
        print(validated_data_json)
        redis_connection.setex(validated_data['phone_number'], 1800, validated_data_json)
        message_handler = MessageHandler(validated_data['phone_number'], otp)
        try:
            message_handler.send_otp_via_message()
        except Exception as e:
            print("error while sending OTP via message handler, try again: ", e)
        
        return validated_data

    
    
class OTPSerializer(serializers.Serializer):
    """
    Serializer for validating OTP (One-Time Password) data.

    Attributes:
        phone_number (str): The phone number associated with the OTP.
        otp (str): The OTP code to be validated, typically a 6-digit code.
    """

    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class SuperuserLoginSerializer(serializers.Serializer):
    """
    Serializer for validating superuser login credentials.

    Attributes:
        username (str): The username of the superuser.
        password (str): The password of the superuser.
    """
    username = serializers.CharField()
    password = serializers.CharField()
    
    
class MyTokenSerializer(TokenObtainPairSerializer):
    """
    Customizing the token serializer to include additional user information.
    """

    @classmethod
    def get_token(cls, user):
        if user.status:
            token = super().get_token(user)
            token['full_name'] = user.full_name
            token['email'] = user.email
            token['is_active'] = user.is_active
            token['role'] = user.role if user.role else "admin"

            return token
        else:
            raise PermissionDenied("User Is tempararily Blocked")


class InvestorPreferencesSerializer(serializers.ModelSerializer):
    """ your defentition of the class serialzer"""
    preferred_industries = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)
    preferred_locations = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta:
        model = InvestorPreferences
        fields = ['user_id', 'preferred_industries', 'preferred_locations']
        
  
class GoogleAuthSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user.
    """
    class Meta:
        model = CustomUser  
        fields = ['username', 'email', 'password', 'phone_number', 'role', 'full_name']

    

