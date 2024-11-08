from rest_framework import serializers
from .models import Subscriptions, BillingHistory
from user_authentication.models import CustomUser

class BillingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingHistory
        fields = ['stripe_invoice_id', 'amount', 'paid_at', 'status', 'subscription', 'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    billing_histories = BillingHistorySerializer(source='billinghistory_set', many=True, read_only=True)  

    class Meta:
        model = Subscriptions
        fields = ['user', 'stripe_subscription_id', 'plan_type', 'status', 'start_date', 'end_date', 'has_used_free_trial', 'created_at', 'updated_at', 'billing_histories']
