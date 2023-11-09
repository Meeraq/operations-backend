from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.template.loader import render_to_string
from operationsBackend import settings
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
    Behavior,
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
from api.models import Profile, Learner, Organisation, HR, SentEmailActivity
from django.core.mail import EmailMessage, BadHeaderError
from api.serializers import LearnerSerializer
from collections import defaultdict
from django.db.models import BooleanField, F, Exists, OuterRef
from django.db.models import Q
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from django.utils import timezone
from django_rest_passwordreset.tokens import get_token_generator
from django_rest_passwordreset.models import ResetPasswordToken

import uuid
from django.db.models import Q, Prefetch, Exists, OuterRef, Count
import environ

env = environ.Env()


class EmailSendingError(Exception):
    pass


def send_reset_password_link(users):
        # Assuming you are sending a POST request with a list of emails in the body
    for user_data in users:
        try:
            user = User.objects.get(email=user_data['email'])
            # Replace YourUserModel with your actual user model
            token = get_token_generator().generate_token()
            # Save the token to the database
            ResetPasswordToken.objects.create(user=user, key=token)
            # def send_mail_templates(file_name, user_email, email_subject, content, bcc_emails):
            reset_password_link = (
                f"https://assessment.meeraq.com/create-password/{token}"
            )
            send_mail_templates(
                "assessment/assessment_email_to_participant.html",
                [user_data['email']],
                "Meeraq - Welcome to Assessment Platform !",
                {
                    "participant_name": user_data['name'],
                    "link": reset_password_link,
                },
                [],
            )
        except Exception as e:
            print(f"Error sending link to {user_data.email}: {str(e)}")



def create_send_email(user_email, file_name):
    user_email = user_email
    file_name = file_name
    try:
        user = User.objects.get(username=user_email)
        sent_email = SentEmailActivity.objects.create(
            user=user,
            email_subject=file_name,
            timestamp=timezone.now(),
        )
        sent_email.save()
    except Exception as e:
        pass


def send_mail_templates(file_name, user_email, email_subject, content, bcc_emails):
    email_message = render_to_string(file_name, content)

    email = EmailMessage(
        f"{env('EMAIL_SUBJECT_INITIAL',default='')} {email_subject}",
        email_message,
        settings.DEFAULT_FROM_EMAIL,
        user_email,
        bcc_emails,
    )
    email.content_subtype = "html"

    try:
        email.send(fail_silently=False)
        for email in user_email:
            create_send_email(email, file_name)
    except BadHeaderError as e:
        print(f"Error occurred while sending emails: {str(e)}")
        raise EmailSendingError(f"Error occurred while sending emails: {str(e)}")


# def create_notification(user, path, message):
#     notification = Notification.objects.create(user=user, path=path, message=message)
#     return notification


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
        try:
            print(request.data)
            behaviors = request.data.get("behaviors")
            behavior_ids = []

            # Create and save individual behaviors
            for behavior_data in behaviors:
                single_behavior = Behavior(
                    name=behavior_data.get("name"),
                    description=behavior_data.get("description"),
                )
                single_behavior.save()
                behavior_ids.append(single_behavior.id)

            # Create the competency with associated behaviors
            competency = Competency(
                name=request.data.get("name"),
                description=request.data.get("description"),
            )
            competency.save()
            competency.behaviors.set(behavior_ids)

            return Response(
                {
                    "message": "Competency and associated behaviors created successfully.",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {
                    "error": f"Failed to create Competency: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        

    def put(self, request):
        behaviors = request.data.get("behaviors")
        behavior_ids = []
        competency_id = request.data.get("id")
        try:
            competency = Competency.objects.get(id=competency_id)
        except Competency.DoesNotExist:
            return Response(
                {"message": "Competency not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            for behavior_data in behaviors:
                single_behavior, created = Behavior.objects.get_or_create(
                    name=behavior_data.get("name"),
                    description=behavior_data.get("description"),
                )
                single_behavior.save()
                behavior_ids.append(single_behavior.id)

            competency.behaviors.set(behavior_ids)
            competency.name = request.data.get("name")
            competency.description = request.data.get("description")
            competency.save()

            return Response(
                {"message": "Competency updated successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to update Competency"},
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
            assessment.participant_view_name = request.data.get("participant_view_name")
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
          

            particpant_data=[{"name":participant.name,"email":participant.email}]
            send_reset_password_link(particpant_data)

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
                    "label": question.label,
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
            serializer = AssessmentAnsweredSerializerDepthThree(assessment)
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
            observer_link=f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{observer_unique_id.unique_id}"
            send_mail_templates(
                "assessment/assessment_email_to_observer.html",
                [observer.email],
                "Meeraq - Welcome to Assessment Platform !",
                {
                    "assessment_name": assessment.name,
                    "participant_name": participants_observer.participant.name,
                    "observer_name":observer.name,
                    "link":observer_link,
                },
                [],
            )

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
                observer_link=f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{observer_unique_id.unique_id}"
                send_mail_templates(
                "assessment/assessment_email_to_observer.html",
                [observer.email],
                "Meeraq - Welcome to Assessment Platform !",
                {
                    "assessment_name": assessment.name,
                    "participant_name": participants_observer.participant.name,
                    "observer_name":observer.name,
                    "link":observer_link,
                },
                [],
            )

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


class AssessmentsOfHr(APIView):
    def get(self, request, hr_email):
        try:
            hr = HR.objects.get(email=hr_email)

            assessments = Assessment.objects.filter(
                Q(hr=hr) & (Q(status="ongoing") | Q(status="completed"))
            )

            serializer = AssessmentSerializerDepthThree(assessments, many=True)

            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetParticipantResponseForAllAssessment(APIView):
    def get(self, request, hr_email):
        try:
            participant_responses = ParticipantResponse.objects.filter(
                assessment__hr__email=hr_email,
            )

            serializer = ParticipantResponseSerializer(participant_responses, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetObserverResponseForAllAssessment(APIView):
    def get(self, request, hr_email):
        try:
            observer_responses = ObserverResponse.objects.filter(
                assessment__hr__email=hr_email,
            )

            serializer = ObserverResponseSerializer(observer_responses, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReminderMailForObserverByPmoAndParticipant(APIView):
    def put(self, request):
        try:
            assessment_id= request.data.get("assessment_id")
            assessment=Assessment.objects.get(
                    id=assessment_id
            )    
            participant_observers_id = request.data.get("participant_observers_id")
            participants_observer = ParticipantObserverMapping.objects.get(
                id=participant_observers_id
            )
            for observer in participants_observer.observers.all():
                observer_response_data=ObserverResponse.objects.filter(
                    participant__id=participants_observer.participant.id,
                    observer__id=observer.id,
                    assessment__id=assessment.id,
                )    
                observer_unique_id=ObserverUniqueId.objects.get(
                    participant=participants_observer.participant,
                    observer=observer,
                    assessment=assessment,
                )
                
                if not observer_response_data:
                    observer_link=f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{observer_unique_id.unique_id}"
                    send_mail_templates(
                    "assessment/reminder_mail_for_observer_by_pmo_and_participant.html",
                    [observer.email],
                    "Meeraq - Welcome to Assessment Platform !",
                    {
                        "assessment_name": assessment.name,
                        "participant_name": participants_observer.participant.name,
                        "observer_name":observer.name,
                        "link":observer_link,
                    },
                    [],
                )
                
            return Response(
                    {
                        "message": "Notification is send succes successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to send Notification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        