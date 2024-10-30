from django.contrib import admin
from .models import (
    BusinessPreferences,
    VideoPitch,
    DocumentsBusiness,
)

admin.site.register(BusinessPreferences)
admin.site.register(VideoPitch)
admin.site.register(DocumentsBusiness)
