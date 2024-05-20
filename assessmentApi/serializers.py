from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Competency,
    Question,
    Questionnaire,
    Assessment,
    ParticipantResponse,
    ObserverResponse,
    AssessmentNotification,
    ParticipantObserverType,
    ObserverUniqueId,
    ObserverTypes,
    ParticipantReleasedResults,
    ParticipantObserverMapping,
    Behavior
)


class CompetencySerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"
        depth = 1


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"

class BehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Behavior
        fields = "__all__"

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class QuestionSerializerDepthTwo(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        depth = 2


class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = "__all__"


class QuestionnaireSerializerDepthThree(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = "__all__"
        depth = 3


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"


class AssessmentSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"
        depth = 1


class AssessmentSerializerDepthFour(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"
        depth = 4


class AssessmentAnsweredSerializerDepthFour(serializers.ModelSerializer):
    assessment_answered = serializers.BooleanField()

    class Meta:
        model = Assessment
        fields = "__all__"
        depth = 4


class ParticipantResponseSerializerDepthFive(serializers.ModelSerializer):
    class Meta:
        model = ParticipantResponse
        fields = "__all__"
        depth = 5


class ObserverResponseSerializerDepthFour(serializers.ModelSerializer):
    class Meta:
        model = ObserverResponse
        fields = "__all__"
        depth = 4


class ParticipantObserverTypeSerializerDepthTwo(serializers.ModelSerializer):
    class Meta:
        model = ParticipantObserverType
        fields = "__all__"
        depth = 2


class ObserverUniqueIdSerializerDepthTwo(serializers.ModelSerializer):
    class Meta:
        model = ObserverUniqueId
        fields = "__all__"
        depth = 2


class ObserverTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObserverTypes
        fields = "__all__"


class AssessmentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentNotification
        fields = "__all__"


class ParticipantReleasedResultsSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = ParticipantReleasedResults
        fields = "__all__"
        depth = 1


class ParticipantObserverMappingSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = ParticipantObserverMapping
        fields = "__all__"
        depth = 1
