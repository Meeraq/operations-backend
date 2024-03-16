from datetime import date, datetime, timedelta
import uuid
import requests
import random
from django.core.mail import send_mail
from django.template.loader import get_template
from os import name
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from operationsBackend import settings
import jwt
import string
from django.db import transaction, IntegrityError
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.utils import timezone
from openpyxl import Workbook
from django.http import HttpResponse
import pandas as pd
from django.db.models import (
    Q,
    F,
    Case,
    When,
    Value,
    IntegerField,
    BooleanField,
    CharField,
)
from time import sleep
import json
from django.core.exceptions import ObjectDoesNotExist
from api.views import get_date, get_time, add_contact_in_wati
from django.shortcuts import render
from django.http import JsonResponse
from api.models import (
    Organisation,
    HR,
    Coach,
    User,
    Profile,
    Learner,
    Pmo,
    Role,
    UserToken,
    Facilitator,
)
from .serializers import (
    SchedularProjectSerializer,
    SchedularBatchSerializer,
    SessionItemSerializer,
    LearnerDataUploadSerializer,
    LiveSessionSerializerDepthOne,
    EmailTemplateSerializer,
    SentEmailDepthOneSerializer,
    BatchSerializer,
    LiveSessionSerializer,
    CoachingSessionSerializer,
    CoachSchedularAvailibiltySerializer,
    CoachSchedularAvailibiltySerializer2,
    CoachBasicDetailsSerializer,
    AvailabilitySerializer,
    SchedularSessionsSerializer,
    CoachSchedularGiveAvailibiltySerializer,
    CoachSchedularGiveAvailibiltySerializer2,
    RequestAvailibiltySerializerDepthOne,
    RequestAvailibiltySerializer,
    UpdateSerializer,
    SchedularUpdateDepthOneSerializer,
    SchedularBatchDepthSerializer,
    FacilitatorPricingSerializer,
    CoachPricingSerializer,
    ExpenseSerializerDepthOne,
    ExpenseSerializer,
)
from .models import (
    SchedularBatch,
    LiveSession,
    CoachingSession,
    SchedularProject,
    SentEmail,
    EmailTemplate,
    CoachSchedularAvailibilty,
    RequestAvailibilty,
    SchedularSessions,
    SchedularBatch,
    SchedularUpdate,
    CalendarInvites,
    CoachPricing,
    FacilitatorPricing,
    Expense,
)
from api.serializers import (
    FacilitatorSerializer,
    FacilitatorSerializerIsVendor,
    FacilitatorBasicDetailsSerializer,
    CoachSerializer,
    FacilitatorDepthOneSerializer,
)

from courses.models import (
    FeedbackLessonResponse,
    QuizLessonResponse,
    FeedbackLesson,
    QuizLesson,
    LaserCoachingSession,
    LiveSessionLesson,
    Lesson,
)
from courses.models import Course, CourseEnrollment
from courses.serializers import (
    CourseSerializer,
    LessonSerializer,
    CourseEnrollmentDepthOneSerializer,
)
from django.core.serializers import serialize
from courses.views import (
    create_or_get_learner,
    add_question_to_feedback_lesson,
    nps_default_feed_questions,
)
from assessmentApi.models import (
    Assessment,
    ParticipantUniqueId,
    ParticipantObserverMapping,
    ParticipantResponse,
)
from io import BytesIO
from api.serializers import LearnerSerializer
from api.views import (
    create_notification,
    send_mail_templates,
    create_outlook_calendar_invite,
    delete_outlook_calendar_invite,
)
from django.db.models import Max
import io
from time import sleep
from assessmentApi.views import delete_participant_from_assessments
from schedularApi.tasks import (
    celery_send_unbooked_coaching_session_mail,
    get_current_date_timestamps,
    get_coaching_session_according_to_time,
    get_live_session_according_to_time,
)

# Create your views here.
from itertools import chain
import environ
import re
from rest_framework.views import APIView
from api.views import get_user_data
from zohoapi.models import Vendor
from zohoapi.views import fetch_purchase_orders
from zohoapi.tasks import organization_id

env = environ.Env()


def get_feedback_lesson_name(lesson_name):
    # Trim leading and trailing whitespaces
    trimmed_string = lesson_name.strip()
    # Convert to lowercase
    lowercased_string = trimmed_string.lower()
    # Replace spaces between words with underscores
    underscored_string = "_".join(lowercased_string.split())
    return underscored_string


def extract_number_from_name(name):
    # Regular expression to match digits at the end of the string
    match = re.search(r"\d+$", name)
    if match:
        return int(match.group())
    else:
        return None


def get_live_session_name(session_type):

    session_name = None
    if session_type == "live_session":
        session_name = "Live Session"
    elif session_type == "check_in_session":
        session_name = "Check In Session"
    elif session_type == "in_person_session":
        session_name = "In Person Session"
    elif session_type == "kickoff_session":
        session_name = "Kickoff Session"
    elif session_type == "virtual_session":
        session_name = "Virtual Session"

    return session_name


def send_whatsapp_message_template(phone, payload):
    try:
        if not phone:
            return {"error": "Phone not available"}, 500
        wati_api_endpoint = env("WATI_API_ENDPOINT")
        wati_authorization = env("WATI_AUTHORIZATION")
        wati_api_url = (
            f"{wati_api_endpoint}/api/v1/sendTemplateMessage?whatsappNumber={phone}"
        )
        headers = {
            "content-type": "text/json",
            "Authorization": wati_authorization,
        }
        response = requests.post(wati_api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json(), response.status_code
    except Exception as e:
        print(str(e))


def updateLastLogin(email):
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = User.objects.get(username=email)
    user.last_login = today
    user.save()


def get_upcoming_availabilities_of_coaching_session(coaching_session_id):
    coaching_session = CoachingSession.objects.get(id=coaching_session_id)
    if (
        not coaching_session.start_date
        or not coaching_session.end_date
        or not coaching_session.end_date
    ):
        return None
    coaches_in_batch = coaching_session.batch.coaches.all()
    start_date = datetime.combine(coaching_session.start_date, datetime.min.time())
    end_date = (
        datetime.combine(coaching_session.end_date, datetime.min.time())
        + timedelta(days=1)
        - timedelta(milliseconds=1)
    )
    start_timestamp = str(int(start_date.timestamp() * 1000))
    end_timestamp = str(int(end_date.timestamp() * 1000))
    coach_availabilities = CoachSchedularAvailibilty.objects.filter(
        coach__in=coaches_in_batch,
        start_time__gte=start_timestamp,
        end_time__lte=end_timestamp,
        is_confirmed=False,
    )
    current_time = timezone.now()
    timestamp_milliseconds = str(int(current_time.timestamp() * 1000))
    upcoming_availabilities = coach_availabilities.filter(
        start_time__gt=timestamp_milliseconds
    )
    serializer = AvailabilitySerializer(upcoming_availabilities, many=True)
    return serializer.data


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_project_schedular(request):
    organisation = Organisation.objects.filter(
        id=request.data["organisation_name"]
    ).first()
    junior_pmo = None
    if "junior_pmo" in request.data:
        junior_pmo = Pmo.objects.filter(id=request.data["junior_pmo"]).first()
    if not organisation:
        organisation = Organisation(
            name=request.data["organisation_name"], image_url=request.data["image_url"]
        )
    organisation.save()
    existing_projects_with_same_name = SchedularProject.objects.filter(
        name=request.data["project_name"]
    )
    if existing_projects_with_same_name.exists():
        return Response({"error": "Project with same name already exists."}, status=400)
    try:
        schedularProject = SchedularProject(
            name=request.data["project_name"],
            organisation=organisation,
            email_reminder=request.data["email_reminder"],
            whatsapp_reminder=request.data["whatsapp_reminder"],
            calendar_invites=request.data["calendar_invites"],
            nudges=request.data["nudges"],
            pre_post_assessment=request.data["pre_post_assessment"],
            is_finance_enabled=request.data["finance"],
            junior_pmo=junior_pmo,
        )
        schedularProject.save()
    except IntegrityError:
        return Response({"error": "Project with this name already exists"}, status=400)
    except Exception as e:
        return Response({"error": "Failed to create project."}, status=400)
    hr_emails = []
    project_name = schedularProject.name
    print(request.data["hr"], "HR ID")
    for hr in request.data["hr"]:
        single_hr = HR.objects.get(id=hr)
        # print(single_hr)
        schedularProject.hr.add(single_hr)
        # Send email notification to the HR
        # subject = f'Hey HR! You have been assigned to a project {project_name}'
        # message = f'Dear {single_hr.first_name},\n\n You can use your email to log-in via OTP.'
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [single_hr.email])

    # hrs= create_hr(request.data['hr'])
    # for hr in hrs:
    #     project.hr.add(hr)

    # try:
    #     path = f"/projects/caas/progress/{project.id}"
    #     message = f"A new project - {project.name} has been created for the organisation - {project.organisation.name}"
    #     create_notification(project.hr.first().user.user, path, message)
    # except Exception as e:
    #     print(f"Error occurred while creating notification: {str(e)}")
    # return Response({"message": "Project created succesfully"}, status=200)
    try:
        path = ""
        message = f"A new project - {schedularProject.name} has been created for the organisation - {schedularProject.organisation.name}"
        for hr_member in schedularProject.hr.all():
            create_notification(hr_member.user.user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response(
        {"message": "Project created successfully", "project_id": schedularProject.id},
        status=200,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_Schedular_Projects(request):
    status = request.query_params.get("status")
    pmo_id = request.query_params.get("pmo")
    projects = SchedularProject.objects.all()
    if pmo_id:
        pmo = Pmo.objects.get(id=int(pmo_id))

        if pmo.sub_role == "junior_pmo":
            projects = SchedularProject.objects.filter(junior_pmo=pmo)
        else:
            projects = SchedularProject.objects.all()

    if status:
        projects = projects.exclude(status="completed")

    serializer = SchedularProjectSerializer(projects, many=True)
    for project_data in serializer.data:
        latest_update = (
            SchedularUpdate.objects.filter(project__id=project_data["id"])
            .order_by("-created_at")
            .first()
        )
        project_data["latest_update"] = latest_update.message if latest_update else None
    return Response(serializer.data, status=200)


def create_facilitator_pricing(batch, facilitator):
    project_structure = batch.project.project_structure

    for session in project_structure:

        if session["session_type"] in [
            "check_in_session",
            "in_person_session",
            "kickoff_session",
            "virtual_session",
            "live_session",
        ]:
            live_session = LiveSession.objects.filter(
                batch=batch,
                order=session["order"],
                session_type=session["session_type"],
            ).first()

            facilitator_pricing, created = FacilitatorPricing.objects.get_or_create(
                project=batch.project,
                facilitator=facilitator,
                session_type=live_session.session_type,
                live_session_number=live_session.live_session_number,
                order=live_session.order,
                duration=live_session.duration,
            )
            if created:
                facilitator_pricing.price = session["price"]
                facilitator_pricing.save()


def delete_facilitator_pricing(batch, facilitator):
    project_structure = batch.project.project_structure

    for session in project_structure:

        if session["session_type"] in [
            "check_in_session",
            "in_person_session",
            "kickoff_session",
            "virtual_session",
            "live_session",
        ]:
            live_session = LiveSession.objects.filter(
                batch=batch,
                order=session["order"],
                session_type=session["session_type"],
            ).first()

            facilitator_pricing = FacilitatorPricing.objects.filter(
                project=batch.project,
                facilitator=facilitator,
                session_type=live_session.session_type,
                live_session_number=live_session.live_session_number,
                order=live_session.order,
                price=session["price"],
            ).delete()


# @api_view(["POST"])
# def save_live_session(request):
#     data = request.data

#     if "requestData" not in data or "otherData" not in data:
#         return Response(
#             {"error": "Invalid data format in request"},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     requestData = data["requestData"]

#     if not requestData:
#         return Response(
#             {"error": "requestData is empty"},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     live_sessions = []

#     for item in requestData:
#         zoom_id = item.get("zoom_id", None)
#         batch_id = item.get("batch_id", None)
#         live_session_number = item.get("live_session_number", None)
#         live_session_order = item.get("live_session_order", None)
#         if None in [zoom_id, batch_id]:
#             return Response(
#                 {"error": "Missing one or more required fields in request data"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         live_session = LiveSession.objects.create(
#             zoom_id=zoom_id,
#             batch_id=batch_id,
#             live_session_number=live_session_number,
#             live_session_order=live_session_order,
#         )

#         live_sessions.append(live_session)

#     return Response(status=status.HTTP_201_CREATED)


# @api_view(["POST"])
# def save_coaching_session(request):
#     data = request.data

#     try:
#         requestData = data.get("requestData", [])[0]  # Get the first element of the requestData list

#         coaching_session = CoachingSession.objects.create(
#             booking_link=requestData["booking_link"],
#             batch_id=requestData["batch_id"],
#             coaching_session_number=requestData["coaching_session_number"],
#             coaching_session_order=requestData["coaching_session_order"],
#             start_date=datetime.strptime(requestData["start_date"], "%d-%m-%y"),
#             end_date=datetime.strptime(requestData["end_date"], "%d-%m-%y"),
#             expiry_date=datetime.strptime(requestData["expiry_date"], "%d-%m-%Y"),
#         )

#         # Now, let's handle the otherData:
#         sessions_data = data.get("otherData", {}).get("sessions", {}).get("index", {})

#         session_type = sessions_data.get("sessionType", "")
#         duration = sessions_data.get("duration", "")

#         # You can add session_type and duration to the coaching_session if needed
#         coaching_session.session_type = session_type
#         coaching_session.duration = duration

#         coaching_session.save()

#         return Response(
#             {"message": "Coaching session created successfully."},
#             status=200,
#         )

#     except Exception as e:
#         return Response(
#             {"message": f"Failed to create coaching session. Error: {str(e)}"},
#             status=400,
#         )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_project_structure(request, project_id):
    try:
        project = get_object_or_404(SchedularProject, id=project_id)
        serializer = SessionItemSerializer(data=request.data, many=True)
        if serializer.is_valid():
            is_editing = len(project.project_structure) > 0
            project.project_structure = serializer.data
            project.save()

            return Response(
                {
                    "message": (
                        "Project structure edited successfully."
                        if is_editing
                        else "Project structure added successfully."
                    )
                },
                status=200,
            )
        return Response({"error": "Invalid sessions found."}, status=400)
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_schedular_batches(request):
    try:
        project_id = request.GET.get("project_id")
        facilitator_id = request.GET.get("facilitator_id")
        if not project_id:
            batches = SchedularBatch.objects.all()
        else:
            batches = SchedularBatch.objects.filter(project__id=project_id)
        if facilitator_id:
            batches = batches.filter(
                livesession__facilitator__id=facilitator_id
            ).distinct()
        serializer = SchedularBatchSerializer(batches, many=True)
        return Response(serializer.data)
    except SchedularBatch.DoesNotExist:
        return Response({"message": "No batches found"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_schedular_project(request, project_id):
    try:
        project = get_object_or_404(SchedularProject, id=project_id)
        serializer = SchedularProjectSerializer(project)
        return Response(serializer.data)
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )


# print(slots_by_coach)
# res = []
# for key,slots_of_coach in slots_by_coach.items():
#     # print(slots_of_coach)
#     # return slots_of_coach
#     slots_of_coach.sort(key=lambda x: x["start_time"])
#     merged_slots_of_coach = []
#     for i in range(len(slots_of_coach)):
#         if (
#         len(merged_slots_of_coach) == 0
#         or slots_of_coach[i]["start_time"] > merged_slots_of_coach[-1]["end_time"]
#     ):
#             merged_slots_of_coach.append(slots_of_coach[i])
#         else:
#             merged_slots_of_coach[-1]["end_time"] = max(
#             merged_slots_of_coach[-1]["end_time"], slots_of_coach[i]["end_time"]
#         )
#     res.append([*merged_slots_of_coach])
# return res


def merge_time_slots(slots, slots_by_coach):
    res = []
    for key in slots_by_coach:
        sorted_slots = sorted(slots_by_coach[key], key=lambda x: x["start_time"])
        merged_slots = []
        for i in range(len(sorted_slots)):
            if (
                len(merged_slots) == 0
                or sorted_slots[i]["start_time"] > merged_slots[-1]["end_time"]
            ):
                merged_slots.append(sorted_slots[i])
            else:
                merged_slots[-1]["end_time"] = max(
                    merged_slots[-1]["end_time"], sorted_slots[i]["end_time"]
                )
        res.extend(merged_slots)

    return res

    slots.sort(key=lambda x: x["start_time"])
    merged_slots = []
    for i in range(len(slots)):
        if (
            len(merged_slots) == 0
            or slots[i]["start_time"] > merged_slots[-1]["end_time"]
        ):
            merged_slots.append(slots[i])
        else:
            merged_slots[-1]["end_time"] = max(
                merged_slots[-1]["end_time"], slots[i]["end_time"]
            )
    return merged_slots


def timestamp_to_datetime(timestamp):
    return datetime.utcfromtimestamp(int(timestamp) / 1000.0)


def generate_slots(start, end, duration):
    slots = []
    current_time = timestamp_to_datetime(start)

    while current_time + timedelta(minutes=duration) <= timestamp_to_datetime(end):
        new_end_time = current_time + timedelta(minutes=duration)
        slots.append(
            {
                "start_time": int(current_time.timestamp() * 1000),
                "end_time": int(new_end_time.timestamp() * 1000),
            }
        )
        current_time += timedelta(minutes=15)
    return slots


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_batch_calendar(request, batch_id):
    try:
        live_sessions = LiveSession.objects.filter(batch__id=batch_id)
        coaching_sessions = CoachingSession.objects.filter(batch__id=batch_id)
        live_sessions_serializer = LiveSessionSerializerDepthOne(
            live_sessions, many=True
        )
        coaching_sessions_serializer = CoachingSessionSerializer(
            coaching_sessions, many=True
        )
        coaching_sessions_result = []
        for coaching_session in coaching_sessions_serializer.data:
            session_duration = coaching_session["duration"]
            booked_session_count = SchedularSessions.objects.filter(
                coaching_session__id=coaching_session["id"]
            ).count()
            availabilities = get_upcoming_availabilities_of_coaching_session(
                coaching_session["id"]
            )
            result = []
            if availabilities is not None and len(availabilities):
                slots = []
                slots_by_coach = {}
                for availability in availabilities:
                    slots_by_coach[availability["coach"]] = (
                        [*slots_by_coach[availability["coach"]], availability]
                        if availability["coach"] in slots_by_coach
                        else [availability]
                    )
                    slots.append(availability)
                final_merge_slots = merge_time_slots(slots, slots_by_coach)
                for slot in final_merge_slots:
                    startT = slot["start_time"]
                    endT = slot["end_time"]
                    small_session_duration = int(session_duration)
                    result += generate_slots(startT, endT, small_session_duration)

            # Retrieve participants who have not booked this session
            participants = Learner.objects.filter(schedularbatch__id=batch_id).exclude(
                schedularsessions__coaching_session__id=coaching_session["id"]
            )
            coaching_sessions_result.append(
                {
                    **coaching_session,
                    "available_slots_count": (
                        len(result) if availabilities is not None else 0
                    ),
                    # if session_duration > '30'
                    # else (len(availabilities) if availabilities is not None else 0),
                    "booked_session_count": booked_session_count,
                    "participants_not_booked": LearnerSerializer(
                        participants, many=True
                    ).data,
                }
            )

        participants = Learner.objects.filter(schedularbatch__id=batch_id)
        participants_serializer = LearnerSerializer(participants, many=True)
        coaches = Coach.objects.filter(schedularbatch__id=batch_id)
        facilitator = (
            Facilitator.objects.filter(livesession__batch__id=batch_id)
            .distinct()
            .annotate(
                is_vendor=Case(
                    When(user__vendor__isnull=False, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
                vendor_id=Case(
                    When(user__vendor__isnull=False, then=F("user__vendor__vendor_id")),
                    default=None,
                    output_field=CharField(max_length=255, null=True),
                ),
                purchase_order_id=Case(
                    When(expense__isnull=False, then=F("expense__purchase_order_id")),
                    default=None,
                    output_field=CharField(max_length=200, null=True),
                ),
                purchase_order_no=Case(
                    When(expense__isnull=False, then=F("expense__purchase_order_no")),
                    default=None,
                    output_field=CharField(max_length=200, null=True),
                ),
            )
        )

        coaches_serializer = CoachSerializer(coaches, many=True)
        facilitator_serializer = FacilitatorSerializerIsVendor(facilitator, many=True)

        try:
            purchase_orders = fetch_purchase_orders(organization_id)
            for facilitator_item in facilitator_serializer.data:
                expense = Expense.objects.filter(batch__id=batch_id , facilitator__id = facilitator_item['id']).first()
                if expense.purchase_order_id:
                    facilitator_item['purchase_order_id'] = expense.purchase_order_id
                    facilitator_item['purchase_order_no'] = expense.purchase_order_no
                else:
                    facilitator_item['purchase_order_id'] = expense.purchase_order_id
                    facilitator_item['purchase_order_no'] = expense.purchase_order_no
                if facilitator_item['purchase_order_id'] is not None:
                    purchase_order = get_purchase_order(purchase_orders, facilitator_item['purchase_order_id'])
                    facilitator_item['purchase_order'] = purchase_order
                else:
                    facilitator_item['purchase_order'] = None
        except Exception as e:
            print(str(e))

        sessions = [*live_sessions_serializer.data, *coaching_sessions_result]
        sorted_sessions = sorted(sessions, key=lambda x: x["order"])
        try:
            course = Course.objects.get(batch__id=batch_id)
            course_serailizer = CourseSerializer(course)
            for participant in participants_serializer.data:
                course_enrollment = CourseEnrollment.objects.get(
                    learner__id=participant["id"], course=course
                )
                participant["is_certificate_allowed"] = (
                    course_enrollment.is_certificate_allowed
                )
                course_enrollment_serializer = CourseEnrollmentDepthOneSerializer(
                    course_enrollment
                )
                participant["course_enrollment"] = course_enrollment_serializer.data
                completed_lessons_length = len(
                    participant.get("course_enrollment", {}).get(
                        "completed_lessons", []
                    )
                )
                lessons = Lesson.objects.filter(
                    Q(course=course_enrollment.course),
                    Q(status="public"),
                    ~Q(lesson_type="feedback"),
                )
                completed_lesson_count = completed_lessons_length
                total_lesson_count = lessons.count()
                participant["progress"] = 0
                if total_lesson_count > 0:
                    participant["progress"] = int(
                        round((completed_lesson_count / total_lesson_count) * 100)
                    )
        except Exception as e:
            print(str(e))
            course = None
        batch_for_response = SchedularBatch.objects.filter(id=batch_id).first()
        return Response(
            {
                "sessions": sorted_sessions,
                "participants": participants_serializer.data,
                "coaches": coaches_serializer.data,
                "course": course_serailizer.data if course else None,
                "batch": batch_id,
                "facilitator": facilitator_serializer.data,
                "batch_name": batch_for_response.name,
                "project_id": batch_for_response.project.id,
            }
        )
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_live_session(request, live_session_id):
    try:
        with transaction.atomic():
            live_session = LiveSession.objects.get(id=live_session_id)

            existing_date_time = live_session.date_time
            serializer = LiveSessionSerializer(
                live_session, data=request.data, partial=True
            )
            if serializer.is_valid():
                update_live_session = serializer.save()
                current_time = timezone.now()
                if update_live_session.date_time > current_time:
                    try:
                        scheduled_for = update_live_session.date_time - timedelta(
                            minutes=30
                        )
                        clocked = ClockedSchedule.objects.create(
                            clocked_time=scheduled_for
                        )
                        # time is utc one here
                        periodic_task = PeriodicTask.objects.create(
                            name=f"send_whatsapp_reminder_30_min_before_live_session_{uuid.uuid1()}",
                            task="schedularApi.tasks.send_whatsapp_reminder_30_min_before_live_session",
                            args=[update_live_session.id],
                            clocked=clocked,
                            one_off=True,
                        )
                        periodic_task.save()
                        if update_live_session.pt_30_min_before:
                            update_live_session.pt_30_min_before.enabled = False
                            update_live_session.pt_30_min_before.save()
                        live_session.pt_30_min_before = periodic_task
                        live_session.save()
                    except Exception as e:
                        print(str(e))
                        pass
                live_session_lesson = LiveSessionLesson.objects.filter(
                    live_session=live_session
                ).first()
                lesson = live_session_lesson.lesson

                lesson.drip_date = live_session.date_time + timedelta(
                    hours=5, minutes=30
                )

                lesson.save()

                AIR_INDIA_PROJECT_ID = 3
                if (
                    not update_live_session.batch.project.id == AIR_INDIA_PROJECT_ID
                    and update_live_session.batch.project.status == "ongoing"
                    and update_live_session.batch.project.calendar_invites
                ):
                    try:
                        learners = live_session.batch.learners.all()
                        facilitators = [live_session.facilitator]
                        attendees = []

                        # Adding learners to attendees list
                        for learner in learners:
                            attendee = {
                                "emailAddress": {
                                    "name": learner.name,
                                    "address": learner.email,
                                },
                                "type": "required",
                            }
                            attendees.append(attendee)

                        # Adding facilitators to attendees list
                        for facilitator in facilitators:
                            attendee = {
                                "emailAddress": {
                                    "name": facilitator.first_name
                                    + " "
                                    + facilitator.last_name,
                                    "address": facilitator.email,
                                },
                                "type": "required",
                            }
                            attendees.append(attendee)

                        start_time_stamp = (
                            update_live_session.date_time.timestamp() * 1000
                        )
                        end_time_stamp = (
                            start_time_stamp + int(update_live_session.duration) * 60000
                        )
                        start_datetime_obj = datetime.fromtimestamp(
                            int(start_time_stamp) / 1000
                        ) + timedelta(hours=5, minutes=30)
                        start_datetime_str = (
                            start_datetime_obj.strftime("%d-%m-%Y %H:%M") + " IST"
                        )
                        description = (
                            f"Your Meeraq Live Training Session is scheduled at {start_datetime_str}. "
                            + update_live_session.description
                            if update_live_session.description
                            else (
                                "" + update_live_session.description
                                if update_live_session.description
                                else ""
                            )
                        )
                        if not existing_date_time:
                            create_outlook_calendar_invite(
                                "Meeraq - Live Session",
                                description,
                                start_time_stamp,
                                end_time_stamp,
                                attendees,
                                env("CALENDAR_INVITATION_ORGANIZER"),
                                None,
                                None,
                                update_live_session,
                                update_live_session.meeting_link,
                            )
                        elif not existing_date_time.strftime(
                            "%d-%m-%Y %H:%M"
                        ) == update_live_session.date_time.strftime("%d-%m-%Y %H:%M"):
                            existing_calendar_invite = CalendarInvites.objects.filter(
                                live_session=live_session
                            ).first()
                            # delete the current one
                            if existing_calendar_invite:
                                delete_outlook_calendar_invite(existing_calendar_invite)
                            # create the new one
                            create_outlook_calendar_invite(
                                "Meeraq - Live Session",
                                description,
                                start_time_stamp,
                                end_time_stamp,
                                attendees,
                                env("CALENDAR_INVITATION_ORGANIZER"),
                                None,
                                None,
                                update_live_session,
                                update_live_session.meeting_link,
                            )
                    except Exception as e:
                        print(str(e))
                        pass
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to updated live session"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_coaching_session(request, coaching_session_id):
    try:
        with transaction.atomic():
            coaching_session = CoachingSession.objects.get(id=coaching_session_id)

            serializer = CoachingSessionSerializer(
                coaching_session, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                coaching_session_lesson = LaserCoachingSession.objects.filter(
                    coaching_session=coaching_session
                ).first()
                lesson = coaching_session_lesson.lesson
                lesson.drip_date = coaching_session.start_date
                lesson.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to updated coaching session"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def pending_scheduled_mails_exists(request, email_template_id):
    sent_emails = SentEmail.objects.filter(
        template__id=email_template_id, status="pending"
    )
    return Response({"exists": sent_emails.count() > 0}, status=200)


@api_view(["PUT"])
@permission_classes([AllowAny])
def editEmailTemplate(request, template_id):
    try:
        email_template = EmailTemplate.objects.get(pk=template_id)
    except EmailTemplate.DoesNotExist:
        return Response(
            {"success": False, "message": "Template not found."}, status=404
        )

    if request.method == "PUT":
        title = request.data.get("title", None)
        template_data = request.data.get("templatedata", None)
        print(template_data, "request.data")

        if template_data is not None:
            try:
                email_template.title = title
                email_template.template_data = template_data
                email_template.save()
                return Response(
                    {"success": True, "message": "Template updated successfully."}
                )
            except Exception as e:
                return Response(
                    {"success": False, "message": "Failed to update template."}
                )

    return Response({"success": False, "message": "Invalid request."})


@api_view(["POST"])
@permission_classes([AllowAny])
def addEmailTemplate(request):
    if request.method == "POST":
        title = request.data.get("title", None)
        template_data = request.data.get("templatedata", None)
        print(title, "Title")
        print(template_data, "request.data")

        if template_data is not None:
            try:
                email_template = EmailTemplate.objects.create(
                    title=title, template_data=template_data
                )
                # email_template = EmailTemplate.objects.create(title=title, template_data=template_data)
                # (template_data=template_data,template_title)
                print(email_template, "email template")
                return Response(
                    {"success": True, "message": "Template saved successfully."}
                )
            except Exception as e:
                return Response(
                    {"success": False, "message": "Failed to save template."}
                )

    return Response({"success": False, "message": "Invalid request."})


@api_view(["POST"])
@permission_classes([AllowAny])
def send_test_mails(request):
    try:
        emails = request.data.get("emails", [])
        subject = request.data.get("subject")
        # email_content = request.data.get('email_content', '')  # Assuming you're sending email content too
        temp1 = request.data.get("htmlContent", "")

        print(emails, "emails")

        # if not subject:
        #     return Response({'error': "Subject is required."}, status=400)

        if len(emails) > 0:
            for email in emails:
                email_message_learner = render_to_string(
                    "default.html",
                    {
                        "email_content": mark_safe(temp1),
                        "email_title": "hello",
                        "subject": subject,
                    },
                )
                email = EmailMessage(
                    subject,
                    email_message_learner,
                    settings.DEFAULT_FROM_EMAIL,  # from email address
                    [email],  # to email address
                )
                email.content_subtype = "html"
                email.send()
                print("Email sent to:", email)

            return Response({"message": "Emails sent successfully"}, status=200)
        else:
            return Response({"error": "No email addresses found."}, status=400)
    except Exception as e:
        return Response({"error": "Failed to send mail."}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def participants_list(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
    except SchedularBatch.DoesNotExist:
        return Response({"detail": "Batch not found"}, status=404)
    learners = batch.learners.all()
    serializer = LearnerSerializer(learners, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def getSavedTemplates(request):
    emailTemplate = EmailTemplate.objects.all()
    serilizer = EmailTemplateSerializer(emailTemplate, many=True)
    return Response({"status": "success", "data": serilizer.data}, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_batches(request):
    batches = SchedularBatch.objects.all()
    serializer = BatchSerializer(batches, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def send_mails(request):
    subject = request.data.get("subject")
    scheduled_for = request.data.get("scheduledFor", "")
    recipients_data = request.data.get("recipients_data", [])
    try:
        template = EmailTemplate.objects.get(id=request.data.get("template_id", ""))
        if len(recipients_data) > 0:
            sent_email_instance = SentEmail(
                recipients=recipients_data,
                subject=subject,
                template=template,
                status="pending",
                scheduled_for=scheduled_for,
            )
            sent_email_instance.save()
            clocked = ClockedSchedule.objects.create(
                clocked_time=scheduled_for
            )  # time is utc one here
            periodic_task = PeriodicTask.objects.create(
                name=uuid.uuid1(),
                task="schedularApi.tasks.send_email_to_recipients",
                args=[sent_email_instance.id],
                clocked=clocked,
                one_off=True,
            )
            sent_email_instance.periodic_task = periodic_task
            sent_email_instance.save()
            return Response({"message": "Emails sent successfully"}, status=200)
        else:
            return Response({"error": "No email addresses found."}, status=400)
    except EmailTemplate.DoesNotExist:
        return Response({"error": "Failed to schedule emails"}, status=400)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_mail_data(request):
    sent_emails = SentEmail.objects.all()
    serializer = SentEmailDepthOneSerializer(sent_emails, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([AllowAny])
def cancel_scheduled_mail(request, sent_mail_id):
    try:
        sent_email = SentEmail.objects.get(id=sent_mail_id)
    except SentEmail.DoesNotExist:
        return Response({"error": "Scheduled email not found."}, status=404)

    if sent_email.status == "cancelled":
        return Response({"error": "Email is already cancelled."}, status=400)
    if sent_email.status == "completed":
        return Response({"error": "Email is already sent."}, status=400)

    sent_email.status = "cancelled"
    sent_email.save()

    return Response({"message": "Email has been successfully cancelled."})


@api_view(["DELETE"])
@permission_classes([AllowAny])
def deleteEmailTemplate(request, template_id):
    try:
        delete_template = EmailTemplate.objects.get(pk=template_id)
        delete_template.delete()
        return Response({"success": True, "message": "Template deleted successfully."})
    except EmailTemplate.DoesNotExist:
        return Response(
            {"success": False, "message": "Template not found."}, status=404
        )
    except Exception as e:
        return Response({"success": False, "message": "Failed to delete template."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_schedular_availabilities(request):
    coach_id = request.GET.get("coach_id")
    if coach_id:
        availabilities = RequestAvailibilty.objects.filter(coach__id=coach_id)
    else:
        availabilities = RequestAvailibilty.objects.all()
    serializer = CoachSchedularAvailibiltySerializer2(availabilities, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_coach_schedular_availibilty(request):
    if request.method == "POST":
        serializer = RequestAvailibiltySerializer(data=request.data)
        if serializer.is_valid():
            request_availability = serializer.save()

            # Get the list of selected coaches from the serializer data
            selected_coaches = serializer.validated_data.get("coach")
            availability_data = request_availability.availability
            dates = list(availability_data.keys())
            date_str_arr = []
            for date in dates:
                formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime(
                    "%d-%B-%Y"
                )
                date_str_arr.append(formatted_date)
            exp = datetime.strptime(
                str(request_availability.expiry_date), "%Y-%m-%d"
            ).strftime("%d-%B-%Y")
            for coach in selected_coaches:
                send_mail_templates(
                    "create_coach_schedular_availibilty.html",
                    [coach.email],
                    "Meeraq -Book Coaching Session",
                    {
                        "name": coach.first_name + " " + coach.last_name,
                        "dates": date_str_arr,
                        "expiry_date": exp,
                    },
                    [],
                )
                create_notification(
                    coach.user.user,
                    "/slot-request",
                    "Admin has asked your availability!",
                )
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [coach.email]
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_slot_request(request, request_id):
    request_availability = RequestAvailibilty.objects.get(id=request_id)
    serializer = RequestAvailibiltySerializer(
        request_availability, data=request.data, partial=True
    )
    if serializer.is_valid():
        request_availability = serializer.save()
        request_availability.provided_by = []
        request_availability.save()
        # Get the list of selected coaches from the serializer data
        selected_coaches = serializer.validated_data.get("coach")
        availability_data = request_availability.availability
        dates = list(availability_data.keys())
        date_str_arr = []
        for date in dates:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%B-%Y")
            date_str_arr.append(formatted_date)
        exp = datetime.strptime(
            str(request_availability.expiry_date), "%Y-%m-%d"
        ).strftime("%d-%B-%Y")
        for coach in selected_coaches:
            send_mail_templates(
                "create_coach_schedular_availibilty.html",
                [coach.email],
                "Meeraq -Book Coaching Session",
                {
                    "name": coach.first_name + " " + coach.last_name,
                    "dates": date_str_arr,
                    "expiry_date": exp,
                },
                [],
            )
            create_notification(
                coach.user.user,
                "/slot-request",
                "Admin has asked your availability!",
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [coach.email]
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_batch(request, project_id):
    try:
        with transaction.atomic():
            participants_data = request.data.get("participants", [])
            project = SchedularProject.objects.get(id=project_id)
            learners_in_excel_sheet = len(participants_data)
            learners_in_excel_which_already_exists = 0
            for participant_data in participants_data:
                email = participant_data.get("email", "").strip().lower()
                if Learner.objects.filter(email=email).exists():
                    learners_in_excel_which_already_exists += 1
            for participant_data in participants_data:
                name = participant_data.get("name")
                email = participant_data.get("email", "").strip().lower()
                phone = participant_data.get("phone", None)
                batch_name = participant_data.get("batch").strip().upper()
                # Assuming 'project_id' is in your request data

                # Check if batch with the same name exists
                batch = SchedularBatch.objects.filter(
                    name=batch_name, project=project
                ).first()

                if not batch:
                    # If batch does not exist, create a new batch
                    batch = SchedularBatch.objects.create(
                        name=batch_name, project=project
                    )

                    # Create Live Sessions and Coaching Sessions based on project structure
                    for session_data in project.project_structure:
                        order = session_data.get("order")
                        duration = session_data.get("duration")
                        session_type = session_data.get("session_type")

                        if session_type in [
                            "live_session",
                            "check_in_session",
                            "in_person_session",
                            "kickoff_session",
                            "virtual_session",
                        ]:
                            session_number = (
                                LiveSession.objects.filter(
                                    batch=batch, session_type=session_type
                                ).count()
                                + 1
                            )
                            live_session = LiveSession.objects.create(
                                batch=batch,
                                live_session_number=session_number,
                                order=order,
                                duration=duration,
                                session_type=session_type,
                            )
                        elif session_type == "laser_coaching_session":
                            coaching_session_number = (
                                CoachingSession.objects.filter(
                                    batch=batch, session_type=session_type
                                ).count()
                                + 1
                            )
                            booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{str(uuid.uuid4())}"  # Generate a unique UUID for the booking link
                            coaching_session = CoachingSession.objects.create(
                                batch=batch,
                                coaching_session_number=coaching_session_number,
                                order=order,
                                duration=duration,
                                booking_link=booking_link,
                                session_type=session_type,
                            )
                        elif session_type == "mentoring_session":
                            coaching_session_number = (
                                CoachingSession.objects.filter(
                                    batch=batch, session_type=session_type
                                ).count()
                                + 1
                            )

                            booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{str(uuid.uuid4())}"  # Generate a unique UUID for the booking link
                            coaching_session = CoachingSession.objects.create(
                                batch=batch,
                                coaching_session_number=coaching_session_number,
                                order=order,
                                duration=duration,
                                booking_link=booking_link,
                                session_type=session_type,
                            )

                # Check if participant with the same email exists

                learner = create_or_get_learner(
                    {"name": name, "email": email, "phone": phone}
                )
                if learner:
                    name = learner.name
                    if learner.phone:
                        add_contact_in_wati("learner", name, learner.phone)

                # Add participant to the batch if not already added
                if learner and learner not in batch.learners.all():
                    batch.learners.add(learner)
                    try:
                        course = Course.objects.get(batch=batch)
                        course_enrollments = CourseEnrollment.objects.filter(
                            learner=learner, course=course
                        )
                        if not course_enrollments.exists():
                            datetime = timezone.now()
                            CourseEnrollment.objects.create(
                                learner=learner,
                                course=course,
                                enrollment_date=datetime,
                            )
                    except Exception:
                        pass
            learner_message = (
                f"{learners_in_excel_sheet-learners_in_excel_which_already_exists} learner"
                if (learners_in_excel_sheet - learners_in_excel_which_already_exists)
                == 1
                else f"{learners_in_excel_sheet-learners_in_excel_which_already_exists} learners"
            )
            learner_msg = (
                f"{learners_in_excel_which_already_exists} learner"
                if (learners_in_excel_which_already_exists) == 1
                else f"{learners_in_excel_which_already_exists} learners"
            )
            return Response(
                {
                    "message": f"{learner_message} uploaded successfully {learner_msg} already existing."
                },
                status=status.HTTP_201_CREATED,
            )
    except Exception as e:
        print(str(e))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_coaches(request):
    coaches = Coach.objects.filter(is_approved=True)
    serializer = CoachBasicDetailsSerializer(coaches, many=True)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_batch(request, batch_id):
    existing_coaches = None
    coaches = request.data.get("coaches")

    try:
        with transaction.atomic():
            batch = SchedularBatch.objects.get(id=batch_id)
            existing_coaches = batch.coaches.all()
            for coach_id in coaches:
                coach = Coach.objects.get(id=coach_id)
                if coach not in existing_coaches:
                    project_structure = batch.project.project_structure

                    for session in project_structure:

                        if session["session_type"] in [
                            "laser_coaching_session",
                            "mentoring_session",
                        ]:
                            coaching_session = CoachingSession.objects.filter(
                                batch=batch,
                                order=session["order"],
                                session_type=session["session_type"],
                            ).first()
                            coach_pricing, created = CoachPricing.objects.get_or_create(
                                project=batch.project,
                                coach=coach,
                                session_type=coaching_session.session_type,
                                coaching_session_number=coaching_session.coaching_session_number,
                                order=coaching_session.order,
                            )
                            if created:
                                coach_pricing.price = session["price"]
                                coach_pricing.save()

            serializer = SchedularBatchSerializer(
                batch, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()

                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to add coach"}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_coach_availabilities_booking_link(request):
    booking_link_id = request.GET.get("booking_link_id")
    coaching_session_id = request.GET.get("coaching_session_id")

    if booking_link_id or coaching_session_id:
        booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{booking_link_id}"
        try:
            if coaching_session_id:
                coaching_session = CoachingSession.objects.get(id=coaching_session_id)
            else:
                coaching_session = CoachingSession.objects.get(
                    booking_link=booking_link
                )
            current_date = datetime.now().date()
            if (
                coaching_session.expiry_date
                and coaching_session.expiry_date < current_date
            ):
                return Response({"error": "The booking link has expired."})

            session_duration = coaching_session.duration
            session_type = coaching_session.session_type

            coaches_in_batch = coaching_session.batch.coaches.all()
            start_date = datetime.combine(
                coaching_session.start_date, datetime.min.time()
            )
            end_date = (
                datetime.combine(coaching_session.end_date, datetime.min.time())
                + timedelta(days=1)
                - timedelta(milliseconds=1)
            )
            start_timestamp = str(int(start_date.timestamp() * 1000))
            end_timestamp = str(int(end_date.timestamp() * 1000))

            coach_availabilities = CoachSchedularAvailibilty.objects.filter(
                coach__in=coaches_in_batch,
                start_time__gte=start_timestamp,
                end_time__lte=end_timestamp,
                is_confirmed=False,
            )
            serializer = AvailabilitySerializer(coach_availabilities, many=True)
            coaches_serializer = (
                CoachBasicDetailsSerializer(
                    coaching_session.batch.coaches.all(), many=True
                )
                if coaching_session_id
                else None
            )
            return Response(
                {
                    "project_status": coaching_session.batch.project.status,
                    "slots": serializer.data,
                    "session_duration": session_duration,
                    "session_type": session_type,
                    "coaches": coaches_serializer.data if coaches_serializer else None,
                }
            )
        except Exception as e:
            print(str(e))
            return Response({"error": "Unable to get slots"}, status=400)
    else:
        return Response({"error": "Booking link is not available"})


@api_view(["POST"])
@permission_classes([AllowAny])
def schedule_session(request):
    try:
        booking_link_id = request.data.get("booking_link_id", "")
        booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{booking_link_id}"
        participant_email = request.data.get("participant_email", "")
        # coach_availability_id = request.data.get("availability_id", "")
        timestamp = request.data.get("timestamp", "")
        end_time = request.data.get("end_time", "")
        coach_id = request.data.get("coach_id", "")
        request_id = request.data.get("request_id", "")

        request_avail = RequestAvailibilty.objects.get(id=request_id)
        coach = Coach.objects.get(id=coach_id)
        coach_availability = CoachSchedularAvailibilty.objects.create(
            request=request_avail,
            coach=coach,
            start_time=timestamp,
            end_time=end_time,
            is_confirmed=False,
        )
        coach_availability.save()
        coach_availability_id = coach_availability.id
        print("coach avail", coach_availability_id)
        new_timestamp = int(timestamp) / 1000
        date_obj = datetime.fromtimestamp(new_timestamp)
        date_str = date_obj.strftime("%Y-%m-%d")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d %B %Y")

        p_booking_start_time_stamp = timestamp
        p_booking_end_time_stamp = end_time
        p_block_from = int(p_booking_start_time_stamp) - 900000
        p_block_till = int(p_booking_end_time_stamp) + 900000

        date_for_mail = get_date(int(timestamp))
        start_time_for_mail = get_time(int(timestamp))
        end_time_for_mail = get_time(int(end_time))
        session_time = f"{start_time_for_mail} - {end_time_for_mail} IST"
        all_coach_availability = CoachSchedularAvailibilty.objects.filter(
            (
                Q(start_time__gte=p_block_from, start_time__lt=p_block_till)
                | Q(end_time__gt=p_block_from, end_time__lte=p_block_till)
            ),
            request=request_avail,
            coach=coach,
            is_confirmed=False,
        )
        unblock_slots = []
        coaching_session = get_object_or_404(CoachingSession, booking_link=booking_link)
        # Retrieve batch from the coaching session
        batch = coaching_session.batch
        session_type = coaching_session.session_type

        # Check if the participant is in the batch
        learner = get_object_or_404(Learner, email=participant_email)
        if learner not in batch.learners.all():
            return Response(
                {"error": "Email not found. Please use the registered Email"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the participant has already booked the session for the same coaching session
        existing_session = SchedularSessions.objects.filter(
            learner=learner, coaching_session=coaching_session
        ).first()

        if existing_session:
            return Response(
                {
                    "error": "You have already booked the session for the same coaching session"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Retrieve coach availability
        coach_availability = get_object_or_404(
            CoachSchedularAvailibilty, id=coach_availability_id
        )
        # Check if the coaching session has expired
        if (
            coaching_session.expiry_date
            and coaching_session.expiry_date < timezone.now().date()
        ):
            return Response(
                {"error": "Coaching session has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Check if the coach availability is confirmed
        if coach_availability.is_confirmed:
            return Response(
                {"error": "This slot is already booked. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create session
        session_data = {
            "learner": learner.id,
            "availibility": coach_availability.id,
            "coaching_session": coaching_session.id,
            "status": "pending",
        }

        serializer = SchedularSessionsSerializer(data=session_data)
        if serializer.is_valid():
            serializer.save()
            coach_availability.is_confirmed = True
            coach_availability.save()
            coach_name = f"{coach_availability.coach.first_name} {coach_availability.coach.last_name}"
            for availability_c in all_coach_availability:
                availability_c.is_confirmed = True
                print(availability_c.id)
                availability_c.save()
                if (
                    int(availability_c.start_time)
                    < p_block_from
                    < int(availability_c.end_time)
                ) and (int(availability_c.start_time) < p_block_from):
                    new_slot = {
                        "start_time": int(availability_c.start_time),
                        "end_time": p_block_from,
                        "conflict": False,
                    }
                    unblock_slots.append(new_slot)
                    availability_c.delete()
                if (
                    int(availability_c.start_time)
                    < p_block_till
                    < int(availability_c.end_time)
                ) and (int(availability_c.end_time) > p_block_till):
                    new_slot = {
                        "start_time": p_block_till,
                        "end_time": int(availability_c.end_time),
                        "conflict": False,
                    }
                    unblock_slots.append(new_slot)
                    availability_c.delete()
            for unblock_slot in unblock_slots:
                slot_created = CoachSchedularAvailibilty.objects.create(
                    request=request_avail,
                    coach=coach,
                    start_time=unblock_slot["start_time"],
                    end_time=unblock_slot["end_time"],
                    is_confirmed=False,
                )
                print(slot_created)
            booking_id = coach_availability.coach.room_id
            print(json.dumps(unblock_slots))
            # Only send email if project status is ongoing
            if coaching_session.batch.project.status == "ongoing":
                send_mail_templates(
                    "schedule_session.html",
                    [coach_availability.coach.email],
                    "Meeraq - Participant booked session",
                    {
                        "name": coach_name,
                        "date": date_for_mail,
                        "time": session_time,
                        "booking_id": booking_id,
                    },
                    [],
                )

                send_mail_templates(
                    "coach_templates/coaching_email_template.html",
                    [participant_email],
                    (
                        "Meeraq - Laser Coaching Session Booked"
                        if session_type == "laser_coaching_session"
                        else "Meeraq - Mentoring Session Booked"
                    ),
                    {
                        "name": learner.name,
                        "date": date_for_mail,
                        "time": session_time,
                        "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                        "session_type": (
                            "Mentoring"
                            if session_type == "mentoring_session"
                            else "Laser Coaching"
                        ),
                    },
                    [],
                )

            return Response(
                {"message": "Session scheduled successfully."},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to book the session."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


TIME_INTERVAL = 900000


def check_if_selected_slot_can_be_booked(coach_id, start_time, end_time):
    slot_date = datetime.fromtimestamp((int(start_time) / 1000)).date()
    start_timestamp = str(
        int(datetime.combine(slot_date, datetime.min.time()).timestamp() * 1000)
    )
    end_timestamp = str(
        int(datetime.combine(slot_date, datetime.max.time()).timestamp() * 1000)
    )
    selected_date_availabilities = CoachSchedularAvailibilty.objects.filter(
        start_time__lte=end_timestamp,
        end_time__gte=start_timestamp,
        coach__id=coach_id,
        is_confirmed=False,
    )
    availability_serializer = AvailabilitySerializer(
        selected_date_availabilities, many=True
    )
    sorted_slots = sorted(availability_serializer.data, key=lambda x: x["start_time"])
    merged_slots = []
    for i in range(len(sorted_slots)):
        if (
            len(merged_slots) == 0
            or sorted_slots[i]["start_time"] > merged_slots[-1]["end_time"]
        ):
            merged_slots.append(sorted_slots[i])
        else:
            merged_slots[-1]["end_time"] = max(
                merged_slots[-1]["end_time"], sorted_slots[i]["end_time"]
            )
    for slot in merged_slots:
        if int(start_time) >= int(slot["start_time"]) and int(end_time) <= int(
            slot["end_time"]
        ):
            return True


@api_view(["POST"])
@permission_classes([AllowAny])
def schedule_session_fixed(request):
    try:
        with transaction.atomic():
            booking_link_id = request.data.get("booking_link_id", "")
            booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{booking_link_id}"
            participant_email = request.data.get("participant_email", "")
            timestamp = request.data.get("timestamp", "")
            end_time = request.data.get("end_time", "")
            coach_id = request.data.get("coach_id", "")
            request_id = request.data.get("request_id", "")
            request_avail = RequestAvailibilty.objects.get(id=request_id)
            coach = Coach.objects.get(id=coach_id)
            if not check_if_selected_slot_can_be_booked(coach_id, timestamp, end_time):
                return Response(
                    {
                        "error": "Sorry! This slot has just been booked. Please refresh and try selecting a different time."
                    },
                    status=401,
                )
            coach_availability = CoachSchedularAvailibilty.objects.create(
                request=request_avail,
                coach=coach,
                start_time=timestamp,
                end_time=end_time,
                is_confirmed=False,
            )
            coach_availability.save()
            coach_availability_id = coach_availability.id

            new_timestamp = int(timestamp) / 1000
            date_obj = datetime.fromtimestamp(new_timestamp, timezone.utc)
            formatted_date = date_obj.strftime("%d %B %Y")

            p_booking_start_time_stamp = timestamp
            p_booking_end_time_stamp = end_time
            p_block_from = int(p_booking_start_time_stamp) - TIME_INTERVAL
            p_block_till = int(p_booking_end_time_stamp) + TIME_INTERVAL

            date_for_mail = get_date(int(timestamp))
            start_time_for_mail = get_time(int(timestamp))
            end_time_for_mail = get_time(int(end_time))
            session_time = f"{start_time_for_mail} - {end_time_for_mail} IST"
            all_coach_availability = CoachSchedularAvailibilty.objects.filter(
                (
                    Q(start_time__gte=p_block_from, start_time__lt=p_block_till)
                    | Q(end_time__gt=p_block_from, end_time__lte=p_block_till)
                ),
                request=request_avail,
                coach=coach,
                is_confirmed=False,
            ).exclude(id=coach_availability.id)
            unblock_slots_to_delete = []
            coaching_session = get_object_or_404(
                CoachingSession, booking_link=booking_link
            )
            batch = coaching_session.batch
            session_type = coaching_session.session_type

            learner = get_object_or_404(Learner, email=participant_email)
            if learner not in batch.learners.all():
                return Response(
                    {"error": "Email not found. Please use the registered Email"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_session = SchedularSessions.objects.filter(
                learner=learner, coaching_session=coaching_session
            ).first()

            if existing_session:
                return Response(
                    {
                        "error": "You have already booked the session for the same coaching session"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            coach_availability = get_object_or_404(
                CoachSchedularAvailibilty, id=coach_availability_id
            )

            if (
                coaching_session.expiry_date
                and coaching_session.expiry_date < timezone.now().date()
            ):
                return Response(
                    {"error": "Coaching session has expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if coach_availability.is_confirmed:
                return Response(
                    {"error": "This slot is already booked. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            session_data = {
                "learner": learner.id,
                "availibility": coach_availability.id,
                "coaching_session": coaching_session.id,
                "status": "pending",
            }

            serializer = SchedularSessionsSerializer(data=session_data)
            if serializer.is_valid():
                scheduled_session = serializer.save()
                coach_availability.is_confirmed = True
                coach_availability.save()
                coach_name = f"{coach_availability.coach.first_name} {coach_availability.coach.last_name}"
                unblock_slots = []

                for availability_c in all_coach_availability:
                    availability_c.is_confirmed = True
                    availability_c.save()
                    if (
                        int(availability_c.start_time)
                        < p_block_from
                        < int(availability_c.end_time)
                    ) and (int(availability_c.start_time) < p_block_from):
                        new_slot = {
                            "start_time": int(availability_c.start_time),
                            "end_time": p_block_from,
                            "conflict": False,
                        }
                        unblock_slots.append(new_slot)
                        unblock_slots_to_delete.append(availability_c)
                    if (
                        int(availability_c.start_time)
                        < p_block_till
                        < int(availability_c.end_time)
                    ) and (int(availability_c.end_time) > p_block_till):
                        new_slot = {
                            "start_time": p_block_till,
                            "end_time": int(availability_c.end_time),
                            "conflict": False,
                        }
                        unblock_slots.append(new_slot)
                        unblock_slots_to_delete.append(availability_c)

                for availability_c in unblock_slots_to_delete:
                    availability_c.delete()

                for unblock_slot in unblock_slots:
                    created_availability = CoachSchedularAvailibilty.objects.create(
                        request=request_avail,
                        coach=coach,
                        start_time=unblock_slot["start_time"],
                        end_time=unblock_slot["end_time"],
                        is_confirmed=False,
                    )
                session_type_value = (
                    "coaching"
                    if session_type == "laser_coaching_session"
                    else "mentoring"
                )
                booking_id = coach_availability.coach.room_id
                meeting_location = f"{env('CAAS_APP_URL')}/call/{booking_id}"
                # Only send email if project status is ongoing
                if coaching_session.batch.project.status == "ongoing":
                    attendees = None
                    if coaching_session.batch.project.calendar_invites:
                        attendees = [
                            {
                                "emailAddress": {
                                    "name": coach_name,
                                    "address": coach_availability.coach.email,
                                },
                                "type": "required",
                            },
                            {
                                "emailAddress": {
                                    "name": learner.name,
                                    "address": participant_email,
                                },
                                "type": "required",
                            },
                        ]
                    else:
                        attendees = [
                            {
                                "emailAddress": {
                                    "name": coach_name,
                                    "address": coach_availability.coach.email,
                                },
                                "type": "required",
                            }
                        ]
                    create_outlook_calendar_invite(
                        f"Meeraq - {session_type_value.capitalize()} Session",
                        f"Your {session_type_value} session has been confirmed. Book your calendars for the same. Please join the session at scheduled date and time",
                        coach_availability.start_time,
                        coach_availability.end_time,
                        attendees,
                        env("CALENDAR_INVITATION_ORGANIZER"),
                        None,
                        scheduled_session,
                        None,
                        meeting_location,
                    )
                    send_mail_templates(
                        "schedule_session.html",
                        [coach_availability.coach.email],
                        "Meeraq - Participant booked session",
                        {
                            "name": coach_name,
                            "date": date_for_mail,
                            "time": session_time,
                            "booking_id": booking_id,
                        },
                        [],
                    )

                # WHATSAPP MESSAGE CHECK

                # before 5 mins whatsapp msg
                start_datetime_obj = datetime.fromtimestamp(
                    int(coach_availability.start_time) / 1000
                )
                # Decrease 5 minutes
                five_minutes_prior_start_datetime = start_datetime_obj - timedelta(
                    minutes=5
                )
                clocked = ClockedSchedule.objects.create(
                    clocked_time=five_minutes_prior_start_datetime
                )
                periodic_task = PeriodicTask.objects.create(
                    name=uuid.uuid1(),
                    task="schedularApi.tasks.send_whatsapp_reminder_to_users_before_5mins_in_seeq",
                    args=[scheduled_session.id],
                    clocked=clocked,
                    one_off=True,
                )
                periodic_task.save()

                # after 3 mins whatsapp msg
                three_minutes_ahead_start_datetime = start_datetime_obj + timedelta(
                    minutes=3
                )
                clocked = ClockedSchedule.objects.create(
                    clocked_time=three_minutes_ahead_start_datetime
                )
                periodic_task = PeriodicTask.objects.create(
                    name=uuid.uuid1(),
                    task="schedularApi.tasks.send_whatsapp_reminder_to_users_after_3mins_in_seeq",
                    args=[scheduled_session.id],
                    clocked=clocked,
                    one_off=True,
                )
                periodic_task.save()

                # WHATSAPP MESSAGE CHECK
                # Only send email if project status is ongoing
                if coaching_session.batch.project.status == "ongoing":
                    send_mail_templates(
                        "coach_templates/coaching_email_template.html",
                        [participant_email],
                        (
                            "Meeraq - Laser Coaching Session Booked"
                            if session_type == "laser_coaching_session"
                            else "Meeraq - Mentoring Session Booked"
                        ),
                        {
                            "name": learner.name,
                            "date": date_for_mail,
                            "time": session_time,
                            "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                            "session_type": (
                                "Mentoring"
                                if session_type == "mentoring_session"
                                else "Laser Coaching"
                            ),
                        },
                        [],
                    )

                return Response(
                    {"message": "Session scheduled successfully."},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": f"Failed to book the session. {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reschedule_session(request, session_id):
    try:
        with transaction.atomic():
            session_to_reschedule = SchedularSessions.objects.get(id=session_id)
            timestamp = request.data.get("timestamp", "")
            end_time = request.data.get("end_time", "")
            coach_id = request.data.get("coach_id", "")
            request_id = request.data.get("request_id", "")
            request_avail = RequestAvailibilty.objects.get(id=request_id)
            coach = Coach.objects.get(id=coach_id)
            if not check_if_selected_slot_can_be_booked(coach_id, timestamp, end_time):
                return Response(
                    {
                        "error": "Sorry! This slot has just been booked. Please refresh and try selecting a different time."
                    },
                    status=401,
                )
            coach_availability = CoachSchedularAvailibilty.objects.create(
                request=request_avail,
                coach=coach,
                start_time=timestamp,
                end_time=end_time,
                is_confirmed=False,
            )
            coach_availability.save()
            coach_availability_id = coach_availability.id

            new_timestamp = int(timestamp) / 1000
            date_obj = datetime.fromtimestamp(new_timestamp, timezone.utc)
            formatted_date = date_obj.strftime("%d %B %Y")
            p_booking_start_time_stamp = timestamp
            p_booking_end_time_stamp = end_time
            p_block_from = int(p_booking_start_time_stamp) - TIME_INTERVAL
            p_block_till = int(p_booking_end_time_stamp) + TIME_INTERVAL

            date_for_mail = get_date(int(timestamp))
            start_time_for_mail = get_time(int(timestamp))
            end_time_for_mail = get_time(int(end_time))
            session_time = f"{start_time_for_mail} - {end_time_for_mail} IST"
            all_coach_availability = CoachSchedularAvailibilty.objects.filter(
                (
                    Q(start_time__gte=p_block_from, start_time__lt=p_block_till)
                    | Q(end_time__gt=p_block_from, end_time__lte=p_block_till)
                ),
                request=request_avail,
                coach=coach,
                is_confirmed=False,
            ).exclude(id=coach_availability.id)
            unblock_slots_to_delete = []
            coaching_session = session_to_reschedule.coaching_session
            batch = coaching_session.batch
            session_type = coaching_session.session_type
            learner = session_to_reschedule.learner
            if learner not in batch.learners.all():
                return Response(
                    {"error": "Email not found. Please use the registered Email"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            coach_availability = get_object_or_404(
                CoachSchedularAvailibilty, id=coach_availability_id
            )

            if (
                coaching_session.expiry_date
                and coaching_session.expiry_date < timezone.now().date()
            ):
                return Response(
                    {"error": "Coaching session has expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if coach_availability.is_confirmed:
                return Response(
                    {"error": "This slot is already booked. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            session_data = {
                "learner": learner.id,
                "availibility": coach_availability.id,
                "coaching_session": coaching_session.id,
                "status": "pending",
            }

            serializer = SchedularSessionsSerializer(data=session_data)
            if serializer.is_valid():
                # new session created
                scheduled_session = serializer.save()
                coach_availability.is_confirmed = True
                coach_availability.save()

                coach_name = f"{coach_availability.coach.first_name} {coach_availability.coach.last_name}"
                unblock_slots = []

                for availability_c in all_coach_availability:
                    availability_c.is_confirmed = True
                    availability_c.save()
                    if (
                        int(availability_c.start_time)
                        < p_block_from
                        < int(availability_c.end_time)
                    ) and (int(availability_c.start_time) < p_block_from):
                        new_slot = {
                            "start_time": int(availability_c.start_time),
                            "end_time": p_block_from,
                            "conflict": False,
                        }
                        unblock_slots.append(new_slot)
                        unblock_slots_to_delete.append(availability_c)
                    if (
                        int(availability_c.start_time)
                        < p_block_till
                        < int(availability_c.end_time)
                    ) and (int(availability_c.end_time) > p_block_till):
                        new_slot = {
                            "start_time": p_block_till,
                            "end_time": int(availability_c.end_time),
                            "conflict": False,
                        }
                        unblock_slots.append(new_slot)
                        unblock_slots_to_delete.append(availability_c)

                for availability_c in unblock_slots_to_delete:
                    availability_c.delete()

                for unblock_slot in unblock_slots:
                    created_availability = CoachSchedularAvailibilty.objects.create(
                        request=request_avail,
                        coach=coach,
                        start_time=unblock_slot["start_time"],
                        end_time=unblock_slot["end_time"],
                        is_confirmed=False,
                    )
                session_type_value = (
                    "coaching"
                    if session_type == "laser_coaching_session"
                    else "mentoring"
                )

                booking_id = coach_availability.coach.room_id
                meeting_location = f"{env('CAAS_APP_URL')}/call/{booking_id}"
                # Only send email if project status is ongoing
                if coaching_session.batch.project.status == "ongoing":
                    attendees = None
                    if coaching_session.batch.project.calendar_invites:
                        attendees = [
                            {
                                "emailAddress": {
                                    "name": coach_name,
                                    "address": coach_availability.coach.email,
                                },
                                "type": "required",
                            },
                            {
                                "emailAddress": {
                                    "name": learner.name,
                                    "address": learner.email,
                                },
                                "type": "required",
                            },
                        ]
                    else:
                        attendees = [
                            {
                                "emailAddress": {
                                    "name": coach_name,
                                    "address": coach_availability.coach.email,
                                },
                                "type": "required",
                            }
                        ]
                    create_outlook_calendar_invite(
                        f"Meeraq - {session_type_value.capitalize()} Session",
                        f"Your {session_type_value} session has been confirmed. Book your calendars for the same. Please join the session at scheduled date and time",
                        coach_availability.start_time,
                        coach_availability.end_time,
                        attendees,
                        env("CALENDAR_INVITATION_ORGANIZER"),
                        None,
                        scheduled_session,
                        None,
                        meeting_location,
                    )
                    send_mail_templates(
                        "schedule_session.html",
                        [coach_availability.coach.email],
                        "Meeraq - Participant booked session",
                        {
                            "name": coach_name,
                            "date": date_for_mail,
                            "time": session_time,
                            "booking_id": booking_id,
                        },
                        [],
                    )

                # WHATSAPP MESSAGE CHECK

                # before 5 mins whatsapp msg
                start_datetime_obj = datetime.fromtimestamp(
                    int(coach_availability.start_time) / 1000
                )
                # Decrease 5 minutes
                five_minutes_prior_start_datetime = start_datetime_obj - timedelta(
                    minutes=5
                )
                clocked = ClockedSchedule.objects.create(
                    clocked_time=five_minutes_prior_start_datetime
                )
                periodic_task = PeriodicTask.objects.create(
                    name=uuid.uuid1(),
                    task="schedularApi.tasks.send_whatsapp_reminder_to_users_before_5mins_in_seeq",
                    args=[scheduled_session.id],
                    clocked=clocked,
                    one_off=True,
                )
                periodic_task.save()

                # after 3 mins whatsapp msg
                three_minutes_ahead_start_datetime = start_datetime_obj + timedelta(
                    minutes=3
                )
                clocked = ClockedSchedule.objects.create(
                    clocked_time=three_minutes_ahead_start_datetime
                )
                periodic_task = PeriodicTask.objects.create(
                    name=uuid.uuid1(),
                    task="schedularApi.tasks.send_whatsapp_reminder_to_users_after_3mins_in_seeq",
                    args=[scheduled_session.id],
                    clocked=clocked,
                    one_off=True,
                )
                periodic_task.save()

                # WHATSAPP MESSAGE CHECK
                # Only send email if project status is ongoing
                if (
                    coaching_session.batch.project.status == "ongoing"
                    and not coach_availability.start_time
                    == session_to_reschedule.availibility.start_time
                ):
                    send_mail_templates(
                        "coach_templates/coaching_email_template.html",
                        [learner.email],
                        (
                            "Meeraq - Laser Coaching Session Booked"
                            if session_type == "laser_coaching_session"
                            else "Meeraq - Mentoring Session Booked"
                        ),
                        {
                            "name": learner.name,
                            "date": date_for_mail,
                            "time": session_time,
                            "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                            "session_type": (
                                "Mentoring"
                                if session_type == "mentoring_session"
                                else "Laser Coaching"
                            ),
                        },
                        [],
                    )
                # deleting existing session and cancelling calendar invite for existing one
                calendar_invites = CalendarInvites.objects.filter(
                    schedular_session=session_to_reschedule
                )
                if calendar_invites.exists():
                    calendar_invite = calendar_invites.first()
                    try:
                        delete_outlook_calendar_invite(calendar_invite)
                    except Exception as e:
                        print(str(e))
                        pass
                session_to_reschedule.delete()
                return Response(
                    {"message": "Session rescheduled successfully."},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": f"Failed to book the session. {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_coach_availabilities(request):
    try:
        slots_data = request.data.get("slots", [])
        slots_length = request.data.get("slots_length")
        request_id = request.data.get("request_id", [])
        coach_id = request.data.get("coach_id", [])
        request = RequestAvailibilty.objects.get(id=request_id)
        serializer = CoachSchedularGiveAvailibiltySerializer(data=slots_data, many=True)

        unique_dates = set()
        for date in slots_data:
            slot_id = date["id"]
            parts = slot_id.split("_")
            slot_date = parts[0]
            unique_dates.add(slot_date)

        coach = Coach.objects.get(id=coach_id)
        coach_name = f"{coach.first_name} {coach.last_name}"

        if serializer.is_valid():
            serializer.save()
            request.provided_by.append(int(coach_id))
            request.save()

            # Convert dates from 'YYYY-MM-DD' to 'DD-MM-YYYY' format
            formatted_dates = []
            for date in unique_dates:
                datetime_obj = datetime.strptime(date, "%Y-%m-%d")
                formatted_date = datetime_obj.strftime("%d-%m-%Y")
                formatted_dates.append(formatted_date)
            pmo_user = User.objects.filter(profile__roles__name="pmo").first()
            send_mail_templates(
                "create_coach_availibilities.html",
                [pmo_user.email],
                "Meeraq - Availability given by coach",
                {
                    "name": coach_name,
                    "total_slots": slots_length,
                    "dates": formatted_dates,
                },
                [],
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response(
            {"error": "Failed to confirm the availability"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_coach_availabilities(request):
    coach_id = request.GET.get("coach_id")
    if coach_id:
        coach_schedular_availabilities = CoachSchedularAvailibilty.objects.filter(
            coach__id=coach_id
        )
    else:
        coach_schedular_availabilities = CoachSchedularAvailibilty.objects.all()
    serializer = CoachSchedularGiveAvailibiltySerializer2(
        coach_schedular_availabilities, many=True
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sessions(request):
    coach_id = request.query_params.get("coach_id")
    if coach_id:
        # Get sessions based on coach ID
        sessions = SchedularSessions.objects.filter(availibility__coach__id=coach_id)
    else:
        # Get all sessions
        sessions = SchedularSessions.objects.all()
    session_details = []
    for session in sessions:
        session_detail = {
            "batch_name": session.coaching_session.batch.name,
            "coach_name": session.availibility.coach.first_name
            + " "
            + session.availibility.coach.last_name,
            "participant_name": session.learner.name,
            "coaching_session_number": session.coaching_session.coaching_session_number,
            "participant_email": session.learner.email,
            "meeting_link": f"{env('CAAS_APP_URL')}/call/{session.availibility.coach.room_id}",
            "room_id": f"{session.availibility.coach.room_id}",
            "start_time": session.availibility.start_time,
        }
        session_details.append(session_detail)
    return Response(session_details, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sessions_by_type(request, sessions_type):
    coach_id = request.query_params.get("coach_id")
    current_time = timezone.now()
    timestamp_milliseconds = str(int(current_time.timestamp() * 1000))
    if coach_id:
        # Get sessions based on coach ID
        sessions = SchedularSessions.objects.filter(availibility__coach__id=coach_id)
    else:
        # Get all sessions
        sessions = SchedularSessions.objects.all()
    # filtering based on upcoming or past sessions
    if sessions_type == "upcoming":
        sessions = sessions.filter(availibility__end_time__gt=timestamp_milliseconds)
    elif sessions_type == "past":
        sessions = sessions.filter(availibility__end_time__lt=timestamp_milliseconds)
    else:
        sessions = []

    session_details = []
    for session in sessions:
        session_detail = {
            "id": session.id,
            "batch_name": (
                session.coaching_session.batch.name if coach_id is None else None
            ),
            "project_name": session.coaching_session.batch.project.name,
            "project_id": (
                session.coaching_session.batch.project.id if coach_id is None else None
            ),
            "coach_name": session.availibility.coach.first_name
            + " "
            + session.availibility.coach.last_name,
            "coach_email": session.availibility.coach.email,
            "coach_phone": "+"
            + session.availibility.coach.phone_country_code
            + session.availibility.coach.phone,
            "participant_name": session.learner.name,
            "participant_email": session.learner.email,
            "participant_phone": session.learner.phone,
            "coaching_session_number": (
                session.coaching_session.coaching_session_number
                if coach_id is None
                else None
            ),
            "meeting_link": f"{env('CAAS_APP_URL')}/call/{session.availibility.coach.room_id}",
            "start_time": session.availibility.start_time,
            "room_id": f"{session.availibility.coach.room_id}",
            "status": session.status,
            "session_type": session.coaching_session.session_type,
            "end_time": session.availibility.end_time,
        }
        session_details.append(session_detail)
    return Response(session_details, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_session_status(request, session_id):
    try:
        session = SchedularSessions.objects.get(id=session_id)
    except SchedularSessions.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)
    new_status = request.data.get("status")
    if not new_status:
        return Response({"error": "Status is required."}, status=400)
    session.status = new_status
    session.save()
    return Response({"message": "Session status updated successfully."}, status=200)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_session_date_time(request, session_id):
    try:
        session = SchedularSessions.objects.get(id=session_id)
    except SchedularSessions.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)
    start_time = request.data.get("start_time")
    end_time = request.data.get("end_time")
    if not start_time or not end_time:
        return Response({"error": "Start or end time is not provided."}, status=400)
    session.availibility.start_time = start_time
    session.availibility.end_time = end_time
    session.availibility.save()
    return Response({"message": "Session time updated successfully."}, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_session(request, user_type, room_id, user_id):
    five_minutes_in_milliseconds = 300000
    current_time = int(timezone.now().timestamp() * 1000)
    five_minutes_plus_current_time = str(current_time + five_minutes_in_milliseconds)
    if user_type == "coach":
        sessions = SchedularSessions.objects.filter(
            availibility__start_time__lt=five_minutes_plus_current_time,
            availibility__end_time__gt=current_time,
            availibility__coach__id=user_id,
        )
    if len(sessions) == 0:
        return Response({"error": "You don't have any sessions right now."}, status=404)
    return Response({"message": "success"}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
def get_current_session_of_learner(request, room_id):
    five_minutes_in_milliseconds = 300000
    current_time = int(timezone.now().timestamp() * 1000)
    five_minutes_plus_current_time = str(current_time + five_minutes_in_milliseconds)
    participant_email = request.data.get("email", "")
    if participant_email:
        sessions = SchedularSessions.objects.filter(
            availibility__start_time__lt=five_minutes_plus_current_time,
            availibility__end_time__gt=current_time,
            learner__email=participant_email,
            availibility__coach__room_id=room_id,
        )
        if len(sessions) == 0:
            return Response(
                {"error": "You don't have any sessions right now."}, status=404
            )
        learner = Learner.objects.get(email=participant_email)
        return Response(
            {
                "message": "success",
                "name": learner.name,
                "email": learner.email,
            },
            status=200,
        )
    else:
        return Response({"error": "Please input your email"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_requests_of_coach(request, coach_id):
    try:
        coach = get_object_or_404(Coach, id=coach_id)
    except Coach.DoesNotExist:
        return Response({"error": "Coach not found"}, status=status.HTTP_404_NOT_FOUND)
    current_date = date.today()
    # Get New requests where coach ID is not in provided_by
    new_requests = RequestAvailibilty.objects.filter(
        coach=coach, expiry_date__gt=current_date
    ).exclude(provided_by__contains=coach_id)
    # Get Active requests where coach ID exists in provided_by
    active_requests = RequestAvailibilty.objects.filter(
        coach=coach, provided_by__contains=coach_id, expiry_date__gt=current_date
    )
    new_requests_serializer = RequestAvailibiltySerializerDepthOne(
        new_requests, many=True
    )
    active_requests_serializer = RequestAvailibiltySerializerDepthOne(
        active_requests, many=True
    )
    # Serialize and return the requests
    return Response(
        {
            "new": new_requests_serializer.data,
            "active": active_requests_serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_slots_of_request(request, request_id):
    coach_id = request.GET.get("coach_id")
    if coach_id:
        availabilities = CoachSchedularAvailibilty.objects.filter(
            request__id=request_id, coach__id=coach_id
        )
    else:
        availabilities = CoachSchedularAvailibilty.objects.filter(
            request__id=request_id
        )
    serializer = CoachSchedularAvailibiltySerializer(availabilities, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_slots_of_coach(request, coach_id):
    current_time = timezone.now()
    timestamp_milliseconds = str(int(current_time.timestamp() * 1000))
    availabilities = CoachSchedularAvailibilty.objects.filter(
        coach__id=coach_id, start_time__gt=timestamp_milliseconds
    )
    serializer = CoachSchedularAvailibiltySerializer(availabilities, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_slots(request):
    slot_ids = request.data.get("slot_ids", [])
    # Assuming slot_ids is a list of integers
    slots_to_delete = CoachSchedularAvailibilty.objects.filter(id__in=slot_ids)
    if not slots_to_delete.exists():
        return Response({"error": "No matching slots found."}, status=404)

    slots_to_delete.delete()
    return Response({"detail": "Slots deleted successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_unbooked_coaching_session_mail(request):
    try:
        celery_send_unbooked_coaching_session_mail.delay(request.data)

        return Response({"message": "Emails sent to participants."}, status.HTTP_200_OK)

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to send emails."}, status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_existing_slots_of_coach_on_request_dates(request, request_id, coach_id):
    try:
        request_availability = RequestAvailibilty.objects.get(id=request_id)
    except RequestAvailibilty.DoesNotExist:
        return Response(
            {"error": "Request availability not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    availability = request_availability.availability
    dates = list(availability.keys())
    coach_availabilities_date_wise = {}
    for date in dates:
        date_format = datetime.strptime(date, "%Y-%m-%d")
        start_date = datetime.combine(date_format, datetime.min.time())
        end_date = (
            datetime.combine(date_format, datetime.min.time())
            + timedelta(days=1)
            - timedelta(milliseconds=1)
        )
        start_timestamp = str(int(start_date.timestamp() * 1000))
        end_timestamp = str(int(end_date.timestamp() * 1000))
        coach_availabilities = CoachSchedularAvailibilty.objects.filter(
            coach__id=coach_id,
            start_time__gte=start_timestamp,
            end_time__lte=end_timestamp,
            is_confirmed=True,
        )
        coach_availabilities_date_wise[date] = CoachSchedularAvailibiltySerializer(
            coach_availabilities, many=True
        ).data

    return Response(
        {"coach_availabilities_date_wise": coach_availabilities_date_wise},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def export_available_slot(request):
    current_datetime = timezone.now()
    current_timestamp = int(
        current_datetime.timestamp() * 1000
    )  # Current date and time timestamp

    # Retrieve all InvoiceData objects with availabilities greater than the current timestamp
    queryset = CoachSchedularAvailibilty.objects.filter(
        start_time__gt=current_timestamp, is_confirmed=False
    )

    # Create a new workbook and add a worksheet
    wb = Workbook()
    ws = wb.active

    # Write headers to the worksheet
    headers = ["Coach Name", "Date", "Availability"]

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    # Write data to the worksheet
    for row_num, availabilities in enumerate(queryset, 2):
        start_time = datetime.fromtimestamp(
            (int(availabilities.start_time) / 1000) + 19800
        )
        end_time = datetime.fromtimestamp((int(availabilities.end_time) / 1000) + 19800)

        ws.append(
            [
                availabilities.coach.first_name + " " + availabilities.coach.last_name,
                start_time.strftime("%d %B %Y"),
                start_time.strftime("%I:%M %p") + " - " + end_time.strftime("%I:%M %p"),
            ]
        )

    # Create a response with the Excel file
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=Available Slot.xlsx"
    wb.save(response)

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_participant_to_batch(request, batch_id):
    # batch_id = request.data.get("batch_id")
    with transaction.atomic():
        name = request.data.get("name")
        email = request.data.get("email", "").strip().lower()
        phone = request.data.get("phone", None)
        try:
            batch = SchedularBatch.objects.get(id=batch_id)
        except SchedularBatch.DoesNotExist:
            return Response(
                {"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND
            )

        assessments = Assessment.objects.filter(
            assessment_modal__lesson__course__batch=batch
        )

        try:
            learner = Learner.objects.get(email=email)
            # Check if participant is already in the batch
            if learner in batch.learners.all():
                return Response(
                    {"error": "Participant already exists in the batch"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Learner.DoesNotExist:
            # Participant doesn't exist, create a new one
            learner = create_or_get_learner(
                {"name": name, "email": email, "phone": phone}
            )
        # Add the participant to the batch
        if learner:
            if assessments:
                for assessment in assessments:
                    if assessment.participants_observers.filter(
                        participant__email=learner.email
                    ).exists():
                        continue

                    unique_id = uuid.uuid4()

                    unique_id_instance = ParticipantUniqueId.objects.create(
                        participant=learner,
                        assessment=assessment,
                        unique_id=unique_id,
                    )

                    mapping = ParticipantObserverMapping.objects.create(
                        participant=learner
                    )

                    mapping.save()
                    assessment.participants_observers.add(mapping)
                    assessment.save()

            batch.learners.add(learner)
            batch.save()
            name = learner.name
            if learner.phone:
                add_contact_in_wati("learner", name, learner.phone)
            try:
                course = Course.objects.get(batch=batch)
                course_enrollments = CourseEnrollment.objects.filter(
                    learner=learner, course=course
                )
                if not course_enrollments.exists():
                    datetime = timezone.now()
                    CourseEnrollment.objects.create(
                        learner=learner,
                        course=course,
                        enrollment_date=datetime,
                    )
            except Exception:
                # course doesnt exists
                pass

            return Response(
                {"message": "Participant added to the batch successfully"},
                status=status.HTTP_201_CREATED,
            )
    return Response(
        {"error": "Failed to add participants."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def finalize_project_structure(request, project_id):
    try:
        project = get_object_or_404(SchedularProject, id=project_id)
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
        )
    # Update is_project_structure_finalized to True
    project.is_project_structure_finalized = True
    project.save()
    return Response(
        {"message": "Project structure finalized successfully"},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_live_session_link(request):
    live_session = LiveSession.objects.get(id=request.data.get("live_session_id"))
    for learner in live_session.batch.learners.all():
        # Only send email if project status is ongoing
        if live_session.batch.project.status == "ongoing":
            send_mail_templates(
                "send_live_session_link.html",
                [learner.email],
                "Meeraq - Live Session",
                {
                    "participant_name": learner.name,
                    "live_session_name": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                    "project_name": live_session.batch.project.name,
                    "description": (
                        live_session.description if live_session.description else ""
                    ),
                    "meeting_link": live_session.meeting_link,
                },
                [],
            )
            sleep(4)
    return Response({"message": "Emails sent successfully"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_live_session_link_whatsapp(request):
    live_session = LiveSession.objects.get(id=request.data.get("live_session_id"))
    for learner in live_session.batch.learners.all():
        # Only send email or whatsapp if project status is ongoing
        if live_session.batch.project.status == "ongoing":
            send_whatsapp_message_template(
                learner.phone,
                {
                    "broadcast_name": "Instant_live_session_whatsapp_reminder",
                    "parameters": [
                        {
                            "name": "name",
                            "value": learner.name,
                        },
                        {
                            "name": "live_session_name",
                            "value": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                        },
                        {
                            "name": "project_name",
                            "value": live_session.batch.project.name,
                        },
                        {
                            "name": "description",
                            "value": (
                                (
                                    live_session.description
                                    if live_session.description
                                    else ""
                                )
                                + (
                                    f" Please join using this link: {live_session.meeting_link}"
                                    if live_session.meeting_link
                                    else ""
                                )
                            ),
                        },
                    ],
                    "template_name": "instant_whatsapp_live_session",
                },
            )

    return Response({"message": "Message sent successfully"})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_session_status(request, session_id):
    status = request.data.get("status")
    if not session_id or not status:
        return Response(
            {"error": "Failed to update status"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        session = get_object_or_404(SchedularSessions, id=session_id)
    except SchedularSessions.DoesNotExist:
        return Response(
            {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
        )
    # Update the session status
    session.status = status
    session.save()
    return Response({"message": "Session status updated successfully"}, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def project_batch_wise_report_download(request, project_id, session_to_download):
    project = get_object_or_404(SchedularProject, pk=project_id)
    batches = SchedularBatch.objects.filter(project=project)
    # Create a Pandas DataFrame for each batch
    dfs = []
    for batch in batches:
        data = {
            "Session name": [],
            "Attendance": [],
            "Total Participants": [],
            "Percentage": [],
            "Date": [],
        }
        if session_to_download == "both":
            live_sessions = LiveSession.objects.filter(batch=batch)
            coaching_sessions = CoachingSession.objects.filter(batch=batch)
            sessions = list(live_sessions) + list(coaching_sessions)
        elif session_to_download == "live":
            live_sessions = LiveSession.objects.filter(batch=batch)
            sessions = list(live_sessions)
        elif session_to_download == "coaching":
            coaching_sessions = CoachingSession.objects.filter(batch=batch)
            sessions = list(coaching_sessions)

        sorted_sessions = sorted(sessions, key=lambda x: x.order)
        for session in sorted_sessions:
            if isinstance(session, LiveSession):
                session_name = f"{get_live_session_name(session.session_type)} {session.live_session_number}"
                attendance = len(session.attendees)
                if session.date_time:
                    adjusted_date_time = session.date_time + timedelta(
                        hours=5, minutes=30
                    )
                    date = adjusted_date_time.strftime("%d-%m-%Y %I:%M %p") + " IST"
                else:
                    date = "Not added"
            elif isinstance(session, CoachingSession):
                if session.session_type == "laser_coaching_session":
                    session_type_name = "Laser Coaching Session"
                else:
                    session_type_name = "Mentoring Session"
                session_name = f"{session_type_name} {session.coaching_session_number}"
                attendance = SchedularSessions.objects.filter(
                    coaching_session=session, status="completed"
                ).count()
                date = ""
            else:
                session_name = "Unknown Session"
                attendance = ""
                date = ""
            total_participants = batch.learners.count()
            percentage = None
            if not total_participants:
                percentage = "0%"
            else:
                percentage = str(int((attendance / total_participants) * 100)) + " %"
            data["Session name"].append(session_name)
            data["Attendance"].append(attendance)
            data["Total Participants"].append(total_participants)
            data["Percentage"].append(percentage)
            data["Date"].append(date)

        df = pd.DataFrame(data)
        dfs.append((batch.name, df))

    # Create an Excel file with multiple sheets
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = (
        f'attachment; filename="{project.name}_batches.xlsx"'
    )

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        for batch_name, df in dfs:
            df.to_excel(writer, sheet_name=batch_name, index=False)

    return response


@api_view(["GET"])
@permission_classes([AllowAny])
def project_report_download_live_session_wise(request, project_id, batch_id):
    try:
        sessions = None
        if batch_id == "all":
            sessions = LiveSession.objects.filter(batch__project__id=project_id)
        else:
            sessions = LiveSession.objects.filter(batch__id=int(batch_id))

        dfs = {}

        for session in sessions:
            session_key = f"{get_live_session_name(session.session_type)} {session.live_session_number}"
            if session_key not in dfs:
                dfs[session_key] = []

            for learner in session.batch.learners.all():

                participant_name = learner.name
                data = {
                    "Participant name": participant_name,
                    "Batch name": session.batch.name,
                    "Attended": "Yes" if learner.id in session.attendees else "No",
                }

                dfs[session_key].append(data)

        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = 'attachment; filename="batches.xlsx"'

        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            for session_name, df in dfs.items():
                pd.DataFrame(df).to_excel(writer, sheet_name=session_name, index=False)

        return response

    except Exception as e:
        print(str(e))


@api_view(["GET"])
@permission_classes([AllowAny])
def project_report_download_coaching_session_wise(request, project_id, batch_id):
    try:
        sessions = None
        if batch_id == "all":
            sessions = CoachingSession.objects.filter(batch__project__id=project_id)
        else:
            sessions = CoachingSession.objects.filter(batch__id=int(batch_id))

        dfs = {}

        sessions = CoachingSession.objects.filter(batch__project__id=project_id)

        for session in sessions:
            session_name = None
            if session.session_type == "laser_coaching_session":
                session_name = "Laser coaching"
            elif session.session_type == "mentoring_session":
                session_name = "Mentoring session"
            session_key = f"{session_name} {session.coaching_session_number}"
            if session_key not in dfs:
                dfs[session_key] = []

            for learner in session.batch.learners.all():
                session_exist = SchedularSessions.objects.filter(
                    coaching_session=session, learner=learner
                ).first()

                participant_name = learner.name

                if session_exist:
                    attendance = "YES" if session_exist.status == "completed" else "NO"
                    data = {
                        "Participant name": participant_name,
                        "Batch name": session.batch.name,
                        "Completed": attendance,
                    }
                else:
                    data = {
                        "Participant name": participant_name,
                        "Batch name": session.batch.name,
                        "Completed": "Not Scheduled",
                    }
                dfs[session_key].append(data)

        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = 'attachment; filename="batches.xlsx"'

        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            for session_name, df in dfs.items():
                pd.DataFrame(df).to_excel(writer, sheet_name=session_name, index=False)

        return response

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "An error occurred "},
            status=500,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_facilitator(request):
    first_name = request.data.get("first_name", "")
    last_name = request.data.get("last_name", "")
    email = request.data.get("email", "").strip().lower()
    age = request.data.get("age")
    gender = request.data.get("gender", "")
    domain = json.loads(request.data["domain"])
    phone_country_code = request.data.get("phone_country_code", "")
    phone = request.data.get("phone", "")
    level = json.loads(request.data["level"])
    rating = request.data.get("rating", "")
    area_of_expertise = json.loads(request.data["area_of_expertise"])
    profile_pic = request.data.get("profile_pic", None)
    education = json.loads(request.data["education"])
    years_of_corporate_experience = request.data.get(
        "years_of_corporate_experience", ""
    )
    language = json.loads(request.data["language"])
    job_roles = json.loads(request.data["job_roles"])
    city = json.loads(request.data["city"])
    country = json.loads(request.data["country"])
    linkedin_profile_link = request.data.get("linkedin_profile_link", "")
    companies_worked_in = json.loads(request.data["companies_worked_in"])
    other_certification = json.loads(request.data["other_certification"])
    currency = request.data.get("currency", "")
    client_companies = json.loads(request.data["client_companies"])
    educational_qualification = json.loads(request.data["educational_qualification"])
    fees_per_hour = request.data.get("fees_per_hour", "")
    fees_per_day = request.data.get("fees_per_day", "")
    topic = json.loads(request.data["topic"])
    corporate_experience = request.data.get("corporate_experience", "")
    coaching_experience = request.data.get("coaching_experience", "")
    education_pic = request.data.get("education_pic", None)
    # education_upload_file = request.data.get("education_upload_file", None)
    username = email
    # Check if required data is provided
    if not all(
        [
            first_name,
            last_name,
            email,
            gender,
            phone,
            phone_country_code,
            level,
            username,
        ]
    ):
        return Response({"error": "All required fields must be provided."}, status=400)

    try:
        with transaction.atomic():
            # Check if the user already exists
            user = User.objects.filter(email=email).first()

            if not user:
                # If the user does not exist, create a new user
                temp_password = "".join(
                    random.choices(
                        string.ascii_uppercase + string.ascii_lowercase + string.digits,
                        k=8,
                    )
                )
                user = User.objects.create_user(
                    username=username, password=temp_password, email=email
                )
                profile = Profile.objects.create(user=user)
            else:
                profile = Profile.objects.get(user=user)

            facilitator_role, created = Role.objects.get_or_create(name="facilitator")
            # Create the Profile linked to the User
            profile.roles.add(facilitator_role)
            profile.save()

            # Create the Coach User using the Profile
            facilitator_user = Facilitator.objects.create(
                user=profile,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                city=city,
                country=country,
                phone_country_code=phone_country_code,
                level=level,
                currency=currency,
                education=education,
                rating=rating,
                area_of_expertise=area_of_expertise,
                age=age,
                gender=gender,
                domain=domain,
                years_of_corporate_experience=years_of_corporate_experience,
                profile_pic=profile_pic,
                language=language,
                job_roles=job_roles,
                fees_per_hour=fees_per_hour,
                fees_per_day=fees_per_day,
                topic=topic,
                linkedin_profile_link=linkedin_profile_link,
                companies_worked_in=companies_worked_in,
                other_certification=other_certification,
                client_companies=client_companies,
                educational_qualification=educational_qualification,
                corporate_experience=corporate_experience,
                coaching_experience=coaching_experience,
                education_pic=education_pic,
                is_approved=True,
                # education_upload_file=education_upload_file,
            )

            # Approve coach
            facilitator_user.is_approved = True
            facilitator_user.save()

            # Send email notification to the coach
            full_name = facilitator_user.first_name + " " + facilitator_user.last_name
            microsoft_auth_url = (
                f'{env("BACKEND_URL")}/api/microsoft/oauth/{facilitator_user.email}/'
            )
            user_token_present = False
            try:
                user_token = UserToken.objects.get(
                    user_profile__user__username=facilitator_user.email
                )
                if user_token:
                    user_token_present = True
            except Exception as e:
                print(str(e))
                pass
            # send_mail_templates(
            #     "coach_templates/pmo-adds-coach-as-user.html",
            #     [facilitator_user.email],
            #     "Meeraq Coaching | New Beginning !",
            #     {
            #         "name": facilitator_user.first_name,
            #         "email": facilitator_user.email,
            #         "microsoft_auth_url": microsoft_auth_url,
            #         "user_token_present": user_token_present,
            #     },
            #     [],  # no bcc emails
            # )

        return Response({"message": "Facilitator added successfully."}, status=201)

    except IntegrityError as e:
        print(str(e))
        return Response(
            {"error": "A facilitator user with this email already exists."}, status=400
        )

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "An error occurred while creating the facilitator user."},
            status=500,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_facilitators(request):
    try:
        # Get all the Coach objects
        facilitators = Facilitator.objects.filter(is_approved=True)

        # Serialize the Coach objects
        serializer = FacilitatorSerializer(facilitators, many=True)

        # Return the serialized Coach objects as the response
        return Response(serializer.data, status=200)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


# @api_view(["POST"])
# def add_multiple_facilitator(request):
#     data = request.data.get("coaches", [])
#     facilitators = []
#     for coach_data in data:
#         email = coach_data["email"]

#         if Facilitator.objects.filter(email=email).exists():
#             return Response(
#                 {"message": f"Facilitator with email {email} already exists"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         facilitator = Facilitator(
#             first_name=coach_data["first_name"],
#             last_name=coach_data["last_name"],
#             email=email,
#             age=coach_data["age"],
#             gender=coach_data["gender"],
#             domain=coach_data.get("functional_domain", []),
#             phone=coach_data["mobile"],
#             level=coach_data.get("level", []),
#             rating=coach_data.get("rating", ""),
#             area_of_expertise=coach_data.get("industries", []),
#             education=coach_data.get("education", []),
#             years_of_corporate_experience=coach_data.get("corporate_yoe", ""),
#             city=coach_data.get("city", []),
#             language=coach_data.get("language", []),
#             job_roles=coach_data.get("job_roles", []),
#             country=coach_data.get("country", []),
#             linkedin_profile_link=coach_data.get("linkedin_profile", ""),
#             companies_worked_in=coach_data.get("companies_worked_in", []),
#             educational_qualification=coach_data.get("educational_qualification", []),
#             client_companies=coach_data.get("client_companies", []),
#             fees_per_hour=coach_data.get("fees_per_hour", ""),
#             fees_per_day=coach_data.get("fees_per_day", ""),
#             topic=coach_data.get("topic", []),
#             other_certification=coach_data.get("other_certification", []),
#         )
#         facilitators.append(facilitator)

#     Facilitator.objects.bulk_create(
#         facilitators
#     )  # Bulk create facilitators in the database

#     return Response(
#         {"message": "Facilitators added successfully"}, status=status.HTTP_201_CREATED
#     )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_multiple_facilitator(request):
    data = request.data.get("coaches", [])
    print(data)
    facilitators = []
    try:
        for facilitator_data in data:
            email = facilitator_data["email"]

            if Facilitator.objects.filter(email=email).exists():
                return Response(
                    {"message": f"Facilitator with email {email} already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                # Create Django User
                user, created = User.objects.get_or_create(username=email, email=email)
                if created:
                    temp_password = "".join(
                        random.choices(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits,
                            k=8,
                        )
                    )
                    user.set_password(temp_password)
                    user.save()

                    profile = Profile.objects.create(user=user)
                else:
                    profile = Profile.objects.get(user=user)

                facilitator_role, created = Role.objects.get_or_create(
                    name="facilitator"
                )
                profile.roles.add(facilitator_role)
                profile.save()

                facilitator = Facilitator(
                    user=profile,
                    first_name=facilitator_data["first_name"],
                    last_name=facilitator_data["last_name"],
                    email=email,
                    age=facilitator_data.get("age", ""),
                    gender=facilitator_data.get("gender", ""),
                    domain=facilitator_data.get("functional_domain", []),
                    phone=facilitator_data.get("mobile", ""),
                    level=facilitator_data.get("level", []),
                    rating=facilitator_data.get("rating", ""),
                    area_of_expertise=facilitator_data.get("industries", []),
                    education=facilitator_data.get("education", []),
                    years_of_corporate_experience=facilitator_data.get(
                        "corporate_yoe", ""
                    ),
                    city=facilitator_data.get("city", []),
                    language=facilitator_data.get("language", []),
                    job_roles=facilitator_data.get("job_roles", []),
                    country=facilitator_data.get("country", []),
                    linkedin_profile_link=facilitator_data.get("linkedin_profile", ""),
                    companies_worked_in=facilitator_data.get("companies_worked_in", []),
                    educational_qualification=facilitator_data.get(
                        "educational_qualification", []
                    ),
                    client_companies=facilitator_data.get("client_companies", []),
                    fees_per_hour=facilitator_data.get("fees_per_hour", ""),
                    fees_per_day=facilitator_data.get("fees_per_day", ""),
                    topic=facilitator_data.get("topic", []),
                    other_certification=facilitator_data.get("other_certification", []),
                    is_approved=True,
                )
                facilitators.append(facilitator)

        Facilitator.objects.bulk_create(
            facilitators
        )  # Bulk create facilitators in the database

        return Response(
            {"message": "Facilitators added successfully"},
            status=status.HTTP_201_CREATED,
        )

    except KeyError as e:
        return Response(
            {"error": f"Missing key in facilitator data: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        print(e)
        return Response(
            {"error": "An error occurred while creating the facilitators."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_facilitator_profile(request, id):
    try:
        with transaction.atomic():
            facilitator = Facilitator.objects.get(id=id)
            user = facilitator.user.user
            new_email = request.data.get("email", "").strip().lower()
            #  other user exists with the new email
            if (
                new_email
                and User.objects.filter(username=new_email).exclude(id=user.id).exists()
            ):
                return Response(
                    {"error": "Email already exists. Please choose a different email."},
                    status=400,
                )

            # no other user exists with the new email
            elif new_email and new_email != user.username:
                user.email = new_email
                user.username = new_email
                user.save()

                # updating emails in all user's
                for role in user.profile.roles.all():
                    if role.name == "pmo":
                        pmo = Pmo.objects.get(user=user.profile)
                        pmo.email = new_email
                        pmo.save()
                    if role.name == "hr":
                        hr = HR.objects.get(user=user.profile)
                        hr.email = new_email
                        hr.save()
                    if role.name == "learner":
                        learner = Learner.objects.get(user=user.profile)
                        learner.email = new_email
                        learner.save()
                    if role.name == "vendor":
                        vendor = Vendor.objects.get(user=user.profile)
                        vendor.email = new_email
                        vendor.save()
                    if role.name == "coach":

                        coach = Coach.objects.get(user=user.profile)
                        coach.email = new_email

                        coach.save()

            serializer = FacilitatorSerializer(
                facilitator, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                roles = []
                for role in user.profile.roles.all():
                    roles.append(role.name)
                serializer = FacilitatorDepthOneSerializer(user.profile.facilitator)
                return Response(
                    {
                        **serializer.data,
                        "roles": roles,
                        "user": {**serializer.data["user"], "type": "facilitator"},
                    }
                )
                # user_data = get_user_data(facilitator.user.user)
                # return Response(user_data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to update details."}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_facilitator(request):
    data = request.data
    facilitator_id = data.get("facilitator_id")

    if facilitator_id is None:
        return Response(
            {"error": "Facilitator ID is missing in the request data"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        facilitator = Facilitator.objects.get(pk=facilitator_id)
    except Facilitator.DoesNotExist:
        return Response(
            {"error": "Facilitator not found"}, status=status.HTTP_404_NOT_FOUND
        )

    facilitator.delete()
    return Response(
        {"message": "Facilitator deleted successfully"},
        status=200,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_facilitator_field_values(request):
    job_roles = set()
    languages = set()
    companies_worked_in = set()
    other_certifications = set()
    industries = set()
    functional_domain = set()
    institute = set()
    city = set()
    country = set()
    topic = set()
    client_companies = set()
    education_qualifications = set()
    for coach in Facilitator.objects.all():
        # 1st coach
        for role in coach.job_roles:
            job_roles.add(role)
        for language in coach.language:
            languages.add(language)
        for company in coach.companies_worked_in:
            companies_worked_in.add(company)
        for certificate in coach.other_certification:
            other_certifications.add(certificate)
        for industry in coach.area_of_expertise:
            industries.add(industry)
        for functional_dom in coach.domain:
            functional_domain.add(functional_dom)
        for edu in coach.education:
            institute.add(edu)
        for cities in coach.city:
            city.add(cities)
        for client_company in coach.client_companies:
            client_companies.add(client_company)
        for countries in coach.country:
            country.add(countries)
        for topics in coach.topic:
            topic.add(topics)
        for qualifications in coach.educational_qualification:
            education_qualifications.add(qualifications)

        # domains.add(coach.domain)
        # educations.add(coach.education)
    return Response(
        {
            "job_roles": list(job_roles),
            "languages": list(languages),
            "educations": list(institute),
            "companies_worked_in": list(companies_worked_in),
            "other_certifications": list(other_certifications),
            "domains": list(functional_domain),
            "industries": list(industries),
            "city": list(city),
            "country": list(country),
            "client_companies": list(client_companies),
            "topic": list(topic),
            "educational_qualifications": list(education_qualifications),
        },
        status=200,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_learner_from_course(request):
    learner_id = request.data.get("learnerId")
    batch_id = request.data.get("batchId")

    try:
        learner = Learner.objects.get(id=learner_id)
        batch = SchedularBatch.objects.get(id=batch_id)

        if learner in batch.learners.all():
            batch.learners.remove(learner)
            # Remove the learner from FeedbackLessonResponse if present
            feedback_responses = FeedbackLessonResponse.objects.filter(
                learner=learner, feedback_lesson__lesson__course__batch=batch
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

            if assessment:
                deleted = delete_participant_from_assessments(
                    assessment, learner.id, assessment.id
                )
                if deleted:
                    return Response(
                        {
                            "message": f"Coachee removed from batch and assessments successfully."
                        }
                    )
            return Response({"message": f"Coachee removed from batch successfully."})
        else:
            return Response({"message": f"Coachee is not part of batch."}, status=400)

    except ObjectDoesNotExist:
        return Response({"message": "Object not found."}, status=404)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_schedular_project(request, project_id):
    try:
        project = SchedularProject.objects.get(pk=project_id)
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
        )
    junior_pmo = None
    if "junior_pmo" in request.data:
        junior_pmo = Pmo.objects.filter(id=request.data["junior_pmo"]).first()
    # Assuming 'request.data' contains the updated project information
    project_name = request.data.get("project_name")
    organisation_id = request.data.get("organisation_id")
    hr_ids = request.data.get("hr", [])
    if project_name:
        project.name = project_name
    if organisation_id:
        try:
            organisation = Organisation.objects.get(pk=organisation_id)
            project.organisation = organisation

        except Organisation.DoesNotExist:
            return Response(
                {"error": "Organisation not found"}, status=status.HTTP_404_NOT_FOUND
            )
    # Clear existing HR associations and add the provided ones
    project.hr.clear()
    for hr_id in hr_ids:
        try:
            hr = HR.objects.get(pk=hr_id)
            project.hr.add(hr)
        except HR.DoesNotExist:
            return Response(
                {"error": f"HR with ID {hr_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    project.email_reminder = request.data.get("email_reminder")
    project.whatsapp_reminder = request.data.get("whatsapp_reminder")
    project.calendar_invites = request.data.get("calendar_invites")
    project.nudges = request.data.get("nudges")
    project.pre_post_assessment = request.data.get("pre_post_assessment")
    project.is_finance_enabled = request.data.get("finance")
    project.junior_pmo = junior_pmo
    project.save()
    if not project.pre_post_assessment:
        batches = SchedularBatch.objects.filter(project=project)
        if batches:
            for batch in batches:
                course = Course.objects.filter(batch=batch).first()
                if course:
                    lessons = Lesson.objects.filter(course=course)
                    for lesson in lessons:
                        if lesson.lesson_type == "assessment":
                            lesson.status = "draft"
                            lesson.save()
    return Response(
        {"message": "Project updated successfully"}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_schedular_project_update(request, project_id):
    try:
        project = SchedularProject.objects.get(id=project_id)
    except SchedularProject.DoesNotExist:
        return Response({"error": "Project not found"}, status=404)
    # Assuming your request data has a "message" field for the update message
    update_data = {
        "pmo": request.data.get(
            "pmo", ""
        ),  # Assuming the PMO is associated with the user
        "project": project.id,
        "message": request.data.get("message", ""),
    }
    serializer = UpdateSerializer(data=update_data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Update added to project successfully!"}, status=201
        )
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_schedular_project_updates(request, project_id):
    updates = SchedularUpdate.objects.filter(project__id=project_id).order_by(
        "-created_at"
    )
    serializer = SchedularUpdateDepthOneSerializer(updates, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_live_sessions_by_status(request):
    status = request.query_params.get("status", None)
    now = timezone.now()
    if status == "upcoming":
        queryset = LiveSession.objects.filter(date_time__gt=now).order_by("date_time")
    elif status == "past":
        queryset = LiveSession.objects.filter(date_time__lt=now).order_by("-date_time")
    elif status == "unscheduled":
        queryset = LiveSession.objects.filter(date_time__isnull=True).order_by(
            "created_at"
        )

    else:
        queryset = LiveSession.objects.all()

    pmo_id = request.query_params.get("pmo", None)

    if pmo_id:
        pmo = Pmo.objects.get(id=int(pmo_id))
        if pmo.sub_role == "junior_pmo":
            queryset = queryset.filter(batch__project__junior_pmo=pmo)
        else:
            queryset = LiveSession.objects.all()
    hr_id = request.query_params.get("hr", None)
    if hr_id:
        queryset = queryset.filter(batch__project__hr__id=hr_id)

    facilitator_id = request.query_params.get("facilitator_id", None)
    if facilitator_id:
        batches = SchedularBatch.objects.filter(
            livesession__facilitator__id=facilitator_id
        )
        queryset = queryset.filter(batch__in=batches)

    res = []
    for live_session in queryset:
        session_name = get_live_session_name(live_session.session_type)
        res.append(
            {
                "id": live_session.id,
                "name": f"{session_name} {live_session.live_session_number}",
                "organization": live_session.batch.project.organisation.name,
                "batch_name": live_session.batch.name,
                "batch_id": live_session.batch.id,
                "project_name": live_session.batch.project.name,
                "project_id": live_session.batch.project.id,
                "date_time": live_session.date_time,
                "description": live_session.description,
                "meeting_link": live_session.meeting_link,
                "attendees": len(live_session.attendees),
                "total_learners": live_session.batch.learners.count(),
            }
        )
    return Response(res)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def live_session_detail_view(request, pk):
    try:
        live_session = LiveSession.objects.get(pk=pk)
    except LiveSession.DoesNotExist:
        return Response({"error": "LiveSession not found"}, status=404)

    participants = Learner.objects.filter(schedularbatch__id=live_session.batch.id)
    participants_serializer = LearnerSerializer(participants, many=True)
    live_session_serializer = LiveSessionSerializerDepthOne(live_session)

    response_data = {
        "live_session": live_session_serializer.data,
        "participants": participants_serializer.data,
    }

    return Response(response_data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def facilitator_projects(request, facilitator_id):
    try:
        projects = SchedularProject.objects.filter(
            schedularbatch__livesession__facilitator__id=facilitator_id
        ).distinct()
        serializer = SchedularProjectSerializer(projects, many=True)
        return Response(serializer.data)
    except Facilitator.DoesNotExist:
        return Response({"message": "Facilitator does not exist"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_facilitator_sessions(request, facilitator_id):
    try:
        facilitator = Facilitator.objects.get(id=facilitator_id)
        batches = SchedularBatch.objects.filter(facilitator=facilitator)

        serialized_data = []

        for batch in batches:
            batch_data = {
                "batch_name": batch.name,
                "project_name": batch.project.name if batch.project else None,
                "organisation_name": (
                    batch.project.organisation.name
                    if (batch.project and batch.project.organisation)
                    else None
                ),
                "live_sessions": [],
            }

            # Fetch all live sessions related to the batch and serialize
            live_sessions = LiveSession.objects.filter(batch=batch)
            serialized_live_sessions = LiveSessionSerializer(
                live_sessions, many=True
            ).data

            for session in serialized_live_sessions:
                live_session_data = {
                    "date_time": session.get("date_time"),
                    "meeting_link": session.get("meeting_link"),
                }
                batch_data["live_sessions"].append(live_session_data)

            serialized_data.append(batch_data)

        return Response(serialized_data)

    except Facilitator.DoesNotExist:
        return Response({"message": "Facilitator not found"}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_certificate_status(request):
    try:
        participant_id = request.data.get("participantId")
        is_certificate_allowed = request.data.get("is_certificate_allowed")
        course_id = request.data.get("courseId")

        # Use filter instead of get to handle multiple instances
        course_enrollments = CourseEnrollment.objects.filter(
            learner__id=participant_id, course__id=course_id
        )

        # If there are multiple instances, you need to decide which one to update
        # For example, you might want to update the first one:
        if course_enrollments.exists():
            course_for_that_participant = course_enrollments.first()
            course_for_that_participant.is_certificate_allowed = is_certificate_allowed
            course_for_that_participant.save()
            return JsonResponse(
                {"message": "Certificate status updated successfully"}, status=200
            )
        else:
            return JsonResponse(
                {"error": "No Course Enrolled in this Batch"}, status=404
            )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_new_session_in_project_structure(request):
    try:
        with transaction.atomic():
            project_id = request.data.get("project_id")
            session_type = request.data.get("session_type")
            duration = request.data.get("duration")
            description = request.data.get("description")
            price = request.data.get("price")
            # Get the project and batches
            project = get_object_or_404(SchedularProject, id=project_id)
            batches = SchedularBatch.objects.filter(project=project)

            # Get the previous structure
            prev_structure = project.project_structure

            # Create a new session object
            new_session = {
                "order": len(prev_structure) + 1,
                "duration": duration,
                "session_type": session_type,
                "description": description,
                "price": price,
            }

            # Update the project structure
            prev_structure.append(new_session)
            project.project_structure = prev_structure
            project.save()

            # Update the sessions for each batch
            for batch in batches:
                course = Course.objects.filter(batch=batch).first()
                if session_type in [
                    "live_session",
                    "check_in_session",
                    "in_person_session",
                    "kickoff_session",
                    "virtual_session",
                ]:
                    session_number = (
                        LiveSession.objects.filter(
                            batch=batch, session_type=session_type
                        ).count()
                        + 1
                    )
                    live_session = LiveSession.objects.create(
                        batch=batch,
                        live_session_number=session_number,
                        order=new_session["order"],
                        duration=new_session["duration"],
                        session_type=session_type,
                    )
                    if course:
                        max_order = (
                            Lesson.objects.filter(course=course).aggregate(
                                Max("order")
                            )["order__max"]
                            or 0
                        )
                        session_name = None
                        if live_session.session_type == "live_session":
                            session_name = "Live Session"
                        elif live_session.session_type == "check_in_session":
                            session_name = "Check In Session"
                        elif live_session.session_type == "in_person_session":
                            session_name = "In Person Session"
                        elif live_session.session_type == "kickoff_session":
                            session_name = "Kickoff Session"
                        elif live_session.session_type == "virtual_session":
                            session_name = "Virtual Session"
                        new_lesson = Lesson.objects.create(
                            course=course,
                            name=f"{session_name} {live_session.live_session_number}",
                            status="draft",
                            lesson_type="live_session",
                            order=max_order,
                        )
                        LiveSessionLesson.objects.create(
                            lesson=new_lesson, live_session=live_session
                        )
                        max_order_feedback = (
                            Lesson.objects.filter(course=course).aggregate(
                                Max("order")
                            )["order__max"]
                            or 0
                        )

                        new_feedback_lesson = Lesson.objects.create(
                            course=course,
                            name=f"Feedback for {session_name} {live_session.live_session_number}",
                            status="draft",
                            lesson_type="feedback",
                            order=max_order_feedback,
                        )
                        unique_id = uuid.uuid4()
                        feedback_lesson = FeedbackLesson.objects.create(
                            lesson=new_feedback_lesson,
                            unique_id=unique_id,
                            live_session=live_session,
                        )
                        if live_session.session_type in [
                            "in_person_session",
                            "virtual_session",
                        ]:
                            add_question_to_feedback_lesson(
                                feedback_lesson, nps_default_feed_questions
                            )
                elif session_type in ["laser_coaching_session", "mentoring_session"]:
                    coaching_session_number = (
                        CoachingSession.objects.filter(
                            batch=batch, session_type=session_type
                        ).count()
                        + 1
                    )

                    booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{str(uuid.uuid4())}"  # Generate a unique UUID for the booking link
                    coaching_session = CoachingSession.objects.create(
                        batch=batch,
                        coaching_session_number=coaching_session_number,
                        order=new_session["order"],
                        duration=new_session["duration"],
                        booking_link=booking_link,
                        session_type=session_type,
                    )
                    if course:
                        max_order = (
                            Lesson.objects.filter(course=course).aggregate(
                                Max("order")
                            )["order__max"]
                            or 0
                        )
                        max_order = max_order + 1
                        session_name = None
                        if coaching_session.session_type == "laser_coaching_session":
                            session_name = "Laser coaching"
                        elif coaching_session.session_type == "mentoring_session":
                            session_name = "Mentoring session"
                        new_lesson = Lesson.objects.create(
                            course=course,
                            name=f"{session_name} {coaching_session.coaching_session_number}",
                            status="draft",
                            lesson_type="laser_coaching",
                            order=max_order,
                        )
                        LaserCoachingSession.objects.create(
                            lesson=new_lesson, coaching_session=coaching_session
                        )

            return Response({"message": "Session added successfully."}, status=200)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to add session"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_completed_sessions_for_project(request, project_id):
    try:
        current_datetime = timezone.now()

        # Get all LiveSessions where date_time is in the past
        complete_live_sessions = LiveSession.objects.filter(
            batch__project__id=project_id, date_time__lt=current_datetime
        )

        # Get all CoachingSessions where end_date is in the past
        complete_coaching_sessions = CoachingSession.objects.filter(
            batch__project__id=project_id, end_date__lt=current_datetime
        )

        # Convert LiveSession objects to dictionaries
        live_session_data = [
            {
                "id": session.id,
                "live_session_number": session.live_session_number,
                "order": session.order,
                "date_time": session.date_time,
                "attendees": session.attendees,
                "description": session.description,
                "status": session.status,
                "duration": session.duration,
                "pt_30_min_before": session.pt_30_min_before_id,
                "session_type": session.session_type,
            }
            for session in complete_live_sessions
        ]

        # Convert CoachingSession objects to dictionaries
        coaching_session_data = [
            {
                "id": session.id,
                "booking_link": session.booking_link,
                "start_date": session.start_date,
                "end_date": session.end_date,
                "expiry_date": session.expiry_date,
                "batch_id": session.batch_id,
                "coaching_session_number": session.coaching_session_number,
                "order": session.order,
                "duration": session.duration,
                "session_type": session.session_type,
            }
            for session in complete_coaching_sessions
        ]

        # Combine both lists into a single list
        complete_sessions = live_session_data + coaching_session_data

        return Response(complete_sessions, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_session_from_project_structure(request):
    try:
        with transaction.atomic():
            project_id = request.data.get("project_id")
            session_to_delete = request.data.get("session_to_delete")

            project = SchedularProject.objects.get(id=project_id)
            batches = SchedularBatch.objects.filter(project=project)

            order = session_to_delete.get("order")
            session_type = session_to_delete.get("session_type")

            project_structure = project.project_structure
            if session_to_delete in project_structure:
                project_structure.remove(session_to_delete)
                project.project_structure = project_structure
                project.save()

                for session in project_structure:
                    if session.get("order") > order:
                        session["order"] -= 1
                project.project_structure = project_structure
                project.save()

            for batch in batches:
                course = Course.objects.filter(batch=batch).first()

                if session_type in [
                    "live_session",
                    "check_in_session",
                    "in_person_session",
                    "kickoff_session",
                    "virtual_session",
                ]:
                    live_session = LiveSession.objects.filter(
                        batch=batch, order=order, session_type=session_type
                    ).first()
                    if live_session:
                        live_session_lesson = LiveSessionLesson.objects.filter(
                            live_session=live_session
                        ).first()
                        if live_session_lesson:
                            feedback_lesson_name = f"feedback_for_{session_type}_{live_session_lesson.live_session.live_session_number}"
                            feedback_lessons = FeedbackLesson.objects.filter(
                                lesson__course=course,
                            )

                            for feedback_lesson in feedback_lessons:
                                if feedback_lesson:
                                    current_lesson_name = feedback_lesson.lesson.name
                                    formatted_lesson_name = get_feedback_lesson_name(
                                        current_lesson_name
                                    )

                                    if formatted_lesson_name == feedback_lesson_name:
                                        feedback_lesson_lesson = feedback_lesson.lesson
                                        feedback_lesson_lesson.delete()
                                        feedback_lesson.delete()
                            lesson = live_session_lesson.lesson
                            lesson.delete()
                        live_session.delete()

                elif session_type in ["laser_coaching_session", "mentoring_session"]:
                    coaching_session = CoachingSession.objects.filter(
                        batch=batch, order=order, session_type=session_type
                    ).first()
                    if coaching_session:
                        coaching_session_lesson = LaserCoachingSession.objects.filter(
                            coaching_session=coaching_session
                        ).first()
                        if coaching_session_lesson:
                            lesson = coaching_session_lesson.lesson
                            lesson.delete()
                        coaching_session.delete()

                LiveSession.objects.filter(batch=batch, order__gt=order).update(
                    order=F("order") - 1,
                    live_session_number=Case(
                        When(
                            session_type=session_type, then=F("live_session_number") - 1
                        ),
                        default=F("live_session_number"),
                        output_field=IntegerField(),
                    ),
                )
                CoachingSession.objects.filter(batch=batch, order__gt=order).update(
                    order=F("order") - 1,
                    coaching_session_number=Case(
                        When(
                            session_type=session_type,
                            then=F("coaching_session_number") - 1,
                        ),
                        default=F("coaching_session_number"),
                        output_field=IntegerField(),
                    ),
                )

                # Update lesson names for remaining sessions
                if session_type in [
                    "live_session",
                    "check_in_session",
                    "in_person_session",
                    "kickoff_session",
                    "virtual_session",
                ]:
                    for lesson in Lesson.objects.filter(
                        course=course, lesson_type="live_session"
                    ):
                        live_session_lesson = LiveSessionLesson.objects.filter(
                            lesson=lesson
                        ).first()

                        if (
                            live_session_lesson
                            and live_session_lesson.live_session.session_type
                            == session_type
                        ):
                            lesson_number = extract_number_from_name(lesson.name)

                            session_type_display = session_type.replace(
                                "_", " "
                            ).title()
                            lesson_name = f"{session_type_display} {live_session_lesson.live_session.live_session_number}"

                            lesson.name = lesson_name
                            lesson.save()

                            feedback_lesson_name = (
                                f"feedback_for_{session_type}_{lesson_number}"
                            )

                            feedback_lessons = FeedbackLesson.objects.filter(
                                lesson__course=course,
                            )

                            for feedback_lesson in feedback_lessons:
                                if feedback_lesson:
                                    current_lesson_name = feedback_lesson.lesson.name
                                    formatted_lesson_name = get_feedback_lesson_name(
                                        current_lesson_name
                                    )

                                    if formatted_lesson_name == feedback_lesson_name:
                                        session_type_display = session_type.replace(
                                            "_", " "
                                        ).title()

                                        feedback_lesson.lesson.name = f"Feedback for {session_type_display} {live_session_lesson.live_session.live_session_number}"

                                        feedback_lesson.lesson.save()
                                        feedback_lesson.save()

                elif session_type in ["laser_coaching_session", "mentoring_session"]:
                    for lesson in Lesson.objects.filter(
                        course=course, lesson_type="laser_coaching"
                    ):
                        coaching_session_lesson = LaserCoachingSession.objects.filter(
                            lesson=lesson
                        ).first()
                        if (
                            coaching_session_lesson
                            and coaching_session_lesson.coaching_session.session_type
                            == session_type
                        ):
                            session_type_display = session_type.replace(
                                "_", " "
                            ).title()
                            lesson_name = f"{session_type_display} {coaching_session_lesson.coaching_session.coaching_session_number}"
                            lesson.name = lesson_name
                            lesson.save()

            return Response({"message": "Session deleted successfully."}, status=200)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to delete session"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_certificate_status_for_multiple_participants(request):
    try:
        with transaction.atomic():
            participants_ids = request.data.get("participants")
            course_id = request.data.get("course_id")

            for participant_id in participants_ids:
                participant = Learner.objects.get(id=participant_id)

                course_enrollments = CourseEnrollment.objects.filter(
                    learner=participant, course__id=course_id
                ).first()

                if course_enrollments:
                    course_for_that_participant = course_enrollments
                    course_for_that_participant.is_certificate_allowed = True
                    course_for_that_participant.save()
                else:
                    return JsonResponse(
                        {"error": "No Course Enrolled in this Batch"}, status=404
                    )
            return Response({"message": "Certificate released successfully"})
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to release certificate"}, status=500)


class GetAllBatchesCoachDetails(APIView):
    def get(self, request, project_id):
        try:
            batches = SchedularBatch.objects.filter(project__id=project_id)
            all_coaches = []
            all_facilitator = []

            for batch in batches:
                for coach in batch.coaches.all():
                    coach_serializer = CoachSerializer(coach)
                    coach_data = {
                        **coach_serializer.data,
                        "batchNames": [batch.name],
                    }
                    all_coaches.append(coach_data)
                for facilitator in Facilitator.objects.filter(livesession__batch=batch):
                    facilitator_serializer = FacilitatorSerializer(facilitator)
                    facilitator_data = {
                        **facilitator_serializer.data,
                        "batchNames": [batch.name],
                    }
                    all_facilitator.append(facilitator_data)

            unique_coaches = {}
            for coach_data in all_coaches:
                coach_id = coach_data["id"]
                if coach_id not in unique_coaches:
                    unique_coaches[coach_id] = coach_data
                else:
                    unique_coaches[coach_id]["batchNames"].extend(
                        coach_data["batchNames"]
                    )

            unique_facilitator = {}
            for facilitator_data in all_facilitator:
                facilitator_id = facilitator_data["id"]
                if facilitator_id not in unique_facilitator:
                    unique_facilitator[facilitator_id] = facilitator_data
                else:
                    unique_facilitator[facilitator_id]["batchNames"].extend(
                        facilitator_data["batchNames"]
                    )

            return Response(
                {
                    "unique_coaches": list(unique_coaches.values()),
                    "unique_facilitator": list(unique_facilitator.values()),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get coaches data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetAllBatchesParticipantDetails(APIView):
    def get(self, request, project_id):
        try:
            batches = SchedularBatch.objects.filter(project__id=project_id)

            learner_data_dict = {}

            for batch in batches:
                for learner in batch.learners.all():
                    learner_id = learner.id
                    if learner_id not in learner_data_dict:
                        learner_data_dict[learner_id] = {
                            "id": learner_id,
                            "name": learner.name,
                            "email": learner.email,
                            "batchNames": [
                                batch.name
                            ],  # Initialize with list containing batch name
                            "phone": learner.phone,
                        }
                    else:
                        learner_data_dict[learner_id]["batchNames"].append(batch.name)

            unique_learner_data = list(learner_data_dict.values())

            return Response(unique_learner_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get learners data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def coach_inside_skill_training_or_not(request, project_id, batch_id):
    try:
        if batch_id == "all":
            sessions = SchedularSessions.objects.filter(
                coaching_session__batch__project__id=project_id
            )
        else:
            batch = get_object_or_404(SchedularBatch, pk=batch_id)
            sessions = SchedularSessions.objects.filter(coaching_session__batch=batch)
        coach_status_list = []
        for session in sessions:
            coach_detail = session.availibility.coach
            coach_status_list.append(coach_detail.id)
        return Response({"coach_status_list": coach_status_list})
    except SchedularBatch.DoesNotExist:
        return Response({"error": "Batch not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def facilitator_inside_that_batch(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
        facilitators = batch.facilitator.all()
        facilitator_serializer = FacilitatorSerializer(facilitators, many=True)
        return Response({"facilitators_in_batch": facilitator_serializer.data})
    except SchedularBatch.DoesNotExist:
        return Response({"error": "Batch not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_coach_from_that_batch(request):
    try:
        with transaction.atomic():
            batch_id = request.data.get("batch_id")
            coach_id = request.data.get("coach_id")
            batch = get_object_or_404(SchedularBatch, pk=batch_id)
            coach = get_object_or_404(Coach, pk=coach_id)
            batch.coaches.remove(coach)
            batch.save()
            is_coach_existing_in_other_batched = Coach.objects.filter(
                schedularbatch__project__id=batch.project.id
            ).exists()
            if not is_coach_existing_in_other_batched:
                for session in batch.project.project_structure:
                    if session["session_type"] in [
                        "laser_coaching_session",
                        "mentoring_session",
                    ]:
                        coaching_session = CoachingSession.objects.filter(
                            batch=batch,
                            order=session["order"],
                            session_type=session["session_type"],
                        ).first()
                        coach_pricing = CoachPricing.objects.filter(
                            project=batch.project,
                            coach=coach,
                            session_type=coaching_session.session_type,
                            coaching_session_number=coaching_session.coaching_session_number,
                            order=coaching_session.order,
                            price=session["price"],
                        ).delete()

            return Response({"message": f"Coach successfully removed from this batch."})
    except SchedularBatch.DoesNotExist:
        return Response({"error": "Batch not found"}, status=404)
    except Coach.DoesNotExist:
        return Response({"error": "Coach not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_facilitator_from_that_batch(request):
    try:
        batch_id = request.data.get("batch_id")
        facilitator_id = request.data.get("facilitator_id")
        batch = get_object_or_404(SchedularBatch, pk=batch_id)
        facilitator = get_object_or_404(Facilitator, pk=facilitator_id)
        live_sessions = LiveSession.objects.filter(batch=batch, facilitator=facilitator)
        for live_session in live_sessions:
            live_session.facilitator = None
            live_session.save()
        return Response(
            {"message": f"Facilitator successfully removed from this batch."}
        )
    except SchedularBatch.DoesNotExist:
        return Response({"error": "Batch not found"}, status=404)
    except Facilitator.DoesNotExist:
        return Response({"error": "Facilitator not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_project_status(request):
    project_id = request.data.get("id")

    try:
        project = SchedularProject.objects.get(id=project_id)

        project.status = request.data.get("status")

        project.save()

        return Response(
            {"message": "Update successfully."},
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_skill_dashboard_card_data(request, project_id):
    try:
        hr_id = request.query_params.get("hr", None)
        if project_id == "all":
            start_timestamp, end_timestamp = get_current_date_timestamps()
            # schedular sessions scheduled today
            today_sessions = SchedularSessions.objects.filter(
                availibility__start_time__lte=end_timestamp,
                availibility__end_time__gte=start_timestamp,
            )
            if hr_id:
                today_sessions = today_sessions.filter(
                    coaching_session__batch__project__hr__id=hr_id
                )

            today = timezone.now().date()
            today_live_sessions = LiveSession.objects.filter(date_time__date=today)

            if hr_id:
                today_live_sessions = today_live_sessions.filter(
                    batch__project__hr__id=hr_id
                )

            ongoing_assessment = Assessment.objects.filter(
                assessment_modal__isnull=False, status="ongoing"
            )

            completed_assessments = Assessment.objects.filter(
                assessment_modal__isnull=False, status="completed"
            )
        else:
            start_timestamp, end_timestamp = get_current_date_timestamps()
            # schedular sessions scheduled today
            today_sessions = SchedularSessions.objects.filter(
                availibility__start_time__lte=end_timestamp,
                availibility__end_time__gte=start_timestamp,
                coaching_session__batch__project__id=int(project_id),
            )

            today = timezone.now().date()
            today_live_sessions = LiveSession.objects.filter(
                date_time__date=today, batch__project__id=int(project_id)
            )

            ongoing_assessment = Assessment.objects.filter(
                assessment_modal__isnull=False,
                status="ongoing",
                assessment_modal__lesson__course__batch__project__id=int(project_id),
            )
            if hr_id:
                ongoing_assessment = ongoing_assessment.filter(hr__id=hr_id)

            completed_assessments = Assessment.objects.filter(
                assessment_modal__isnull=False,
                status="completed",
                assessment_modal__lesson__course__batch__project__id=int(project_id),
            )
            if hr_id:
                completed_assessments = completed_assessments.filter(hr__id=hr_id)
        return Response(
            {
                "today_coaching_sessions": len(today_sessions),
                "today_live_sessions": len(today_live_sessions),
                "ongoing_assessments": len(ongoing_assessment),
                "completed_assessments": len(completed_assessments),
            },
            status=200,
        )
    except Exception as e:
        print(str(e))
        return Response(
            {
                "error": "Failed to get data",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_coaching_session_dashboard_data(request, project_id):
    try:
        hr_id = request.query_params.get("hr", None)
        current_time_seeq = timezone.now()
        timestamp_milliseconds = str(int(current_time_seeq.timestamp() * 1000))
        if project_id == "all":
            schedular_session = SchedularSessions.objects.all()
        else:
            schedular_session = SchedularSessions.objects.filter(
                coaching_session__batch__project__id=int(project_id)
            )
        if hr_id:
            schedular_session = schedular_session.filter(
                coaching_session__batch__project__hr__id=hr_id
            )

        upcoming_schedular_sessions = get_coaching_session_according_to_time(
            schedular_session, "upcoming"
        )
        upcoming_schedular_session_data = []
        for session in upcoming_schedular_sessions:
            temp = {
                "date_time": session.availibility.start_time,
                "coach": session.availibility.coach.first_name
                + " "
                + session.availibility.coach.last_name,
                "batch_name": session.coaching_session.batch.name,
                "learner": session.learner.name,
                "project_name": session.coaching_session.batch.project.name,
            }
            upcoming_schedular_session_data.append(temp)
        return Response(upcoming_schedular_session_data, status=status.HTTP_200_OK)

    except SchedularSessions.DoesNotExist:
        return Response(
            {"error": f"SchedularSession with id {project_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_past_coaching_session_dashboard_data(request, project_id):
    try:
        hr_id = request.query_params.get("hr", "")
        current_time_seeq = timezone.now()
        timestamp_milliseconds = str(int(current_time_seeq.timestamp() * 1000))
        if project_id == "all":
            schedular_session = SchedularSessions.objects.all()
        else:
            schedular_session = SchedularSessions.objects.filter(
                coaching_session__batch__project__id=int(project_id)
            )
        if hr_id:
            schedular_session = schedular_session.filter(
                coaching_session__batch__project__hr__id=hr_id
            )

        past_schedular_sessions = get_coaching_session_according_to_time(
            schedular_session, "past"
        )

        past_schedular_session_data = []
        for session in past_schedular_sessions:
            temp = {
                "date_time": session.availibility.start_time,
                "coach": session.availibility.coach.first_name
                + " "
                + session.availibility.coach.last_name,
                "batch_name": session.coaching_session.batch.name,
                "learner": session.learner.name,
                "project_name": session.coaching_session.batch.project.name,
            }
            past_schedular_session_data.append(temp)
        return Response(past_schedular_session_data, status=status.HTTP_200_OK)

    except SchedularSessions.DoesNotExist:
        return Response(
            {"error": f"SchedularSession with id {project_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_live_session_dashboard_data(request, project_id):
    try:
        hr_id = request.query_params.get("hr", None)
        current_time_seeq = timezone.now()
        if project_id == "all":
            live_sessions = LiveSession.objects.all()
        else:
            live_sessions = LiveSession.objects.filter(
                batch__project__id=int(project_id)
            )

        if hr_id:
            live_sessions = live_sessions.filter(batch__project__hr__id=hr_id)
        upcoming_live_sessions = live_sessions.filter(date_time__gt=current_time_seeq)

        upcoming_live_session_data = []

        for live_session in upcoming_live_sessions:
            facilitator_names = (
                [
                    f"{live_session.facilitator.first_name} {live_session.facilitator.last_name}"
                ]
                if live_session.facilitator
                else []
            )
            coach_names = [
                f"{coach.first_name} {coach.last_name}"
                for coach in live_session.batch.coaches.all()
            ]
            temp = {
                "date_time": live_session.date_time,
                "facilitator_names": facilitator_names,
                "session_name": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                "batch_name": live_session.batch.name,
                "project_name": live_session.batch.project.name,
                "coach_names": coach_names,
            }

            upcoming_live_session_data.append(temp)
        return Response(upcoming_live_session_data, status=status.HTTP_200_OK)

    except LiveSession.DoesNotExist:
        return Response(
            {"error": f"LiveSession with id {project_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_past_live_session_dashboard_data(request, project_id):
    try:
        hr_id = request.query_params.get("hr", None)
        current_time_seeq = timezone.now()
        if project_id == "all":
            live_sessions = LiveSession.objects.all()
        else:
            live_sessions = LiveSession.objects.filter(
                batch__project__id=int(project_id)
            )
        if hr_id:
            live_sessions = live_sessions.filter(batch__project__hr__id=hr_id)
        past_live_sessions = live_sessions.filter(date_time__lt=current_time_seeq)

        past_live_session_data = []

        for live_session in past_live_sessions:
            facilitator_names = (
                [
                    f"{live_session.facilitator.first_name} {live_session.facilitator.last_name}"
                ]
                if live_session.facilitator
                else []
            )
            coach_names = [
                f"{coach.first_name} {coach.last_name}"
                for coach in live_session.batch.coaches.all()
            ]

            temp = {
                "date_time": live_session.date_time,
                "facilitator_names": facilitator_names,
                "session_name": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                "batch_name": live_session.batch.name,
                "project_name": live_session.batch.project.name,
                "coach_names": coach_names,
            }

            past_live_session_data.append(temp)

        return Response(past_live_session_data, status=status.HTTP_200_OK)

    except LiveSession.DoesNotExist:
        return Response(
            {"error": f"LiveSession with id {project_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def pre_post_assessment_or_nudge_update_in_project(request):
    try:

        operation = request.data.get("operation")
        nudge_or_assessment = request.data.get("nudgeOrAssessment")
        project_id = request.data.get("projectId")

        project = SchedularProject.objects.get(id=project_id)

        if nudge_or_assessment == "nudge" and operation == "delete":
            project.nudges = False
        elif nudge_or_assessment == "nudge" and operation == "add":
            project.nudges = True
        elif nudge_or_assessment == "assessment" and operation == "delete":
            project.pre_post_assessment = False
        elif nudge_or_assessment == "assessment" and operation == "add":
            project.pre_post_assessment = True

        project.save()

        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {
                "error": "Failed to perform operation.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def add_facilitator_to_batch(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)

        facilitator_id = request.data.get("facilitator_id", "")
        facilitator = Facilitator.objects.get(id=facilitator_id)

        live_sessions = LiveSession.objects.filter(batch=batch)
        for live_session in live_sessions:
            live_session.facilitator = facilitator
            live_session.save()

        # create_facilitator_pricing(batch, facilitator)

        return Response({"message": "Facilitator added successfully."}, status=201)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to add facilitator."}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sessions_pricing_for_a_coach(request, coach_id, project_id):
    try:
        project = SchedularProject.objects.get(id=project_id)
        coach_pricing = CoachPricing.objects.filter(
            project__id=project_id, coach__id=coach_id
        )
        serialize = CoachPricingSerializer(coach_pricing, many=True)
        return Response(serialize.data)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data."}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sessions_pricing_for_a_facilitator(request, facilitator_id, project_id):
    try:
        facilitator_picing = FacilitatorPricing.objects.filter(
            project__id=project_id, facilitator__id=facilitator_id
        )
        serialize = FacilitatorPricingSerializer(facilitator_picing, many=True)
        return Response(serialize.data)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data."}, status=201)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_facilitator_price(request, facilitator_price_id):
    try:
        price = request.data.get("price")
        facilitator_price = FacilitatorPricing.objects.get(id=facilitator_price_id)
        facilitator_price.price = price

        facilitator_price.save()

        return Response({"message": "Facilitator price updated."}, status=201)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to update price."}, status=201)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_coach_price(request, coach_price_id):
    try:
        price = request.data.get("price")
        coach_price = CoachPricing.objects.get(id=coach_price_id)

        coach_price.price = price
        coach_price.save()

        return Response({"message": "Coach price updated."}, status=201)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to update price."}, status=201)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_price_in_project_structure(request):
    try:

        project_id = int(request.data.get("project_id"))
        price = request.data.get("price")
        session_type = request.data.get("session_type")
        order = request.data.get("order")

        project = SchedularProject.objects.get(id=project_id)
        for session in project.project_structure:
            if session["session_type"] == session_type and session["order"] == order:
                session["price"] = price
        project.save()
        if session_type in [
            "check_in_session",
            "in_person_session",
            "kickoff_session",
            "virtual_session",
        ]:
            facilitator_pricings = FacilitatorPricing.objects.filter(
                project_id=project_id, session_type=session_type, order=order
            )
            for facilitator_pricing in facilitator_pricings:
                if facilitator_pricing:
                    facilitator_pricing.price = price
                    facilitator_pricing.save()
        elif session_type in ["laser_coaching_session", "mentoring_session"]:
            coach_pricings = CoachPricing.objects.filter(
                project_id=project_id, session_type=session_type, order=order
            )
            for coach_pricing in coach_pricings:
                if coach_pricing:
                    coach_pricing.price = price
                    coach_pricing.save()

        return Response({"message": "Price updated successfully."}, status=201)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to update price"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def show_facilitator_inside_courses(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
        all_live_session = LiveSession.objects.filter(batch=batch)
        facilitators = set()
        for live_session in all_live_session:
            if live_session.facilitator:
                facilitators.add(live_session.facilitator)

        facilitator_serializer = FacilitatorSerializer(list(facilitators), many=True)
        return Response(
            {"facilitators": facilitator_serializer.data}, status=status.HTTP_200_OK
        )

    except SchedularBatch.DoesNotExist:
        return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_coach_of_project_or_batch(request, project_id, batch_id):
    try:

        if project_id == "all":
            projects = SchedularProject.objects.exclude(status="completed")
        else:
            projects = SchedularProject.objects.filter(id=int(project_id))
        all_coach = set()

        for project in projects:
            if project_id == "all" or batch_id == "all":
                batches = SchedularBatch.objects.filter(project__id=project.id)
            else:
                batches = SchedularBatch.objects.filter(id=int(batch_id))

            for batch in batches:
                for coach in batch.coaches.all():
                    if coach.active_inactive:
                        all_coach.add(coach)

        serialize = CoachSerializer(list(all_coach), many=True)
        return Response(serialize.data)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def merge_coaching_sessions(coaching_sessions):
    if not coaching_sessions:
        return []

    coaching_sessions = list(coaching_sessions)  # Convert QuerySet to list
    coaching_sessions.sort(key=lambda session: session.start_date)  # Sort list

    merged_sessions = []
    current_start = coaching_sessions[0].start_date
    current_end = coaching_sessions[0].end_date

    for session in coaching_sessions[1:]:
        if session.start_date <= current_end:  # Overlapping or contiguous
            current_end = max(current_end, session.end_date)
        else:
            merged_sessions.append((current_start, current_end))
            current_start = session.start_date
            current_end = session.end_date

    merged_sessions.append((current_start, current_end))

    return merged_sessions


def get_merged_date_of_coaching_session_for_a_batches(batches):
    try:
        data = []

        coaching_sessions = CoachingSession.objects.filter(batch__in=batches)

        for coaching_session in coaching_sessions:
            if coaching_session.start_date:
                data.append([coaching_session.start_date, coaching_session.end_date])

        data.sort(key=lambda x: x[0])
        merged = [data[0]]

        for current_start, current_end in data[1:]:
            last_merged_start, last_merged_end = merged[-1]

            if current_start <= last_merged_end:
                merged[-1] = [last_merged_start, max(last_merged_end, current_end)]
            else:
                merged.append([current_start, current_end])
        if merged:
            return merged
        else:
            return []
    except Exception as e:
        print(str(e))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_slots_based_on_project_batch_coach(request, project_id, batch_id, coach_id):
    try:
        range_start_date = request.query_params.get("start_date")
        range_end_date = request.query_params.get("end_date")

        current_time = timezone.now()
        timestamp_milliseconds = current_time.timestamp() * 1000

        data = []
        if project_id == "all":
            projects = SchedularProject.objects.exclude(status="completed")
            for project in projects:
                temp = {
                    "project_id": project.id,
                    "project_name": project.name,
                    "coaches_batches_slots": {},
                }
                data.append(temp)
            return Response(data)

        else:
            projects = SchedularProject.objects.filter(id=int(project_id))

        for project in projects:
            temp = {
                "project_id": project.id,
                "project_name": project.name,
                "coaches_batches_slots": {},
            }

            if batch_id == "all":
                batches = SchedularBatch.objects.filter(project=project)
            else:
                batches = SchedularBatch.objects.filter(id=int(batch_id))
            coaches = list(
                {coach for batch in batches for coach in batch.coaches.all()}
            )

            merged_dates = get_merged_date_of_coaching_session_for_a_batches(batches)

            count = 0
            if merged_dates:
                for merged_date in merged_dates:
                    start_date, end_date = merged_date
                    count = count + 1
                    start_date = datetime.combine(start_date, datetime.min.time())
                    end_date = (
                        datetime.combine(end_date, datetime.min.time())
                        + timedelta(days=1)
                        - timedelta(milliseconds=1)
                    )

                    start_timestamp = str(int(start_date.timestamp() * 1000))
                    end_timestamp = str(int(end_date.timestamp() * 1000))
                    if range_start_date and range_end_date:
                        start_timestamp = str(
                            max((int(start_timestamp)), int(range_start_date))
                        )
                        end_timestamp = str(
                            min((int(end_timestamp)), int(range_end_date))
                        )
                    else:

                        start_timestamp = str(
                            max((int(start_timestamp)), timestamp_milliseconds)
                        )
                    if coach_id == "all":
                        availabilities = CoachSchedularAvailibilty.objects.filter(
                            coach__in=coaches,
                            start_time__gte=start_timestamp,
                            end_time__lte=end_timestamp,
                        )
                    else:
                        coach_ids = [int(coach_id)]  # Convert coach_id to int if needed
                        availabilities = CoachSchedularAvailibilty.objects.filter(
                            coach_id__in=coach_ids,
                            start_time__gte=start_timestamp,
                            end_time__lte=end_timestamp,
                        )

                    for availability in availabilities:
                        coach_id = availability.coach.id
                        if coach_id not in temp["coaches_batches_slots"]:
                            temp["coaches_batches_slots"][coach_id] = {
                                "coach_name": availability.coach.first_name
                                + " "
                                + availability.coach.last_name,
                                "slots": [],
                                "batches": list({batch.name for batch in batches}),
                            }
                        serializer = CoachSchedularAvailibiltySerializer(availability)
                        temp["coaches_batches_slots"][coach_id]["slots"].append(
                            serializer.data
                        )

            data.append(temp)
        return Response(data)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_wise_progress_data(request, project_id):
    try:
        batch_id = request.query_params.get("batch_id", None)

        project = SchedularProject.objects.get(id=int(project_id))

        if batch_id:
            batches = SchedularBatch.objects.filter(id=int(batch_id))
        else:
            batches = SchedularBatch.objects.filter(project=project)

        data = []

        for batch in batches:

            assessments = Assessment.objects.filter(
                assessment_modal__lesson__course__batch=batch
            )
            pre_assessment = assessments.filter(assessment_timing="pre").first()
            post_assessment = assessments.filter(assessment_timing="post").first()

            for participant in batch.learners.all():

                temp = {"participant_name": participant.name, "batch_name": batch.name}

                pre_participant_response = ParticipantResponse.objects.filter(
                    assessment=pre_assessment, participant=participant
                ).first()
                post_participant_response = ParticipantResponse.objects.filter(
                    assessment=post_assessment, participant=participant
                ).first()

                if project and project.pre_post_assessment:
                    temp["pre_assessment"] = "Yes" if pre_participant_response else "No"

                for session in project.project_structure:
                    session_type = session["session_type"]
                    if session_type in [
                        "live_session",
                        "check_in_session",
                        "in_person_session",
                        "kickoff_session",
                        "virtual_session",
                    ]:
                        live_session = LiveSession.objects.filter(
                            batch=batch,
                            session_type=session_type,
                            order=int(session["order"]),
                        ).first()
                        if live_session:
                            temp[
                                f"{get_live_session_name(session_type)} {live_session.live_session_number}"
                            ] = (
                                "Yes"
                                if participant.id in live_session.attendees
                                else "No"
                            )

                    elif session_type in [
                        "laser_coaching_session",
                        "mentoring_session",
                    ]:
                        coaching_session = CoachingSession.objects.filter(
                            batch=batch,
                            order=int(session["order"]),
                            session_type=session_type,
                        ).first()
                        if coaching_session:
                            schedular_session = SchedularSessions.objects.filter(
                                coaching_session=coaching_session,
                                learner__id=participant.id,
                            ).first()
                            if schedular_session:
                                temp[
                                    f"{session_type} {schedular_session.coaching_session.coaching_session_number}"
                                ] = (
                                    "Yes"
                                    if schedular_session.status == "completed"
                                    else "No"
                                )
                            else:
                                temp[
                                    f"{session_type} {coaching_session.coaching_session_number}"
                                ] = "No"
                        else:
                            temp[f"{session_type} {session['order']}"] = "No"

                if project and project.pre_post_assessment:
                    temp["post_assessment"] = (
                        "Yes" if post_participant_response else "No"
                    )
                data.append(temp)
        return Response(data)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_request_with_availabilities(request, request_id):
    try:
        request_obj = RequestAvailibilty.objects.get(pk=request_id)
    except RequestAvailibilty.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    # Check if any confirmed availability exists
    confirmed_availabilities_exist = CoachSchedularAvailibilty.objects.filter(
        request=request_obj, is_confirmed=True
    ).exists()
    if confirmed_availabilities_exist:
        return Response(
            {"error": "Cannot delete request, confirmed availabilities exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Delete associated availabilities where is_confirmed = False
    unconfirmed_availabilities = CoachSchedularAvailibilty.objects.filter(
        request=request_obj, is_confirmed=False
    )
    unconfirmed_availabilities.delete()
    # Delete the request
    request_obj.delete()
    return Response(
        {"message": "Request deleted successfully."}, status=status.HTTP_204_NO_CONTENT
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_session_progress_data_for_dashboard(request, project_id):
    try:
        current_time = timezone.now()
        project = SchedularProject.objects.get(id=int(project_id))
        batches = SchedularBatch.objects.filter(project=project)
        data = []

        for batch in batches:
            temp = {"batch_name": batch.name}
            yes_count = 0
            total_count = 0

            for session in project.project_structure:

                session_type = session["session_type"]
                if session_type in [
                    "live_session",
                    "check_in_session",
                    "in_person_session",
                    "kickoff_session",
                    "virtual_session",
                ]:
                    total_count += 1
                    live_session = LiveSession.objects.filter(
                        batch=batch,
                        session_type=session_type,
                        order=int(session["order"]),
                    ).first()
                    if (
                        live_session
                        and live_session.date_time
                        and live_session.date_time <= current_time
                    ):
                        temp[
                            f"{get_live_session_name(session_type)} {live_session.live_session_number}"
                        ] = "Done"
                        yes_count += 1
                    else:
                        temp[
                            f"{get_live_session_name(session_type)} {live_session.live_session_number}"
                        ] = "Pending"

                elif session_type in [
                    "laser_coaching_session",
                    "mentoring_session",
                ]:
                    total_count += 1
                    coaching_session = CoachingSession.objects.filter(
                        batch=batch,
                        order=int(session["order"]),
                        session_type=session_type,
                    ).first()
                    if (
                        coaching_session
                        and coaching_session.end_date
                        and coaching_session.end_date < current_time.date()
                    ):
                        temp[
                            f"{session_type} {coaching_session.coaching_session_number}"
                        ] = "Done"
                        yes_count += 1
                    else:
                        temp[
                            f"{session_type} {coaching_session.coaching_session_number}"
                        ] = "Pending"

            progress = yes_count / total_count if total_count > 0 else 0
            temp["progress"] = round(progress * 100)
            data.append(temp)
        return Response(data)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_coach_session_progress_data_for_skill_training_project(request, batch_id):
    try:

        batch = SchedularBatch.objects.get(id=batch_id)
        data = {}

        for coach in batch.coaches.all():
            schedular_sessions = SchedularSessions.objects.filter(
                coaching_session__batch=batch, availibility__coach=coach
            )
            total = len(schedular_sessions)
            count = 0
            for schedular_session in schedular_sessions:
                if schedular_session.status == "completed":
                    count += 1

            data[coach.id] = (count / total) * 100 if total > 0 else 0
        return Response(data)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_purchase_order(purchase_orders, purchase_order_id):
    for po in purchase_orders:
        if po.get("purchaseorder_id") == purchase_order_id:
            return po
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_facilitators_and_pricing_for_project(request, project_id):
    try:
        facilitators = Facilitator.objects.filter(
            livesession__batch__project__id=project_id
        ).distinct()
        facilitators_pricing = FacilitatorPricing.objects.filter(project__id=project_id)
        facilitators_data = []
        purchase_orders = fetch_purchase_orders(organization_id)
        for facilitator in facilitators:
            serializer = FacilitatorBasicDetailsSerializer(facilitator)
            is_vendor = facilitator.user.roles.filter(name="vendor").exists()
            vendor_id = None
            if is_vendor:
                vendor_id = Vendor.objects.get(user=facilitator.user).vendor_id
            facilitator_data = serializer.data
            pricing = facilitators_pricing.filter(facilitator__id=facilitator.id)
            purchase_order = None
            if pricing.exists():
                pricing_serializer = FacilitatorPricingSerializer(pricing.first())
                if pricing_serializer.data["purchase_order_id"]:
                    purchase_order = get_purchase_order(
                        purchase_orders, pricing_serializer.data["purchase_order_id"]
                    )
            else:
                pricing_serializer = None
            facilitator_data["pricing_details"] = (
                pricing_serializer.data if pricing_serializer else None
            )
            facilitator_data["vendor_id"] = vendor_id
            facilitator_data["purchase_order"] = purchase_order
            facilitators_data.append(facilitator_data)
        return Response(facilitators_data)
    except Exception as e:
        print(str(e))
        return Response(status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_coaches_and_pricing_for_project(request, project_id):
    try:
        coaches = Coach.objects.filter(
            schedularbatch__project__id=project_id
        ).distinct()
        coaches_data = []
        purchase_orders = fetch_purchase_orders(organization_id)
        for coach in coaches:
            coaches_pricing = CoachPricing.objects.filter(
                project__id=project_id, coach=coach
            )
            serializer = CoachBasicDetailsSerializer(coach)
            is_vendor = coach.user.roles.filter(name="vendor").exists()
            vendor_id = None
            if is_vendor:
                vendor_id = Vendor.objects.get(user=coach.user).vendor_id
            coach_data = serializer.data
            pricing = coaches_pricing.filter(coach__id=coach.id)
            all_pricings_serializer = CoachPricingSerializer(coaches_pricing, many=True)
            purchase_order = None
            if pricing.exists():
                pricing_serializer = CoachPricingSerializer(pricing.first())
                if pricing_serializer.data["purchase_order_id"]:
                    purchase_order = get_purchase_order(
                        purchase_orders, pricing_serializer.data["purchase_order_id"]
                    )
            else:
                pricing_serializer = None
            coach_data["pricing_details"] = (
                pricing_serializer.data if pricing_serializer else None
            )

            coach_data["vendor_id"] = vendor_id
            coach_data["purchase_order"] = purchase_order
            coach_data["all_pricings"] = all_pricings_serializer.data
            coaches_data.append(coach_data)
        return Response(coaches_data)
    except Exception as e:
        print(str(e))
        return Response(status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_facilitator_pricing(request):
    serializer = FacilitatorPricingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_facilitator_pricing(request, facilitator_pricing_id):
    pricing_instance = get_object_or_404(FacilitatorPricing, id=facilitator_pricing_id)
    serializer = FacilitatorPricingSerializer(pricing_instance, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_expense(request):
    try:
        name = request.data.get("name")
        description = request.data.get("description")
        date_of_expense = request.data.get("date_of_expense")
        live_session = request.data.get("live_session")
        batch = request.data.get("batch")
        facilitator = request.data.get("facilitator")
        file = request.data.get("file")
        amount = request.data.get("amount")
        if not file:
            return Response(
                {"error": "Please upload file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if not batch or not facilitator:
            return Response(
                {"error": "Failed to create expense."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if name and date_of_expense and description and amount:
            facilitator = Facilitator.objects.get(id=int(facilitator))
            batch = SchedularBatch.objects.get(id=int(batch))
            if live_session:
                live_session = LiveSession.objects.filter(id=int(live_session)).first()
            expense = Expense.objects.create(
                name=name,
                description=description,
                date_of_expense=date_of_expense,
                live_session=live_session,
                batch=batch,
                facilitator=facilitator,
                file=file,
                amount=amount,
            )

            return Response({"message": "Expense created successfully!"}, status=201)
        else:
            return Response(
                {"error": "Fill in all the required feild"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to create expense"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_expense_amount(request):
    try:

        amount = request.data.get("amount")
        expense_id = int(request.data.get("expense_id"))

        if amount:
            expense = Expense.objects.get(
                id=expense_id,
            )
            expense.amount = amount
            expense.save()
            return Response({"message": "Amount updated successfully!"}, status=201)
        else:
            return Response(
                {"error": "Fill in the required feild"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to update amount"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_expense(request):
    try:
        name = request.data.get("name")
        description = request.data.get("description")
        date_of_expense = request.data.get("date_of_expense")
        live_session = request.data.get("live_session")
        batch = request.data.get("batch")
        facilitator = request.data.get("facilitator")
        file = request.data.get("file")
        expense_id = request.data.get("expense_id")

        if not file:
            return Response(
                {"error": "Please upload file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if not batch or not facilitator:
            return Response(
                {"error": "Failed to create expense."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if name and date_of_expense and description:
            facilitator = Facilitator.objects.get(id=int(facilitator))
            batch = SchedularBatch.objects.get(id=int(batch))
            if live_session:
                live_session = LiveSession.objects.filter(id=int(live_session)).first()

            expense = Expense.objects.get(id=int(expense_id))

            expense.name = name
            expense.description = description
            expense.date_of_expense = date_of_expense
            expense.live_session = live_session
            expense.batch = batch
            expense.facilitator = facilitator
            if not file == "null":
                expense.file = file

            expense.save()

            return Response({"message": "Expense created successfully!"}, status=201)
        else:
            return Response(
                {"error": "Fill in all the required feild"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to create expense"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_expense_for_facilitator(request, batch_id, usertype, user_id):
    try:
        expenses = []
        if usertype == "facilitator":
            expenses = Expense.objects.filter(
                batch__id=batch_id, facilitator__id=user_id
            )

        elif usertype == "pmo":
            expenses = Expense.objects.filter(batch__id=batch_id)

        serializer = ExpenseSerializerDepthOne(expenses, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to create expense"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_status_expense(request):
    try:
        status = request.data.get("status")
        expense_id = request.data.get("expense_id")

        expenses = Expense.objects.get(id=int(expense_id))
        expenses.status = status
        expenses.save()
        return Response(
            {"success": f"Expense {status.title()} successfully!"},
        )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": f"Failed to {status.title()} the expense."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
