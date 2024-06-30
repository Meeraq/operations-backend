from rest_framework import serializers
from .models import Batches, Faculties, Sessions, MentorCoachSessions


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

class MentorCoachSessionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorCoachSessions
        fields = '__all__'