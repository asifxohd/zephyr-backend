from django.db import models
from django.core.validators import URLValidator, FileExtensionValidator
from user_authentication.models import Industry, Location, CustomUser


class BusinessPreferences(models.Model):
    """
    Model to store business preferences.
    """
    cover_image = models.ImageField(upload_to='cover_images/', blank=True, null=True)
    avatar_image = models.ImageField(upload_to='avatar_images/', blank=True, null=True)
    company_name = models.CharField(max_length=255, help_text="Enter your company name")
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    business_type = models.CharField(max_length=100, help_text="Enter business type")
    company_stage = models.CharField(max_length=100, help_text="Enter current company stage")
    listed_status = models.BooleanField(default=False, help_text="Activate / Deactivate")
    company_description = models.TextField(
        max_length=1000, 
        help_text="Describe your company (250 words or more)"
    )
    seeking_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text="Enter amount seeking"
    )
    website = models.URLField(validators=[URLValidator()], help_text="Enter website URL")
    product_type = models.CharField(max_length=100, help_text="Enter product type")
    annual_revenue = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        help_text="Enter annual revenue"
    )
    employee_count = models.PositiveIntegerField(help_text="Enter employee count")
    linkedIn = models.URLField(blank=True, null=True, validators=[URLValidator()])
    facebook = models.URLField(blank=True, null=True, validators=[URLValidator()])
    twitter = models.URLField(blank=True, null=True, validators=[URLValidator()])
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='business_preferences')

    def __str__(self):
        return f"Business Preferences for {self.company_name}"
    

class DocumentsBusiness(models.Model):
    """
    Model to store documents related to business preferences.
    """
    document_title = models.CharField(max_length=255, help_text="Enter document title")
    document_description = models.TextField(help_text="Enter document description")
    document_file = models.FileField(
        upload_to='business_documents/', 
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'])],
        help_text="Choose File"
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='business_documents')

    def __str__(self):
        return self.document_title

class VideoPitch(models.Model):
    """
    Model to store video pitches related to business preferences.
    """
    video_title = models.CharField(max_length=255, help_text="Enter video title")
    video_description = models.TextField(help_text="Enter video description")
    video_file = models.FileField(
        upload_to='business_video_pitches/',
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi'])],
        help_text="Upload Video"
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='video_pitches')

    def __str__(self):
        return self.video_title

