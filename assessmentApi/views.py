from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Competency, Question, Questionnaire
from .serializers import (
    CompetencySerializer,
    QuestionSerializer,
    QuestionnaireSerializer,
    QuestionSerializerDepthOne,
)

# Create your views here.


class CompetencyView(APIView):
    def get(self, request):
        competencies = Competency.objects.all()
        serializer = CompetencySerializer(competencies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CompetencySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Competency created successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "error": f"{serializer.errors}",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request):
        competency_id = request.data.get("id")
        try:
            competency = Competency.objects.get(id=competency_id)
        except Competency.DoesNotExist:
            return Response(
                {"message": "Competency not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompetencySerializer(competency, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Competency updated successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": f"{serializer.errors}",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request):
        competency_id = request.data.get("id")
        try:
            competency = Competency.objects.get(id=competency_id)
        except Competency.DoesNotExist:
            return Response(
                {"message": "Competency not found"}, status=status.HTTP_404_NOT_FOUND
            )

        competency.delete()
        return Response(
            {"message": "Competency deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class OneCompetencyDetail(APIView):
    def get(self, request):
        competency_id = request.data.get("id")
        try:
            competency = Competency.objects.get(id=competency_id)
        except Competency.DoesNotExist:
            return Response(
                {"message": "Competency not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompetencySerializer(competency)
        return Response(serializer.data)


class QuestionView(APIView):
    def get(self, request):
        questions = Question.objects.all()
        serializer = QuestionSerializerDepthOne(questions, many=True)
        print(serializer)
        return Response(serializer.data)

    def post(self, request):

        serializer = QuestionSerializer(data=request.data)
    
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Question created successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "error": f"{serializer.errors}",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request):
        question_id = request.data.get("id")
        competency=request.data.get("competency")
        
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer=None
        if isinstance(competency, dict):
            serializer = QuestionSerializerDepthOne(question, data=request.data)
        else:
            serializer = QuestionSerializer(question, data=request.data)

        if serializer.is_valid():   
            serializer.save()
            return Response(
                {"message": "Question updated successfully"}, status=status.HTTP_200_OK
            )
        return Response(
            {
                "error": f"{serializer.errors}",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request):
        question_id = request.data.get("id")
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )

        question.delete()
        return Response(
            {"message": "Question deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class OneQuestionDetail(APIView):
    def get(self, request):
        question_id = request.data.get("id")
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = QuestionSerializer(question)
        return Response(serializer.data)


class QuestionnaireView(APIView):
    def get(self, request):
        questionnaires = Questionnaire.objects.all()
        serializer = QuestionnaireSerializer(questionnaires, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = QuestionnaireSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Questionnaire created successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "error": f"{serializer.errors}",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request):
        questionnaire_id = request.data.get("id")
        try:
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)
        except Questionnaire.DoesNotExist:
            return Response(
                {"message": "Questionnaire not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = QuestionnaireSerializer(questionnaire, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Questionnaire updated successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": f"{serializer.errors}",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request):
        questionnaire_id = request.data.get("id")
        try:
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)
        except Questionnaire.DoesNotExist:
            return Response(
                {"message": "Questionnaire not found"}, status=status.HTTP_404_NOT_FOUND
            )

        questionnaire.delete()
        return Response(
            {"message": "Questionnaire deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class OneQuestionnaireDetail(APIView):
    def get(self, request):
        questionnaire_id = request.data.get("id")
        try:
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)
        except Questionnaire.DoesNotExist:
            return Response(
                {"message": "Questionnaire not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = QuestionnaireSerializer(questionnaire)
        return Response(serializer.data)
