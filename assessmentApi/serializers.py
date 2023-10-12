from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Competency


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"