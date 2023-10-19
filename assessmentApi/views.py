from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    Competency,
    Question,
    Questionnaire,
    Assessment,
    Observer,
    ParticipantObserverMapping,
)
from .serializers import (
    CompetencySerializer,
    QuestionSerializer,
    QuestionnaireSerializer,
    QuestionSerializerDepthOne,
    QuestionnaireSerializerDepthTwo,
    AssessmentSerializer,
    AssessmentSerializerDepthThree,
)
from django.db import transaction, IntegrityError
import json
import string
import random
from django.contrib.auth.models import User
from api.models import Profile, Learner
from api.serializers import LearnerSerializer
from collections import defaultdict

def create_learner(learner_name,learner_email):
    try:
        with transaction.atomic():
            if not learner_email:
                raise ValueError("Username field is required")

            user = User.objects.filter(username=learner_email).first()
            learner_profile = None
            if user:
                learner_profile = Profile.objects.filter(
                    user=user, type="learner"
                ).first()

            else:
                temp_password = "".join(
                    random.choices(
                        string.ascii_uppercase + string.ascii_lowercase + string.digits,
                        k=8,
                    )
                )
                user = User.objects.create_user(
                    username=learner_email,
                    password=temp_password,
                    email=learner_email,
                )

                user.save()

                learner_profile = Profile.objects.create(user=user, type="learner")

                learner = Learner.objects.create(
                        user=learner_profile,
                        name=learner_name,
                        email=learner_email,
                    )
            return learner
    except ValueError as e:
        raise ValueError(str(e))

    except Exception as e:
        raise Exception(str(e))


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
            questionnaire = Questionnaire.objects.get(
                id=request.data.get("questionnaire")
            )
            assessment.name = request.data.get("name")
            assessment.assessment_type = request.data.get("assessment_type")
            if request.data.get("assessment_type") == "self":
                assessment.number_of_observers = 0
            else:
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


class AssessmentStatusOrEndDataChange(APIView):
    def put(self, request):
        assessment_id = request.data.get("id")

        try:
            assessment = Assessment.objects.get(id=assessment_id)
            assessment.status = request.data.get("status")
            assessment.assessment_end_date = request.data.get("assessment_end_date")
            assessment.save()
            serializer = AssessmentSerializerDepthThree(assessment)
            return Response(
                {"message": "Update successfully.", "assessment_data": serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddParticipantObserverToAssessment(APIView):
    def put(self, request):
        assessment_id = request.data.get("assessment_id")

        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            participants = request.data.get("participants", [])
            participant=create_learner(participants[0]["participantName"],participants[0]["participantEmail"])

            mapping = ParticipantObserverMapping.objects.create(participant=participant)

            if assessment.assessment_type == "360":
                observers = request.data.get("observers", [])
                for observer_data in observers:
                    observer, created = Observer.objects.get_or_create(
                        name=observer_data["observerName"],
                        email=observer_data["observerEmail"],
                    )
                    if created:
                        observer.save()
                    mapping.observers.add(observer)

            mapping.save()
            assessment.participants_observers.add(mapping)
            assessment.save()

            serializer = AssessmentSerializerDepthThree(assessment)
            return Response(
                {
                    "message": "Participant added successfully.",
                    "assessment_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AssessmentsOfParticipant(APIView):
    def get(self, request, participant_email):
        try:
        
            participant = Learner.objects.get(email=participant_email)

            assessments = Assessment.objects.filter(
                participants_observers__participant=participant
            )
            
            serializer = AssessmentSerializerDepthThree(assessments, many=True)

            return Response(serializer.data)

        except Learner.DoesNotExist:
            return Response(
                {"error": "Participant not found"}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class QuestionsForAssessment(APIView):
    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
            questionnaire = assessment.questionnaire

            competency_questions = {}

            for question in questionnaire.questions.all():
                competency_name = question.competency.name
                full_question = {
                    "id": question.id,
                    "self_question": question.self_question,
                    # "observer_question": question.observer_question,
                }

                if competency_name in competency_questions:
                    competency_questions[competency_name].append(full_question)
                else:
                    competency_questions[competency_name] = [full_question]

            return Response(competency_questions, status=status.HTTP_200_OK)

        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )