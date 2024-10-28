from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import PermissionDenied
from .models import CustomUser
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password


class MyTokenSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that includes additional user information in the JWT.

    This serializer extends the default TokenObtainPairSerializer to include
    custom claims in the generated JWT. It adds the user's full name, email,
    active status, and role to the token payload.

    Raises:
        PermissionDenied: If the user's status is inactive (blocked), a permission
                          error is raised.
    """

    @classmethod
    def get_token(cls, user):
        """
        Customize the token payload with additional user information.

        Args:
            user (CustomUser): The user instance for which the token is being generated.

        Returns:
            token (Token): The customized JWT token with additional claims.

        Raises:
            PermissionDenied: If the user's status is inactive.
        """
        if user.status:
            token = super().get_token(user)
            token["full_name"] = user.full_name
            token["email"] = user.email
            token["is_active"] = user.is_active
            token["role"] = user.role if user.role else "admin"
            return token
        else:
            raise PermissionDenied("User is temporarily blocked.")

class CustomeUserModelSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model, used for validating user data.

    This serializer is designed to validate user registration data, including
    password confirmation, without saving the user object.

    Fields:
        full_name (str): The user's full name.
        email (str): The user's email address.
        phone_number (str): The user's phone number.
        password (str): The user's password (write-only).
        confirm_password (str): A field for confirming the user's password (write-only).
        role (str): The user's role in the system.
    """

    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "full_name",
            "email",
            "phone_number",
            "password",
            "confirm_password",
            "role",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        """
        Validate the password and confirm_password fields.

        Ensures that the password and confirm_password match during registration.
        It also applies Django's built-in password validators.

        Args:
            data (dict): The validated data from the serializer.

        Returns:
            dict: The validated data.

        Raises:
            serializers.ValidationError: If the passwords do not match or
                                         if the password doesn't meet validation criteria.
        """
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(password)
        return data

class OtpVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying OTPs (One-Time Passwords).

    This serializer validates the OTP and email address provided in the request.
    - `email`: Must be a valid email address.
    - `otp`: Must be a numeric string of exactly 6 digits.
    """

    email = serializers.EmailField(max_length=255)
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        """
        Validate the OTP field.

        Ensures that the OTP:
        - Contains only digits.
        - Is exactly 6 digits long.

        Args:
            value (str): The OTP value to validate.

        Returns:
            str: The validated OTP.

        Raises:
            serializers.ValidationError: If the OTP is not valid.
        """
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        if len(value) != 6:
            raise serializers.ValidationError("OTP must be exactly 6 digits long.")
        return value

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["email", "full_name", "role"]

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords must match."})

        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user is associated with this email.")
        return value
    
class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        try:
            validate_password(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        return value