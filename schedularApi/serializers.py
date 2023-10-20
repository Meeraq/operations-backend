from rest_framework import serializers
from .models import (
    SchedularProject,
    LiveSession,
    CoachingSession,
    SchedularBatch,
    SchedularParticipants,
    EmailTemplate,
    SentEmail,
    CoachSchedularAvailibilty,
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


class LearnerDataUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularBatch
        fields = "__all__"


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = "__all__"


class SentEmailDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentEmail
        fields = "__all__"
        depth = 1


class CoachSchedularAvailibiltySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachSchedularAvailibilty
        fields = "__all__"


class CoachSchedularAvailibiltySerializer2(serializers.ModelSerializer):
    class Meta:
        model = CoachSchedularAvailibilty
        fields = "__all__"
        depth = 1
