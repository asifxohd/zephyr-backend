from django.db import models
from user_authentication.models import CustomUser

class Subscriptions(models.Model):
    FREE_TRIAL = 'free_trial'
    MONTHLY = 'monthly'
    SEMI_ANNUAL = 'semi_annual'
    ANNUAL = 'annual'

    PLAN_TYPE_CHOICES = [
        (FREE_TRIAL, 'Free Trial'),
        (MONTHLY, 'Monthly'),
        (SEMI_ANNUAL, 'Semi-Annual'),
        (ANNUAL, 'Annual'),
    ]
    
    ACTIVE = 'active'
    CANCELED = 'canceled'
    PAST_DUE = 'past_due'
    UNPAID = 'unpaid'

    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (CANCELED, 'Canceled'),
        (PAST_DUE, 'Past Due'),
        (UNPAID, 'Unpaid'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPE_CHOICES)  # Subscription plan
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)  # Active, Canceled, Past Due, etc.
    start_date = models.DateTimeField()  # The date when the subscription starts
    end_date = models.DateTimeField()  # The date when the subscription ends
    has_used_free_trial = models.BooleanField(default=False)  # Track if the user has used the free trial
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.plan_type} - {self.status}"


class BillingHistory(models.Model):
    PAID = 'paid'
    FAILED = 'failed'
    PENDING = 'pending'

    INVOICE_STATUS_CHOICES = [
        (PAID, 'Paid'),
        (FAILED, 'Failed'),
        (PENDING, 'Pending'),
    ]

    # Fields
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    stripe_invoice_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Invoice amount
    paid_at = models.DateTimeField()  # When the invoice was paid
    status = models.CharField(max_length=50, choices=INVOICE_STATUS_CHOICES)  # Paid, Failed, Pending status
    subscription = models.ForeignKey('Subscriptions', on_delete=models.CASCADE)  # Link to Subscription

    # Timestamps for tracking updates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.stripe_invoice_id} for {self.user.email}"