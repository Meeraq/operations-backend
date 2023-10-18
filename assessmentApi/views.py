from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Competency, Question, Questionnaire,Assessment
from .serializers import (
    CompetencySerializer,
    QuestionSerializer,
    QuestionnaireSerializer,
    QuestionSerializerDepthOne,
    QuestionnaireSerializerDepthTwo,
    AssessmentSerializer,
    AssessmentSerializerDepthThree
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
        competency = request.data.get("competency")

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = None
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

        serializer = QuestionSerializerDepthOne(question)
        return Response(serializer.data)


class QuestionnaireView(APIView):
    def get(self, request):
        questionnaires = Questionnaire.objects.all()
        serializer = QuestionnaireSerializerDepthTwo(questionnaires, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = QuestionnaireSerializer(data=request.data)
        if serializer.is_valid():
            questionnaire = serializer.save()

            question_ids = request.data.get("questions", [])
            questionnaire.questions.set(question_ids)

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

        serializer = QuestionnaireSerializerDepthTwo(questionnaire)
        return Response(serializer.data)


class AssessmentView(APIView):
    def get(self, request):
        assessments = Assessment.objects.all()
        serializer = AssessmentSerializerDepthThree(assessments, many=True)
        return Response(serializer.data)

    def post(self, request):
        
        serializer = AssessmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Assessment created successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "error": f"{serializer.errors}",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request):
        assessment_id = request.data.get("id")

        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response(
                {"message": "Assessment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            
            questionnaire=Questionnaire.objects.get(id=request.data.get("questionnaire"))
            assessment.name = request.data.get("name")
            assessment.assessment_type = request.data.get("assessment_type")
            assessment.number_of_observers = request.data.get("number_of_observers")
            assessment.assessment_end_date = request.data.get("assessment_end_date")
            assessment.rating_type = request.data.get("rating_type")
            assessment.questionnaire = questionnaire
            assessment.descriptive_questions = request.data.get("descriptive_questions")
            assessment.save()
            return Response(
            {"message": "Assessment updated successfully"},
            status=status.HTTP_200_OK,
             )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request):
        assessment_id = request.data.get("id")
        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response(
                {"message": "Assessment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        assessment.delete()
        return Response(
            {"message": "Assessment deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )
    
class AssessmentStatusOrTypeOrEndDataChange(APIView):
    def put(self, request):
        assessment_id = request.data.get("id")

        try:
            assessment = Assessment.objects.get(id=assessment_id)
            assessment.status=request.data.get("status")
            assessment.assessment_type=request.data.get("assessment_type")
            assessment.assessment_end_date=request.data.get("assessment_end_date")
            assessment.save()
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )