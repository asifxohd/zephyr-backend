from rest_framework_simplejwt.views import TokenObtainPairView
from .serializer import *
from rest_framework.views import APIView
from django_redis import get_redis_connection
import json , random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status, generics
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from decouple import config
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password




class MyTokenObtainPairView(TokenObtainPairView):
    """
    token class view jwt
    """

    serializer_class = MyTokenSerializer


class UserRegistrationView(APIView):
    """
    API view to handle user registration, cache validated data in Redis,
    and send a One-Time Password (OTP) to the client's email.

    The process includes:
    - Validating the incoming registration data.
    - Caching the validated data along with an OTP and expiry time in Redis.
    - Sending the OTP to the provided email address.
    """

    def post(self, request):
        """
        Handle POST requests to register a user.

        Steps:
        1. Validate the user data using `CustomeUserModelSerializer`.
        2. Generate an OTP and expiry time.
        3. Cache the validated data and OTP in Redis with a time-to-live (TTL) of 30 minutes.
        4. Send the OTP to the user's email.

        Returns:
            - HTTP 200 OK: If the OTP is successfully sent to the user's email.
            - HTTP 400 Bad Request: If the provided data is invalid.
            - HTTP 500 Internal Server Error: If caching the data or sending the OTP fails.
        """
        try:
            print(request.data)
            serializer = CustomeUserModelSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                redis_connection = get_redis_connection("default")
                email = validated_data.get("email")
                otp_expiry_time = (datetime.now() + timedelta(minutes=1)).strftime(
                    "%H:%M:%S"
                )
                validated_data["otp_expiry_time"] = otp_expiry_time
                otp = random.randint(111111, 999999)
                validated_data["otp"] = otp
                validated_data_json = json.dumps(validated_data)
                try:
                    redis_connection.setex(email, 3600, validated_data_json)

                except Exception as e:
                    return Response(
                        {"error": "Failed to cache data. Please try again."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                if validated_data.get("email"):
                    try:
                        email_view = EmailSendingView()
                        email_view.send_otp(validated_data.get("email"), otp)
                    except Exception as e:
                        return Response(
                            {"error": "Failed to send OTP email. Please try again."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                return Response(
                    {"message": "OTP sent to email id."}, status=status.HTTP_200_OK
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except (ValidationError, DjangoValidationError) as e:
            return Response(
                {"error": "Validation error. Please check your data and try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EmailSendingView:
    """
    Handles sending emails, such as sending an OTP to the user's email.
    """

    def send_otp(self, email, otp):
        """
        Sends the OTP to the provided email address.

        Args:
            email (str): The recipient's email address.
            otp (int): The OTP to be sent.
        """
        subject = "Your OTP Code"
        message = f"Your OTP code is {otp}. It is valid for the next 1 minutes."
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        send_mail(subject, message, email_from, recipient_list)
        print(f"OTP sent to {email}")


class OtpVerificationView(APIView):
    """
    Handles OTP (One-Time Password) verification.

    This view checks the validity of the OTP provided by the user against
    the OTP stored in Redis. It also ensures that the OTP has not expired.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize Redis connection once.
        """
        super().__init__(*args, **kwargs)
        self.redis_connection = get_redis_connection("default")

    def post(self, request):
        """
        POST method to verify OTP.

        Validates the OTP and checks it against the cached OTP in Redis.
        If valid and not expired, it creates a new user and deletes the OTP
        from Redis.

        Args:
            request (Request): The incoming HTTP request containing the email and OTP.

        Returns:
            Response: A response indicating whether the OTP verification was successful or not.
        """
        otp_serializer = OtpVerificationSerializer(data=request.data)
        print(otp_serializer)
        if otp_serializer.is_valid():
            email = otp_serializer.validated_data["email"]
            input_otp = request.data.get("otp")

            user_data = self._get_user_data_from_redis(email)
            if user_data:
                response = self._validate_otp(user_data, input_otp)
                if response:
                    return response

            return Response(
                {
                    "message": "No OTP found for the provided email. Please restart the registration process."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {"message": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST
        )

    def _get_user_data_from_redis(self, email):
        """
        Retrieves user data from Redis using the provided email.

        Args:
            email (str): The email address to retrieve data for.

        Returns:
            dict or None: The user data if found, otherwise None.
        """
        data_json = self.redis_connection.get(email)
        print(data_json)
        return json.loads(data_json) if data_json else None

    def _validate_otp(self, user_data, input_otp):
        """
        Validates the OTP against the stored OTP and checks for expiry.

        Args:
            user_data (dict): The user data retrieved from Redis.
            input_otp (str): The OTP provided by the user.

        Returns:
            Response or None: A response indicating the result of OTP validation, or None if valid.
        """
        stored_otp = str(user_data.get("otp"))
        otp_expiry_time_str = user_data.get("otp_expiry_time")

        if input_otp == stored_otp:
            current_time = datetime.now()
            otp_expiry_time = datetime.strptime(otp_expiry_time_str, "%H:%M:%S").time()

            if current_time.time() <= otp_expiry_time:
                user_data.pop("otp", None)
                user_data.pop("otp_expiry_time", None)
                user_data.pop("confirm_password", None)
                user = CustomUser.objects.create_user(**user_data)
                self.redis_connection.delete(user_data.get("email"))

                return Response(
                    {"message": "OTP successfully validated"}, status=status.HTTP_200_OK
                )
            return Response(
                {"otp": "OTP has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"otp": "Invalid OTP. Please try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResendOtpView(APIView):
    """
    Handles resending of OTP (One-Time Password).

    This view generates a new OTP, updates the cached user data in Redis
    with the new OTP and expiry time, and sends the new OTP to the user via email.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize Redis connection once.
        """
        super().__init__(*args, **kwargs)
        self.redis_connection = get_redis_connection("default")

    def post(self, request):
        """
        POST method to resend OTP.

        Validates the email and generates a new OTP. Updates the cached user data
        in Redis with the new OTP and expiry time, and sends the new OTP to the user.

        Args:
            request (Request): The incoming HTTP request containing the email.

        Returns:
            Response: A response indicating whether the OTP was successfully resent or not.
        """
        email = request.data.get("email")
        print(email)

        if not email:
            return Response(
                {"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_data = self._get_user_data_from_redis(email)
        if user_data:
            new_otp = random.randint(111111, 999999)
            otp_expiry_time = (datetime.now() + timedelta(minutes=1)).strftime(
                "%H:%M:%S"
            )

            user_data["otp"] = new_otp
            user_data["otp_expiry_time"] = otp_expiry_time
            user_data_json = json.dumps(user_data)

            try:
                self.redis_connection.setex(email, 3600, user_data_json)
                email_view = EmailSendingView()
                email_view.send_otp(email, new_otp)

                return Response(
                    {"message": "New OTP has been sent to your email."},
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {"message": "Failed to resend OTP. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(
                {
                    "message": "No user data found for the provided email. Please restart the registration process."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_user_data_from_redis(self, email):
        """
        Retrieves user data from Redis using the provided email.

        Args:
            email (str): The email address to retrieve data for.

        Returns:
            dict or None: The user data if found, otherwise None.
        """
        data_json = self.redis_connection.get(email)
        return json.loads(data_json) if data_json else None


class GoogleLoginAPIView(APIView):
    """
    API view to handle Google login for users.
    """

    def post(self, request, *args, **kwargs):
        """
        Handles the POST request for Google login.

        - Retrieves email, full_name, and role from the request data.
        - Checks if a user with the provided email already exists.
        - If the user exists, generates JWT tokens for the user.
        - If the user does not exist, creates a new user, sets a password that cannot be used, and generates JWT tokens.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: A JSON response containing user data and JWT tokens, or an error message.
        """
        email = request.data.get("email")
        full_name = request.data.get("full_name")
        role = request.data.get("role", CustomUser.DEFAULT_ROLE)

        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = CustomUser.objects.filter(email=email).first()
        if user:
            serializer = CustomUserSerializer(user)
        else:
            user = CustomUser.objects.create(
                email=email, full_name=full_name, role=role
            )
            user.set_unusable_password()
            user.save()
            serializer = CustomUserSerializer(user)

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        access_token["email"] = user.email
        access_token["role"] = user.role
        access_token["full_name"] = user.full_name

        tokens = {
            "access": str(access_token),
            "refresh": str(refresh),
        }
        if user.status:
            return Response({"tokens": tokens}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied("User is temporarily blocked.")
        

class ChangePasswordViewProfile(generics.UpdateAPIView):
    """
    View to change the password of an authenticated user.

    This endpoint allows users to update their password. The user must be authenticated to access this view. 
    The request must contain the current password and the new password.

    **Request Body:**
    
    - `current_password`: string, the user's current password (required).
    - `new_password`: string, the new password the user wishes to set (required).

    **Responses:**

    - **200 OK**: Password successfully changed.
    - **400 Bad Request**: Validation errors, such as incorrect current password or weak new password.
    - **401 Unauthorized**: If the user is not authenticated.

    **Example Request:**
    
    .. code-block:: json

        {
            "current_password": "old_password",
            "new_password": "new_password123"
        }

    **Example Response:**
    
    .. code-block:: json

        {
            "status": "password set"
        }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        update_session_auth_hash(request, user)

        return Response({'status': 'password set'}, status=status.HTTP_200_OK)
    
    
    
class PasswordResetRequestView(generics.GenericAPIView):
    """
    Handles the password reset request by sending a password reset email to the user.

    **Request:**
    - Method: POST
    - Body: 
      - `email` (string): The email address associated with the user account.

    **Response:**
    - 200: Successful operation indicating that the reset email has been sent.
    - 400: Validation error if the email is not associated with any user.

    Example:
    ```
    {
        "email": "user@example.com"
    }
    ```
    """

    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        redis_connection = get_redis_connection("default")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = CustomUser.objects.get(email=email)
        token = default_token_generator.make_token(user)
        reset_link = config('BASE_URL') + f"change/password/{token}/"
        print(reset_link)
        redis_connection.setex(f"password_reset_token:{token}", 86400, user.id)
        
        # HTML content for the email
        html_content = f"""
        <div style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #3B81F6;">Reset Your Password</h2>
            <p>Hello,</p>
            <p>We received a request to reset your password. Click the button below to set a new password for your account:</p>
            <p>This will be Valid for only 24 Hours</p>
            <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; margin-top: 20px; color: white; background-color: #3B81F6; text-decoration: none; border-radius: 5px;">Reset Password</a>
            <p style="margin-top: 20px; font-size: 12px; color: #888;">If you did not request this, you can safely ignore this email.</p>
            <p>Thank you,<br>The Zephyr Team</p>
        </div>
        """
        
        # Create an email message with HTML content
        email_message = EmailMessage(
            subject='Password Reset Request',
            body=html_content,
            from_email='noreply@yourdomain.com',
            to=[email],
        )
        email_message.content_subtype = "html"  # Specify HTML content type
        
        # Send the email
        email_message.send()

        return Response({"detail": "Password reset email has been sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirms the password reset using a token and uid, and updates the user's password.

    **Request:**
    - Method: POST
    - Path Parameters:
      - `uidb64` (string): Base64 encoded user ID.
      - `token` (string): Token for password reset validation.
    - Body:
      - `password` (string): The new password to be set for the user.

    **Response:**
    - 200: Successful operation indicating the password has been reset.
    - 400: Validation error if the token is invalid or if password validation fails.

    Example:
    ```
    {
        "password": "newSecurePassword123"
    }
    ```
    """

    serializer_class = SetNewPasswordSerializer

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user.set_password(serializer.validated_data['password'])
            user.save()

            return Response({"detail": "Password has been reset."}, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
    
class ValidateTokenView(APIView):
    """
    post:
    Validate a password reset token.

    This endpoint is used to verify if a provided password reset token is valid. 
    The token is expected to be passed in the request body.

    Request Body:
        - token (string): Required. The password reset token to be validated.

    Responses:
        - 200 OK: Token is valid.
          Example response:
          {
              "success": True
          }
        
        - 400 Bad Request: Token is missing or the JSON is invalid.
          Example response:
          {
              "success": False,
              "error": "Token is required"
          }
          or
          {
              "success": False,
              "error": "Invalid JSON"
          }

        - 404 Not Found: Token is invalid or has expired.
          Example response:
          {
              "success": False
          }

        - 500 Internal Server Error: Unexpected error.
          Example response:
          {
              "success": False,
              "error": "Description of the error"
          }

    Exceptions:
        - JSONDecodeError: Raised if the provided JSON data is invalid.
        - Exception: Raised for any unexpected errors during processing.
    """
    def post(self, request):
        try:
            token = request.data.get('token')
            if not token:
                return Response({'success': False, 'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
            redis_connection = get_redis_connection("default")
            user_id = redis_connection.get(f"password_reset_token:{token}")
            if user_id:
                return Response({'success': True}, status=status.HTTP_200_OK)
            else:
                return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({'success': False, 'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
class ChangePasswordView(APIView):
    """
    post:
    Change the user's password using a password reset token.

    This endpoint allows users to change their password by providing a valid reset token and a new password.
    The token and new password are expected in the request body.

    Request Body:
        - token (string): Required. The password reset token used to verify the user's identity.
        - new_password (string): Required. The new password to be set for the user.

    Responses:
        - 200 OK: Password successfully changed.
          Example response:
          {
              "success": True,
              "message": "Password has been successfully changed"
          }
        
        - 400 Bad Request: Missing token or new password in the request.
          Example response:
          {
              "success": False,
              "error": "Token is required"
          }
          or
          {
              "success": False,
              "error": "New password is required"
          }

        - 404 Not Found: Invalid or expired token.
          Example response:
          {
              "success": False,
              "error": "Invalid or expired token"
          }

        - 500 Internal Server Error: Unexpected error during processing.
          Example response:
          {
              "success": False,
              "error": "Description of the error"
          }

    Exceptions:
        - Exception: Handles unexpected errors, returning a 500 status with the error message.
    """
    def post(self, request):
        try:
            token = request.data.get('token')
            new_password = request.data.get('new_password')
            if not token:
                return Response({'success': False, 'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
            if not new_password:
                return Response({'success': False, 'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)

            redis_connection = get_redis_connection("default")
            user_id = redis_connection.get(f"password_reset_token:{token}")
            if not user_id:
                return Response({'success': False, 'error': 'Invalid or expired token'}, status=status.HTTP_404_NOT_FOUND)

            user_id = int(user_id) 
            user = get_object_or_404(CustomUser, id=user_id)

            user.password = make_password(new_password)  
            user.save()

            redis_connection.delete(f"password_reset_token:{token}")

            return Response({'success': True, 'message': 'Password has been successfully changed'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)