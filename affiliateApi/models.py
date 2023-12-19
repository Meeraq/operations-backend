from django.db import models
from api.models import Profile

class Affiliate(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    first_name = models.CharField(max_length=255,blank=True)
    last_name = models.CharField(max_length=255,blank=True)
    email = models.CharField(max_length=255,blank=True)
    phone = models.CharField(max_length=25,blank=True)
    is_approved = models.BooleanField(blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
