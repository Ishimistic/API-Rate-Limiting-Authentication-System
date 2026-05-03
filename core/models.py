from django.db import models
from django.contrib.auth.models import User
import secrets
class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255, unique=True, default=secrets.token_hex)
    rate_limit = models.IntegerField(default=20)
    window = models.IntegerField(default=30)
    
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = secrets.token_hex(32)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.user.username}"