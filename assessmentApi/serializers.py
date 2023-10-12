from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Competency, Question, Questionnaire


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
        depth = 1
