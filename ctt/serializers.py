from rest_framework import serializers
from .models import Batches, Faculties, Sessions


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batches
        fields = "__all__"


class FacultiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculties
        fields = "__all__"


class SessionsSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Sessions
        fields = "__all__"
        depth = 1
