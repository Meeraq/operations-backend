from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from django.db import models
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User


class Profile(models.Model):
    user_types = [
        ('pmo', 'pmo'),
        ('coach', 'coach'),
        ('learner', 'learner'),
        ('hr', 'hr') 
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=50, choices=user_types)
    def __str__(self):
        return self.user.username


class Pmo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()    
    phone = models.CharField(max_length=25)

    def __str__(self):
        return self.name

class Coach(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    meet_link = models.CharField(max_length=50)
    phone = models.CharField(max_length=25)    
    level = models.CharField(max_length=50)
    rating = models.CharField(max_length=20)
    area_of_expertise = models.CharField(max_length=50)
    completed_sessions = models.IntegerField(blank=True,default=0)
    is_approved = models.BooleanField(blank=True,default=False)
    def __str__(self):
        return self.name




