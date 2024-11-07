from django.contrib import admin
from .models import BillingHistory, Subscriptions
# Register your models here.
admin.site.register(BillingHistory)
admin.site.register(Subscriptions)