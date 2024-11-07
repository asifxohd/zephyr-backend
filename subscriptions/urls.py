from django.urls import path
from .views import CreateCheckoutSession, SubscriptionSuccess, SubscriptionCancel, HandleStripeWebhook, CheckSubscriptionStatusView

urlpatterns = [
    path('create-checkout-session/<str:plan_type>/', CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path('subscription/success/', SubscriptionSuccess.as_view(), name='subscription-success'),
    path('subscription/cancel/', SubscriptionCancel.as_view(), name='subscription-cancel'),
    path('webhook/', HandleStripeWebhook.as_view(), name='stripe-webhook'),
    path('check-subscription/', CheckSubscriptionStatusView.as_view(), name='check-subscription'),

]
