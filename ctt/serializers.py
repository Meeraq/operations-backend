from rest_framework import serializers
from .models import Batches , Faculties


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batches
        fields = "__all__"


class FacultiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculties
        fields = "__all__"
