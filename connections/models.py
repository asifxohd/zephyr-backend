from django.db import models
from django.conf import settings

class Connections(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')
        db_table = 'connections'  
    
    def __str__(self):
        return f"{self.follower.email} follows {self.followed.email}"

    def is_mutual(self):
        """Check if this connection is mutual."""
        return Connections.objects.filter(follower=self.followed, followed=self.follower).exists()
