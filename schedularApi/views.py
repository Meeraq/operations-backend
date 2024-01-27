from datetime import date, datetime, timedelta
import uuid
import requests
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
from django.db.models import Q, F, Case, When, Value, IntegerField
from time import sleep
import json
from django.core.exceptions import ObjectDoesNotExist
from api.views import get_date, get_time, add_contact_in_wati
from django.shortcuts import render
from django.http import JsonResponse
from api.models import Organisation, HR, Coach, User, Learner, Pmo
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
    FacilitatorSerializer,
    UpdateSerializer,
    SchedularUpdateDepthOneSerializer,
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
    Facilitator,
    SchedularBatch,
    SchedularUpdate,
    CalendarInvites,
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
from courses.serializers import CourseSerializer
from django.core.serializers import serialize
from courses.views import create_or_get_learner
from assessmentApi.models import (
    Assessment,
    ParticipantUniqueId,
    ParticipantObserverMapping,
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

# Create your views here.
from itertools import chain
import environ

env = environ.Env()


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
            automated_reminder=request.data["automated_reminder"],
            nudges=request.data["nudges"],
            pre_post_assessment=request.data["pre_post_assessment"],
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
    projects = SchedularProject.objects.all()
    serializer = SchedularProjectSerializer(projects, many=True)
    for project_data in serializer.data:
        latest_update = (
            SchedularUpdate.objects.filter(project__id=project_data["id"])
            .order_by("-created_at")
            .first()
        )
        project_data["latest_update"] = latest_update.message if latest_update else None
    return Response(serializer.data, status=200)


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
                    "message": "Project structure edited successfully."
                    if is_editing
                    else "Project structure added successfully."
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
        if not project_id:
            batches = SchedularBatch.objects.all()
        else:
            batches = SchedularBatch.objects.filter(project__id=project_id)
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
                    "available_slots_count": len(result)
                    if availabilities is not None
                    else 0,
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
        coaches_serializer = CoachBasicDetailsSerializer(coaches, many=True)
        sessions = [*live_sessions_serializer.data, *coaching_sessions_result]
        sorted_sessions = sorted(sessions, key=lambda x: x["order"])
        try:
            course = Course.objects.get(batch__id=batch_id)
            course_serailizer = CourseSerializer(course)
            for participant in participants_serializer.data:
                course_enrollment = CourseEnrollment.objects.get(
                    learner__id=participant["id"], course=course
                )
                participant[
                    "is_certificate_allowed"
                ] = course_enrollment.is_certificate_allowed

        except Exception as e:
            print(str(e))
            course = None
        return Response(
            {
                "sessions": sorted_sessions,
                "participants": participants_serializer.data,
                "coaches": coaches_serializer.data,
                "course": course_serailizer.data if course else None,
                "batch": batch_id,
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
        live_session = LiveSession.objects.get(id=live_session_id)
    except LiveSession.DoesNotExist:
        return Response(
            {"error": "LiveSession not found"}, status=status.HTTP_404_NOT_FOUND
        )
    existing_date_time = live_session.date_time
    serializer = LiveSessionSerializer(live_session, data=request.data, partial=True)
    if serializer.is_valid():
        update_live_session = serializer.save()
        current_time = timezone.now()
        if update_live_session.date_time > current_time:
            try:
                scheduled_for = update_live_session.date_time - timedelta(minutes=30)
                clocked = ClockedSchedule.objects.create(clocked_time=scheduled_for)
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
                    update_live_session.pt_30_min_before.enabled= False
                    update_live_session.pt_30_min_before.save()
                live_session.pt_30_min_before = periodic_task
                live_session.save()
            except Exception as e:
                # Handle any exceptions that may occur during task creation
                print(str(e))
                pass
        AIR_INDIA_PROJECT_ID = 3
        if not update_live_session.batch.project.id == AIR_INDIA_PROJECT_ID:				
            try:
                learners = live_session.batch.learners.all()
                attendees = list(
										map(
												lambda learner: {
														"emailAddress": {
																"name": learner.name,
																"address": learner.email,
														},
														"type": "required",
												},
												learners,
										)
								)
                start_time_stamp = update_live_session.date_time.timestamp() * 1000
                end_time_stamp = (
										start_time_stamp + int(update_live_session.duration) * 60000
								)
                start_datetime_obj = datetime.fromtimestamp(
										int(start_time_stamp) / 1000
								) + timedelta(hours=5, minutes=30)
                start_datetime_str = start_datetime_obj.strftime("%d-%m-%Y %H:%M") + " IST"
                description = (
										f"Your Meeraq Live Training Session is scheduled at {start_datetime_str}. "
										+ update_live_session.description
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
												None,
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
												None,
										)
            except Exception as e:
                print(str(e))
                pass
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_coaching_session(request, coaching_session_id):
    try:
        coaching_session = CoachingSession.objects.get(id=coaching_session_id)
    except CoachingSession.DoesNotExist:
        return Response(
            {"error": "Coaching session not found"}, status=status.HTTP_404_NOT_FOUND
        )
    serializer = CoachingSessionSerializer(
        coaching_session, data=request.data, partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_batch(request, project_id):
    try:
        with transaction.atomic():
            participants_data = request.data.get("participants", [])
            project = SchedularProject.objects.get(id=project_id)

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

            return Response(
                {"message": "Batch created successfully."},
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
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
    except SchedularBatch.DoesNotExist:
        return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = SchedularBatchSerializer(batch, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_coach_availabilities_booking_link(request):
    booking_link_id = request.GET.get("booking_link_id")

    if booking_link_id:
        booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{booking_link_id}"
        try:
            coaching_session = CoachingSession.objects.get(booking_link=booking_link)
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
            return Response(
                {
                    "slots": serializer.data,
                    "session_duration": session_duration,
                    "session_type": session_type,
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
                "Meeraq - Laser Coaching Session Booked"
                if session_type == "laser_coaching_session"
                else "Meeraq - Mentoring Session Booked",
                {
                    "name": learner.name,
                    "date": date_for_mail,
                    "time": session_time,
                    "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                    "session_type": "Mentoring"
                    if session_type == "mentoring_session"
                    else "Laser Coaching",
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
                    print("conflicting", availability_c.id)
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
                    print("deleted", availability_c.id)
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
                create_outlook_calendar_invite(
                    f"Meeraq - {session_type_value.capitalize()} Session",
                    f"Your {session_type_value} session has been confirmed. Book your calendars for the same. Please join the session at scheduled date and time",
                    coach_availability.start_time,
                    coach_availability.end_time,
                    [
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
                    ],
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

                send_mail_templates(
                    "coach_templates/coaching_email_template.html",
                    [participant_email],
                    "Meeraq - Laser Coaching Session Booked"
                    if session_type == "laser_coaching_session"
                    else "Meeraq - Mentoring Session Booked",
                    {
                        "name": learner.name,
                        "date": date_for_mail,
                        "time": session_time,
                        "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                        "session_type": "Mentoring"
                        if session_type == "mentoring_session"
                        else "Laser Coaching",
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
            "batch_name": session.coaching_session.batch.name
            if coach_id is None
            else None,
            "project_name": session.coaching_session.batch.project.name,
            "project_id": session.coaching_session.batch.project.id
            if coach_id is None
            else None,
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
            "coaching_session_number": session.coaching_session.coaching_session_number
            if coach_id is None
            else None,
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
    batch_name = request.data.get("batchName", "")
    project_name = request.data.get("project_name", "")
    participants = request.data.get("participants", [])
    booking_link = request.data.get("bookingLink", "")
    expiry_date = request.data.get("expiry_date", "")
    date_obj = datetime.strptime(expiry_date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d %B %Y")
    session_type = request.data.get("session_type", "")
    for participant in participants:
        try:
            learner_name = Learner.objects.get(email=participant).name
        except:
            continue
        send_mail_templates(
            "seteventlink.html",
            [participant],
            "Meeraq -Book Laser Coaching Session"
            if session_type == "laser_coaching_session"
            else "Meeraq - Book Mentoring Session",
            {
                "name": learner_name,
                "project_name": project_name,
                "event_link": booking_link,
                "expiry_date": formatted_date,
                "session_type": "mentoring"
                if session_type == "mentoring_session"
                else "laser coaching",
            },
            [],
        )
        sleep(5)
    return Response("Emails sent to participants.")


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
        send_mail_templates(
            "send_live_session_link.html",
            [learner.email],
            "Meeraq - Live Session",
            {
                "participant_name": learner.name,
                "live_session_name": f"Live Session {live_session.order}",
                "project_name": live_session.batch.project.name,
                "description": live_session.description,
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
                        "value": f"Live Session {live_session.order}",
                    },
                    {
                        "name": "project_name",
                        "value": live_session.batch.project.name,
                    },
                    {
                        "name": "description",
                        "value": live_session.description,
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
def project_report_download(request, project_id):
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
        live_sessions = LiveSession.objects.filter(batch=batch)
        coaching_sessions = CoachingSession.objects.filter(batch=batch)
        sessions = list(live_sessions) + list(coaching_sessions)
        sorted_sessions = sorted(sessions, key=lambda x: x.order)
        for session in sorted_sessions:
            if isinstance(session, LiveSession):
                session_name = f"Live Session {session.live_session_number}"
                attendance = len(session.attendees)
                if session.date_time:
                    adjusted_date_time = session.date_time + timedelta(
                        hours=5, minutes=30
                    )
                    date = adjusted_date_time.strftime("%d-%m-%Y %I:%M %p") + " IST"
                else:
                    date = "Not added"
            elif isinstance(session, CoachingSession):
                session_name = f"Coaching Session {session.coaching_session_number}"
                attendance = SchedularSessions.objects.filter(
                    coaching_session=session, status="completed"
                ).count()
                date = ""
            else:
                session_name = "Unknown Session"
                attendance = ""
                date = ""
            total_participants = batch.learners.count()
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
    response[
        "Content-Disposition"
    ] = f'attachment; filename="{project.name}_batches.xlsx"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        for batch_name, df in dfs:
            df.to_excel(writer, sheet_name=batch_name, index=False)

    return response


@api_view(["GET"])
def project_report_download_session_wise(request, project_id, batch_id):
    try:
        batch = get_object_or_404(SchedularBatch, pk=batch_id)
        live_sessions = LiveSession.objects.filter(batch=batch)
        dfs = []

        for session in live_sessions:
            data = {
                "Participant name": [],
                "Attended or Not": [],
            }

            for learner in session.batch.learners.all():
                participant_name = learner.name

                if learner.id in session.attendees:
                    attendance = "YES"
                else:
                    attendance = "NO"

                # Append data inside the learner loop
                data["Participant name"].append(participant_name)
                data["Attended or Not"].append(attendance)

            # Move these lines inside the session loop
            session_name = f"Live Session {session.order}"
            df = pd.DataFrame(data)
            dfs.append((session_name, df))

        response = HttpResponse(content_type="application/ms-excel")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{batch.name}_batches.xlsx"'

        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            for session_name, df in dfs:
                df.to_excel(writer, sheet_name=session_name, index=False)

        return response
    except Exception as e:
        print(str(e))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def addFacilitator(request):
    data = request.data
    email = data.get("email", "")

    # Check if a Facilitator with the same email already exists
    existing_facilitator = Facilitator.objects.filter(email=email).first()
    if existing_facilitator:
        return Response("Email already exists", status=status.HTTP_400_BAD_REQUEST)

    facilitator = Facilitator(
        first_name=data.get("firstName", ""),
        last_name=data.get("lastName", ""),
        email=email,
        age=data.get("age", ""),
        gender=data.get("gender", ""),
        domain=data.get("domain", []),
        phone_country_code=data.get("phoneCountryCode", ""),
        phone=data.get("phone", ""),
        level=data.get("level", []),
        rating=data.get("rating", ""),
        area_of_expertise=data.get("areaOfExpertise", []),
        profile_pic=data.get("profilePic", ""),
        education=data.get("education", []),
        years_of_corporate_experience=data.get("corporateyearsOfExperience", ""),
        language=data.get("language", []),
        job_roles=data.get("job_roles", []),
        city=data.get("city", []),
        country=data.get("country", []),
        linkedin_profile_link=data.get("linkedin_profile_link", ""),
        companies_worked_in=data.get("companies_worked_in", []),
        other_certification=data.get("other_certification", []),
        currency=data.get("currency", ""),
        client_companies=data.get("client_companies", []),
        educational_qualification=data.get("educational_qualification", []),
        fees_per_hour=data.get("fees_per_hour", ""),
        fees_per_day=data.get("fees_per_day", ""),
        topic=data.get("topic", []),
    )

    facilitator.save()

    return Response("Facilitator added successfully", status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_facilitators(request):
    facilitators = Facilitator.objects.all()
    serializer = FacilitatorSerializer(facilitators, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_multiple_facilitator(request):
    data = request.data.get("coaches", [])
    facilitators = []
    for coach_data in data:
        email = coach_data["email"]

        if Facilitator.objects.filter(email=email).exists():
            return Response(
                {"message": f"Facilitator with email {email} already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        facilitator = Facilitator(
            first_name=coach_data["first_name"],
            last_name=coach_data["last_name"],
            email=email,
            age=coach_data["age"],
            gender=coach_data["gender"],
            domain=coach_data.get("functional_domain", []),
            phone=coach_data["mobile"],
            level=coach_data.get("level", []),
            rating=coach_data.get("rating", ""),
            area_of_expertise=coach_data.get("industries", []),
            education=coach_data.get("education", []),
            years_of_corporate_experience=coach_data.get("corporate_yoe", ""),
            city=coach_data.get("city", []),
            language=coach_data.get("language", []),
            job_roles=coach_data.get("job_roles", []),
            country=coach_data.get("country", []),
            linkedin_profile_link=coach_data.get("linkedin_profile", ""),
            companies_worked_in=coach_data.get("companies_worked_in", []),
            educational_qualification=coach_data.get("educational_qualification", []),
            client_companies=coach_data.get("client_companies", []),
            fees_per_hour=coach_data.get("fees_per_hour", ""),
            fees_per_day=coach_data.get("fees_per_day", ""),
            topic=coach_data.get("topic", []),
            other_certification=coach_data.get("other_certification", []),
        )
        facilitators.append(facilitator)

    Facilitator.objects.bulk_create(
        facilitators
    )  # Bulk create facilitators in the database

    return Response(
        {"message": "Facilitators added successfully"}, status=status.HTTP_201_CREATED
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_facilitator_profile(request, id):
    try:
        facilitator = Facilitator.objects.get(pk=id)
    except Facilitator.DoesNotExist:
        return Response(
            {"error": "Facilitator not found"}, status=status.HTTP_404_NOT_FOUND
        )

    serializer = FacilitatorSerializer(facilitator, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    project.automated_reminder = request.data.get("automated_reminder")
    project.nudges = request.data.get("nudges")
    project.pre_post_assessment = request.data.get("pre_post_assessment")
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
    hr_id = request.query_params.get("hr", None)
    if hr_id:
        queryset = queryset.filter(batch__project__hr__id=hr_id)
    res = []
    for live_session in queryset:
        res.append(
            {
                "id": live_session.id,
                "name": f"Live Session {live_session.live_session_number}",
                "organization": live_session.batch.project.organisation.name,
                "batch_name": live_session.batch.name,
                "batch_id": live_session.batch.id,
                "project_name": live_session.batch.project.name,
                "project_id": live_session.batch.project.id,
                "date_time": live_session.date_time,
                "description": live_session.description,
                "attendees": len(live_session.attendees),
                "total_learners": live_session.batch.learners.count(),
            }
        )
    return Response(res)


@api_view(["GET"])
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
                "description": description
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
                            lesson=new_feedback_lesson, unique_id=unique_id
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
            project = SchedularProject.objects.get(id=request.data.get("project_id"))
            session_to_delete = request.data.get("session_to_delete")
            batches = SchedularBatch.objects.filter(project=project)
            order = session_to_delete.get("order")
            session_type = session_to_delete.get("session_type")
            duration = session_to_delete.get("duration")

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
                if session_type in [
                    "live_session",
                    "check_in_session",
                    "in_person_session",
                ]:
                    LiveSession.objects.filter(
                        batch=batch, order=order, session_type=session_type
                    ).delete()

                elif session_type in ["laser_coaching_session", "mentoring_session"]:
                    CoachingSession.objects.filter(
                        batch=batch, order=order, session_type=session_type
                    ).delete()

                LiveSession.objects.filter(batch=batch, order__gt=order).update(
                    order=F("order") - 1,
                    live_session_number=Case(
                        When(
                            session_type=session_type,
                            then=F("live_session_number") - 1,
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
            return Response({"message": "Session deleted successfully."}, status=200)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to delete session"}, status=500)
