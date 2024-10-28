from django.db import models
from django.contrib.auth.models import AbstractUser

class Location(models.Model):
    """
    Model to store preferred locations.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Industry(models.Model):
    """
    Model to store preferred industries.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class InvestorPreferences(models.Model):
    """
    Model to store investor preferences.
    """
    cover_image = models.ImageField(upload_to='cover_images/', blank=True, null=True)
    avatar_image = models.ImageField(upload_to='avatar_images/', blank=True, null=True)
    preferred_locations = models.ManyToManyField(Location, blank=True)
    preferred_industries = models.ManyToManyField(Industry, blank=True)
    description = models.TextField(blank=True, null=True)
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='investor_preferences')

    def __str__(self):
        return f"Preferences for {self.user.email}"
class CustomUser(AbstractUser):
    """
    Custom user model for handling different types of users.
    """
    PHONE_NUMBER_LENGTH = 12
    ROLE_CHOICES = (
        ('investor', 'Investor'),
        ('business', 'Business'),
        ('admin', 'Admin'),
    )
    DEFAULT_ROLE = 'admin'
                     
    phone_number = models.CharField(max_length=PHONE_NUMBER_LENGTH, unique=True, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=DEFAULT_ROLE)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=300, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self) -> str:
        """ representation of the CustomUser instance """
        return self.email

