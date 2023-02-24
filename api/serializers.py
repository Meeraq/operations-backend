from rest_framework import serializers
from .models import Pmo,Coach,Profile,Learner
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'is_staff']


class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = '__all__'

class LearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Learner
        fields = '__all__'