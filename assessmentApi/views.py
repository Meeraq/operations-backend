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
    ParticipantResponse,
    ObserverResponse,
    ParticipantObserverType,
    ObserverUniqueId,
)
from .serializers import (
    CompetencySerializer,
    QuestionSerializer,
    QuestionnaireSerializer,
    QuestionSerializerDepthOne,
    QuestionnaireSerializerDepthTwo,
    AssessmentSerializer,
    AssessmentSerializerDepthThree,
    AssessmentAnsweredSerializerDepthThree,
    ParticipantResponseSerializer,
    ObserverResponseSerializer,
    ParticipantObserverTypeSerializer,
    ObserverUniqueIdSerializerDepthOne,
)
from django.db import transaction, IntegrityError
import json
import string
import random
from django.contrib.auth.models import User
from api.models import Profile, Learner, Organisation, HR
from api.serializers import LearnerSerializer
from collections import defaultdict
from django.db.models import BooleanField, F, Exists, OuterRef
from django.db.models import Q
import uuid


def create_learner(learner_name, learner_email):
    try:
        with transaction.atomic():
            if not learner_email:
                raise ValueError("Username field is required")

            user = User.objects.filter(username=learner_email).first()
            learner = None
            if user:
                learner_profile = Profile.objects.filter(
                    user=user, type="learner"
                ).first()
                learner = Learner.objects.get(email=learner_email)
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
                "error": "Failed to create Competency.",
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
                "error": "Failed to update Competency.",
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
                "error": "Failed to create Question.",
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
                "error": "Failed to update Question.",
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
                "error": "Failed to create Questionnaire.",
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
                "error": "Failed to update Questionnaire.",
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
                {"message": "Assessment created successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "error": "Failed to create Assessment.",
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

            organisation = Organisation.objects.get(id=request.data.get("organisation"))
            hr = []
            for hr_id in request.data.get("hr"):
                one_hr = HR.objects.get(id=hr_id)
                hr.append(one_hr)
            assessment.name = request.data.get("name")
            assessment.assessment_type = request.data.get("assessment_type")
            if request.data.get("assessment_type") == "self":
                assessment.number_of_observers = 0
            else:
                assessment.number_of_observers = request.data.get("number_of_observers")
            assessment.assessment_end_date = request.data.get("assessment_end_date")
            # assessment.rating_type = request.data.get("rating_type")
            assessment.questionnaire = questionnaire
            assessment.descriptive_questions = request.data.get("descriptive_questions")
            assessment.organisation = organisation
            assessment.hr.set(hr)
            assessment.save()

            serializer = AssessmentSerializerDepthThree(assessment)
            return Response(
                {
                    "message": "Assessment updated successfully",
                    "assessment_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {
                    "error": "Failed to Update Assessment.",
                },
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
            print(str(e))
            return Response(
                {
                    "error": "Failed to Update Status.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddParticipantObserverToAssessment(APIView):
    @transaction.atomic
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

            if assessment.participants_observers.filter(
                participant__email=participants[0]["participantEmail"]
            ).exists():
                return Response(
                    {"error": "Participant already exists in the assessment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(
                username=participants[0]["participantEmail"]
            ).first()

            if user:
                user_profile = Profile.objects.filter(user=user).first()

                if (
                    user_profile.type == "hr"
                    or user_profile.type == "pmo"
                    or user_profile.type == "coach"
                ):
                    return Response(
                        {
                            "error": "Email Already exist. Please try using another email.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            participant = create_learner(
                participants[0]["participantName"], participants[0]["participantEmail"]
            )

            mapping = ParticipantObserverMapping.objects.create(participant=participant)

            # if assessment.assessment_type == "360":
            if False:
                observers = request.data.get("observers", [])
                for observer_data in observers:
                    observer, created = Observer.objects.get_or_create(
                        email=observer_data["observerEmail"],
                    )
                    observer.name = observer_data["observerName"]
                    observer.save()

                    (
                        participant_observer_type,
                        created1,
                    ) = ParticipantObserverType.objects.get_or_create(
                        participant=participant,
                        observers=observer,
                    )
                    participant_observer_type.type = observer_data["observerType"]
                    participant_observer_type.save()
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
            print(str(e))
            return Response(
                {
                    "error": "Failed to add participant.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class AssessmentsOfParticipant(APIView):
    def get(self, request, participant_email):
        try:
            participant = Learner.objects.get(email=participant_email)

            assessments = Assessment.objects.filter(
                Q(participants_observers__participant=participant)
                & (Q(status="ongoing") | Q(status="completed"))
            )

            assessments = assessments.annotate(
                assessment_answered=Exists(
                    ParticipantResponse.objects.filter(
                        assessment=OuterRef("id"), participant=participant
                    )
                )
            )

            serializer = AssessmentAnsweredSerializerDepthThree(assessments, many=True)

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
                    "rating_type": question.rating_type,
                }

                if competency_name in competency_questions:
                    competency_questions[competency_name].append(full_question)
                else:
                    competency_questions[competency_name] = [full_question]

            return Response(competency_questions, status=status.HTTP_200_OK)

        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuestionsForObserverAssessment(APIView):
    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
            questionnaire = assessment.questionnaire

            competency_questions = {}

            for question in questionnaire.questions.all():
                competency_name = question.competency.name
                full_question = {
                    "id": question.id,
                    "observer_question": question.observer_question,
                    "rating_type": question.rating_type,
                }

                if competency_name in competency_questions:
                    competency_questions[competency_name].append(full_question)
                else:
                    competency_questions[competency_name] = [full_question]

            return Response(competency_questions, status=status.HTTP_200_OK)

        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ObserverView(APIView):
    def post(self, request):
        try:
            request_email = request.data.get("email")
            phone = request.data.get("phone")
            observer = Observer.objects.get(email=request_email)
            observer.phone = phone
            observer.save()
            if observer:
                return Response(
                    {"message": "Verification successful."},
                    status=status.HTTP_200_OK,
                )
        except Observer.DoesNotExist:
            return Response(
                {"message": "Verification failed. Observer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": " Verification failed."}, status=status.HTTP_400_BAD_REQUEST
            )


class ObserverAssessment(APIView):
    def get(self, request, email):
        try:
            assessments = Assessment.objects.filter(
                participants_observers__observers__email=email, status="ongoing"
            ).distinct()

            serializer = AssessmentSerializerDepthThree(assessments, many=True)
            return Response(serializer.data)
        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessments not found for the provided observer's email."},
                status=404,
            )


class CreateParticipantResponseView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            participant_email = request.data.get("participant_email")
            response = request.data.get("response")

            assessment = Assessment.objects.get(id=assessment_id)

            participant = Learner.objects.get(email=participant_email)

            existing_response = ParticipantResponse.objects.filter(
                participant=participant, assessment=assessment
            ).first()

            if existing_response:
                return Response(
                    {"message": "Response already submitted for this assessment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            participant_response = ParticipantResponse.objects.create(
                participant=participant,
                assessment=assessment,
                participant_response=response,
            )
            return Response(
                {"message": "Submit Successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": "Failed to Submit."}, status=status.HTTP_404_NOT_FOUND
            )


class CreateObserverResponseView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            observer_email = request.data.get("observer_email")
            response = request.data.get("response")
            participant_id = request.data.get("participant_id")

            assessment = Assessment.objects.get(id=assessment_id)

            observer = Observer.objects.get(email=observer_email)

            participant = Learner.objects.get(id=participant_id)
            assessments = Assessment.objects.filter(
                participants_observers__observers__email=observer_email
            )

            existing_response = ObserverResponse.objects.filter(
                observer=observer, assessment=assessment, participant=participant
            ).first()

            if existing_response:
                return Response(
                    {"error": "Response already submitted for this assessment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            observer_response = ObserverResponse.objects.create(
                participant=participant,
                observer=observer,
                assessment=assessment,
                observer_response=response,
            )
            return Response(
                {"message": "Submit Successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": "Failed to Submit."}, status=status.HTTP_404_NOT_FOUND
            )


class GetParticipantResponseForParticipant(APIView):
    def get(self, request, participant_email):
        try:
            participant = Learner.objects.get(email=participant_email)

            participant_responses = ParticipantResponse.objects.filter(
                participant=participant,
            )

            serializer = ParticipantResponseSerializer(participant_responses, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetParticipantResponseFormAssessment(APIView):
    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)

            participant_responses = ParticipantResponse.objects.filter(
                assessment=assessment,
            )

            serializer = ParticipantResponseSerializer(participant_responses, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetObserverResponseForObserver(APIView):
    def get(self, request, observer_email):
        try:
            observer = Observer.objects.get(email=observer_email)

            observer_responses = ObserverResponse.objects.filter(
                observer=observer,
            )

            serializer = ObserverResponseSerializer(observer_responses, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetObserverResponseFormAssessment(APIView):
    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)

            observer_responses = ObserverResponse.objects.filter(
                assessment=assessment,
            )

            serializer = ObserverResponseSerializer(observer_responses, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParticipantObserverTypeList(APIView):
    def get(self, request):
        participant_observer_types = ParticipantObserverType.objects.all()
        serializer = ParticipantObserverTypeSerializer(
            participant_observer_types, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteParticipantFromAssessment(APIView):
    @transaction.atomic
    def delete(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            participant_observers = request.data.get("participant_observers")

            assessment = Assessment.objects.get(id=assessment_id)

            assessment.participants_observers.filter(
                participant__id=participant_observers["participant"]["id"]
            ).delete()

            serializer = AssessmentSerializerDepthThree(assessment)
            return Response(
                {
                    "message": "Successfully removed participant from assessment.",
                    "assessment_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to Remove Participant"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeleteObserverFromAssessment(APIView):
    @transaction.atomic
    def delete(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            participant_observers_id = request.data.get("participant_observers_id")
            observer_id = request.data.get("observer_id")

            assessment = Assessment.objects.get(id=assessment_id)
            participants_observer = ParticipantObserverMapping.objects.get(
                id=participant_observers_id
            )
            observer_to_remove = Observer.objects.get(id=observer_id)

            participants_observer.observers.remove(observer_to_remove)

            serializer = AssessmentSerializerDepthThree(assessment)

            return Response(
                {
                    "message": "Successfully removed observer.",
                    "assessment_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to remove observer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AddObserverToParticipant(APIView):
    @transaction.atomic
    def put(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            participant_observers_id = request.data.get("participant_observers_id")
            participants_observer = ParticipantObserverMapping.objects.get(
                id=participant_observers_id
            )
            observerName = request.data.get("observerName")
            observerEmail = request.data.get("observerEmail")
            observerType = request.data.get("observerType")
            assessment = Assessment.objects.get(id=assessment_id)

            if participants_observer.observers.filter(email=observerEmail).exists():
                return Response(
                    {"error": f"Observer with email '{observerEmail}' already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            observer, created = Observer.objects.get_or_create(
                email=observerEmail,
            )
            observer.name = observerName
            observer.save()
            (
                participant_observer_type,
                created1,
            ) = ParticipantObserverType.objects.get_or_create(
                participant=participants_observer.participant,
                observers=observer,
            )
            participant_observer_type.type = observerType
            participant_observer_type.save()
            participants_observer.observers.add(observer)
            participants_observer.save()

            observer_unique_id, created2 = ObserverUniqueId.objects.get_or_create(
                participant=participants_observer.participant,
                observer=observer,
                assessment=assessment,
            )
            observer_unique_id.unique_id = str(uuid.uuid4())
            observer_unique_id.save()

            serializer = AssessmentSerializerDepthThree(assessment)
            return Response(
                {
                    "message": "Observer added successfully.",
                    "assessment_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to add observer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CompetencyIdsInOngoingAndCompletedAssessments(APIView):
    def get(self, request):
        try:
            assessments = Assessment.objects.filter(status__in=["completed", "ongoing"])
            competency_ids = []
            for assessment in assessments:
                questions = assessment.questionnaire.questions.all()
                for question in questions:
                    competency_ids.append(question.competency.id)

            competency_ids = list(set(competency_ids))

            return Response(competency_ids)

        except Exception as e:
            return Response(
                {"error": "Failed to retrieve competency IDs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuestionIdsInOngoingAndCompletedAssessments(APIView):
    def get(self, request):
        try:
            assessments = Assessment.objects.filter(status__in=["completed", "ongoing"])
            questions_ids = []
            for assessment in assessments:
                questions = assessment.questionnaire.questions.all()
                for question in questions:
                    questions_ids.append(question.id)

            questions_ids = list(set(questions_ids))

            return Response(questions_ids)

        except Exception as e:
            return Response(
                {"error": "Failed to retrieve question IDs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuestionnaireIdsInOngoingAndCompletedAssessments(APIView):
    def get(self, request):
        try:
            assessments = Assessment.objects.filter(status__in=["completed", "ongoing"])
            questionnaires_ids = []
            for assessment in assessments:
                questionnaires_ids.append(assessment.questionnaire.id)

            questionnaires_ids = list(set(questionnaires_ids))

            return Response(questionnaires_ids)

        except Exception as e:
            return Response(
                {"error": "Failed to retrieve questionnaire IDs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParticipantAddsObserverToAssessment(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            participant_email = request.data.get("participant_email")

            assessment = Assessment.objects.get(id=assessment_id)

            get_participants_observer = assessment.participants_observers.filter(
                participant__email=participant_email
            ).first()
            participants_observer = ParticipantObserverMapping.objects.get(
                id=get_participants_observer.id
            )
            observers = request.data.get("observers", [])

            for observer_data in observers:
                observerName = observer_data["observerName"]
                observerEmail = observer_data["observerEmail"]
                observerType = observer_data["observerType"]
                if participants_observer.observers.filter(email=observerEmail).exists():
                    return Response(
                        {
                            "error": f"Observer with email '{observerEmail}' already exists."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                observer, created = Observer.objects.get_or_create(
                    email=observerEmail,
                )
                observer.name = observerName
                observer.save()
                (
                    participant_observer_type,
                    created1,
                ) = ParticipantObserverType.objects.get_or_create(
                    participant=participants_observer.participant,
                    observers=observer,
                )
                participant_observer_type.type = observerType
                participant_observer_type.save()
                participants_observer.observers.add(observer)
                participants_observer.save()

                observer_unique_id, created2 = ObserverUniqueId.objects.get_or_create(
                    participant=participants_observer.participant,
                    observer=observer,
                    assessment=assessment,
                )
                observer_unique_id.unique_id = str(uuid.uuid4())
                observer_unique_id.save()

            return Response(
                {
                    "message": "Observer added successfully.",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to add observer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StartAssessmentDataForObserver(APIView):
    def get(self, request, unique_id):
        try:
            observer_unique_id = ObserverUniqueId.objects.get(unique_id=unique_id)

            serializer = AssessmentSerializerDepthThree(observer_unique_id.assessment)

            return Response(
                {
                    "assessment_data": serializer.data,
                    "observer_email": observer_unique_id.observer.email,
                    "participant_id": observer_unique_id.participant.id,
                },
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to retrieve Start Assessment Data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetObserversUniqueIds(APIView):
    def get(self, request, assessment_id):
        try:
            observers_unique_id = ObserverUniqueId.objects.filter(
                assessment__id=assessment_id
            )

            serializer = ObserverUniqueIdSerializerDepthOne(
                observers_unique_id, many=True
            )

            return Response(serializer.data)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to retrieve Observer Unique Id"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetParticipantObserversUniqueIds(APIView):
    def get(self, request, participant_email):
        try:
            observers_unique_id = ObserverUniqueId.objects.filter(
                participant__email=participant_email
            )

            serializer = ObserverUniqueIdSerializerDepthOne(
                observers_unique_id, many=True
            )

            return Response(serializer.data)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to retrieve Observer Unique Id"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StartAssessmentDisabled(APIView):
    def get(self, request, unique_id):
        try:
            observers_unique_id = ObserverUniqueId.objects.filter(
                unique_id=unique_id
            ).first()

            observer_response_data = ObserverResponse.objects.filter(
                participant=observers_unique_id.participant,
                observer=observers_unique_id.observer,
                assessment=observers_unique_id.assessment,
            )
            if observer_response_data:
                return Response({"observer_response": True})
            else:
                return Response({"observer_response": False})
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to retrieve Observer Response Data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReleaseResults(APIView):
    def put(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)

            assessment.result_released = True
            assessment.save()

            serializer = AssessmentSerializerDepthThree(assessment)
            return Response(
                {
                    "success": "Successfully Released Results",
                    "assessment_data": serializer.data,
                }
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to retrieve Observer Response Data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateObserverType(APIView):
    @transaction.atomic
    def post(
        self,
        request,
    ):
        try:
            name = request.data.get("name")
            observer_type = ObserverTypes.objects.create(type=name)
            observer_type.save()

            return Response(
                {
                    "success": "Successfully created observer type",
                }
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to create observer type."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetObserverTypes(APIView):
    def get(self, request):
        try:
            observer_types = ObserverTypes.objects.all()
            serializer = ObserverTypeSerializer(observer_types, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def calculate_average(question_with_answers, assessment_type):
    competency_averages = []

    for competency_data in question_with_answers:
        competency_name = competency_data["competency_name"]
        questions = competency_data["questions"]

        total_participant_responses = 0
        total_observer_responses = {}

        for question in questions:
            total_observers = (
                len(question.keys()) - 2
            )  # two columns substracted question and participant response for number of observer
            if assessment_type == "self":
                total_observers = 1
            total_participant_responses += question["participant_response"]

            # Sum observer responses for each question
            for key, value in question.items():
                if key != "question" and key != "participant_response":
                    if key not in total_observer_responses:
                        total_observer_responses[key] = 0
                    total_observer_responses[key] += value

        # Calculate averages
        num_questions = len(questions)

        average_participant_response = round(
            total_participant_responses / num_questions, 2
        )
        total_observer_responses = sum(total_observer_responses.values())
        average_observer_responses = round(
            (total_observer_responses / num_questions) / total_observers, 2
        )
        competency_average = {
            "competency_name": competency_name,
            "average_participant_response": average_participant_response,
            "average_observer_responses": average_observer_responses,
        }

        competency_averages.append(competency_average)

    return competency_averages


def delete_previous_graphs():
    graph_directory = "graphsAndReports"
    files = os.listdir(graph_directory)
    previous_graphs = [file for file in files if file.startswith("average_responses")]

    for graph in previous_graphs:
        file_path = os.path.join(graph_directory, graph)
        os.remove(file_path)


def generate_graph(data, assessment_type):
    bar_width = 0.1
    competency_names = [competency["competency_name"] for competency in data]
    num_competencies = len(competency_names)
    num_graphs = int(np.ceil(num_competencies / 5.0))

    encoded_images = []  # Array to store base64 encoded images

    for i in range(num_graphs):
        start_index = i * 5
        end_index = min((i + 1) * 5, num_competencies)
        subset_data = data[start_index:end_index]

        fig, ax = plt.subplots(figsize=(10, 6))
        index = np.arange(len(subset_data))
        participant_responses = [
            comp["average_participant_response"] for comp in subset_data
        ]

        if assessment_type != "self":
            observer_responses = [
                comp["average_observer_responses"] for comp in subset_data
            ]
            bar2 = ax.bar(
                index + bar_width,
                observer_responses,
                bar_width,
                label="Observer Response",
                color="#8fa2d4",
            )

        bar1 = ax.bar(
            index,
            participant_responses,
            bar_width,
            label="Participant Response",
            color="#3b64ad",
        )

        plt.title(f"Average Responses by Competency (Graph {i + 1})")
        plt.xlabel("Competency")
        plt.ylabel("Average Response")
        plt.xticks(
            index if assessment_type == "self" else index + bar_width / 2,
            competency_names[start_index:end_index],
            rotation=45,
            ha="right",
        )
        plt.legend()

        plt.tight_layout()

        # Save the image data to a BytesIO object
        image_stream = io.BytesIO()
        plt.savefig(image_stream, format="png")
        plt.close()

        # Convert the image data to base64
        encoded_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")
        encoded_images.append(encoded_image)

    return encoded_images


def generate_report_for_participant(file_name, content):
    try:
        organisation = Organisation.objects.get(id=content["organisation_id"])
        org_serializer = OrganisationSerializer(organisation)

        image_url = org_serializer.data.get("image_url")

        if image_url is not None:
            image_response = requests.get(image_url)
            image_response.raise_for_status()

            image_organisation_base64 = base64.b64encode(image_response.content).decode(
                "utf-8"
            )
            content["image_organisation_base64"] = image_organisation_base64
        else:
            content["image_organisation_base64"] = None

        email_message = render_to_string(file_name, content)

        pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)
        pdf_path = "graphsAndReports/Report.pdf"
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(pdf)

    except Exception as e:
        print(str(e))


def html_for_pdf_preview(file_name, user_email, email_subject, content, body_message):
    try:
        organisation = Organisation.objects.get(id=content["organisation_id"])
        org_serializer = OrganisationSerializer(organisation)

        image_url = org_serializer.data.get("image_url")

        if image_url is not None:
            image_response = requests.get(image_url)
            image_response.raise_for_status()

            image_organisation_base64 = base64.b64encode(image_response.content).decode(
                "utf-8"
            )
            content["image_organisation_base64"] = image_organisation_base64
        else:
            content["image_organisation_base64"] = None

        html_message = render_to_string(file_name, content)

        return html_message
    except Exception as e:
        print(str(e))


def process_question_data(question_with_answer):
    processed_data = []

    for competency_data in question_with_answer:
        competency_name = competency_data["competency_name"]
        questions = competency_data["questions"]
        competency_average = {
            "competency_name": competency_name,
            "total_participant_responses": 0,
        }
        for question in questions:
            competency_average["total_participant_responses"] += question[
                "participant_response"
            ]

            for key, value in question.items():
                if key != "question" and key != "participant_response":
                    if key not in competency_average:
                        competency_average[key] = 0
                    competency_average[key] += value
        num_questions = len(questions)
        competency_average["total_participant_responses"] = round(
            competency_average["total_participant_responses"] / num_questions, 2
        )
        for key, value in competency_average.items():
            if key != "competency_name" and key != "total_participant_responses":
                competency_average[key] = round(
                    competency_average[key] / num_questions, 2
                )
        competency_array = [[key, value] for key, value in competency_average.items()]

        processed_data.append(competency_array)

    return processed_data


def get_total_observer_types(participant_observer, participant_id):
    observer_types_total = {}
    for observer in participant_observer.observers.all():
        observer_type = (
            ParticipantObserverType.objects.filter(
                participant__id=participant_id,
                observers__id=observer.id,
            )
            .first()
            .type.type
        )
        if observer_type in observer_types_total:
            observer_types_total[observer_type] = (
                observer_types_total[observer_type] + 1
            )
        else:
            observer_types_total[observer_type] = 1
    return observer_types_total


def get_data_for_score_analysis(question_with_answer):
    res = []
    for competency in question_with_answer:
        unique_columns = []
        rows = []

        for question in competency["questions"]:
            for key in question:
                if key not in unique_columns:
                    unique_columns.append(key)

        for question in competency["questions"]:
            question_data = []
            for column in unique_columns:
                if column in question:
                    question_data.append(question[column])
                else:
                    question_data.append("Not available")
            rows.append(question_data)
        res.append(
            {
                "competency_name": competency["competency_name"],
                "rows": rows,
                "unique_columns": unique_columns,
            }
        )

    return res


def get_frequency_analysis_data(
    questions, participant_response, participant_observer, participant_id, assessment_id
):
    question_with_labels = []
    for competency in questions.values("competency").distinct():
        competency_id = competency["competency"]
        competency_questions = questions.filter(competency__id=competency_id)

        max_key = max(map(int, competency_questions[0].label.keys()))

        result_array = []
        for i in range(1, max_key + 1):
            if competency_questions[0].label.get(str(i), "Not Avaliable") == "":
                result_array.append("Not Avaliable")
            else:
                result_array.append(
                    competency_questions[0].label.get(str(i), "Not Avaliable")
                )

        competency_object = {
            "competency_name": Competency.objects.get(id=competency_id).name,
            "labels_name": result_array,
            "questions": [],
        }
        for question in competency_questions:
            question_object = {
                "question": question.self_question,
            }

            participant_question_response = (
                participant_response.participant_response.get(str(question.id), "")
            )

            if participant_question_response in question_object:
                question_object[participant_question_response] += 1
            else:
                question_object[participant_question_response] = 1

            for observer in participant_observer.observers.all():
                observer_response = ObserverResponse.objects.get(
                    participant__id=participant_id,
                    observer__id=observer.id,
                    assessment__id=assessment_id,
                )
                observer_question_response = observer_response.observer_response.get(
                    str(question.id), ""
                )

                if observer_question_response in question_object:
                    question_object[observer_question_response] += 1
                else:
                    question_object[observer_question_response] = 1

            final_array = [question_object["question"]] + [
                question_object.get(i, "") for i in range(1, max_key + 1)
            ]
            competency_object["questions"].append(final_array)

        question_with_labels.append(competency_object)

    return question_with_labels


class DownloadParticipantResultReport(APIView):
    def post(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            participant_id = request.data.get("participant_id")
            assessment = Assessment.objects.get(id=assessment_id)
            participant = Learner.objects.get(id=participant_id)
            participant_observer = assessment.participants_observers.filter(
                participant__id=participant_id
            ).first()
            participant_response = ParticipantResponse.objects.get(
                participant__id=participant_id, assessment__id=assessment_id
            )

            question_with_answers = []

            frequency_analysis_data = get_frequency_analysis_data(
                assessment.questionnaire.questions,
                participant_response,
                participant_observer,
                participant_id,
                assessment_id,
            )
            # Group questions by competency
            for competency in assessment.questionnaire.questions.values(
                "competency"
            ).distinct():
                competency_id = competency["competency"]
                competency_questions = assessment.questionnaire.questions.filter(
                    competency__id=competency_id
                )

                competency_object = {
                    "competency_name": Competency.objects.get(id=competency_id).name,
                    "questions": [],
                }

                for question in competency_questions:
                    question_object = None

                    question_object = {
                        "question": question.self_question,
                        "participant_response": participant_response.participant_response.get(
                            str(question.id)
                        ),
                    }

                    count = 1
                    observer_types_total = get_total_observer_types(
                        participant_observer, participant_id
                    )
                    # Collect observer responses
                    for observer in participant_observer.observers.all():
                        observer_response = ObserverResponse.objects.get(
                            participant__id=participant_id,
                            observer__id=observer.id,
                            assessment__id=assessment_id,
                        )

                        observer_question_response = (
                            observer_response.observer_response.get(str(question.id))
                        )
                        observer_type = (
                            ParticipantObserverType.objects.filter(
                                participant__id=participant_id,
                                observers__id=observer.id,
                            )
                            .first()
                            .type.type
                        )

                        if observer_type in question_object:
                            existing_responses = question_object[observer_type]
                            new_response = observer_question_response
                            averaged_response = existing_responses + new_response
                            question_object[observer_type] = averaged_response
                        else:
                            question_object[observer_type] = observer_question_response

                        count = count + 1
                    for key, value in observer_types_total.items():
                        question_object[key] = question_object[key] / value

                    competency_object["questions"].append(question_object)

                question_with_answers.append(competency_object)

            averages = calculate_average(
                question_with_answers, assessment.assessment_type
            )

            graph_images = generate_graph(averages, assessment.assessment_type)

            data_for_assessment_overview_table = process_question_data(
                question_with_answers
            )
            data_for_score_analysis = get_data_for_score_analysis(question_with_answers)

            html_message = html_for_pdf_preview(
                "assessment/report/assessment_report.html",
                ["shashank@meeraq.com"],
                f"Report for {participant.name}",
                {
                    "name": participant.name,
                    "assessment_name": assessment.name,
                    "organisation_name": assessment.organisation.name,
                    "assessment_type": assessment.assessment_type,
                    "organisation_id": assessment.organisation.id,
                    "data_for_score_analysis": data_for_score_analysis,
                    "data_for_assessment_overview_table": data_for_assessment_overview_table,
                    "frequency_analysis_data": frequency_analysis_data,
                    "image_base64_array": graph_images,
                },
                f"This new report generated for {participant.name}",
            )

            return Response(
                {"html_pdf_preview": html_message},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to download report."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, assessment_id, participant_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
            participant = Learner.objects.get(id=participant_id)
            participant_observer = assessment.participants_observers.filter(
                participant__id=participant_id
            ).first()
            participant_response = ParticipantResponse.objects.get(
                participant__id=participant_id, assessment__id=assessment_id
            )

            question_with_answers = []

            frequency_analysis_data = get_frequency_analysis_data(
                assessment.questionnaire.questions,
                participant_response,
                participant_observer,
                participant_id,
                assessment_id,
            )
            # Group questions by competency
            for competency in assessment.questionnaire.questions.values(
                "competency"
            ).distinct():
                competency_id = competency["competency"]
                competency_questions = assessment.questionnaire.questions.filter(
                    competency__id=competency_id
                )

                competency_object = {
                    "competency_name": Competency.objects.get(id=competency_id).name,
                    "questions": [],
                }

                for question in competency_questions:
                    question_object = None

                    question_object = {
                        "question": question.self_question,
                        "participant_response": participant_response.participant_response.get(
                            str(question.id)
                        ),
                    }

                    count = 1
                    observer_types_total = get_total_observer_types(
                        participant_observer, participant_id
                    )
                    # Collect observer responses
                    for observer in participant_observer.observers.all():
                        observer_response = ObserverResponse.objects.get(
                            participant__id=participant_id,
                            observer__id=observer.id,
                            assessment__id=assessment_id,
                        )

                        observer_question_response = (
                            observer_response.observer_response.get(str(question.id))
                        )
                        observer_type = (
                            ParticipantObserverType.objects.filter(
                                participant__id=participant_id,
                                observers__id=observer.id,
                            )
                            .first()
                            .type.type
                        )

                        if observer_type in question_object:
                            existing_responses = question_object[observer_type]
                            new_response = observer_question_response
                            averaged_response = existing_responses + new_response
                            question_object[observer_type] = averaged_response
                        else:
                            question_object[observer_type] = observer_question_response

                        count = count + 1
                    for key, value in observer_types_total.items():
                        question_object[key] = question_object[key] / value

                    competency_object["questions"].append(question_object)

                question_with_answers.append(competency_object)

            averages = calculate_average(
                question_with_answers, assessment.assessment_type
            )

            graph_images = generate_graph(averages, assessment.assessment_type)

            data_for_assessment_overview_table = process_question_data(
                question_with_answers
            )
            data_for_score_analysis = get_data_for_score_analysis(question_with_answers)

            generate_report_for_participant(
                "assessment/report/assessment_report.html",
                {
                    "name": participant.name,
                    "assessment_name": assessment.name,
                    "organisation_name": assessment.organisation.name,
                    "assessment_type": assessment.assessment_type,
                    "organisation_id": assessment.organisation.id,
                    "data_for_score_analysis": data_for_score_analysis,
                    "data_for_assessment_overview_table": data_for_assessment_overview_table,
                    "frequency_analysis_data": frequency_analysis_data,
                    "image_base64_array": graph_images,
                },
            )
            pdf_path = "graphsAndReports/Report.pdf"

            with open(pdf_path, "rb") as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type="application/pdf")
                response[
                    "Content-Disposition"
                ] = f'attachment; filename={f"{participant.name} Report.pdf"}'
            # Close the file after reading
            pdf_file.close()

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to download report."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetAssessmentNotification(APIView):
    def get(self, request, user_id):
        notifications = AssessmentNotification.objects.filter(
            user__id=user_id
        ).order_by("-created_at")

        serializer = AssessmentNotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class MarkAllNotificationAsRead(APIView):
    def put(self, request):
        notifications = AssessmentNotification.objects.filter(
            read_status=False, user__id=request.data["user_id"]
        )
        notifications.update(read_status=True)
        return Response("Notifications marked as read.")


class MarkNotificationAsRead(APIView):
    def put(self, request):
        user_id = request.data.get("user_id")
        notification_ids = request.data.get("notification_ids")

        if user_id is None or notification_ids is None:
            return Response(
                "Both user_id and notification_ids are required.", status=400
            )

        notifications = AssessmentNotification.objects.filter(
            id=notification_ids, user__id=user_id, read_status=False
        )

        notifications.update(read_status=True)
        return Response("Notifications marked as read.")


class GetUnreadNotificationCount(APIView):
    def get(self, request, user_id):
        count = AssessmentNotification.objects.filter(
            user__id=user_id, read_status=False
        ).count()
        return Response({"count": count})
