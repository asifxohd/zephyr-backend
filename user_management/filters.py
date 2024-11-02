import django_filters
from user_authentication.models import CustomUser

class CustomUserFilter(django_filters.FilterSet):
    full_name = django_filters.CharFilter(field_name='full_name', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    phone_number = django_filters.CharFilter(field_name='phone_number', lookup_expr='icontains')

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number']
