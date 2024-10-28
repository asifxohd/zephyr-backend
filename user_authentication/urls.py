from django.urls import path
from .views import (
    UserRegistrationView,
    OtpVerificationView,
    ResendOtpView,
    GoogleLoginAPIView,
    ChangePasswordView,
    PasswordResetRequestView,
)

urlpatterns = [
    path("register-user/", UserRegistrationView.as_view(), name="user-registration"),
    path(
        "otp-verification/", OtpVerificationView.as_view(), name="user-otp-verification"
    ),
    path("resent-otp/", ResendOtpView.as_view(), name="resent-otp"),
    path("google-login/", GoogleLoginAPIView.as_view(), name="google-login"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path('forgot-password/', PasswordResetRequestView.as_view(), name="password-reset")
]
