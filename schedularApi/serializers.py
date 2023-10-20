from rest_framework import serializers
from .models import (
    SchedularProject,
    LiveSession,
    CoachingSession,
    SchedularParticipants,
    SchedularBatch,
)


class SchedularProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularProject
        fields = "__all__"
        depth = 1


class SessionItemSerializer(serializers.Serializer):
    session_type = serializers.CharField()
    duration = serializers.IntegerField()
    order = serializers.IntegerField(required=False, allow_null=True)


class SchedularParticipantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularParticipants
        fields = ["name", "email", "phone"]


class GetSchedularParticipantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularParticipants
        fields = "__all__"


class SchedularBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularBatch
        fields = "__all__"


class LiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = "__all__"


class CoachingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachingSession
        fields = "__all__"
