"""Imports"""
import json
import random
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from twilio.rest import Client
from django_redis import get_redis_connection
from .models import CustomUser, Industry, Location , InvestorPreferences
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializer import *
from django.contrib.auth import authenticate
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from django.db.models import Q
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken




class UserViewSet(viewsets.ModelViewSet):
    """Handles user registration."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class MessageHandler:
    """Handles sending OTP messages."""
    phone_number = None
    otp = None
    
    def __init__(self, phone_number, otp) -> None:
        self.phone_number = phone_number
        self.otp = otp
    
    def send_otp_via_message(self):     
        """Send OTP via SMS."""
        client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
        message = client.messages.create(body=f'Your One Time OTP For Zephyr Registrations is: {self.otp}. Do not share this OTP with anyone',
                                        from_=f'{settings.TWILIO_PHONE_NUMBER}',
                                        to=f'{settings.COUNTRY_CODE}{self.phone_number}')

class OTPVerificationView(APIView):
    """Handles OTP verification."""
    def post(self, request):
        """POST method to verify OTP."""
        otp_serializer = OTPSerializer(data=request.data)
        if otp_serializer.is_valid():
            phone_number = otp_serializer.validated_data['phone_number']
            input_otp = request.data.get('otp')
            redis_connection = get_redis_connection("default")
            data_json = redis_connection.get(phone_number)
            if data_json is not None:
                user_data = json.loads(data_json)
                if input_otp == str(user_data['otp']):
                    current_time = datetime.now()
                    otp_generated_time_str = user_data['otp_generated_time']
                    otp_generated_time_str_with_date = f"{current_time.date()} {otp_generated_time_str}"
                    otp_generated_time = datetime.strptime(otp_generated_time_str_with_date, "%Y-%m-%d %H:%M:%S")
                    time_difference = current_time - otp_generated_time
                    if time_difference <= timedelta(seconds=80):
                        user_data.pop('otp', None)
                        user_data.pop('otp_generated_time', None)
                        user = CustomUser.objects.create_user(**user_data)
                        print(user)
                        redis_connection.delete(phone_number)
                        print("OTP successfully validated")
                        return Response({"message": "OTP successfully validated", "user":user.id}, status=status.HTTP_200_OK)
                    else:
                        return Response({"message": "OTP validation timeout"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                message = "Something went wrong. Please restart the registration process."
                return Response({"message": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)


class ResendOtpView(APIView):
    """ Handles OTP Resending """
    def post(self, request):
        """POST method to resend OTP."""
        print(request.data)
        phone_number = request.data.get('phone_number')
        print(phone_number)
        current_time = datetime.now()
        redis_connection = get_redis_connection("default")
        
        if redis_connection.exists(phone_number):
            data_json = redis_connection.get(phone_number)
            user_data = json.loads(data_json)
            
            new_otp = random.randint(100000, 999999)
            print(new_otp)
            
            user_data['otp'] = new_otp
            user_data['otp_generated_time'] = current_time.strftime("%H:%M:%S")
            
            redis_connection.set(phone_number, json.dumps(user_data))
            message_handler = MessageHandler(phone_number, new_otp)
            try:
                message_handler.send_otp_via_message()
            except Exception as e:
                print("Error while sending OTP via message handler, try again: ", e)
            
            return Response({"message": "OTP resent successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Retry the registration process"}, status=status.HTTP_400_BAD_REQUEST)
        
        
class MyTokenObtainPairView(TokenObtainPairView):

    """
    Your view class description.
    """
    serializer_class = MyTokenSerializer
    
    


class IndustryAndLocation(APIView):
    """
    API endpoint to retrieve industry and location data.
    """

    def get(self, request):
        """
        Handle GET request to fetch industry and location data.

        Returns:
            JsonResponse: JSON response containing industryData and locationData.
        """
        industry_data = Industry.objects.all()
        location_data = Location.objects.all()
        
        serialized_industry_data = [{'value': industry.name, 'label': industry.name} for industry in industry_data]
        serialized_location_data = [{'value': location.name, 'label': location.name} for location in location_data]
        
        return Response({
            'industryData': serialized_industry_data,
            'locationData': serialized_location_data
        })


class SaveInvestorPreferences(APIView):
    """
    API endpoint for saving investor preferences.
    """

    def post(self, request):
        """
        Handle POST request to save investor preferences.
        """
        user_id = request.data.get('user_id')
        user_instance = CustomUser.objects.filter(pk=user_id).first()
        if not user_instance:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        industries = request.data.get('industries', [])
        locations = request.data.get('locations', [])

        industries_objs = Industry.objects.filter(name__in=industries)
        locations_objs = Location.objects.filter(name__in=locations)

        with transaction.atomic():
            investor_preferences = InvestorPreferences.objects.create(user_id=user_instance)
            investor_preferences.preferred_industries.set(industries_objs)
            investor_preferences.preferred_locations.set(locations_objs)
        
        # saved_preferences = InvestorPreferences.objects.filter(user_id=user_instance)
        # saved_preferences_data = InvestorPreferencesSerializer(saved_preferences, many=True).data


        response_data = {
            'message': 'Investor preferences saved successfully',
            'user_id': user_id,
            'saved_industries': [ind.name for ind in industries_objs],
            'saved_locations': [loc.name for loc in locations_objs]
        }

        return Response(response_data, status=status.HTTP_200_OK)

class GoogleAuthVerificationRequest(APIView):
    """
    Handling the second step of the GoogleAuthVerificationRequest.
    """
    def post(self, request):
        """
        Verify Google authentication and create a new user

        Parameters:
        - request (HttpRequest): HTTP request object containing user data.

        Returns:
        - Response: JSON response containing user data, access token, and refresh token, or error message.
        """
        new_user = request.data
        print(new_user)
        serializer = GoogleAuthSerializer(data=new_user)
        if serializer.is_valid():
            user = serializer.save()
            tokens_data = self.generate_tokens(user)
            return Response(tokens_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                        
    def generate_tokens(self, user):
        """
        Generate access and refresh tokens for the given user and return them along with additional user data.
        
        Parameters:
        - user (CustomUser): User object for which tokens are generated.

        Returns:
        - dict: Dictionary containing access and refresh tokens along with additional user data.
        """
        token = AccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)
        additional_data = {
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'email': user.email,
            'role': user.role
        }
        token.payload.update(additional_data)
        refresh.payload.update(additional_data)

        return {
            'refresh': str(refresh),
            'access': str(token)
        }


class CheckUserForGoogleAuth(APIView):
    """API endpoint to check user existence and generate Google authentication tokens."""

    def post(self, request):
        """Handles POST requests to check user existence and generate tokens.

        Request Body:
            email (str): The email address of the user.

        Returns:
            Response: Tokens if user exists, else user existence status.
        """
        email = request.data.get('email')
        print(email)
        user = CustomUser.objects.filter(email=email).first()
        if user:
            if user.status != False:
                google_auth_request = GoogleAuthVerificationRequest()
                tokens_data = google_auth_request.generate_tokens(user)
                return Response(tokens_data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'User is blocked'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'user_exists': False}, status=status.HTTP_404_NOT_FOUND)
