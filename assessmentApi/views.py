from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.template.loader import render_to_string
from operationsBackend import settings
from openpyxl import Workbook
import openpyxl
from rest_framework.decorators import api_view, permission_classes
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
    ObserverTypes,
    AssessmentNotification,
    ParticipantUniqueId,
    ParticipantReleasedResults,
)
from .serializers import (
    CompetencySerializerDepthOne,
    QuestionSerializer,
    QuestionnaireSerializer,
    QuestionSerializerDepthTwo,
    QuestionnaireSerializerDepthThree,
    AssessmentSerializer,
    AssessmentSerializerDepthFour,
    AssessmentAnsweredSerializerDepthFour,
    ParticipantResponseSerializerDepthFive,
    ObserverResponseSerializerDepthFour,
    ParticipantObserverTypeSerializerDepthTwo,
    ObserverUniqueIdSerializerDepthTwo,
    ObserverTypeSerializer,
    AssessmentNotificationSerializer,
    ParticipantReleasedResultsSerializerDepthOne,
    ParticipantObserverMappingSerializerDepthOne,
)
from django.db import transaction, IntegrityError
import json
import string
import random
import pandas as pd
from django.contrib.auth.models import User
from api.models import Profile, Learner, Organisation, HR, SentEmailActivity, Role, Pmo
from api.serializers import OrganisationSerializer
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
import requests
import uuid
from django.db.models import Q, Prefetch, Exists, OuterRef, Count
import environ
import base64
from django.core.mail import EmailMessage
from xhtml2pdf import pisa
import pdfkit
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import os
from time import sleep
from django.http import HttpResponse
from datetime import datetime
import io
from api.views import add_contact_in_wati
from schedularApi.tasks import (
    send_assessment_invitation_mail,
    send_whatsapp_message,
    send_assessment_invitation_mail_on_click,
)
from django.shortcuts import render, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from django.http import Http404
from courses.models import (
    Course,
    Lesson,
    Assessment as AssessmentLesson,
    FeedbackLessonResponse,
    QuizLessonResponse,
    CourseEnrollment,
)
from schedularApi.models import SchedularBatch, SchedularSessions, SchedularProject
from api.permissions import IsInRoles

matplotlib.use("Agg")
env = environ.Env()

from io import BytesIO
from apryse_sdk import PDFNet, Convert, StructuredOutputModule

wkhtmltopdf_path = os.environ.get(
    "WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")


def send_reset_password_link(users):
    # Assuming you are sending a POST request with a list of emails in the body
    for user_data in users:
        try:
            user = User.objects.get(username=user_data["email"])
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
                [user_data["email"]],
                "Meeraq - Welcome to Assessment Platform !",
                {
                    "participant_name": user_data["name"],
                    "link": reset_password_link,
                },
                [],
            )
        except Exception as e:
            print(f"Error sending link to {user_data['email']}: {str(e)}")


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
    try:
        email_message = render_to_string(file_name, content)

        email = EmailMessage(
            f"{env('EMAIL_SUBJECT_INITIAL',default='')} {email_subject}",
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            user_email,
            bcc_emails,
        )
        email.content_subtype = "html"

        email.send(fail_silently=False)
        for email in user_email:
            create_send_email(email, file_name)
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")


# def create_notification(user, path, message):
#     notification = Notification.objects.create(user=user, path=path, message=message)
#     return notification

#         for participant_observer_mapping in participants_observers:
#             participant = participant_observer_mapping.participant
#             participant_unique_id = ParticipantUniqueId.objects.filter(participant=participant)
#             print("hello")
#             print(participant_unique_id)

#             # if participant_unique_id:
#             #     # Send WhatsApp messages to the participant and observers
#             #     send_whatsapp_message("learner", participant, assessment)


from django.core.exceptions import ObjectDoesNotExist


def create_learner(learner_name, learner_email):
    try:
        with transaction.atomic():
            if not learner_email:
                raise ValueError("Username field is required")

            user = User.objects.filter(username=learner_email).first()
            learner = None
            if user:
                learner = Learner.objects.filter(user__user=user).first()
                if learner:
                    profile = Profile.objects.get(user=user)
                    learner_role, created = Role.objects.get_or_create(name="learner")
                    profile.roles.add(learner_role)
                    learner.name = learner_name.strip().title()
                    learner.save()
                    return learner
                else:
                    profile = Profile.objects.get(user=user)
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
                profile = Profile.objects.create(user=user)
            learner_role, created = Role.objects.get_or_create(name="learner")
            profile.roles.add(learner_role)
            profile.save()
            learner = Learner.objects.create(
                user=profile,
                name=learner_name.strip().title(),
                email=learner_email,
            )
            return learner
    except ValueError as e:
        raise ValueError(str(e))

    except Exception as e:
        raise Exception(str(e))


class CompetencyView(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        competencies = Competency.objects.all()
        serializer = CompetencySerializerDepthOne(competencies, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
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
                {"message": "Competency not found"}, status=status.HTTP_404_NOT_FOUND
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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        competency_id = request.data.get("id")
        try:
            competency = Competency.objects.get(id=competency_id)
        except Competency.DoesNotExist:
            return Response(
                {"message": "Competency not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompetencySerializerDepthOne(competency)
        return Response(serializer.data)


class QuestionView(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        questions = Question.objects.all()
        serializer = QuestionSerializerDepthTwo(questions, many=True)

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
            serializer = QuestionSerializerDepthTwo(question, data=request.data)
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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        question_id = request.data.get("id")
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"message": "Question not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = QuestionSerializerDepthTwo(question)
        return Response(serializer.data)


class QuestionnaireView(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        questionnaires = Questionnaire.objects.all()
        serializer = QuestionnaireSerializerDepthThree(questionnaires, many=True)
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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        questionnaire_id = request.data.get("id")
        try:
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)
        except Questionnaire.DoesNotExist:
            return Response(
                {"message": "Questionnaire not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = QuestionnaireSerializerDepthThree(questionnaire)
        return Response(serializer.data)


def create_pre_post_assessments(request):
    try:
        pre_assessment_serializer = AssessmentSerializer(
            data=request.data["pre_assessment_data"]
        )
        post_assessment_serializer = AssessmentSerializer(
            data=request.data["post_assessment_data"]
        )
        if (
            pre_assessment_serializer.is_valid()
            and post_assessment_serializer.is_valid()
        ):
            pre_assessment = pre_assessment_serializer.save()
            post_assessment = post_assessment_serializer.save()
            post_assessment.pre_assessment = pre_assessment
            post_assessment.save()

            return True, pre_assessment.id, post_assessment.id
        return False, None, None
    except Exception as e:
        return False, None, None


class AssessmentView(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        assessments = Assessment.objects.all()
        serializer = AssessmentSerializerDepthFour(assessments, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.data["assessment_creation_type"] == "individual":
            serializer = AssessmentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Assessment created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {"error": "Failed to create Assessment."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif request.data["assessment_creation_type"] == "pre_post":
            (
                created,
                pre_assessment_id,
                post_assessment_id,
            ) = create_pre_post_assessments(request)
            if created:
                return Response(
                    {"message": "Assessment created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {"error": "Failed to create Assessment."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"error": "Failed to create Assessment."},
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
            if request.data.get("assessment_timing") == "post":
                pre_assessment = Assessment.objects.get(
                    id=request.data.get("pre_assessment")
                )

            organisation = Organisation.objects.get(id=request.data.get("organisation"))
            hr = []
            for hr_id in request.data.get("hr"):
                one_hr = HR.objects.get(id=hr_id)
                hr.append(one_hr)
            observer_types = []
            for observer_type_id in request.data.get("observer_types"):
                one_observer_type = ObserverTypes.objects.get(id=observer_type_id)
                observer_types.append(one_observer_type)

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
            assessment.observer_types.set(observer_types)
            assessment.assessment_start_date = request.data.get("assessment_start_date")
            assessment.whatsapp_reminder = request.data.get("whatsapp_reminder")
            assessment.email_reminder = request.data.get("email_reminder")
            assessment.reminders = request.data.get("reminders")
            assessment.assessment_timing = request.data.get("assessment_timing")
            if request.data.get("assessment_timing") == "post":
                assessment.pre_assessment = pre_assessment
            else:
                assessment.pre_assessment = None
            assessment.save()

            serializer = AssessmentSerializerDepthFour(assessment)
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


class AssessmentStatusChange(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def put(self, request):
        assessment_id = request.data.get("id")

        try:
            with transaction.atomic():
                assessment = Assessment.objects.get(id=assessment_id)
                prev_status = assessment.status
                assessment.status = request.data.get("status")
                # assessment.assessment_end_date = request.data.get("assessment_end_date")
                assessment.save()
                assessment_lesson = AssessmentLesson.objects.filter(
                    assessment_modal=assessment
                ).first()

                if assessment_lesson:
                    lesson = Lesson.objects.filter(
                        id=assessment_lesson.lesson.id
                    ).first()

                    if assessment.status == "ongoing":
                        lesson.status = "public"
                        lesson.save()
                    if assessment.status == "draft":
                        lesson.status = "draft"
                        lesson.save()

                if (
                    prev_status == "draft"
                    and assessment.status == "ongoing"
                    and not assessment.initial_reminder
                ):
                    send_assessment_invitation_mail.delay(assessment.id)
                    assessment.initial_reminder = True
                    assessment.save()
                    # for hr in assessment.hr.all():
                    #     user = User.objects.get(email=hr.email)

                    #     token = get_token_generator().generate_token()

                    #     ResetPasswordToken.objects.create(user=user, key=token)

                    #     create_password_link = (
                    #         f"https://assessment.meeraq.com/create-password/{token}"
                    #     )

                    # send_mail_templates(
                    #     "assessment/create_password_to_hr.html",
                    #     [hr.email],
                    #     "Meeraq - Welcome to Assessment Platform !",
                    #     {
                    #         "hr_name": hr.first_name,
                    #         "link": create_password_link,
                    #         "assessment_name": assessment.participant_view_name,
                    #     },
                    #     [],
                    # )
                    # if not assessment.initial_reminder:
                    #     for (
                    #         participant_observers
                    #     ) in assessment.participants_observers.all():
                    #         participant = participant_observers.participant
                    #         participant_response = ParticipantResponse.objects.filter(
                    #             participant=participant, assessment=assessment
                    #         ).first()

                    #         if not participant_response:
                    #             participant_unique_id = ParticipantUniqueId.objects.filter(
                    #                 participant=participant, assessment=assessment
                    #             ).first()

                    #             if participant_unique_id:
                    #                 assessment_link = f"{env('ASSESSMENT_URL')}/participant/meeraq/assessment/{participant_unique_id.unique_id}"
                    #                 send_mail_templates(
                    #                     "assessment/assessment_initial_reminder.html",
                    #                     [participant.email],
                    #                     "Meeraq - Welcome to Assessment Platform !",
                    #                     {
                    #                         "assessment_name": assessment.participant_view_name,
                    #                         "participant_name": participant.name.title(),
                    #                         "link": assessment_link,
                    #                     },
                    #                     [],
                    #                 )
                    # send_assessment_invitation_mail.delay(assessment.id)
                    # assessment.initial_reminder = True
                    # assessment.save()

                serializer = AssessmentSerializerDepthFour(assessment)
                return Response(
                    {
                        "message": "Update successfully.",
                        "assessment_data": serializer.data,
                    },
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


class AssessmentEndDataChange(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def put(self, request):
        assessment_id = request.data.get("id")

        try:
            assessment = Assessment.objects.get(id=assessment_id)
            # assessment.status = request.data.get("status")
            assessment.assessment_end_date = request.data.get("assessment_end_date")
            assessment.save()
            serializer = AssessmentSerializerDepthFour(assessment)
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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    @transaction.atomic
    def put(self, request):
        assessment_id = request.data.get("assessment_id")
        phone = request.data.get("phone")

        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        assessment.result_released = False
        assessment.save()
        try:
            participants = request.data.get("participants", [])

            if assessment.participants_observers.filter(
                participant__email=participants[0]["participantEmail"]
            ).exists():
                return Response(
                    {"error": "Participant already exists in the assessment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            participant = create_learner(
                participants[0]["participantName"].title(),
                participants[0]["participantEmail"],
            )
            if phone:
                participant.phone = phone
                participant.save()
            unique_id = uuid.uuid4()  # Generate a UUID4
            if phone:
                add_contact_in_wati(
                    "learner", participant.name.title(), participant.phone
                )
            # Creating a ParticipantUniqueId instance with a UUID as unique_id
            unique_id_instance = ParticipantUniqueId.objects.create(
                participant=participant,
                assessment=assessment,
                unique_id=unique_id,
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

            particpant_data = [{"name": participant.name, "email": participant.email}]
            # send_reset_password_link(particpant_data)

            if assessment.assessment_timing == "pre":
                post_assessment = Assessment.objects.filter(
                    pre_assessment=assessment
                ).first()

                if not post_assessment.participants_observers.filter(
                    participant__email=participants[0]["participantEmail"]
                ).exists():
                    mapping = ParticipantObserverMapping.objects.create(
                        participant=participant
                    )
                    mapping.save()
                    post_assessment.participants_observers.add(mapping)
                    post_assessment.save()
                    post_unique_id = uuid.uuid4()
                    post_unique_id_instance = ParticipantUniqueId.objects.create(
                        participant=participant,
                        assessment=post_assessment,
                        unique_id=post_unique_id,
                    )
            elif assessment.assessment_timing == "post":
                pre_assessment = Assessment.objects.get(id=assessment.pre_assessment.id)

                if not pre_assessment.participants_observers.filter(
                    participant__email=participants[0]["participantEmail"]
                ).exists():
                    mapping = ParticipantObserverMapping.objects.create(
                        participant=participant
                    )
                    mapping.save()
                    pre_assessment.participants_observers.add(mapping)
                    pre_assessment.save()
                    pre_unique_id = uuid.uuid4()
                    pre_unique_id_instance = ParticipantUniqueId.objects.create(
                        participant=participant,
                        assessment=pre_assessment,
                        unique_id=pre_unique_id,
                    )
            serializer = AssessmentSerializerDepthFour(assessment)
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
    permission_classes = [IsAuthenticated, IsInRoles("learner")]

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

            serializer = AssessmentAnsweredSerializerDepthFour(assessments, many=True)

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
    permission_classes = [AllowAny]

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
                    "response_type": question.response_type,
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
    permission_classes = [AllowAny]

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
                    "label": question.label,
                    "rating_type": question.rating_type,
                    "response_type": question.response_type,
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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

    def get(self, request, email):
        try:
            assessments = Assessment.objects.filter(
                participants_observers__observers__email=email, status="ongoing"
            ).distinct()

            serializer = AssessmentSerializerDepthFour(assessments, many=True)
            return Response(serializer.data)
        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessments not found for the provided observer's email."},
                status=404,
            )


class CreateParticipantResponseView(APIView):
    permission_classes = [AllowAny]

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
            serializer = AssessmentAnsweredSerializerDepthFour(assessment)
            return Response(
                {"message": "Submit Successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": "Failed to Submit."}, status=status.HTTP_404_NOT_FOUND
            )


class CreateObserverResponseView(APIView):
    permission_classes = [AllowAny]

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
    permission_classes = [IsAuthenticated]

    def get(self, request, participant_email):
        try:
            participant = Learner.objects.get(email=participant_email)

            participant_responses = ParticipantResponse.objects.filter(
                participant=participant,
            )

            serializer = ParticipantResponseSerializerDepthFive(
                participant_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetParticipantResponseFormAssessment(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr")]

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)

            participant_responses = ParticipantResponse.objects.filter(
                assessment=assessment,
            )

            serializer = ParticipantResponseSerializerDepthFive(
                participant_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetObserverResponseForObserver(APIView):
    permission_classes = [AllowAny]

    def get(self, request, observer_email):
        try:
            observer = Observer.objects.get(email=observer_email)

            observer_responses = ObserverResponse.objects.filter(
                observer=observer,
            )

            serializer = ObserverResponseSerializerDepthFour(
                observer_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetObserverResponseFormAssessment(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr", "learner")]

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)

            observer_responses = ObserverResponse.objects.filter(
                assessment=assessment,
            )

            serializer = ObserverResponseSerializerDepthFour(
                observer_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParticipantObserverTypeList(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr", "learner")]

    def get(self, request):
        participant_observer_types = ParticipantObserverType.objects.all()
        serializer = ParticipantObserverTypeSerializerDepthTwo(
            participant_observer_types, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


def delete_participant_from_assessments(assessment, participant_id, assessment_id):
    try:
        with transaction.atomic():
            if assessment.assessment_timing == "pre":
                post_assessment = Assessment.objects.filter(
                    pre_assessment=assessment
                ).first()
                post_assessment.participants_observers.filter(
                    participant__id=participant_id
                ).delete()
                participant_unique_id = ParticipantUniqueId.objects.filter(
                    participant__id=participant_id,
                    assessment=post_assessment,
                )
                if participant_unique_id:
                    participant_unique_id.delete()
                post_assessment_participant_response = (
                    ParticipantResponse.objects.filter(
                        participant__id=participant_id,
                        assessment=post_assessment,
                    )
                )
                if post_assessment_participant_response:
                    post_assessment_participant_response.delete()
            elif assessment.assessment_timing == "post":
                pre_assessment = assessment.pre_assessment
                pre_assessment.participants_observers.filter(
                    participant__id=participant_id
                ).delete()
                participant_unique_id = ParticipantUniqueId.objects.filter(
                    participant__id=participant_id,
                    assessment=pre_assessment,
                )
                if participant_unique_id:
                    participant_unique_id.delete()
                pre_assessment_participant_response = (
                    ParticipantResponse.objects.filter(
                        participant__id=participant_id,
                        assessment=pre_assessment,
                    )
                )
                if pre_assessment_participant_response:
                    pre_assessment_participant_response.delete()

            assessment.participants_observers.filter(
                participant__id=participant_id
            ).delete()
            assessment_participant_unique_id = ParticipantUniqueId.objects.filter(
                participant__id=participant_id,
                assessment=assessment,
            )
            if assessment_participant_unique_id:
                assessment_participant_unique_id.delete()
            assessment_participant_response = ParticipantResponse.objects.filter(
                participant__id=participant_id,
                assessment=assessment,
            )
            if assessment_participant_response:
                assessment_participant_response.delete()

            return True
        return False
    except Exception as e:
        print(str(e))
        return False


class DeleteParticipantFromAssessment(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    @transaction.atomic
    def delete(self, request):
        try:
            with transaction.atomic():
                assessment_id = request.data.get("assessment_id")
                participant_observers = request.data.get("participant_observers")
                assessment = Assessment.objects.get(id=assessment_id)

                assessment_lesson = AssessmentLesson.objects.filter(
                    assessment_modal=assessment
                ).first()
                if assessment_lesson:
                    learner = Learner.objects.get(
                        id=participant_observers["participant"]["id"]
                    )

                    batch = assessment_lesson.lesson.course.batch
                    if learner in batch.learners.all():
                        batch.learners.remove(learner)
                        # Remove the learner from FeedbackLessonResponse if present
                        feedback_responses = FeedbackLessonResponse.objects.filter(
                            learner=learner,
                            feedback_lesson__lesson__course__batch=batch,
                        )
                        feedback_responses.delete()
                        # Remove the learner from QuizLessonResponse if present
                        quiz_responses = QuizLessonResponse.objects.filter(
                            learner=learner, quiz_lesson__lesson__course__batch=batch
                        )
                        quiz_responses.delete()

                        # Remove the learner from CourseEnrollment if enrolled
                        enrollments = CourseEnrollment.objects.filter(
                            learner=learner, course__batch=batch
                        )
                        enrollments.delete()

                        # Remove the learner from SchedularSessions if present
                        schedular_sessions = SchedularSessions.objects.filter(
                            learner=learner, coaching_session__batch=batch
                        )
                        schedular_sessions.delete()

                        assessment = Assessment.objects.filter(
                            assessment_modal__lesson__course__batch=batch
                        ).first()

                deleted = delete_participant_from_assessments(
                    assessment,
                    participant_observers["participant"]["id"],
                    assessment_id,
                )
                if deleted:
                    serializer = AssessmentSerializerDepthFour(assessment)
                    return Response(
                        {
                            "message": "Successfully removed participant from assessments.",
                            "assessment_data": serializer.data,
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {"error": "Failed to Remove Participant"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "learner")]

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

            serializer = AssessmentSerializerDepthFour(assessment)

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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    @transaction.atomic
    def put(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            participant_observers_id = request.data.get("participant_observers_id")
            participants_observer = ParticipantObserverMapping.objects.get(
                id=participant_observers_id
            )
            observerName = request.data.get("observerName").title()
            observerEmail = request.data.get("observerEmail")
            observerType = request.data.get("observerType")

            assessment = Assessment.objects.get(id=assessment_id)
            observer_type = ObserverTypes.objects.get(id=observerType)

            if participants_observer.observers.filter(email=observerEmail).exists():
                return Response(
                    {"error": f"Observer with email '{observerEmail}' already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if participants_observer.participant.email == observerEmail:
                return Response(
                    {
                        "error": f"Cannot add the same email observer to a participant with the same email address: {observerEmail}"
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
                type=observer_type,
            )

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
            observer_link = f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{observer_unique_id.unique_id}"
            
            # send_mail_templates(
            #     "assessment/assessment_email_to_observer.html",
            #     [observer.email],
            #     "Meeraq - Welcome to Assessment Platform !",
            #     {
            #         "assessment_name": assessment.participant_view_name,
            #         "participant_name": participants_observer.participant.name,
            #         "observer_name": observer.name,
            #         "link": observer_link,
            #     },
            #     [],
            # )

            serializer = AssessmentSerializerDepthFour(assessment)
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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

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
    permission_classes = [IsAuthenticated, IsInRoles("learner")]

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
                observer_type = ObserverTypes.objects.get(id=observerType)
                if participants_observer.observers.filter(email=observerEmail).exists():
                    return Response(
                        {
                            "error": f"Observer with email '{observerEmail}' already exists."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if participants_observer.participant.email == observerEmail:
                    return Response(
                        {
                            "error": f"Cannot add the same email observer to a participant with the same email address: {observerEmail}"
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
                    type=observer_type,
                )
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
                observer_link = f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{observer_unique_id.unique_id}"
                send_mail_templates(
                    "assessment/assessment_email_to_observer.html",
                    [observer.email],
                    "Meeraq - Welcome to Assessment Platform !",
                    {
                        "assessment_name": assessment.participant_view_name,
                        "participant_name": participants_observer.participant.name,
                        "observer_name": observer.name,
                        "link": observer_link,
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
    permission_classes = [AllowAny]

    def get(self, request, unique_id):
        try:
            observer_unique_id = ObserverUniqueId.objects.get(unique_id=unique_id)

            serializer = AssessmentSerializerDepthFour(observer_unique_id.assessment)

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
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr", "learner")]

    def get(self, request, assessment_id):
        try:
            observers_unique_id = ObserverUniqueId.objects.filter(
                assessment__id=assessment_id
            )

            serializer = ObserverUniqueIdSerializerDepthTwo(
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
    permission_classes = [IsAuthenticated, IsInRoles("learner")]

    def get(self, request, participant_email):
        try:
            observers_unique_id = ObserverUniqueId.objects.filter(
                participant__email=participant_email
            )

            serializer = ObserverUniqueIdSerializerDepthTwo(
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
    permission_classes = [AllowAny]

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


class StartAssessmentParticipantDisabled(APIView):
    permission_classes = [AllowAny]

    def get(self, request, unique_id):
        try:
            participant_unique_id = ParticipantUniqueId.objects.filter(
                unique_id=unique_id
            ).first()

            participant_response_data = ParticipantResponse.objects.filter(
                participant=participant_unique_id.participant,
                assessment=participant_unique_id.assessment,
            )
            if participant_response_data:
                return Response({"participant_response": True})
            else:
                return Response({"participant_response": False})
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to retrieve participant response data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AssessmentsOfHr(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("hr")]

    def get(self, request, hr_email):
        try:
            hr = HR.objects.get(email=hr_email)

            assessments = Assessment.objects.filter(
                Q(hr=hr) & (Q(status="ongoing") | Q(status="completed"))
            )

            serializer = AssessmentSerializerDepthFour(assessments, many=True)

            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetParticipantResponseForAllAssessment(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("hr")]

    def get(self, request, hr_email):
        try:
            participant_responses = ParticipantResponse.objects.filter(
                assessment__hr__email=hr_email,
            )

            serializer = ParticipantResponseSerializerDepthFive(
                participant_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetObserverResponseForAllAssessment(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("hr")]

    def get(self, request, hr_email):
        try:
            observer_responses = ObserverResponse.objects.filter(
                assessment__hr__email=hr_email,
            )

            serializer = ObserverResponseSerializerDepthFour(
                observer_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReminderMailForObserverByPmoAndParticipant(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "learner")]

    def put(self, request):
        try:
            assessment_id = request.data.get("assessment_id")
            assessment = Assessment.objects.get(id=assessment_id)
            participant_observers_id = request.data.get("participant_observers_id")
            participants_observer = ParticipantObserverMapping.objects.get(
                id=participant_observers_id
            )
            for observer in participants_observer.observers.all():
                observer_response_data = ObserverResponse.objects.filter(
                    participant__id=participants_observer.participant.id,
                    observer__id=observer.id,
                    assessment__id=assessment.id,
                )
                observer_unique_id = ObserverUniqueId.objects.get(
                    participant=participants_observer.participant,
                    observer=observer,
                    assessment=assessment,
                )

                if not observer_response_data:
                    observer_link = f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{observer_unique_id.unique_id}"
                    send_mail_templates(
                        "assessment/reminder_mail_for_observer_by_pmo_and_participant.html",
                        [observer.email],
                        "Meeraq - Welcome to Assessment Platform !",
                        {
                            "assessment_name": assessment.participant_view_name,
                            "participant_name": participants_observer.participant.name,
                            "observer_name": observer.name,
                            "link": observer_link,
                        },
                        [],
                    )
                    sleep(3)
            return Response(
                {
                    "message": "Reminders are Send Successfully",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to send Notification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetParticipantResponseForAllAssessments(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            participant_responses = ParticipantResponse.objects.all()

            serializer = ParticipantResponseSerializerDepthFive(
                participant_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetObserverResponseForAllAssessments(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            observer_responses = ObserverResponse.objects.all()
            serializer = ObserverResponseSerializerDepthFour(
                observer_responses, many=True
            )

            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddMultipleQuestions(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    @transaction.atomic
    def post(self, request):
        try:
            with transaction.atomic():

                questions = request.data.get("questions")

                for question in questions:
                    behavior, created = Behavior.objects.get_or_create(
                        name=question["behaviour"].strip(),
                        description="This is a demo description",
                    )
                    behavior.save()
                    competency, created = Competency.objects.get_or_create(
                        name=question["compentency_name"].strip()
                    )
                    competency.description = question["compentency_description"]
                    competency.behaviors.add(behavior)
                    competency.save()

                    if question["rating_type"].strip() == "1-5":
                        labels = {
                            "1": question["label1"].strip(),
                            "2": question["label2"].strip(),
                            "3": question["label3"].strip(),
                            "4": question["label4"].strip(),
                            "5": question["label5"].strip(),
                        }
                    elif question["rating_type"] == "1-10":
                        labels = {
                            "1": question["label1"].strip(),
                            "2": question["label2"].strip(),
                            "3": question["label3"].strip(),
                            "4": question["label4"].strip(),
                            "5": question["label5"].strip(),
                            "6": question["label6"].strip(),
                            "7": question["label7"].strip(),
                            "8": question["label8"].strip(),
                            "9": question["label9"].strip(),
                            "10": question["label10"].strip(),
                        }

                    new_question, created = Question.objects.get_or_create(
                        type=question["type"].strip(),
                        reverse_question=(
                            True
                            if question["reverse_question"].strip() == "Yes"
                            else False
                        ),
                        behavior=behavior,
                        competency=competency,
                        self_question=question["self_question"].strip(),
                        observer_question=question["observer_question"].strip(),
                        rating_type=question["rating_type"].strip(),
                        label=labels,
                        correct_answer=question["correct_answer"],
                        response_type=question["response_type"].strip(),
                    )
                    new_question.save()

                return Response(
                    {
                        "message": "Questions created successfully.",
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to add questions."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def add_multiple_participants(participant, assessment_id, assessment, name_seperated):
    if assessment.participants_observers.filter(
        participant__email=participant["email"]
    ).exists():
        return Response(
            {
                "error": f"Participant with email {participant['email']} already exists in the assessment."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    name = None
    if name_seperated:
        name = (
            participant["first_name"].capitalize()
            + " "
            + participant.get("last_name", "").capitalize()
        )
    else:
        name = participant["name"]
    new_participant = create_learner(name, participant["email"])
    if participant["phone"]:
        new_participant.phone = participant["phone"]
    new_participant.save()
    mapping = ParticipantObserverMapping.objects.create(participant=new_participant)
    if participant["phone"]:
        add_contact_in_wati("learner", new_participant.name, new_participant.phone)
    unique_id = uuid.uuid4()  # Generate a UUID4
    # Creating a ParticipantUniqueId instance with a UUID as unique_id
    unique_id_instance = ParticipantUniqueId.objects.create(
        participant=new_participant,
        assessment=assessment,
        unique_id=unique_id,
    )
    mapping.save()
    assessment.participants_observers.add(mapping)
    assessment.save()
    particpant_data = [{"name": name, "email": participant["email"]}]
    # send_reset_password_link(particpant_data)
    if assessment.assessment_timing == "pre":
        post_assessment = Assessment.objects.filter(pre_assessment=assessment).first()
        mapping = ParticipantObserverMapping.objects.create(participant=new_participant)
        mapping.save()
        post_assessment.participants_observers.add(mapping)
        post_assessment.save()
        post_unique_id = uuid.uuid4()
        post_unique_id_instance = ParticipantUniqueId.objects.create(
            participant=new_participant,
            assessment=post_assessment,
            unique_id=post_unique_id,
        )
    elif assessment.assessment_timing == "post":
        pre_assessment = Assessment.objects.get(id=assessment.pre_assessment.id)
        mapping = ParticipantObserverMapping.objects.create(participant=new_participant)
        mapping.save()
        pre_assessment.participants_observers.add(mapping)
        pre_assessment.save()
        pre_unique_id = uuid.uuid4()
        pre_unique_id_instance = ParticipantUniqueId.objects.create(
            participant=new_participant,
            assessment=pre_assessment,
            unique_id=pre_unique_id,
        )
    serializer = AssessmentSerializerDepthFour(assessment)
    return serializer


class AddMultipleParticipants(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    @transaction.atomic
    def post(self, request):
        try:
            participants = request.data.get("participants")
            assessment_id = request.data.get("assessment_id")
            assessment = Assessment.objects.get(id=assessment_id)
            for participant in participants:
                serializer = add_multiple_participants(
                    participant, assessment_id, assessment, True
                )
            return Response(
                {
                    "message": "Participants added successfully.",
                    "assessment_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to add participants."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateObserverType(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

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
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

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
        return pdf

    except Exception as e:
        print(str(e))


def word_generate_report_for_participant(file_name, content):
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
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "learner")]

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
            competency_array = []
            assessment_rating_type = None
            for competency in assessment.questionnaire.questions.values(
                "competency"
            ).distinct():
                competency_id = competency["competency"]
                competency_questions = assessment.questionnaire.questions.filter(
                    competency__id=competency_id
                )
                competency_name_for_object = Competency.objects.get(
                    id=competency_id
                ).name
                competency_object = {
                    "competency_name": competency_name_for_object,
                    "questions": [],
                }
                if len(competency_array) < 14:
                    competency_array.append(competency_name_for_object)

                for question in competency_questions:
                    question_object = None

                    question_object = {
                        "question": question.self_question,
                        "participant_response": participant_response.participant_response.get(
                            str(question.id)
                        ),
                    }
                    assessment_rating_type = question.rating_type
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
                    "assessment_name": assessment.participant_view_name,
                    "organisation_name": assessment.organisation.name,
                    "assessment_type": assessment.assessment_type,
                    "organisation_id": assessment.organisation.id,
                    "data_for_score_analysis": data_for_score_analysis,
                    "data_for_assessment_overview_table": data_for_assessment_overview_table,
                    "frequency_analysis_data": frequency_analysis_data,
                    "image_base64_array": graph_images,
                    "competency_array": competency_array,
                    "assessment_rating_type": assessment_rating_type,
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
            assessment_rating_type = None
            competency_array = []
            for competency in assessment.questionnaire.questions.values(
                "competency"
            ).distinct():
                competency_id = competency["competency"]
                competency_questions = assessment.questionnaire.questions.filter(
                    competency__id=competency_id
                )
                competency_name_for_object = Competency.objects.get(
                    id=competency_id
                ).name
                competency_object = {
                    "competency_name": competency_name_for_object,
                    "questions": [],
                }

                if len(competency_array) < 14:
                    competency_array.append(competency_name_for_object)

                for question in competency_questions:
                    question_object = None

                    question_object = {
                        "question": question.self_question,
                        "participant_response": participant_response.participant_response.get(
                            str(question.id)
                        ),
                    }
                    assessment_rating_type = question.rating_type
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

            pdf = generate_report_for_participant(
                "assessment/report/assessment_report.html",
                {
                    "name": participant.name,
                    "assessment_name": assessment.participant_view_name,
                    "organisation_name": assessment.organisation.name,
                    "assessment_type": assessment.assessment_type,
                    "organisation_id": assessment.organisation.id,
                    "data_for_score_analysis": data_for_score_analysis,
                    "data_for_assessment_overview_table": data_for_assessment_overview_table,
                    "frequency_analysis_data": frequency_analysis_data,
                    "image_base64_array": graph_images,
                    "competency_array": competency_array,
                    "assessment_rating_type": assessment_rating_type,
                },
            )
            # pdf_path = "graphsAndReports/Report.pdf"

            # with open(pdf_path, "rb") as pdf_file:
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename={f"{participant.name} Report.pdf"}'
            )
            # Close the file after reading
            # pdf_file.close()

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to download report."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetAssessmentNotification(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        notifications = AssessmentNotification.objects.filter(
            user__id=user_id
        ).order_by("-created_at")

        serializer = AssessmentNotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class MarkAllNotificationAsRead(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        notifications = AssessmentNotification.objects.filter(
            read_status=False, user__id=request.data["user_id"]
        )
        notifications.update(read_status=True)
        return Response("Notifications marked as read.")


class MarkNotificationAsRead(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        count = AssessmentNotification.objects.filter(
            user__id=user_id, read_status=False
        ).count()
        return Response({"count": count})


class DownloadWordReport(APIView):
    permission_classes = [AllowAny]

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
            competency_array = []
            assessment_rating_type = None
            for competency in assessment.questionnaire.questions.values(
                "competency"
            ).distinct():
                competency_id = competency["competency"]
                competency_questions = assessment.questionnaire.questions.filter(
                    competency__id=competency_id
                )
                competency_name_for_object = Competency.objects.get(
                    id=competency_id
                ).name
                competency_object = {
                    "competency_name": competency_name_for_object,
                    "questions": [],
                }
                if len(competency_array) < 14:
                    competency_array.append(competency_name_for_object)

                for question in competency_questions:
                    question_object = None

                    question_object = {
                        "question": question.self_question,
                        "participant_response": participant_response.participant_response.get(
                            str(question.id)
                        ),
                    }
                    assessment_rating_type = question.rating_type
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

            word_generate_report_for_participant(
                "assessment/report/assessment_report.html",
                {
                    "name": participant.name,
                    "assessment_name": assessment.participant_view_name,
                    "organisation_name": assessment.organisation.name,
                    "assessment_type": assessment.assessment_type,
                    "organisation_id": assessment.organisation.id,
                    "data_for_score_analysis": data_for_score_analysis,
                    "data_for_assessment_overview_table": data_for_assessment_overview_table,
                    "frequency_analysis_data": frequency_analysis_data,
                    "image_base64_array": graph_images,
                    "competency_array": competency_array,
                    "assessment_rating_type": assessment_rating_type,
                },
            )
            pdf_path = "graphsAndReports/Report.pdf"

            PDFNet.Initialize(
                "demo:1702970002104:7c8f102f0300000000f9a19766ccfb8d39844f0d25c1beea57ea6833ba"
            )

            PDFNet.AddResourceSearchPath("Lib/Windows")

            if not StructuredOutputModule.IsModuleAvailable():
                print(
                    "Unable to run the sample: PDFTron SDK Structured Output module not available."
                )
                return Response(
                    {"error": "Failed to download report."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            Convert.ToWord(pdf_path, "graphsAndReports/WordReport.docx")

            with open("graphsAndReports/WordReport.docx", "rb") as word_file:
                output_stream = BytesIO(word_file.read())

            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{participant.name} Report.docx"'
            )

            response.write(output_stream.getvalue())

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to download report."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetLearnersUniqueId(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr", "facilitator")]

    def get(self, request, assessment_id):
        try:
            # Assuming assessment_id is a valid Assessment ID
            participants_unique_ids = ParticipantUniqueId.objects.filter(
                assessment_id=assessment_id
            ).select_related("participant")

            participants_data = []
            for entry in participants_unique_ids:
                participant_data = {
                    "participant_id": entry.participant.id,
                    "participant_name": entry.participant.name,
                    "participant_email": entry.participant.email,
                    "unique_id": entry.unique_id,
                }
                participants_data.append(participant_data)

            return Response(participants_data)

        except ParticipantUniqueId.DoesNotExist:
            return Response(
                {"error": "No participants found for this assessment ID"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StartAssessmentDataForParticipant(APIView):
    permission_classes = [AllowAny]

    def get(self, request, unique_id):
        try:
            participant_unique_id = ParticipantUniqueId.objects.get(unique_id=unique_id)

            serializer = AssessmentSerializerDepthFour(participant_unique_id.assessment)

            return Response(
                {
                    "assessment_data": serializer.data,
                    "participant_email": participant_unique_id.participant.email,
                    "participant_id": participant_unique_id.participant.id,
                },
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to retrieve Start Assessment Data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def swap_positions(length):
    numbers = list(range(1, length + 1))

    midpoint = length // 2

    for i in range(midpoint):
        numbers[i], numbers[-(i + 1)] = numbers[-(i + 1)], numbers[i]

    swapped_dict = {
        orig: swapped for orig, swapped in zip(range(1, length + 1), numbers)
    }
    return swapped_dict


def generate_graph_for_pre_assessment(competency_percentage, total_for_each_comp):
    comp_labels = list(competency_percentage.keys())
    percentage_values = list(competency_percentage.values())
    colors1 = ["#eb0081", "#d1cdcd"]
    colors2 = ["#b91689", "#d1cdcd"]
    colors3 = ["#7a3191", "#d1cdcd"]
    colors4 = ["#374e9c", "#d1cdcd"]

    fig = plt.figure(figsize=(15, len(comp_labels) * 0.6 + 3))
    ax = fig.add_subplot(111)

    bottom = np.zeros(len(comp_labels))
    bar_positions = np.arange(len(comp_labels))
    for i in range(len(comp_labels)):
        color_index = i % 4  # Use modulo to repeat colors after every four bars

        if color_index == 0:
            color = colors1
        elif color_index == 1:
            color = colors2
        elif color_index == 2:
            color = colors3
        else:
            color = colors4

        ax.barh(comp_labels[i], percentage_values[i], color=color, left=bottom[i])

    for index, value in enumerate(percentage_values):
        # new_value = value / 100 * total_for_each_comp[comp_labels[index]]
        ax.text(
            value,
            bar_positions[index],
            f"{value}%",
            ha="left",
            va="center",
            color="black",
        )
    ax.set_yticks(bar_positions)
    ax.set_yticklabels(
        [f"{comp}\n" if len(comp) > 15 else comp for comp in comp_labels],
        fontweight="bold",
        fontsize=14,
    )
    plt.title("Your Awareness Level", fontweight="bold", fontsize=14)
    plt.xlim(0, 100)
    plt.xlabel("Percentage")
    plt.tight_layout()

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="png")
    plt.close()

    encoded_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return encoded_image


def generate_spider_web_for_pre_assessment(competency_percentage, total_for_each_comp):
    comp_labels = list(competency_percentage.keys())
    percentage_values = list(competency_percentage.values())

    categories = comp_labels
    values = percentage_values

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Plot the background polygons
    ax.fill(angles, [100] * len(angles), color="lightgray", alpha=0.7)

    # Plot the data
    ax.plot(
        angles,
        values,
        linewidth=2,
        linestyle="solid",
        color="#eb0081",
        label="Your Competency",
    )

    # Add labels with padding
    ax.set_thetagrids(
        np.degrees(angles[:-1]),
        labels=comp_labels,
        fontweight="bold",
        fontsize=6,
        rotation=45,
        ha="right",
    )

    # Add percentage values with padding
    for angle, value, label in zip(angles, values[:-1], comp_labels):
        ax.text(
            np.degrees(angle),
            value + 3,
            f"{value}%",
            ha="center",
            va="center",
            fontsize=6,
        )

    # Add a title with adjusted position
    plt.title(
        "Your Competency Chart", size=10, color="#eb0081", y=1.1, fontweight="bold"
    )

    # Adjust layout for better visibility and centering
    plt.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.1)

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="png")
    plt.close()

    encoded_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return encoded_image


def generate_graph_for_pre_post_assessment(
    pre_competency_percentage, competency_percentage, total_for_each_comp
):
    comp_labels = list(competency_percentage.keys())
    pre_percentage_values = list(pre_competency_percentage.values())
    post_percentage_values = list(competency_percentage.values())

    fig = plt.figure(figsize=(15, len(comp_labels) * 0.6 + 5))
    ax = fig.add_subplot(111)

    width = 0.4  # Width of each bar
    bar_positions = np.arange(len(comp_labels))

    # Plot pre-assessment values
    pre_bars = ax.barh(
        bar_positions - width / 2,
        pre_percentage_values,
        height=width,
        label="Pre-Assessment",
        color="#eb0081",
    )

    # Plot post-assessment values
    post_bars = ax.barh(
        bar_positions + width / 2,
        post_percentage_values,
        height=width,
        label="Post-Assessment",
        color="#374e9c",
    )

    ax.set_yticks(bar_positions)
    ax.set_yticklabels(comp_labels)
    ax.legend()
    ax.set_yticklabels(
        [f"{comp}\n" if len(comp) > 15 else comp for comp in comp_labels],
        fontweight="bold",
    )
    plt.title("Your Awareness Level", fontweight="bold", fontsize=14)
    plt.xlabel("Percentage")
    plt.xlim(0, 100)
    plt.tight_layout()

    # Add numbers on top of the pre-assessment bars
    for index, value in enumerate(pre_percentage_values):
        # new_value = value / 100 * total_for_each_comp[comp_labels[index]]
        ax.text(
            value,
            bar_positions[index] - width / 2,
            f"{value}%",
            ha="left",
            va="center",
            color="black",
        )

    # Add numbers on top of the post-assessment bars
    for index, value in enumerate(post_percentage_values):
        # new_value = value / 100 * total_for_each_comp[comp_labels[index]]
        ax.text(
            value,
            bar_positions[index] + width / 2,
            f"{value}%",
            ha="left",
            va="center",
            color="black",
        )

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="png")
    plt.close()

    encoded_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return encoded_image


def generate_spider_web_for_pre_post_assessment(
    pre_competency_percentage, competency_percentage, total_for_each_comp
):
    comp_labels = list(competency_percentage.keys())
    pre_percentage_values = list(pre_competency_percentage.values())
    post_percentage_values = list(competency_percentage.values())

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Plot pre-assessment values
    angles = np.linspace(0, 2 * np.pi, len(comp_labels), endpoint=False).tolist()
    angles += angles[:1]
    pre_bars = ax.plot(
        angles,
        pre_percentage_values + pre_percentage_values[:1],
        label="Pre-Assessment",
        color="#eb0081",
        marker="o",
    )

    # Plot post-assessment values
    post_bars = ax.plot(
        angles,
        post_percentage_values + post_percentage_values[:1],
        label="Post-Assessment",
        color="#374e9c",
        marker="o",
    )

    ax.set_thetagrids(
        np.degrees(angles[:-1]),
        labels=comp_labels,
        fontweight="bold",
        fontsize=5.5,
        rotation=45,
        ha="right",
    )

    # Add percentage values on top of the lines
    for angle, pre_value, post_value in zip(
        angles, pre_percentage_values, post_percentage_values
    ):
        ax.text(
            np.degrees(angle),
            pre_value,
            f"{pre_value}%",
            ha="center",
            va="center",
            color="#eb0081",
            fontsize=8,
        )
        ax.text(
            np.degrees(angle),
            post_value,
            f"{post_value}%",
            ha="center",
            va="center",
            color="#374e9c",
            fontsize=8,
        )

    ax.legend(loc="upper right")

    plt.title("Your Awareness Level", fontweight="bold", fontsize=12)
    plt.tight_layout()

    # Adjust layout for better visibility and centering
    plt.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.2)

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="png")
    plt.close()

    encoded_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return encoded_image


def generate_graph_for_participant(
    participant, assessment_id, assessment, project_wise=False
):
    participant_response = ParticipantResponse.objects.filter(
        participant__id=participant.id, assessment__id=assessment_id
    ).first()

    if participant_response:
        total_for_each_comp = {}
        compentency_with_description = []

        for competency in assessment.questionnaire.questions.values(
            "competency"
        ).distinct():
            competency_id = competency["competency"]

            competency_name_for_object = Competency.objects.get(id=competency_id).name
            competency_description_for_object = Competency.objects.get(
                id=competency_id
            ).description
            competency_object = {
                "competency_name": competency_name_for_object,
                "competency_description": competency_description_for_object,
            }
            compentency_with_description.append(competency_object)

        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in total_for_each_comp:
                total_for_each_comp[question.competency.name] = 1
            else:
                total_for_each_comp[question.competency.name] += 1

        competency_object = {}
        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in competency_object:
                competency_object[question.competency.name] = 0

            participant_response_value = participant_response.participant_response.get(
                str(question.id)
            )

            if question.response_type == "correct_answer":
                correct_answer = (
                    assessment.questionnaire.questions.filter(id=question.id)
                    .first()
                    .correct_answer
                )

                if str(participant_response_value) in correct_answer:
                    competency_object[question.competency.name] = (
                        competency_object[question.competency.name] + 1
                    )

            elif question.response_type == "rating_type":
                if participant_response_value:
                    label_count = sum(
                        1 for key in question.label.keys() if question.label[key]
                    )
                    if not question.reverse_question:

                        swap_dict = swap_positions(label_count)

                        competency_object[question.competency.name] = competency_object[
                            question.competency.name
                        ] + (swap_dict[participant_response_value] / label_count)
                    else:

                        competency_object[question.competency.name] = competency_object[
                            question.competency.name
                        ] + (participant_response_value / label_count)

        competency_percentage = {}
        for comp in total_for_each_comp:
            competency_percentage[comp] = round(
                (competency_object[comp] / total_for_each_comp[comp]) * 100
            )

        if project_wise:
            return competency_percentage

        encoded_image = generate_graph_for_pre_assessment(
            competency_percentage, total_for_each_comp
        )

        return encoded_image, compentency_with_description

    if project_wise:
        return None

    return None, None


def generate_graph_for_participant_for_post_assessment(
    participant, assessment_id, assessment, project_wise=False
):
    participant_response = ParticipantResponse.objects.filter(
        participant__id=participant.id, assessment__id=assessment_id
    ).first()

    pre_assessment_participant_response = ParticipantResponse.objects.filter(
        participant__id=participant.id, assessment__id=assessment.pre_assessment.id
    ).first()

    if participant_response and pre_assessment_participant_response:
        total_for_each_comp = {}
        compentency_with_description = []

        for competency in assessment.questionnaire.questions.values(
            "competency"
        ).distinct():
            competency_id = competency["competency"]

            competency_name_for_object = Competency.objects.get(id=competency_id).name
            competency_description_for_object = Competency.objects.get(
                id=competency_id
            ).description
            competency_object = {
                "competency_name": competency_name_for_object,
                "competency_description": competency_description_for_object,
            }
            compentency_with_description.append(competency_object)

        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in total_for_each_comp:
                total_for_each_comp[question.competency.name] = 1
            else:
                total_for_each_comp[question.competency.name] += 1

        competency_object = {}
        pre_competency_object = {}
        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in competency_object:
                competency_object[question.competency.name] = 0
            if question.competency.name not in pre_competency_object:
                pre_competency_object[question.competency.name] = 0

            participant_response_value = participant_response.participant_response.get(
                str(question.id)
            )
            pre_assessment_participant_response_value = (
                pre_assessment_participant_response.participant_response.get(
                    str(question.id)
                )
            )

            if question.response_type == "correct_answer":

                correct_answer = (
                    assessment.questionnaire.questions.filter(id=question.id)
                    .first()
                    .correct_answer
                )

                if str(pre_assessment_participant_response_value) in correct_answer:

                    pre_competency_object[question.competency.name] = (
                        pre_competency_object[question.competency.name] + 1
                    )

                if str(participant_response_value) in correct_answer:
                    competency_object[question.competency.name] = (
                        competency_object[question.competency.name] + 1
                    )

            elif question.response_type == "rating_type":
                if participant_response_value:
                    label_count = sum(
                        1 for key in question.label.keys() if question.label[key]
                    )
                    swap_dict = swap_positions(label_count)
                    if pre_assessment_participant_response_value:
                        if not question.reverse_question:

                            pre_competency_object[
                                question.competency.name
                            ] = pre_competency_object[question.competency.name] + (
                                swap_dict[pre_assessment_participant_response_value]
                                / label_count
                            )
                        else:
                            pre_competency_object[
                                question.competency.name
                            ] = pre_competency_object[question.competency.name] + (
                                pre_assessment_participant_response_value / label_count
                            )

                    if participant_response_value:
                        if question.reverse_question:
                            competency_object[question.competency.name] = (
                                competency_object[question.competency.name]
                                + (swap_dict[participant_response_value] / label_count)
                            )
                        else:
                            competency_object[question.competency.name] = (
                                competency_object[question.competency.name]
                                + (participant_response_value / label_count)
                            )

        competency_percentage = {}
        pre_competency_percentage = {}
        for comp in total_for_each_comp:
            competency_percentage[comp] = round(
                (competency_object[comp] / total_for_each_comp[comp]) * 100
            )
            pre_competency_percentage[comp] = round(
                (pre_competency_object[comp] / total_for_each_comp[comp]) * 100
            )

        if project_wise:
            return pre_competency_percentage, competency_percentage
        encoded_image = generate_graph_for_pre_post_assessment(
            pre_competency_percentage, competency_percentage, total_for_each_comp
        )

        return encoded_image, compentency_with_description

    return None, None


class PrePostReportDownloadForParticipant(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assessment_id, participant_id):
        try:
            try:
                assessment = Assessment.objects.get(id=assessment_id)

            except Assessment.DoesNotExist as e:
                print(str(e))
                return Response(
                    {"error": "Assessment or participant not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            participant = Learner.objects.get(id=participant_id)
            encoded_image = None
            compentency_with_description = None

            if assessment.assessment_timing == "pre":
                (
                    encoded_image,
                    compentency_with_description,
                ) = generate_graph_for_participant(
                    participant, assessment_id, assessment
                )
            elif assessment.assessment_timing == "post":
                (
                    encoded_image,
                    compentency_with_description,
                ) = generate_graph_for_participant_for_post_assessment(
                    participant, assessment_id, assessment
                )

            email_message = render_to_string(
                "assessment/air_india_assessement_report.html",
                {
                    "name": participant.name.title(),
                    "image_base64": encoded_image,
                    "compentency_with_description": compentency_with_description,
                    "assessment_timing": assessment.assessment_timing,
                    "assessment_name": assessment.participant_view_name,
                },
            )

            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename={f"{participant.name} Report.pdf"}'
            )

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to downlaod."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PrePostReportDownloadForAllParticipant(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assessment_id):
        try:
            try:
                assessment = Assessment.objects.get(id=assessment_id)

            except Assessment.DoesNotExist as e:
                print(str(e))
                return Response(
                    {"error": "Assessment or participant not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            participant_context = []
            for participant_observer in assessment.participants_observers.all():
                participant = participant_observer.participant
                encoded_image = None
                compentency_with_description = None

                if assessment.assessment_timing == "pre":
                    (
                        encoded_image,
                        compentency_with_description,
                    ) = generate_graph_for_participant(
                        participant, assessment_id, assessment
                    )
                elif assessment.assessment_timing == "post":
                    (
                        encoded_image,
                        compentency_with_description,
                    ) = generate_graph_for_participant_for_post_assessment(
                        participant, assessment_id, assessment
                    )

                participant_context.append(
                    {
                        "name": participant.name.title(),
                        "image_base64": encoded_image,
                        "compentency_with_description": compentency_with_description,
                        "assessment_timing": assessment.assessment_timing,
                    }
                )

            email_message = render_to_string(
                "assessment/air_india_assessment_report_batch_wise.html",
                {
                    "participant_context": participant_context,
                    "assessment_name": assessment.participant_view_name,
                },
            )

            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename={f"{participant.name} Report.pdf"}'
            )

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to donwlaod report."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PostReportDownloadForParticipant(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assessment_id, participant_id):
        try:
            try:
                assessment = Assessment.objects.get(id=assessment_id)

            except Assessment.DoesNotExist as e:
                print(str(e))
                return Response(
                    {"error": "Assessment or participant not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            participant = Learner.objects.get(id=participant_id)
            encoded_image = None
            compentency_with_description = None

            (
                encoded_image,
                compentency_with_description,
            ) = generate_graph_for_participant(participant, assessment_id, assessment)

            email_message = render_to_string(
                "assessment/air_india_assessement_report.html",
                {
                    "name": participant.name.title(),
                    "image_base64": encoded_image,
                    "compentency_with_description": compentency_with_description,
                    "assessment_timing": assessment.assessment_timing,
                    "assessment_name": assessment.participant_view_name,
                },
            )

            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename={f"{participant.name} Report.pdf"}'
            )

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to downlaod."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PostReportDownloadForAllParticipant(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assessment_id):
        try:
            try:
                assessment = Assessment.objects.get(id=assessment_id)

            except Assessment.DoesNotExist as e:
                print(str(e))
                return Response(
                    {"error": "Assessment or participant not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            participant_context = []
            for participant_observer in assessment.participants_observers.all():
                participant = participant_observer.participant
                encoded_image = None
                compentency_with_description = None

                (
                    encoded_image,
                    compentency_with_description,
                ) = generate_graph_for_participant(
                    participant, assessment_id, assessment
                )

                participant_context.append(
                    {
                        "name": participant.name.title(),
                        "image_base64": encoded_image,
                        "compentency_with_description": compentency_with_description,
                        "assessment_timing": assessment.assessment_timing,
                    }
                )

            email_message = render_to_string(
                "assessment/air_india_assessment_report_batch_wise.html",
                {
                    "participant_context": participant_context,
                    "assessment_name": assessment.participant_view_name,
                },
            )

            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename={f"{participant.name} Report.pdf"}'
            )

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to donwlaod report."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReleaseResults(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def put(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
            if (
                assessment.assessment_timing == "pre"
                or assessment.assessment_timing == "post"
            ):
                (
                    participant_released_results,
                    created,
                ) = ParticipantReleasedResults.objects.get_or_create(
                    assessment=assessment
                )
                participant_with_released_results = []
                if not created:
                    participant_with_released_results = (
                        participant_released_results.participants.all()
                    )

                participant_with_not_released_results = []
                for participant_observer in assessment.participants_observers.all():
                    participant_response_present = ParticipantResponse.objects.filter(
                        assessment=assessment,
                        participant=participant_observer.participant,
                    ).exists()
                    if participant_response_present:
                        if (
                            participant_observer.participant
                            not in participant_with_released_results
                        ):
                            participant_with_not_released_results.append(
                                participant_observer.participant
                            )
                            participant_released_results.participants.add(
                                participant_observer.participant
                            )

                participant_released_results.save()

                if len(assessment.participants_observers.all()) == (
                    len(participant_with_released_results)
                    + len(participant_with_not_released_results)
                ):
                    assessment.result_released = True
                    assessment.save()

                if assessment.assessment_timing != "none":
                    for participant in participant_with_not_released_results:
                        encoded_image = None
                        compentency_with_description = None
                        if assessment.assessment_timing == "pre":
                            (
                                encoded_image,
                                compentency_with_description,
                            ) = generate_graph_for_participant(
                                participant, assessment_id, assessment
                            )
                        elif assessment.assessment_timing == "post":
                            (
                                encoded_image,
                                compentency_with_description,
                            ) = generate_graph_for_participant_for_post_assessment(
                                participant, assessment_id, assessment
                            )
                        send_mail_templates(
                            "assessment/air_india_report_mail.html",
                            [participant.email],
                            "Meeraq Assessment Report",
                            {
                                "name": participant.name.title(),
                                "image_base64": encoded_image,
                                "compentency_with_description": compentency_with_description,
                                "assessment_timing": assessment.assessment_timing,
                                "assessment_name": assessment.participant_view_name,
                            },
                            [],
                        )
            else:
                assessment.result_released = True
                assessment.save()
            serializer = AssessmentSerializerDepthFour(assessment)
            return Response(
                {
                    "success": "Successfully Released Results",
                    "assessment_data": serializer.data,
                }
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to Release Results"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MoveParticipant(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def post(self, request):
        try:
            from_assessment = Assessment.objects.get(
                id=request.data.get("from_assessment_id")
            )
            participant = Learner.objects.get(id=request.data.get("participant_id"))
            to_assessment = Assessment.objects.get(
                id=request.data.get("to_assessment_id")
            )

            if to_assessment.questionnaire.id != from_assessment.questionnaire.id:
                return Response(
                    {
                        "error": "Both assessments must have the same questionnaire to move participant."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if to_assessment.participants_observers.filter(
                participant__email=participant.email
            ).exists():
                return Response(
                    {"error": "Participant already exists in the assessment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            unique_id = uuid.uuid4()  # Generate a UUID4

            # Creating a ParticipantUniqueId instance with a UUID as unique_id
            unique_id_instance = ParticipantUniqueId.objects.create(
                participant=participant,
                assessment=to_assessment,
                unique_id=unique_id,
            )

            mapping = ParticipantObserverMapping.objects.create(participant=participant)

            mapping.save()
            to_assessment.participants_observers.add(mapping)
            to_assessment.save()

            particpant_data = [{"name": participant.name, "email": participant.email}]
            # send_reset_password_link(particpant_data)

            if from_assessment.assessment_timing == "pre":
                post_assessment = Assessment.objects.filter(
                    pre_assessment=to_assessment
                ).first()

                if not post_assessment.participants_observers.filter(
                    participant__email=participant.email
                ).exists():
                    mapping = ParticipantObserverMapping.objects.create(
                        participant=participant
                    )
                    mapping.save()
                    post_assessment.participants_observers.add(mapping)
                    post_assessment.save()
                    post_unique_id = uuid.uuid4()
                    post_unique_id_instance = ParticipantUniqueId.objects.create(
                        participant=participant,
                        assessment=post_assessment,
                        unique_id=post_unique_id,
                    )
                    from_post_assessment = Assessment.objects.filter(
                        pre_assessment=from_assessment
                    ).first()
                    participant_resposne = ParticipantResponse.objects.filter(
                        participant=participant, assessment=from_post_assessment
                    ).first()

                    if participant_resposne:
                        participant_resposne.assessment = post_assessment
                        participant_resposne.save()

                    from_post_assessment.participants_observers.filter(
                        participant__id=participant.id
                    ).delete()

                    participant_unique_id_instance = ParticipantUniqueId.objects.filter(
                        participant=participant,
                        assessment=from_post_assessment,
                    ).first()
                    if participant_unique_id_instance:
                        participant_unique_id_instance.delete()
            elif from_assessment.assessment_timing == "post":
                pre_assessment = Assessment.objects.get(
                    id=to_assessment.pre_assessment.id
                )

                if not pre_assessment.participants_observers.filter(
                    participant=participant
                ).exists():
                    mapping = ParticipantObserverMapping.objects.create(
                        participant=participant
                    )
                    mapping.save()
                    pre_assessment.participants_observers.add(mapping)
                    pre_assessment.save()
                    pre_unique_id = uuid.uuid4()
                    pre_unique_id_instance = ParticipantUniqueId.objects.create(
                        participant=participant,
                        assessment=pre_assessment,
                        unique_id=pre_unique_id,
                    )

                    to_pre_assessment = Assessment.objects.filter(
                        id=from_assessment.pre_assessment.id
                    ).first()

                    participant_resposne = ParticipantResponse.objects.filter(
                        participant=participant, assessment=to_pre_assessment
                    ).first()

                    if participant_resposne:
                        participant_resposne.assessment = pre_assessment
                        participant_resposne.save()

                    to_pre_assessment.participants_observers.filter(
                        participant__id=participant.id
                    ).delete()

                    participant_unique_id_instance = ParticipantUniqueId.objects.filter(
                        participant=participant,
                        assessment=to_pre_assessment,
                    ).first()
                    if participant_unique_id_instance:
                        participant_unique_id_instance.delete()

            participant_resposne = ParticipantResponse.objects.filter(
                participant=participant, assessment=from_assessment
            ).first()

            if participant_resposne:
                participant_resposne.assessment = to_assessment
                participant_resposne.save()

            from_assessment.participants_observers.filter(
                participant__id=participant.id
            ).delete()

            participant_unique_id_instance = ParticipantUniqueId.objects.filter(
                participant=participant,
                assessment=from_assessment,
            ).first()
            if participant_unique_id_instance:
                participant_unique_id_instance.delete()

            serializer = AssessmentSerializerDepthFour(to_assessment)
            return Response(
                {
                    "message": f"Moved {participant.name} participant to {to_assessment.name} assessment.",
                    "assessment_data": serializer.data,
                }
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to move participant"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetAllLearnersUniqueId(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("learner")]

    def get(self, request):
        try:
            # Assuming assessment_id is a valid Assessment ID
            participants_unique_ids = ParticipantUniqueId.objects.all().select_related(
                "participant"
            )

            participants_data = []
            for entry in participants_unique_ids:
                participant_data = {
                    "participant_id": entry.participant.id,
                    "assessment_id": entry.assessment.id,
                    "participant_name": entry.participant.name,
                    "participant_email": entry.participant.email,
                    "unique_id": entry.unique_id,
                }
                participants_data.append(participant_data)

            return Response(participants_data)

        except ParticipantUniqueId.DoesNotExist:
            return Response(
                {"error": "No Unique id found."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def getParticipantsResponseStatusForAssessment(assessment):
    try:
        response_data = []

        if (
            assessment.assessment_timing == "pre"
            or assessment.assessment_type == "self"
        ):
            for participant_observers in assessment.participants_observers.all():
                participant_responses = ParticipantResponse.objects.filter(
                    assessment=assessment,
                    participant__id=participant_observers.participant.id,
                ).first()

                data = {
                    "Participant Name": participant_observers.participant.name.title(),
                    "Participant Email": participant_observers.participant.email,
                    "Participant Response Status": (
                        "Responded" if participant_responses else "Not Responded"
                    ),
                }

                response_data.append(data)
            return response_data
        elif assessment.assessment_timing == "post":
            for participant_observers in assessment.participants_observers.all():
                post_participant_responses = ParticipantResponse.objects.filter(
                    assessment=assessment,
                    participant__id=participant_observers.participant.id,
                ).first()

                pre_assessment = assessment.pre_assessment

                pre_participant_responses = ParticipantResponse.objects.filter(
                    assessment=pre_assessment,
                    participant__id=participant_observers.participant.id,
                ).first()

                data = {
                    "Participant Name": participant_observers.participant.name.title(),
                    "Participant Email": participant_observers.participant.email,
                    "Participant pre_response_status": (
                        "Responded" if pre_participant_responses else "Not Responded"
                    ),
                    "Participant post_response_status": (
                        "Responded" if post_participant_responses else "Not Responded"
                    ),
                }
                response_data.append(data)
            return response_data
        elif assessment.assessment_type == "360":
            response_data = {"Participants": [], "Observers": []}
            for participant_observers in assessment.participants_observers.all():
                participant_responses = ParticipantResponse.objects.filter(
                    assessment=assessment,
                    participant__id=participant_observers.participant.id,
                ).first()
                participant_name = participant_observers.participant.name.title()
                participant_email = participant_observers.participant.email
                temp = {
                    "Participant name": participant_name,
                    "Participant email": participant_email,
                    "Participant response_status": (
                        "Responded" if participant_responses else "Not Responded"
                    ),
                }
                response_data["Participants"].append(temp)

                # Initialize an empty list to store observer data for each participant
                observers_data = []

                for observer in participant_observers.observers.all():
                    observer_response = ObserverResponse.objects.filter(
                        assessment=assessment,
                        participant__id=participant_observers.participant.id,
                        observer=observer,
                    ).first()
                    observer_data = {
                        "Participant name": participant_name,
                        "Participant email": participant_email,
                        "Observer Name": observer.name,
                        "Observer Email": observer.email,
                        "Observer Response": (
                            "Responded" if observer_response else "Not Responded"
                        ),
                    }
                    observers_data.append(observer_data)

                # Append observer data for this participant to the response_data
                response_data["Observers"].extend(observers_data)
            return response_data
    except Exception as e:
        print(str(e))


def getAllParticipantResponsesForAssessment(assessment):
    try:
        response_data = {}
        questionnaire = assessment.questionnaire
        questions = questionnaire.questions.all()

        # Fetch all participant responses at once to reduce DB hits
        participant_responses = ParticipantResponse.objects.filter(
            participant__in=assessment.participants_observers.values_list(
                "participant", flat=True
            ),
            assessment=assessment,
        ).select_related("participant")

        for participant_response in participant_responses:
            participant_name = participant_response.participant.name
            if participant_name not in response_data:
                response_data[participant_name] = []

            for question in questions:
                correct_answer_label = (
                    ", ".join(question.correct_answer)
                    if question.correct_answer
                    else "N/A"
                )
                participant_response_value = (
                    participant_response.participant_response.get(
                        str(question.id), "N/A"
                    )
                )

                response_data[participant_name].append(
                    {
                        "Question": question.self_question,
                        "Response": participant_response_value,
                        "Answer": correct_answer_label,
                    }
                )

        return response_data
    except Exception as e:
        print(str(e))
        return {}


class ResponseDownloadForAllParticipants(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
            response_data = getAllParticipantResponsesForAssessment(assessment)
            if (
                assessment.assessment_timing in ["pre", "post"]
                or assessment.assessment_type == "self"
            ):
                excel_writer = BytesIO()
                with pd.ExcelWriter(excel_writer) as writer:
                    for (
                        participant_name,
                        participant_responses,
                    ) in response_data.items():
                        df = pd.DataFrame(participant_responses)
                        df.to_excel(writer, sheet_name=participant_name, index=False)
                excel_writer.seek(0)
                response = HttpResponse(
                    excel_writer.getvalue(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{assessment.name}_all_participant_response_status.xlsx"'
                )

                return response
        except Exception as e:
            print(str(e))
            return HttpResponse(status=500)


class DownloadParticipantResponseStatusData(APIView):
    permission_classes = [AllowAny]

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
            response_data = getParticipantsResponseStatusForAssessment(assessment)
            if (
                assessment.assessment_timing in ["pre", "post"]
                or assessment.assessment_type == "self"
            ):
                df = pd.DataFrame(response_data)
                excel_writer = BytesIO()
                df.to_excel(excel_writer, index=False)
                excel_writer.seek(0)
                response = HttpResponse(
                    excel_writer.getvalue(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{assessment.name}_response_status.xlsx"'
                )

                return response
            elif assessment.assessment_type == "360":
                participants_df = pd.DataFrame(response_data["Participants"])
                observers_df = pd.DataFrame(response_data["Observers"])
                excel_writer = BytesIO()
                with pd.ExcelWriter(excel_writer, engine="openpyxl") as writer:
                    participants_df.to_excel(
                        writer, sheet_name="Participants", index=False
                    )
                    observers_df.to_excel(writer, sheet_name="Observers", index=False)
                excel_writer.seek(0)
                response = HttpResponse(
                    excel_writer.getvalue(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{assessment.name}_response_status.xlsx"'
                )
                return response

        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get download response data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetParticipantReleasedResults(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr")]

    def get(self, request, assessment_id):
        try:
            participant_released_results = ParticipantReleasedResults.objects.filter(
                assessment__id=assessment_id
            ).first()

            serializer = ParticipantReleasedResultsSerializerDepthOne(
                participant_released_results
            )

            return Response(serializer.data)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get download response data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetAllAssessments(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr")]

    def get(self, request):
        pmo = Pmo.objects.filter(email=request.user.username).first()
        hr_id = request.query_params.get("hr")
        assessments = []
        if hr_id:
            assessments = Assessment.objects.filter(
                Q(hr__id=int(hr_id)), Q(status="ongoing") | Q(status="completed")
            )
        elif pmo and pmo.sub_role == "junior_pmo":
            assessments = Assessment.objects.filter(
                assessment_modal__lesson__course__batch__project__junior_pmo=pmo
            )
        else:
            assessments = Assessment.objects.all()
        assessment_list = []
        for assessment in assessments:
            total_responses_count = ParticipantResponse.objects.filter(
                assessment=assessment
            ).count()
            assessment_lesson = AssessmentLesson.objects.filter(
                assessment_modal=assessment
            ).first()

            assessment_data = {
                "id": assessment.id,
                "name": assessment.name,
                "organisation": (
                    assessment.organisation.name if assessment.organisation else ""
                ),
                "assessment_type": assessment.assessment_type,
                "assessment_timing": assessment.assessment_timing,
                "assessment_start_date": assessment.assessment_start_date,
                "assessment_end_date": assessment.assessment_end_date,
                "status": assessment.status,
                "total_learners_count": assessment.participants_observers.count(),
                "total_responses_count": total_responses_count,
                "batch_name": (
                    assessment_lesson.lesson.course.batch.name
                    if assessment_lesson
                    else None
                ),
                "project_name": (
                    assessment_lesson.lesson.course.batch.project.name
                    if assessment_lesson
                    else None
                ),
                "project_id": (
                    assessment_lesson.lesson.course.batch.project.id
                    if assessment_lesson
                    else None
                ),
                "created_at": assessment.created_at,
            }

            assessment_list.append(assessment_data)

        return Response(assessment_list)


class GetOneAssessment(APIView):
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "hr", "learner", "facilitator"),
    ]

    def get(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, id=assessment_id)
        try:
            serializer = AssessmentSerializerDepthFour(assessment)
            return Response(serializer.data)
        except Exception as e:
            # Handle specific exceptions if needed
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetAssessmentsOfHr(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr")]

    def get(self, request, hr_id):
        assessments = Assessment.objects.filter(
            Q(hr__id=hr_id), Q(status="ongoing") | Q(status="completed")
        )
        assessment_list = []
        for assessment in assessments:
            total_responses_count = ParticipantResponse.objects.filter(
                assessment=assessment
            ).count()
            assessment_data = {
                "id": assessment.id,
                "name": assessment.name,
                "participant_view_name": assessment.participant_view_name,
                "assessment_type": assessment.assessment_type,
                "assessment_timing": assessment.assessment_timing,
                "assessment_start_date": assessment.assessment_start_date,
                "assessment_end_date": assessment.assessment_end_date,
                "status": assessment.status,
                "total_learners_count": assessment.participants_observers.count(),
                "total_responses_count": total_responses_count,
                "created_at": assessment.created_at,
            }

            assessment_list.append(assessment_data)

        return Response(assessment_list)


class GetAssessmentsDataForMoveParticipant(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        assessments = Assessment.objects.all()
        assessment_data = []
        for assessment in assessments:
            temp_assessmeent = {
                "id": assessment.id,
                "name": assessment.name,
                "assessment_timing": assessment.assessment_timing,
                "participants_observers": ParticipantObserverMappingSerializerDepthOne(
                    assessment.participants_observers, many=True
                ).data,
            }
            assessment_data.append(temp_assessmeent)
        return Response(assessment_data)


class CreateAssessmentAndAddMultipleParticipantsFromBatch(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def post(self, request):
        try:
            with transaction.atomic():
                (
                    created,
                    pre_assessment_id,
                    post_assessment_id,
                ) = create_pre_post_assessments(request)

                pre_assessment = Assessment.objects.get(id=pre_assessment_id)

                if created:
                    batch = SchedularBatch.objects.get(id=request.data.get("batch_id"))

                    for participant in batch.learners.all():
                        participant_object = {
                            "name": participant.name,
                            "email": participant.email,
                            "phone": participant.phone,
                        }
                        serializer = add_multiple_participants(
                            participant_object, pre_assessment_id, pre_assessment, False
                        )

                        course = Course.objects.get(id=request.data.get("course_id"))

                        pre_assessment_lesson = None
                        post_assessment_lesson = None

                        lessons = Lesson.objects.filter(
                            course=course, lesson_type="assessment"
                        )

                        for lesson in lessons:

                            assessment_lesson = AssessmentLesson.objects.filter(
                                lesson=lesson
                            ).first()

                            if assessment_lesson.type == "pre":
                                lesson.drip_date = pre_assessment.assessment_start_date
                                lesson.save()
                                assessment_lesson.assessment_modal = pre_assessment

                                assessment_lesson.save()

                                if lesson.status == "draft":
                                    pre_assessment.status = "draft"

                                if lesson.status == "public":
                                    pre_assessment.status = "ongoing"
                                pre_assessment.save()

                            elif assessment_lesson.type == "post":

                                post_assessment = Assessment.objects.get(
                                    id=post_assessment_id
                                )
                                lesson.drip_date = post_assessment.assessment_start_date
                                lesson.save()
                                assessment_lesson.assessment_modal = post_assessment
                                assessment_lesson.save()

                                if lesson.status == "draft":
                                    post_assessment.status = "draft"

                                if lesson.status == "public":
                                    post_assessment.status = "ongoing"
                                post_assessment.save()

                    return Response(
                        {
                            "message": "Pre and Post assessment created and batch added successfully.",
                            "assessment_data": serializer.data,
                        },
                        status=status.HTTP_200_OK,
                    )
        except Exception as e:
            print(str(e))
            # Handle specific exceptions if needed
            return Response(
                {"error": "Faliled to create assessments"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AssessmentInAssessmentLesson(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)

            assessment_lesson = AssessmentLesson.objects.filter(
                assessment_modal=assessment
            ).first()

            return Response(
                {
                    "assessment_lesson_added": True if assessment_lesson else False,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Faliled to get data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AllAssessmentInAssessmentLesson(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo")]

    def get(self, request):
        try:
            assessments = Assessment.objects.all()

            assessment_present_in_assessment_lesson_ids = []
            for assessment in assessments:
                assessment_lesson = AssessmentLesson.objects.filter(
                    assessment_modal=assessment
                ).first()

                if assessment_lesson:
                    assessment_present_in_assessment_lesson_ids.append(assessment.id)

            return Response(
                {
                    "assessment_present_in_assessment_lesson_ids": assessment_present_in_assessment_lesson_ids,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Faliled to get data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def send_mail_to_not_responded_participant(request, assessment_id):
    try:
        data = {"req": request.data, "assessment_id": assessment_id}
        send_assessment_invitation_mail_on_click.delay(data)
        return Response({"message": "Email Sent Sucessfully"}, status=200)
    except Exception as e:
        print(str(e))
        return Response({"error": "Faild to send emails"}, status=400)


def get_average_for_all_compentency(compentency_precentages):
    average_percentage = {}
    count_occurrences = {}
    for compentency_precentage in compentency_precentages:
        for competency_name, percentage in compentency_precentage.items():
            average_percentage[competency_name] = (
                average_percentage.get(competency_name, 0) + percentage
            )

            count_occurrences[competency_name] = (
                count_occurrences.get(competency_name, 0) + 1
            )

    for competency_name, total_percentage in average_percentage.items():
        average_percentage[competency_name] = (
            round(total_percentage / count_occurrences[competency_name])
            if count_occurrences[competency_name] != 0
            else 0
        )

    return average_percentage


def get_competency_with_description(average_percentage):
    competency_with_description = []
    for key, value in average_percentage.items():
        competency = Competency.objects.filter(name=key).first()
        competency_with_description.append(
            {
                "competency_name": competency.name,
                "competency_description": competency.description,
            }
        )
    return competency_with_description


class GetProjectWiseReport(APIView):
    permission_classes = [AllowAny]

    def get(self, request, project_id, report_to_download):
        try:
            spider = self.request.query_params.get("spider", None)

            project = SchedularProject.objects.get(id=project_id)
            batch_id = request.query_params.get("batch_id", None)

            if batch_id:
                batches = SchedularBatch.objects.filter(id=int(batch_id))
                batch_name = None
            else:

                batches = SchedularBatch.objects.filter(project__id=project.id)

            pre_compentency_percentages = []
            post_compentency_percentages = []

            total_participant = 0
            total_attended_both_assessments = 0
            for batch in batches:
                if batch_id:
                    batch_name = batch.name
                total_participant = total_participant + len(batch.learners.all())
                assessments = Assessment.objects.filter(
                    assessment_modal__lesson__course__batch=batch
                )
                attended_both_assessments = {}

                for assessment in assessments:
                    assessment_id = assessment.id
                    for (
                        participants_observer
                    ) in assessment.participants_observers.all():
                        participant = participants_observer.participant

                        if assessment.assessment_timing == "pre":
                            compentency_precentage = generate_graph_for_participant(
                                participant, assessment_id, assessment, True
                            )

                            if compentency_precentage:
                                if participant.id not in attended_both_assessments:
                                    attended_both_assessments[participant.id] = 1
                                else:
                                    attended_both_assessments[participant.id] = (
                                        attended_both_assessments[participant.id] + 1
                                    )
                                pre_compentency_percentages.append(
                                    compentency_precentage
                                )
                        elif assessment.assessment_timing == "post":
                            (
                                pre_compentency_precentage,
                                post_compentency_precentage,
                            ) = generate_graph_for_participant_for_post_assessment(
                                participant, assessment_id, assessment, True
                            )

                            if post_compentency_precentage:
                                if participant.id not in attended_both_assessments:
                                    attended_both_assessments[participant.id] = 1
                                else:
                                    attended_both_assessments[participant.id] = (
                                        attended_both_assessments[participant.id] + 1
                                    )
                                post_compentency_percentages.append(
                                    post_compentency_precentage
                                )

                participant_ids_with_value_two = [
                    key for key, value in attended_both_assessments.items() if value > 1
                ]
                total_attended_both_assessments = total_attended_both_assessments + len(
                    participant_ids_with_value_two
                )

            content = {
                "org_name": project.organisation.name,
                "project_name": project.name,
                "total_participant": total_participant,
                "attended_pre_participant": len(pre_compentency_percentages),
                "attended_post_participant": len(post_compentency_percentages),
                "attended_both_assessments": total_attended_both_assessments,
                "batch_name": batch_name if batch_id else None,
            }

            if report_to_download == "pre":

                pre_average_percentage = get_average_for_all_compentency(
                    pre_compentency_percentages
                )
                pre_encoded_image = None
                if spider:
                    pre_encoded_image = generate_spider_web_for_pre_assessment(
                        pre_average_percentage, None
                    )
                else:
                    pre_encoded_image = generate_graph_for_pre_assessment(
                        pre_average_percentage, None
                    )
                content["image_base64"] = pre_encoded_image
                content["competency_with_description"] = (
                    get_competency_with_description(pre_average_percentage)
                )

            elif report_to_download == "post":

                post_average_percentage = get_average_for_all_compentency(
                    post_compentency_percentages
                )
                post_encoded_image = None
                if spider:
                    post_encoded_image = generate_spider_web_for_pre_assessment(
                        post_average_percentage, None
                    )
                else:
                    post_encoded_image = generate_graph_for_pre_assessment(
                        post_average_percentage, None
                    )

                content["image_base64"] = post_encoded_image
                content["competency_with_description"] = (
                    get_competency_with_description(post_average_percentage)
                )
            elif report_to_download == "both":

                pre_average_percentage = get_average_for_all_compentency(
                    pre_compentency_percentages
                )

                post_average_percentage = get_average_for_all_compentency(
                    post_compentency_percentages
                )
                post_encoded_image = None
                if spider:
                    post_encoded_image = generate_spider_web_for_pre_post_assessment(
                        pre_average_percentage, post_average_percentage, None
                    )
                else:
                    post_encoded_image = generate_graph_for_pre_post_assessment(
                        pre_average_percentage, post_average_percentage, None
                    )

                content["image_base64"] = post_encoded_image
                content["competency_with_description"] = (
                    get_competency_with_description(post_average_percentage)
                )

            email_message = render_to_string(
                "assessment/project_wise_report.html",
                content,
            )

            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename={f"{participant.name} Report.pdf"}'
            )

            return response

        except Exception as e:
            print(str(e))
            return Response({"error": "Failed to download report"}, status=500)


class AssessmentsResponseStatusDownload(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("hr", "pmo")]

    def post(self, request):
        try:
            assessment_ids = request.data.get("assessment_ids")

            response_data_for_assessments = {}
            for assessment_id in assessment_ids:
                assessment = Assessment.objects.get(id=assessment_id)
                response_data = getParticipantsResponseStatusForAssessment(assessment)
                response_data_for_assessments[assessment.name] = response_data
            return Response(response_data_for_assessments)
        except Exception as e:
            print(str(e))


class GetAllAssessmentsOfSchedularProjects(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("hr", "pmo")]

    def get(self, request, project_id):
        try:
            hr_id = request.query_params.get("hr", None)
            schedular_projects = []
            assessment_list = []
            if project_id == "all":
                schedular_projects = SchedularProject.objects.all()
            else:
                schedular_projects = SchedularProject.objects.filter(id=int(project_id))
            if hr_id:
                schedular_projects = schedular_projects.filter(hr__id=hr_id)
            for schedular_project in schedular_projects:
                batches = SchedularBatch.objects.filter(project=schedular_project)

                for batch in batches:
                    assessments = Assessment.objects.filter(
                        assessment_modal__lesson__course__batch=batch
                    )

                    for assessment in assessments:

                        total_responses_count = ParticipantResponse.objects.filter(
                            assessment=assessment
                        ).count()
                        assessment_data = {
                            "id": assessment.id,
                            "name": assessment.name,
                            "organisation": (
                                assessment.organisation.name
                                if assessment.organisation
                                else ""
                            ),
                            "assessment_type": assessment.assessment_type,
                            "assessment_timing": assessment.assessment_timing,
                            "assessment_start_date": assessment.assessment_start_date,
                            "assessment_end_date": assessment.assessment_end_date,
                            "status": assessment.status,
                            "total_learners_count": assessment.participants_observers.count(),
                            "total_responses_count": total_responses_count,
                            "created_at": assessment.created_at,
                        }
                        assessment_list.append(assessment_data)

            return Response(assessment_list)
        except Exception as e:
            print(str(e))
            return Response({"error": "Failed to get data"}, status=500)


class GetAssessmentBatchAndProject(APIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "hr")]

    def get(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, id=assessment_id)
        try:
            # get batch and project of assessment
            assessment_lessons = AssessmentLesson.objects.filter(
                assessment_modal__id=assessment_id
            )
            if assessment_lessons.exists():
                assessment_lesson = assessment_lessons.first()
                batch = assessment_lesson.lesson.course.batch
                project = batch.project
                return Response(
                    {"batch": {"id": batch.id}, "project": {"id": project.id}}
                )
            else:
                return Response(
                    {"error": "Batch and project not found for the assessment"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            # Handle specific exceptions if needed
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DownloadQuestionWiseExcelForProject(APIView):
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        try:
            batches = SchedularBatch.objects.filter(project__id=project_id)
            pre_assessments_data = []
            post_assessments_data = []
            for batch in batches:
                assessments = Assessment.objects.filter(
                    assessment_modal__lesson__course__batch=batch
                )
                for assessment in assessments:
                    assessment_id = assessment.id
                    for (
                        participant_observers
                    ) in assessment.participants_observers.all():
                        participant = participant_observers.participant
                        participant_response = ParticipantResponse.objects.filter(
                            participant__id=participant.id, assessment__id=assessment_id
                        ).first()

                        if participant_response:
                            questions_object = {"Participant Name": participant.name}
                            for question in assessment.questionnaire.questions.all():
                                if question.response_type == "descriptive":
                                    continue
                                participant_response_value = (
                                    participant_response.participant_response.get(
                                        str(question.id)
                                    )
                                )

                                if question.response_type == "correct_answer":
                                    correct_answer = (
                                        assessment.questionnaire.questions.filter(
                                            id=question.id
                                        )
                                        .first()
                                        .correct_answer
                                    )

                                    if (
                                        str(participant_response_value)
                                        in correct_answer
                                    ):
                                        questions_object[question.self_question] = (
                                            "100%"
                                        )
                                    else:
                                        questions_object[question.self_question] = "0%"
                                elif question.response_type == "rating_type":
                                    if participant_response_value:
                                        label_count = sum(
                                            1
                                            for key in question.label.keys()
                                            if question.label[key]
                                        )
                                        if not question.reverse_question:
                                            swap_dict = swap_positions(label_count)
                                            questions_object[question.self_question] = (
                                                str(
                                                    round(
                                                        (
                                                            swap_dict[
                                                                participant_response_value
                                                            ]
                                                            / label_count
                                                        )
                                                        * 100
                                                    )
                                                )
                                                + "%"
                                            )
                                        else:
                                            questions_object[question.self_question] = (
                                                str(
                                                    round(
                                                        (
                                                            participant_response_value
                                                            / label_count
                                                        )
                                                        * 100
                                                    )
                                                )
                                                + "%"
                                            )

                            # print(questions_object)
                            if assessment.assessment_timing == "pre":

                                pre_assessments_data.append(questions_object)
                            elif assessment.assessment_timing == "post":
                                post_assessments_data.append(questions_object)

            # Create workbook
            wb = Workbook()
            pre_sheet = wb.active
            pre_sheet.title = "Pre Assessment"
            post_sheet = wb.create_sheet(title="Post Assessment")

            # Write headers if data exists
            if pre_assessments_data:
                pre_sheet.append(list(pre_assessments_data[0].keys()))
            if post_assessments_data:
                post_sheet.append(list(post_assessments_data[0].keys()))

            # Write data
            for data in pre_assessments_data:
                pre_sheet.append(list(data.values()))
            for data in post_assessments_data:
                post_sheet.append(list(data.values()))

            # Create HTTP response with Excel file
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="response.xlsx"'

            # Save workbook to response
            wb.save(response)

            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_learner_assessment_result_image(request, learner_id):
    participant = Learner.objects.get(id=learner_id)
    assessments = Assessment.objects.filter(
        participants_observers__participant__id=learner_id
    ).order_by("-created_at")

    if assessments.exists():
        first_assessment = assessments.first()
        if first_assessment.assessment_timing == "pre":

            pre_assessment = first_assessment
            post_assessment = Assessment.objects.get(pre_assessment=pre_assessment)
        elif first_assessment.assessment_timing == "post":

            pre_assessment = first_assessment.pre_assessment
            post_assessment = first_assessment

        if pre_assessment and post_assessment:
            pre_assessment_image, pre_assessment_compentency_with_description = (
                generate_graph_for_participant(
                    participant, pre_assessment.id, pre_assessment
                )
            )
            post_assessment_image, post_assessment_compentency_with_description = (
                generate_graph_for_participant_for_post_assessment(
                    participant, post_assessment.id, post_assessment
                )
            )

            if post_assessment_image:
                return Response(
                    {"assessment_exists": True, "graph": post_assessment_image}
                )
            if pre_assessment_image:
                return Response(
                    {"assessment_exists": True, "graph": pre_assessment_image}
                )

    return Response({"assessment_exists": False, "graph": None})
