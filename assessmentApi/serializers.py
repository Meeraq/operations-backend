from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Competency, Question, Questionnaire,Assessment,ParticipantResponse,ObserverResponse


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
     

class QuestionSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        depth = 1


class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = "__all__"
        

class QuestionnaireSerializerDepthTwo(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = "__all__"
        depth = 2

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"
        

class AssessmentSerializerDepthThree(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"
        depth = 3

class AssessmentAnsweredSerializerDepthThree(serializers.ModelSerializer):
    assessment_answered = serializers.BooleanField()
    class Meta:
        model = Assessment
        fields = "__all__"
        depth = 3


class ParticipantResponseSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = ParticipantResponse
        fields = "__all__"
        depth=4

class ObserverResponseSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = ObserverResponse
        fields = "__all__"
        depth=4
   
   