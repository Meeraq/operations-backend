from datetime import date
import requests
from django.http import JsonResponse
import calendar
from os import name
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.db import transaction, IntegrityError
from django.core.mail import EmailMessage
from rest_framework.exceptions import ParseError, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from operationsBackend import settings
from .serializers import (
    CoachSerializer,
    UserSerializer,
    LearnerSerializer,
    PmoDepthOneSerializer,
    SessionRequestCaasSerializer,
    CoachDepthOneSerializer,
    ProjectDepthTwoSerializer,
    HrSerializer,
    OrganisationSerializer,
    ProjectSerializer,
    LearnerDepthOneSerializer,
    HrDepthOneSerializer,
    SessionRequestCaasDepthOneSerializer,
    SessionRequestCaasDepthTwoSerializer,
    AvailibilitySerializer,
    NotificationSerializer,
    EngagementDepthOneSerializer,
    GoalSerializer,
    GetGoalSerializer,
    CompetencySerializer,
    CompetencyDepthOneSerializer,
    ActionItemSerializer,
    GetActionItemDepthOneSerializer,
    PendingActionItemSerializer,
    EngagementSerializer,
    SessionRequestWithEngagementCaasDepthOneSerializer,
    ProfileEditActivitySerializer,
    UserLoginActivitySerializer,
    AddGoalActivitySerializer,
    AddCoachActivitySerializer,
    SentEmailActivitySerializer,
    CoachProfileTemplateSerializer,
    StandardizedFieldSerializer,
    StandardizedFieldRequestSerializer,
    StandardizedFieldRequestDepthOneSerializer,
    SessionRequestedActivitySerializer,
    DeleteCoachProfileActivitySerializer,
    RemoveCoachActivitySerializer,
    PastSessionActivitySerializer,
    TemplateSerializer,
    ProjectContractSerializer,
    CoachContractSerializer,
    UpdateSerializer,
    UpdateDepthOneSerializer,
    UserTokenSerializer,
    CalendarEventSerializer,
    ShareCoachProfileActivitySerializer,
    CreateProjectActivitySerializer,
    FinalizeCoachActivitySerializer,
    SessionDataSerializer,
)

from rest_framework import generics
from django.utils.crypto import get_random_string
import jwt
import jwt
import uuid
import pytz
from django.db.models import IntegerField
from django.db.models.functions import Cast
from rest_framework.exceptions import AuthenticationFailed
from datetime import datetime, timedelta
from rest_framework.response import Response
from django.core.mail import EmailMessage, BadHeaderError
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.forms.models import model_to_dict
from .models import (
    Profile,
    Pmo,
    Coach,
    OTP,
    Project,
    HR,
    Organisation,
    SessionRequestCaas,
    Availibility,
    Learner,
    CoachStatus,
    Notification,
    Engagement,
    Goal,
    Competency,
    ActionItem,
    ProfileEditActivity,
    UserLoginActivity,
    AddGoalActivity,
    AddCoachActivity,
    SentEmailActivity,
    CoachProfileTemplate,
    StandardizedField,
    StandardizedFieldRequest,
    Update,
    SessionRequestedActivity,
    DeleteCoachProfileActivity,
    RemoveCoachActivity,
    PastSessionActivity,
    Template,
    CoachContract,
    ProjectContract,
    Role,
    UserToken,
    CalendarEvent,
    ShareCoachProfileActivity,
    CreateProjectActivity,
    FinalizeCoachActivity,
)

from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import string
import random
from django.db.models import Q, Min
from collections import defaultdict
from django.db.models import Avg
from rest_framework import status
from rest_framework.views import APIView

from django.db.models import Count, Sum, Case, When, IntegerField
import io
from openpyxl import Workbook
from openpyxl.styles import Font
from rest_framework import generics
from django.db.models import Subquery, OuterRef
from schedularApi.models import SchedularBatch
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.serializers import EmailSerializer
from django_rest_passwordreset.tokens import get_token_generator
from zohoapi.models import Vendor

from urllib.parse import urlencode
from django.http import HttpResponseRedirect
import pdfkit
import os

# Create your views here.
from collections import defaultdict
import pandas as pd
from django.http import HttpResponse
import environ

env = environ.Env()

wkhtmltopdf_path = os.environ.get("WKHTMLTOPDF_PATH", r"/usr/local/bin/wkhtmltopdf")

pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")


def create_send_email(user_email, file_name):
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


def convert_to_24hr_format(time_str):
    time_obj = datetime.strptime(time_str, "%I:%M %p")
    time_24hr = time_obj.strftime("%H:%M")
    return time_24hr


def refresh_google_access_token(user_token):
    if not user_token:
        return None

    refresh_token = user_token.refresh_token
    access_token_expiry = user_token.access_token_expiry
    auth_code = user_token.authorization_code
    if not refresh_token:
        return None

    access_token_expiry = int(access_token_expiry)

    expiration_timestamp = user_token.updated_at + timezone.timedelta(
        seconds=access_token_expiry
    )

    if expiration_timestamp <= timezone.now():
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "refresh_token": refresh_token,
            "client_id": env("GOOGLE_OAUTH2_CLIENT_ID"),
            "client_secret": env("GOOGLE_OAUTH2_CLIENT_SECRET"),
            "grant_type": "refresh_token",
        }

        response = requests.post(token_url, data=token_data)
        token_json = response.json()

        if "access_token" in token_json:
            user_token.access_token = token_json["access_token"]
            user_token.access_token_expiry = token_json.get("expires_in")
            user_token.updated_at = timezone.now()
            user_token.save()

            return user_token.access_token

    return user_token.access_token


def refresh_microsoft_access_token(user_token):
    if not user_token:
        return None

    refresh_token = user_token.refresh_token
    access_token_expiry = user_token.access_token_expiry
    auth_code = user_token.authorization_code
    if not refresh_token:
        return None

    access_token_expiry = int(access_token_expiry)

    expiration_timestamp = user_token.updated_at + timezone.timedelta(
        seconds=access_token_expiry
    )

    if expiration_timestamp <= timezone.now():
        token_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/token"

        token_data = {
            "client_id": env("MICROSOFT_CLIENT_ID"),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_secret": env("MICROSOFT_CLIENT_SECRET"),
        }

        response = requests.post(token_url, data=token_data)
        token_json = response.json()

        if "access_token" in token_json:
            user_token.access_token = token_json["access_token"]
            user_token.access_token_expiry = token_json.get("expires_in")
            user_token.updated_at = timezone.now()
            user_token.save()

            return user_token.access_token

    return user_token.access_token


def create_google_calendar_event(access_token, event_details, attendee_email, session):
    try:
        formatted_date = datetime.strptime(
            event_details.get("startDate"), "%d-%m-%Y"
        ).strftime("%Y-%m-%d")

        start_time = convert_to_24hr_format(event_details.get("startTime"))
        end_time = convert_to_24hr_format(event_details.get("endTime"))

        event_details_title = event_details.get("title")
        if event_details.get("title") == "Coaching Session Session":
            event_details_title = "Coaching Session"

        event_data = {
            "summary": event_details_title,
            "description": event_details.get("description"),
            "start": {
                "dateTime": f"{formatted_date}T{start_time}:00",
                "timeZone": "IST",
            },
            "end": {
                "dateTime": f"{formatted_date}T{end_time}:00",
                "timeZone": "IST",
            },
            "attendees": [
                {"email": attendee_email},
            ],
        }

        user_token = UserToken.objects.get(access_token=access_token)
        new_access_token = refresh_google_access_token(user_token)
        if not new_access_token:
            new_access_token = access_token

        # Make a POST request to the Google Calendar API
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            json=event_data,
            headers={
                "Authorization": f"Bearer {new_access_token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 200:
            response_data = response.json()

            calendar_event = CalendarEvent(
                event_id=response_data.get("id"),
                title=event_details_title,
                description=event_details.get("description"),
                start_datetime=f"{formatted_date}T{start_time}:00",
                end_datetime=f"{formatted_date}T{end_time}:00",
                attendee=attendee_email,
                creator=response_data.get("creator", {}).get("email", ""),
                session=session,
                account_type="google",
            )
            calendar_event.save()

            return {
                "message": "Event created successfully",
                "event_data": response_data,
            }
        else:
            return {
                "error": "Failed to create event",
                "status_code": response.status_code,
            }

    except Exception as e:
        return {"error": "An error occurred", "details": str(e)}


def create_microsoft_calendar_event(
    access_token, event_details, attendee_email_name, session
):
    event_create_url = "https://graph.microsoft.com/v1.0/me/events"

    formatted_date = datetime.strptime(event_details["startDate"], "%d-%m-%Y").strftime(
        "%Y-%m-%d"
    )

    start_datetime = (
        f"{formatted_date}T{convert_to_24hr_format(event_details['startTime'])}:00"
    )
    end_datetime = (
        f"{formatted_date}T{convert_to_24hr_format(event_details['endTime'])}:00"
    )

    event_details_title = event_details["title"]
    if event_details["title"] == "Coaching Session Session":
        event_details_title = "Coaching Session"

    event_payload = {
        "subject": event_details_title,
        "body": {"contentType": "HTML", "content": event_details["description"]},
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        "attendees": [{"emailAddress": attendee_email_name, "type": "required"}],
    }

    user_token = UserToken.objects.get(access_token=access_token)
    new_access_token = refresh_microsoft_access_token(user_token)
    if not new_access_token:
        new_access_token = access_token

    headers = {
        "Authorization": f"Bearer {new_access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(event_create_url, json=event_payload, headers=headers)

    if response.status_code == 201:
        microsoft_response_data = response.json()

        calendar_event = CalendarEvent(
            event_id=microsoft_response_data.get("id"),
            title=event_details_title,
            description=event_details.get("description"),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendee=attendee_email_name.get("address"),
            creator=microsoft_response_data.get("organizer", {})
            .get("emailAddress", {})
            .get("address", ""),
            session=session,
            account_type="microsoft",
        )
        calendar_event.save()

        print("Event created successfully.")
        return True
    else:
        print(f"Event creation failed. Status code: {response.status_code}")
        print(response.text)
        return False


def delete_google_calendar_event(access_token, event_id):
    try:
        response = requests.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 204:
            return {"message": "Event deleted successfully"}
        elif response.status_code == 404:
            return {"error": "Event not found"}
        else:
            return {
                "error": "Failed to delete event",
                "status_code": response.status_code,
            }

    except Exception as e:
        return {"error": "An error occurred", "details": str(e)}


def delete_microsoft_calendar_event(access_token, event_id):
    try:
        event_delete_url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.delete(event_delete_url, headers=headers)

        if response.status_code == 204:
            return {"message": "Event deleted successfully"}
        elif response.status_code == 404:
            return {"error": "Event not found"}
        else:
            return {
                "error": "Failed to delete event",
                "status_code": response.status_code,
            }

    except Exception as e:
        return {"error": "An error occurred", "details": str(e)}


def create_notification(user, path, message):
    notification = Notification.objects.create(user=user, path=path, message=message)
    return notification


#  this returns in dd-mm-yyyy hh:mm a
def format_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
    return dt.strftime("%d-%m-%Y %I:%M %p")


def get_date(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000) + timedelta(
        hours=5, minutes=30
    )  # Convert milliseconds to seconds
    return dt.strftime("%d-%m-%Y")


def get_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000) + timedelta(
        hours=5, minutes=30
    )  # Convert milliseconds to seconds
    return dt.strftime("%I:%M %p")


def generateManagementToken():
    expires = 24 * 3600
    now = datetime.utcnow()
    exp = now + timedelta(seconds=expires)
    return jwt.encode(
        payload={
            "access_key": env("100MS_APP_ACCESS_KEY"),
            "type": "management",
            "version": 2,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": exp,
            "nbf": now,
        },
        key=env("100MS_APP_SECRET"),
    )


def generate_room_id(email):
    management_token = generateManagementToken()

    try:
        payload = {
            "name": email.replace(".", "-").replace("@", ""),
            "description": "This is a sample description for the room",
            "region": "in",
        }

        response_from_100ms = requests.post(
            "https://api.100ms.live/v2/rooms",
            headers={
                "Authorization": f"Bearer {management_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if response_from_100ms.status_code == 200:
            room_id = response_from_100ms.json().get("id")
            return room_id
        else:
            return None
    except Exception as e:
        print(f"Error while generating meeting link: {str(e)}")
        return None


def get_trimmed_emails(emails):
    res = []
    for email in emails:
        res.append(email.strip())
    return res


SESSION_TYPE_VALUE = {
    "chemistry": "Chemistry",
    "tripartite": "Tripartite",
    "goal_setting": "Goal Setting",
    "coaching_session": "Coaching Session",
    "mid_review": "Mid Review",
    "end_review": "End Review",
    "closure_session": "Closure Session",
    "stakeholder_without_coach": "Tripartite Without Coach",
    "interview": "Interview",
    "stakeholder_interview": "Stakeholder Interview",
}

FIELD_NAME_VALUES = {
    "location": "Work Location",
    "other_certification": "Assessment Certification",
    "area_of_expertise": "Industry",
    "job_roles": "Job roles",
    "companies_worked_in": "Companies worked in",
    "language": "Language Proficiency",
    "education": "Education institutions",
    "domain": "Functional Domain",
    "client_companies": "Client companies",
    "educational_qualification": "Educational Qualification",
}


@api_view(["POST"])
@permission_classes([AllowAny])
def create_pmo(request):
    # Get data from request
    name = request.data.get("name")
    email = request.data.get("email", "").strip()
    phone = request.data.get("phone")
    username = email  # username and email are the same
    password = request.data.get("password")

    room_id = generate_room_id(email)

    # Check if required data is provided
    if not all([name, email, phone, username, password, room_id]):
        return Response({"error": "All required fields must be provided."}, status=400)

    try:
        with transaction.atomic():
            # Check if the user already exists
            user = User.objects.filter(email=email).first()

            if not user:
                # If the user does not exist, create a new user
                user = User.objects.create_user(
                    username=username, password=password, email=email
                )
                profile = Profile.objects.create(user=user)

            else:
                profile = Profile.objects.get(user=user)

            # Create or get the "pmo" role
            pmo_role, created = Role.objects.get_or_create(name="pmo")
            profile.roles.add(pmo_role)
            profile.save()

            # Create the PMO User using the Profile
            pmo_user = Pmo.objects.create(
                user=profile, name=name, email=email, phone=phone, room_id=room_id
            )

            # Return success response without room_id
            return Response({"message": "PMO added successfully."}, status=201)

    except IntegrityError as e:
        return Response({"error": "User with this email already exists."}, status=400)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


# room_id = ""
# management_token = generateManagementToken()
# try:
#     response_from_100ms = requests.post(
#     "https://api.100ms.live/v2/rooms",
#                         headers={
#                             "Authorization": f"Bearer {management_token}",
#                             "Content-Type": "application/json",
#                         },
#                         json={
#                             "name": email.replace(".", "-").replace("@", ""),
#                             "description": "This is a sample description for the room",
#                             "region": "in",
#                         },
#                     )
#     if response_from_100ms.status_code == 200:
#         room_id = response_from_100ms.json().get("id")
# except Exception as e:
#     print(f"Error while generating meeting link, {str(e)}")

# # Create pmo user
# @api_view(["POST"])
# def create_pmo(request):
#     # Get data from request
#     name = request.data.get("name")
#     email = request.data.get("email")
#     phone = request.data.get("phone")
#     username = request.data.get("email")  # username and email are same
#     password = request.data.get("password")
#     # Check if required data is provided
#     if not all([name, email, phone, username, password]):
#         return Response({"error": "All required fields must be provided."}, status=400)

#     try:
#         with transaction.atomic():
#             # Create the Django User
#             user = User.objects.create_user(
#                 username=username, password=password, email=email
#             )
#             # Create the PMO Profile linked to the User
#             pmo_profile = Profile.objects.create(user=user, type="pmo")
#             # Create the PMO User using the Profile
#             pmo_user = Pmo.objects.create(
#                 user=pmo_profile, name=name, email=email, phone=phone
#             )
#         # Return success response
#         return Response({"message": "PMO added successfully."}, status=201)

#     except Exception as e:
#         # Return error response if any exception occurs
#         return Response({"error": str(e)}, status=500)


@api_view(["PUT"])
def approve_coach(request):
    try:
        # Get the Coach object
        unapproved_coach = request.data["coach"]
        room_id = request.data["room_id"]
        coach = Coach.objects.get(id=unapproved_coach["id"])

        # Change the is_approved field to True
        coach.is_approved = True
        coach.room_id = room_id
        coach.save()

        path = f"/profile"

        message = f"Congratulations ! Your profile has been approved. You will be notified for projects that match your profile. Thank You !"

        create_notification(coach.user.user, path, message)
        # Return success response
        # Send approval email to the coach
        send_mail_templates(
            "coach_templates/pmo_approves_profile.html",
            [coach.email],
            "Congratulations! Your Coach Registration is Approved",
            {
                "name": f"{coach.first_name} {coach.last_name}",
            },
            [],
        )
        return Response({"message": "Coach approved successfully."}, status=200)

    except Coach.DoesNotExist:
        # Return error response if Coach with the provided ID does not exist
        return Response({"error": "Coach does not exist."}, status=404)

    except Exception as e:
        # Return error response if any other exception occurs
        return Response({"error": str(e)}, status=500)


@api_view(["PUT"])
def update_coach_profile(request, id):
    try:
        coach = Coach.objects.get(id=id)
        mutable_data = request.data.copy()
        if "coach_id" not in mutable_data or not mutable_data["coach_id"]:
            mutable_data["coach_id"] = coach.coach_id

    except Coach.DoesNotExist:
        return Response(status=404)

    internal_coach = json.loads(request.data["internal_coach"])
    organization_of_coach = request.data.get("organization_of_coach")
    user = coach.user.user
    new_email = mutable_data.get("email").strip()
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
    elif new_email and new_email != user.email:
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

    if internal_coach and not organization_of_coach:
        return Response(
            {
                "error": "Organization field must not be empty if internal coach is selected yes."
            },
            status=400,
        )
    profile_edit_start = ProfileEditActivity.objects.create(
        user=coach.user.user,
        timestamp=timezone.now(),
    )
    serializer = CoachSerializer(coach, data=mutable_data, partial=True)

    coach_id = request.data.get("coach_id")

    # Check if coach_id exists in request.data
    if coach_id is not None:
        # Check if any other coach already has this coach_id
        existing_coach = Coach.objects.exclude(id=id).filter(coach_id=coach_id).first()

        if existing_coach:
            return Response({"error": "Coach ID must be unique"}, status=400)

    if serializer.is_valid():
        serializer.save()
        depth_serializer = CoachDepthOneSerializer(coach)
        is_caas_allowed = Project.objects.filter(
            coaches_status__coach=user.profile.coach
        ).exists()
        is_seeq_allowed = SchedularBatch.objects.filter(
            coaches=user.profile.coach
        ).exists()
        roles = []
        for role in roles:
            roles.append(role.name)
        return Response(
            {
                **depth_serializer.data,
                "is_caas_allowed": is_caas_allowed,
                "is_seeq_allowed": is_seeq_allowed,
                "roles": roles,
                "last_login": coach.user.user.last_login,
                "user": {**depth_serializer.data["user"], "type": "coach"},
            }
        )
    return Response(serializer.errors, status=400)


@api_view(["GET"])
def get_coaches(request):
    try:
        # Get all the Coach objects
        coaches = Coach.objects.filter(is_approved=True)

        # Serialize the Coach objects
        serializer = CoachSerializer(coaches, many=True)

        # Return the serialized Coach objects as the response
        return Response(serializer.data, status=200)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


def updateLastLogin(email):
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = User.objects.get(username=email)
    user.last_login = today
    user.save()


@api_view(["POST"])
def pmo_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if email is None or password is None:
        return Response({"error": "Please provide both email and password"}, status=400)

    user = authenticate(username=email, password=password, type="pmo")
    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    pmo = Pmo.objects.get(user=user.profile)

    updateLastLogin(pmo.email)
    return Response(
        {
            "token": token.key,
            "pmo": {
                "name": pmo.name,
                "email": pmo.email,
                "phone": pmo.phone,
                "last_login": pmo.user.user.last_login,
            },
        }
    )


@api_view(["POST"])
def coach_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if email is None or password is None:
        return Response({"error": "Please provide both email and password"}, status=400)

    user = authenticate(username=email, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    try:
        coach = Coach.objects.get(user=user.profile)
    except Coach.DoesNotExist:
        return Response({"error": "Coach not found"}, status=404)

    # Return the coach information in the response
    coach_serializer = CoachSerializer(coach)
    updateLastLogin(coach.email)
    return Response({"coach": coach_serializer.data}, status=200)


@api_view(["GET"])
def get_management_token(request):
    management_token = generateManagementToken()
    return Response(
        {"message": "Success", "management_token": management_token}, status=200
    )


# @api_view(['POST'])
# def create_user_without_password(request):
#     try:
#         with transaction.atomic():
#             # Check if username field is provided
#             if 'username' not in request.data:
#                 raise ValueError('Username field is required')
#             # Create user object with unusable password
#             user = User.objects.create_user(
#                 username=request.data['username'],
#                 email=request.data['username'])
#             user.set_unusable_password()
#             user.save()

#             # Create the learner profile
#             learner_profile = Profile.objects.create(user=user, type='learner')

#             # Create the learner object
#             learner = Learner.objects.create(user=learner_profile, name=request.data.get('name'), email=request.data['username'], phone=request.data.get('phone'))

#             # Return success response
#             return Response({}, status=200)

#     except ValueError as e:
#         # Handle missing or invalid request data
#         return Response({'error': str(e)}, status=400)

#     except IntegrityError:
#         # Handle username or email already exists
#         return Response({'error': 'Username or email already exists'}, status=409)

#     except Exception as e:
#         # Handle any other exceptions
#         transaction.set_rollback(True) # Rollback the transaction
#         return Response({'error': str(e)}, status=500)


# @api_view(['POST'])
# def otp_generation(request):
#     try:
#         learner = Learner.objects.get(email=request.data['email'])
#         try:
#             # Check if OTP already exists for the learner
#             otp_obj = OTP.objects.get(learner=learner)
#             otp_obj.delete()
#         except OTP.DoesNotExist:
#             pass

#         # Generate OTP and save it to the database
#         otp = get_random_string(length=6, allowed_chars='0123456789')
#         created_otp = OTP.objects.create(learner=learner, otp=otp)

#         # Send OTP on email to learner
#         subject = f'Meeraq Login Otp'
#         message = f'Dear {learner.name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [learner.email])

#         return Response({'success': True,'otp':created_otp.otp})


#     except Learner.DoesNotExist:
#         # Handle the case where the learner with the given email does not exist
#         return Response({'error': 'Learner with the given email does not exist.'}, status=400)

#     except Exception as e:
#         # Handle any other exceptions
#         return Response({'error': str(e)}, status=500)

# @api_view(['POST'])
# def otp_validation(request):
#     otp_obj = OTP.objects.filter(learner__email=request.data['email'], otp=request.data['otp']).order_by('-created_at').first()

#     if otp_obj is None:
#         raise AuthenticationFailed('Invalid OTP')

#     learner = otp_obj.learner
#     token, created = Token.objects.get_or_create(user=learner.user.user)

#     # Delete the OTP object after it has been validated
#     otp_obj.delete()

#     learner_data = {'id':learner.id,'name':learner.name,'email': learner.email,'phone': learner.email,'last_login': learner.user.user.last_login ,'token': token.key}
#     updateLastLogin(learner.email)
#     return Response({ 'learner': learner_data},status=200)


@api_view(["POST"])
def create_project_cass(request):
    organisation = Organisation.objects.filter(
        id=request.data["organisation_name"]
    ).first()
    if not organisation:
        organisation = Organisation(
            name=request.data["organisation_name"], image_url=request.data["image_url"]
        )
    organisation.save()
    desc = request.data["project_description"]
    try:
        project = Project(
            # print(organisation.name, organisation.image_url, "details of org")
            name=request.data["project_name"],
            organisation=organisation,
            approx_coachee=request.data["approx_coachee"],
            frequency_of_session=request.data["frequency_of_session"],
            # currency=request.data["currency"],
            # price_per_hour=request.data["price_per_hour"],
            # coach_fees_per_hour=request.data["coach_fees_per_hour"],
            project_type="CAAS",
            interview_allowed=request.data["interview_allowed"],
            # chemistry_allowed= request.data['chemistry_allowed'],
            specific_coach=request.data["specific_coach"],
            empanelment=request.data["empanelment"],
            end_date=datetime.now() + timedelta(days=365),
            tentative_start_date=request.data["tentative_start_date"],
            mode=request.data["mode"],
            sold=request.data["sold"],
            project_description=desc,
            # updated_to_sold= request.data['updated_to_sold'],
            location=json.loads(request.data["location"]),
            enable_emails_to_hr_and_coachee=request.data.get(
                "enable_emails_to_hr_and_coachee", True
            ),
            steps=dict(
                project_structure={"status": "pending"},
                coach_list={"status": "pending"},
                coach_consent={"status": "pending"},
                coach_list_to_hr={"status": "pending"},
                interviews={"status": "pending"},
                add_learners={"status": "pending"},
                coach_approval={"status": "pending"},
                chemistry_session={"status": "pending"},
                coach_selected={"status": "pending"},
                final_coaches={"status": "pending"},
                project_live="pending",
            ),
            status="presales",
        )

        project.save()
        try:
            userId = request.data.get("user_id")
            user_who_created = User.objects.get(id=userId)
            project = project
            timestamp = timezone.now()

            createProject = CreateProjectActivity.objects.create(
                user_who_created=user_who_created, project=project, timestamp=timestamp
            )

            createProject.save()
        except Exception as e:
            pass

    except IntegrityError as e:
        return Response({"error": "Project with this name already exists"}, status=400)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to create project."}, status=400)
    hr_emails = []
    project_name = project.name

    for hr in request.data["hr"]:
        single_hr = HR.objects.get(id=hr)
        # print(single_hr)
        project.hr.add(single_hr)
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
        path = f"/projects/caas/progress/{project.id}"
        message = f"A new project - {project.name} has been created for the organisation - {project.organisation.name}"
        for hr_member in project.hr.all():
            create_notification(hr_member.user.user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response(
        {"message": "Project created successfully", "project_id": project.id},
        status=200,
    )


# @api_view(['POST'])
# def create_project(request):
#     organisation = Organisation.objects.filter(name=request.data['organisation_name']).first()
#     if not organisation:
#         organisation= Organisation(
#             name=request.data['organisation_name'], image_url=request.data['image_url']
#         )
#     organisation.save()


#     project= Project(
#         project_type = request.data['project_type'],
#         name=request.data['project_name'],
#         organisation=organisation,
#         total_sessions=request.data['total_session'],
# 		end_date=request.data['end_date'],
#         cost_per_session=request.data['cost_per_session'],
#         currency=request.data['currency'],
#         sessions_per_employee=request.data['sessions_per_employee'],
#         session_duration= request.data['session_duration'],
#         status=dict(project_live='pending')
#     )
#     hr_emails=[]
#     coach_emails=[]
#     project.save()
#     project_name= project.name
#     for coach in request.data["coach_id"]:
#         single_coach = Coach.objects.get(id=coach)
#         coach_emails.append(single_coach.email)
#         project.coaches.add(single_coach)

#     # Send email notification to the coach
#     subject = f'Hey Coach! You have assigned to a project {project_name}'
#     message = f'Dear {coach_emails},\n\nPlease be there to book slots requested by learner in this {project_name}. Best of luck!'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, coach_emails)


#     project_name= project.name
#     print(project_name)
#     for hr in request.data["hr_id"]:
#         single_hr = HR.objects.get(id=hr)
#         print(single_hr)
#         hr_emails.append(single_hr.email)
#         project.hr.add(single_hr)


#     hrs= create_hr(request.data['hr'])
#     for hr in hrs:
#         project.hr.add(hr)

#     try:
#         learners = create_learners(request.data['learners'])
#         for learner in learners:
#             project.learner.add(learner)
#     except Exception as e:
#         # Handle any exceptions from create_learners
#         return Response({'error': str(e)}, status=500)

#     return Response({'message': "Project created!"}, status=200)


def create_learners(learners_data):
    try:
        with transaction.atomic():
            if not learners_data:
                raise ValueError("Learners data is required")
            learners = []
            for learner_data in learners_data:
                # Check if username field is provided
                email = learner_data.get('email','').strip()
                if "email" not in learner_data:
                    raise ValueError("Username field is required")
                # Check if user already exists
                user = User.objects.filter(username=email).first()
                if user:
                    # If user exists, check if learner already exists
                    learner = Learner.objects.filter(user__user=user).first()

                    if learner:
                        learners.append(learner)
                        continue
                    else:
                        profile = Profile.objects.get(user=user)

                else:
                    # If learner does not exist, create the user object with an unusable password
                    temp_password = "".join(
                        random.choices(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits,
                            k=8,
                        )
                    )
                    user = User.objects.create_user(
                        username=email,
                        password=temp_password,
                        email=email,
                    )
                    # user.set_unusable_password()
                    user.save()
                    # Create the learner profile
                    profile = Profile.objects.create(user=user)
                learner_role, created = Role.objects.get_or_create(name="learner")
                profile.roles.add(learner_role)
                profile.save()

                learner = Learner.objects.create(
                    user=profile,
                    name=learner_data.get("name"),
                    email=email,
                    phone=learner_data.get("phone"),
                )
                learners.append(learner)
            # Return response with learners created or already existing
            serializer = LearnerSerializer(learners, many=True)
            return learners

    except ValueError as e:
        # Handle missing or invalid request data
        raise ValueError(str(e))

    except Exception as e:
        # Handle any other exceptions
        # transaction.set_rollback(True) # Rollback the transaction
        raise Exception(str(e))


# Create learner user
# @api_view(['POST'])
# def create_learner(request):
#     # Get data from request
#     name = request.data.get('name')
#     email = request.data.get('email')
#     phone = request.data.get('phone')
#     area_of_expertise= request.data.get('area_of_expertise')
#     years_of_experience=request.data.get('years_of_experience')
#     username = request.data.get('email') # username and email are same
#     password = request.data.get('password')
#     # Check if required data is provided
#     if not all([name, email, phone, area_of_expertise, years_of_experience, username, password]):
#         return Response({'error': 'All required fields must be provided.'}, status=400)

#     try:
#         with transaction.atomic():
#             # Create the Django User
#             user = User.objects.create_user(username=username, password=password,email=email)
#             # Create the learner Profile linked to the User
#             learner_profile = Profile.objects.create(user=user, type='learner')
#             # Create the learner User using the Profile
#             learner = Learner.objects.create(user=learner_profile, name=name, email=email, phone=phone)
#         # Return success response
#         return Response({'message': 'Learner added successfully.'}, status=201)

#     except Exception as e:
#         # Return error response if any exception occurs
#         return Response({'error': str(e)}, status=500)


# @api_view(["POST"])
# def get_coaches_by_project(request):
#     project_id = request.data['project_id']
#     project= Project.objects.get(id=project_id)
#     coaches= project.coaches.name
#     return Response({"message": "Success"}, status=200)

# @api_view(["POST"])
# def get_learners_by_project(request):
#     project_id = request.data['project_id']
#     project= Project.objects.get(id=project_id)
#     learner= project.learner.name
#     return Response({"message": "Success"}, status=200)


# get projects details


# @api_view(["GET"])
# def project_details(request, project_id):
#     try:
#         project = Project.objects.get(id=project_id)
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     serializer =  ProjectDepthTwoSerializer(project)
#     return Response(serializer.data, status=200)


# @api_view(['GET'])
# def get_projects(request):
#     projects = Project.objects.all()
#     serializer = ProjectSerializer(projects, many=True)
#     return Response(serializer.data)


@api_view(["GET"])
def get_ongoing_projects(request):
    projects = Project.objects.filter(steps__project_live="pending")
    serializer = ProjectDepthTwoSerializer(projects, many=True)
    for project_data in serializer.data:
        latest_update = (
            Update.objects.filter(project__id=project_data["id"])
            .order_by("-created_at")
            .first()
        )
        project_data["latest_update"] = latest_update.message if latest_update else None
    return Response(serializer.data)


@api_view(["GET"])
def get_project_updates(request, project_id):
    updates = Update.objects.filter(project__id=project_id).order_by("-created_at")
    serializer = UpdateDepthOneSerializer(updates, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def add_project_update(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
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


# @api_view(['GET'])
# def get_completed_projects(request):
#     projects = Project.objects.filter(steps__project_live="complete")
#     serializer = ProjectSerializer(projects, many=True)
#     return Response(serializer.data)


@api_view(["GET"])
def get_projects_of_learner(request, learner_id):
    projects = Project.objects.filter(engagement__learner__id=learner_id)
    serializer = ProjectDepthTwoSerializer(projects, many=True)
    return Response(serializer.data)


# @api_view(['POST'])
# def create_session_request(request):
#     time_arr = []
#     for time in request.data['availibility']:
#         availibility_serilizer = AvailibilitySerializer(data = time)
#         if availibility_serilizer.is_valid():
#             avil_id = availibility_serilizer.save()
#             time_arr.append(avil_id.id)
#         else:
#             return Response({"message": str(availibility_serilizer.errors),}, status=401)
#     session = {
#            "learner": request.data['learner'],
#            "project": request.data['project'],
#            "availibility":time_arr
# 		      }
#     session_serilizer = SessionRequestSerializer(data = session)
#     if session_serilizer.is_valid():
#         session_serilizer.save()
#         return Response({"message": "Success"}, status=201)
#     else:
#         return Response({"message": str(session_serilizer.errors),}, status=401)


# Coach- view session request
# @api_view(["GET"])
# def session_requests_by_coach(request, coach_id):
#     coach = get_object_or_404(Coach, id=coach_id)
#     session_requests = SessionRequest.objects.filter(project__coaches=coach, is_booked=False)
#     serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)

# @api_view(['POST'])
# def book_session(request):
#     serializer = SessionSerializer(data=request.data)
#     if serializer.is_valid():
#         session = serializer.save()
#         # Mark the session request as booked
#         session_request = session.session_request
#         session_request.is_booked = True
#         session_request.save()

#         coach=session.coach
#         coach_email=coach.email
#         learner=session.session_request.learner
#         learner_email= learner.email

#     # Send email notification to the coach
#     subject = 'Hello coach your session is booked.'
#     message = f'Dear {coach.first_name},\n\nThank you booking slots of learner.Please be ready on date and time to complete session. Best of luck!'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [coach_email])


#     # Send email notification to the learner
#     subject = 'Hello learner your session is booked.'
#     message = f'Dear {learner.name},\n\nThank you booking slots of learner.Please be ready on date and time to complete session. Best of luck!'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [learner_email])

#     return Response({'message':'','details':serializer.data}, status=201)
#     return Response(serializer.errors, status=400)


# @api_view(["GET"])
# def get_upcoming_session_coach(request, coach_id):
#     coach = get_object_or_404(Coach, id=coach_id)
#     current_timestamp =  int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(coach=coach,end_time_int__gt=current_timestamp)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_past_session_coach(request, coach_id):
#     coach = get_object_or_404(Coach, id=coach_id)
#     current_timestamp = int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__lt=current_timestamp,coach=coach)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_upcoming_session_learner(request, learner_id):
#     learner = get_object_or_404(Learner, id=learner_id)
#     current_timestamp =  int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__gt=current_timestamp,session_request__learner=learner)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_past_session_learner(request, learner_id):
#     learner = get_object_or_404(Learner, id=learner_id)
#     current_timestamp = int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__lt=current_timestamp,session_request__learner=learner)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)

# @api_view(["POST"])
# def add_learner(request, project_id):
#     try:
#         project = Project.objects.get(id=project_id)
#     except Project.DoesNotExist:
#         raise ParseError("Invalid project id provided.")

#     email = request.data.get('email')
#     if not email:
#         raise ValidationError("Email is required.")

#     with transaction.atomic():
#         # Create user and learner profile
#         user = User.objects.create_user(username=email, email=email)
#         learner_profile = Profile.objects.create(user=user, type='learner')

#         # Create learner
#         learner_data = {'name': request.data.get('name'), 'email': email, 'phone': request.data.get('phone')}
#         learner = Learner.objects.create(user=learner_profile, **learner_data)

#         # Add learner to project
#         project.learner.add(learner)
#         project.save()

#     serializer = ProjectSerializer(project)
#     return Response({'message':'Learner added successfully','details':serializer.data}, status=201)


# @api_view(["GET"])
# def get_upcoming_session(request):
#     current_timestamp =  int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__gt=current_timestamp)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
# return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_past_session(request):
#     current_timestamp = int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__lt=current_timestamp)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_session_requests(request):
#     session_requests = SessionRequest.objects.filter(is_booked=False)
#     serializer = SessionRequestDepthTwoSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)


# @api_view(['POST'])
# def complete_project(request):
#     project = get_object_or_404(Project, id=request.data['project_id'])
#     project.status = 'Completed'
#     project.save()
#     project_serializer = ProjectSerializer(project)
#     return Response({'message':'Project marked as complete!','details':project_serializer.data},status=200)


# @api_view(['POST'])
# def mark_coach_joined_session(request):
#     session = get_object_or_404(Session, id=request.data['session_id'])
#     session.coach_joined = True
#     session.save()
#     session_serializer = SessionSerializer(session)
#     return Response({"message":"","details":session_serializer.data},status=200)


# @api_view(['POST'])
# def mark_learner_joined_session(request):
#     session = get_object_or_404(Session, id=request.data['session_id'])
#     session.learner_joined = True
#     session.save()
#     session_serializer = SessionSerializer(session)
#     return Response({'message':'','details':session_serializer.data},status=200)

# @api_view(['GET'])
# def get_session_request_count(request):
#     session_requests = SessionRequest.objects.filter(is_booked=False)
#     count = len(session_requests)
#     return Response({'session_request_count':count },status=200)


# @api_view(["GET"])
# def get_pending_session_requests_by_learner(request,learner_id):
#     session_requests = SessionRequest.objects.filter(is_booked=False,learner__id=learner_id)
#     serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_all_session_requests_by_learner(request,learner_id):
#     session_requests = SessionRequest.objects.filter(learner__id=learner_id)
#     serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)


# @api_view(['POST'])
# def forgot_password(request):
#     reset_password_request = ResetPasswordRequestTokenView.as_view()

#     response = reset_password_request(request)
#     if response.status_code == 200:
#         email = request.data.get('email')
#         token = response.data.get('token')
#         print(token)
#     return Response(response.data, status=response.status_code)


# @api_view(['POST'])
# def otp_generation_hr(request):
#     try:
#         hr = HR.objects.get(email=request.data['email'])
#         try:
#             # Check if OTP already exists for the hr
#             otp_obj = OTP_HR.objects.get(hr=hr)
#             otp_obj.delete()
#         except OTP_HR.DoesNotExist:
#             pass

#         # Generate OTP and save it to the database
#         otp = get_random_string(length=6, allowed_chars='0123456789')
#         created_otp = OTP_HR.objects.create(hr=hr, otp=otp)

#         # Send OTP on email to hr
#         subject = f'Meeraq Login Otp'
#         message = f'Dear {hr.first_name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [hr.email])

#         return Response({'success': True,'otp':created_otp.otp})


#     except HR.DoesNotExist:
#         # Handle the case where the hr with the given email does not exist
#         return Response({'error': 'HR with the given email does not exist.'}, status=400)

#     except Exception as e:
#         # Handle any other exceptions
#         return Response({'error': str(e)}, status=500)


# @api_view(['POST'])
# def otp_validation_hr(request):
#     otp_obj = OTP_HR.objects.filter(hr__email=request.data['email'], otp=request.data['otp']).order_by('-created_at').first()

#     if otp_obj is None:
#         raise AuthenticationFailed('Invalid OTP')

#     hr = otp_obj.hr
#     token, created = Token.objects.get_or_create(user=hr.user.user)

#     # Delete the OTP object after it has been validated
#     otp_obj.delete()

#     hr_data = {'id':hr.id,'name':hr.first_name,'email': hr.email,'phone': hr.phone,'last_login': hr.user.user.last_login ,'token': token.key}
#     updateLastLogin(hr.email)
#     return Response({ 'hr': hr_data},status=200)


@api_view(["GET"])
def get_ongoing_projects_of_hr(request, hr_id):
    projects = Project.objects.filter(hr__id=hr_id, steps__project_live="pending")
    serializer = ProjectDepthTwoSerializer(projects, many=True)
    return Response(serializer.data, status=200)


# @api_view(['GET'])
# def get_completed_projects_of_hr(request,hr_id):
#     projects = Project.objects.filter(hr__id = hr_id, steps__project_live="complete")
#     serializer = ProjectDepthTwoSerializer(projects, many=True)
#     return Response(serializer.data, status=200)

# @api_view(['POST'])
# def add_coach(request):
#     # Get data from request
#     first_name = request.data.get('first_name')
#     last_name = request.data.get('last_name')
#     email = request.data.get('email')
#     age = request.data.get('age')
#     gender = request.data.get('gender')
#     domain = request.data.get('domain')
#     room_id = request.data.get('room_id')
#     phone = request.data.get('phone')
#     level = request.data.get('level')
#     rating = "5"
#     area_of_expertise = request.data['area_of_expertise']
#     username = request.data.get('email') # keeping username and email same
#     password = request.data.get('password')

#     print(first_name, last_name, email, age, gender, domain, room_id, phone, level,  username, password)

#     # Check if required data is provided
#     if not all([first_name, last_name, email, age, gender, domain, room_id, phone, level,  username, password]):
#         return Response({'error': 'All required fields must be provided.'}, status=400)

#     try:
#         # Create the Django User
#         with transaction.atomic():
#             user = User.objects.create_user(username=username, password=password,email=email)

#             # Create the Coach Profile linked to the User
#             coach_profile = Profile.objects.create(user=user, type='coach')

#             # Create the Coach User using the Profile
#             coach_user = Coach.objects.create(user=coach_profile, first_name= first_name, last_name=last_name, email=email, room_id=room_id, phone=phone, level=level, rating=rating, area_of_expertise=area_of_expertise)

# 			# approve coach
#             coach = Coach.objects.get(id=coach_user.id)
#             # Change the is_approved field to True
#             coach.is_approved = True
#             coach.save()

#             full_name = coach_user.first_name + " " + coach_user.last_name


#             # Send email notification to the coach
#             subject = 'Welcome to our coaching platform'
#             message = f'Dear {full_name},\n\n You have been added to the Meeraq portal as a coach. \n Here is your credentials. \n\n Username: {email} \n Password: {password}\n\n Click on the link to login or reset the password http://localhost:3003/'
#             send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

#             # # Send email notification to the admin
#             admin_email = 'jatin@meeraq.com'
#             admin_message = f'Dear PMO! \n\n A new coach {full_name} has been added on our coaching platform.'
#             send_mail(subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email])

#             # Return success response
#         return Response({'message': 'Coach added successfully.'}, status=201)

#     except IntegrityError:
#         return Response({'error': 'A coach user with this email already exists.'}, status=400)

#     except Exception as e:
#         # Return error response if any other exception occurs
#         return Response({'error': 'An error occurred while creating the coach user.'}, status=500)


@api_view(["GET"])
def get_hr(request):
    try:
        # Get all the Coach objects
        hr = HR.objects.all()

        # Serialize the Coach objects
        serializer = HrSerializer(hr, many=True)

        # Return the serialized Coach objects as the response
        return Response(serializer.data, status=200)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


# def create_hr(hrs_data):
#     try:
#             if not hrs_data:
#                 raise ValueError('HR data is required')
#             hrs = []
#             for hr_data in hrs_data:
#                 print('email',hr_data)
#                 # Check if username field is provided
#                 # if 'email' not in hr_data:
#                 #     raise ValueError('Username field is required')

#                 # Check if user already exists
#                 user = User.objects.filter(username=hr_data).first()
#                 if user:
#                     # If user exists, check if hr already exists
#                     print('user exists',user)
#                     hr_profile = HR.objects.get(user__user=user)
#                     print(hr_profile,'hr_profile')
#                     if hr_profile:
#                         hrs.append(hr_profile)
#                         continue
#                 else:
#                 # If HR does not exist, create the user object with an unusable password
#                     user = User.objects.create_user(
#                         username=hr_data,
#                         email=hr_data
#                         )
#                     user.set_unusable_password()
#                     user.save()

#                 # Create the hr profile
#                     hr_profile = Profile.objects.create(user=user, type='hr')

#                 # Create the hr object
#                     hr = HR.objects.create(user=hr_profile , email=hr_data)
#                     hrs.append(hr)

#             # Return response with hr created or already existing
#             serializer = HrSerializer(hrs, many=True)
#             print(hrs,'helloo')
#             return hrs


#     except ValueError as e:
#         # Handle missing or invalid request data
#         raise ValueError(str(e))

#     except Exception as e:
#         # Handle any other exceptions
#         # transaction.set_rollback(True) # Rollback the transaction
#         raise Exception(str(e))


# @api_view(['POST'])
# def change_password(request):
#     return ResetPasswordConfirmTokenView.as_view()(request)


# @api_view(['POST'])
# def edit_project(request,project_id):
# 		print(project_id)
# 		organisation= Organisation(
#         name=request.data['organisation_name'], image_url=request.data['image_url']
#     )
# 		organisation.save()
# 		project = Project.objects.get(id=project_id)
# 		project.name = request.data['project_name']
# 		project.organisation = organisation
# 		project.total_sessions = request.data['total_sessions']
# 		project.cost_per_session = request.data['cost_per_session']
# 		project.session_duration = request.data['session_duration']
# 		project.sessions_per_employee = request.data['sessions_per_employee']
# 		project.currency=request.data['currency']
# 		project.end_date = request.data['end_date']
# 		project.coaches.clear()
# 		for coach_id in request.data['coach_id']:
# 				coach = Coach.objects.get(id = coach_id)
# 				project.coaches.add(coach)
# 		project.save()
# 		return Response({'message':'Project details updated!','details':{}},status=200)


# @api_view(['POST'])
# def delete_session_request(request, session_request_id):
# 		session_request = SessionRequest.objects.get(id = session_request_id)
# 		session_request.delete()
# 		return Response({'message':'','details':{'deleted_session_request_id': session_request_id}})


# @api_view(['GET'])
# def get_dashboard_details(request):
#     local_time = timezone.localtime(timezone.now())
#     india_tz = pytz.timezone('Asia/Kolkata')
#     india_time = local_time.astimezone(india_tz)
#     print(india_time)
#     current_datetime = timezone.localtime(timezone.now())
#     print(current_datetime)
#     start_of_day = india_time.replace(hour=0, minute=0, second=0, microsecond=0)
#     end_of_day = start_of_day + timedelta(days=1)
#     today_sessions = Session.objects.filter(
#         confirmed_availability__start_time__gte=start_of_day.timestamp() * 1000,
#         confirmed_availability__start_time__lt=end_of_day.timestamp() * 1000
#     )
#     sessions_serializer = SessionsDepthTwoSerializer(today_sessions,many=True)
#     session_requests = SessionRequest.objects.filter(is_booked=False)
#     # session_requests_serializer = SessionRequestDepthTwoSerializer(session_requests, many=True)
#     return Response({'todays_sessions': sessions_serializer.data,'session_requests_count': len(session_requests)})


# @api_view(['POST'])
# def invite_coach(request):
#     serializer = CoachInvitesSerializer(data=request.data)
#     if serializer.is_valid():
#         invite = serializer.save()
#         subject = f'Meeraq Portal invitation'
#         message = f'Dear {invite.name} \n\n Sign up on Meeraq coach portal'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invite.email])
#         return Response({'message':'Coach invited successfully!','details':serializer.data}, status=201)
#     return Response(serializer.errors, status=400)


# @api_view(['GET'])
# def get_coach_invites(request):
#     invites = CoachInvites.objects.order_by('-created_at')
#     serializer = CoachInvitesSerializer(invites, many=True)
#     return Response(serializer.data)


@api_view(["GET"])
def get_projects_and_sessions_by_coach(request, coach_id):
    projects = Project.objects.filter(coaches_status__coach__id=coach_id)
    # sessions = Session.objects.filter(session_request__project__in=projects,coach__id=coach_id)
    # session_serializer = SessionsDepthTwoSerializer(sessions, many=True)
    # sessions_dict = {}
    # for session in session_serializer.data:
    #     project_id = session['session_request']['project']['id']
    #     if project_id in sessions_dict:
    #         sessions_dict[project_id].append(session)
    #     else:
    #         sessions_dict[project_id] = [session]
    project_serializer = ProjectDepthTwoSerializer(projects, many=True)
    return Response({"projects": project_serializer.data})


# @api_view(["GET"])
# def coach_session_list(request, coach_id):
#     projects = Project.objects.filter(coaches_status__coach__id=coach_id)
#     project_serializer = ProjectDepthTwoSerializer(projects, many=True)

#     # Fetch sessions related to the coach
#     sessions = SessionRequestCaas.objects.filter(coach_id=coach_id)
#     session_serializer = SessionsDepthTwoSerializer(sessions, many=True)

#     # Group sessions by project ID
#     sessions_dict = {}
#     for session in session_serializer.data:
#         project_id = session['project']['id']
#         if project_id in sessions_dict:
#             sessions_dict[project_id].append(session)
#         else:
#             sessions_dict[project_id] = [session]

#     # Add the session data to the projects
#     for project_data in project_serializer.data:
#         project_id = project_data['id']
#         if project_id in sessions_dict:
#             project_data['sessions'] = sessions_dict[project_id]
#         else:
#             project_data['sessions'] = []

#     return Response({"projects": project_serializer.data})


@api_view(["GET"])
def coach_session_list(request, coach_id):
    projects = Project.objects.filter(coaches_status__coach__id=coach_id)
    project_serializer = ProjectDepthTwoSerializer(projects, many=True)

    # Fetch sessions related to the coach
    sessions = SessionRequestCaas.objects.filter(coach_id=coach_id)
    session_serializer = SessionRequestCaasSerializer(sessions, many=True)

    # Group sessions by project ID
    sessions_dict = {}
    for session in session_serializer.data:
        project_id = session["project"]
        if project_id in sessions_dict:
            sessions_dict[project_id].append(session)
        else:
            sessions_dict[project_id] = [session]

    # Add the session data to the projects
    for project_data in project_serializer.data:
        project_id = project_data["id"]
        if project_id in sessions_dict:
            project_data["sessions"] = sessions_dict[project_id]
        else:
            project_data["sessions"] = []

    return Response({"projects": project_serializer.data})


# @api_view(['POST'])
# def otp_generation_hr(request):
#     try:
#         hr = HR.objects.get(email=request.data['email'])
#         try:
#             # Check if OTP already exists for the hr
#             otp_obj = OTP_HR.objects.get(hr=hr)
#             otp_obj.delete()
#         except OTP_HR.DoesNotExist:
#             pass

#         # Generate OTP and save it to the database
#         otp = get_random_string(length=6, allowed_chars='0123456789')
#         created_otp = OTP_HR.objects.create(hr=hr, otp=otp)

#         # Send OTP on email to hr
#         subject = f'Meeraq Login Otp'
#         message = f'Dear {hr.first_name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [hr.email])

#         return Response({'success': True,'otp':created_otp.otp})


#     except HR.DoesNotExist:
#         # Handle the case where the hr with the given email does not exist
#         return Response({'error': 'HR with the given email does not exist.'}, status=400)

#     except Exception as e:
#         # Handle any other exceptions
#         return Response({'error': str(e)}, status=500)


# @api_view(['POST'])
# def otp_validation_hr(request):
#     otp_obj = OTP_HR.objects.filter(hr__email=request.data['email'], otp=request.data['otp']).order_by('-created_at').first()

#     if otp_obj is None:
#         raise AuthenticationFailed('Invalid OTP')

#     hr = otp_obj.hr
#     token, created = Token.objects.get_or_create(user=hr.user.user)

#     # Delete the OTP object after it has been validated
#     otp_obj.delete()

#     hr_data = {'id':hr.id,'name':hr.first_name,'email': hr.email,'phone': hr.phone,'last_login': hr.user.user.last_login ,'token': token.key}
#     updateLastLogin(hr.email)
#     return Response({ 'hr': hr_data},status=200)


# @api_view(['GET'])
# def get_ongoing_projects_of_hr(request,hr_id):
#     projects = Project.objects.filter(hr__id = hr_id,steps__project_live="pending")
#     serializer = ProjectDepthTwoSerializer(projects, many=True)
#     return Response(serializer.data, status=200)


# @api_view(['GET'])
# def get_completed_projects_of_hr(request,hr_id):
#     projects = Project.objects.filter(hr__id = hr_id, steps__project_live="complete")
#     serializer = ProjectDepthTwoSerializer(projects, many=True)
#     return Response(serializer.data, status=200)


def coach_exists(coach_id):
    return Coach.objects.filter(coach_id=coach_id).exists()


@api_view(["POST"])
def add_coach(request):
    # Get data from request
    coach_id = request.data.get("coach_id")
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    email = request.data.get("email", "").strip()
    age = request.data.get("age")
    gender = request.data.get("gender")
    domain = json.loads(request.data["domain"])
    room_id = request.data.get("room_id")
    phone = request.data.get("phone")
    phone_country_code = request.data.get("phone_country_code")
    level = request.data.get("level")
    currency = request.data.get("currency")
    education = json.loads(request.data["education"])
    rating = "5"
    min_fees = request.data["min_fees"]
    fee_remark = request.data.get("fee_remark", "")
    coaching_hours = request.data.get("coaching_hours")
    linkedin_profile_link = request.data["linkedin_profile_link"]
    companies_worked_in = json.loads(request.data["companies_worked_in"])
    other_certification = json.loads(request.data["other_certification"])
    active_inactive = json.loads(request.data["active_inactive"])
    area_of_expertise = json.loads(request.data["area_of_expertise"])
    location = json.loads(request.data["location"])
    language = json.loads(request.data["language"])
    job_roles = json.loads(request.data["job_roles"])
    ctt_nctt = json.loads(request.data["ctt_nctt"])
    years_of_coaching_experience = request.data.get("years_of_coaching_experience")
    years_of_corporate_experience = request.data.get("years_of_corporate_experience")
    username = request.data.get("email", "").strip()  # keeping username and email same
    profile_pic = request.data.get("profile_pic", None)
    corporate_experience = request.data.get("corporate_experience", "")
    coaching_experience = request.data.get("coaching_experience", "")
    internal_coach = json.loads(request.data["internal_coach"])
    organization_of_coach = request.data.get("organization_of_coach")
    reason_for_inactive = json.loads(request.data["reason_for_inactive"])
    client_companies = json.loads(request.data["client_companies"])
    education_pic = request.data.get("education_pic", None)
    educational_qualification = json.loads(request.data["educational_qualification"])
    education_upload_file = request.data.get("education_upload_file", None)

    # Check if required data is provided
    if not all(
        [
            coach_id,
            first_name,
            last_name,
            email,
            gender,
            phone,
            phone_country_code,
            level,
            username,
            room_id,
        ]
    ):
        return Response({"error": "All required fields must be provided."}, status=400)
    if internal_coach and not organization_of_coach:
        return Response(
            {
                "error": "Organization field must not be empty if internal coach is selected yes."
            },
            status=400,
        )

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

            coach_role, created = Role.objects.get_or_create(name="coach")
            # Create the Profile linked to the User
            profile.roles.add(coach_role)
            profile.save()

            # Create the Coach User using the Profile
            coach_user = Coach.objects.create(
                user=profile,
                coach_id=coach_id,
                room_id=room_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
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
                ctt_nctt=ctt_nctt,
                years_of_coaching_experience=years_of_coaching_experience,
                profile_pic=profile_pic,
                language=language,
                min_fees=min_fees,
                fee_remark=fee_remark,
                job_roles=job_roles,
                location=location,
                coaching_hours=coaching_hours,
                linkedin_profile_link=linkedin_profile_link,
                companies_worked_in=companies_worked_in,
                other_certification=other_certification,
                active_inactive=active_inactive,
                internal_coach=internal_coach,
                corporate_experience=corporate_experience,
                coaching_experience=coaching_experience,
                organization_of_coach=organization_of_coach,
                reason_for_inactive=reason_for_inactive,
                client_companies=client_companies,
                education_pic=education_pic,
                educational_qualification=educational_qualification,
                education_upload_file=education_upload_file,
            )

            # Approve coach
            coach_user.is_approved = True
            coach_user.save()

            # Send email notification to the coach
            full_name = coach_user.first_name + " " + coach_user.last_name
            microsoft_auth_url = (
                f'{env("BACKEND_URL")}/api/microsoft/oauth/{coach_user.email}/'
            )
            user_token_present = False
            try:
                user_token = UserToken.objects.get(
                    user_profile__user__username=coach_user.email
                )
                if user_token:
                    user_token_present = True
            except Exception as e:
                pass
            send_mail_templates(
                "coach_templates/pmo-adds-coach-as-user.html",
                [coach_user.email],
                "Meeraq Coaching | New Beginning !",
                {
                    "name": coach_user.first_name,
                    "email": coach_user.email,
                    "microsoft_auth_url": microsoft_auth_url,
                    "user_token_present": user_token_present,
                },
                [],  # no bcc emails
            )

        return Response({"message": "Coach added successfully."}, status=201)

    except IntegrityError as e:
        print(e)
        return Response(
            {"error": "A coach user with this email already exists."}, status=400
        )

    except Exception as e:
        print(e)
        return Response(
            {"error": "An error occurred while creating the coach user."}, status=500
        )


@api_view(["POST"])
def delete_coach(request):
    coach_id = request.data.get("coach_id", None)
    user_id = request.data.get("user_id")
    if coach_id:
        try:
            coach = Coach.objects.get(id=coach_id)
            coach_name = coach.first_name + " " + coach.last_name
            coach_user_profile = coach.user
            is_delete_user = True
            for role in coach_user_profile.roles.all():
                if not role.name == "coach":
                    # don't delete user if any other role exists
                    is_delete_user = False
                else:
                    coach_user_profile.roles.remove(role)
                    coach_user_profile.save()
            if is_delete_user:
                user = coach.user.user
                user.delete()
            else:
                coach.delete()
            timestamp = timezone.now()
            current_user = User.objects.get(id=user_id)

            deleteCoachProfile = DeleteCoachProfileActivity.objects.create(
                user_who_got_deleted=coach_name,
                user_who_deleted=current_user,
                timestamp=timestamp,
            )
            deleteCoachProfile.save()
            return Response({"message": "Coach deleted."}, status=200)
        except ObjectDoesNotExist:
            return Response({"message": "Failed to delete coach profile"}, status=400)
    else:
        return Response({"message": "Failed to delete coach profile"}, status=400)


# @api_view(['GET'])
# def get_hr(request):
#     try:
#         # Get all the Coach objects
#         hr = HR.objects.all()

#         # Serialize the Coach objects
#         serializer = HrSerializer(hr, many=True)

#         # Return the serialized Coach objects as the response
#         return Response(serializer.data, status=200)

#     except Exception as e:
#         # Return error response if any exception occurs
#         return Response({'error': str(e)}, status=500)

# def create_hr(hrs_data):
#     try:
#             if not hrs_data:
#                 raise ValueError('HR data is required')
#             hrs = []
#             for hr_data in hrs_data:
#                 print('email',hr_data)
#                 # Check if username field is provided
#                 # if 'email' not in hr_data:
#                 #     raise ValueError('Username field is required')

#                 # Check if user already exists
#                 user = User.objects.filter(username=hr_data).first()
#                 if user:
#                     # If user exists, check if hr already exists
#                     print('user exists',user)
#                     hr_profile = HR.objects.get(user__user=user)
#                     print(hr_profile,'hr_profile')
#                     if hr_profile:
#                         hrs.append(hr_profile)
#                         continue
#                 else:
#                 # If HR does not exist, create the user object with an unusable password
#                     user = User.objects.create_user(
#                         username=hr_data,
#                         email=hr_data
#                         )
#                     user.set_unusable_password()
#                     user.save()

#                 # Create the hr profile
#                     hr_profile = Profile.objects.create(user=user, type='hr')

#                 # Create the hr object
#                     hr = HR.objects.create(user=hr_profile , email=hr_data)
#                     hrs.append(hr)

#             # Return response with hr created or already existing
#             serializer = HrSerializer(hrs, many=True)
#             print(hrs,'helloo')
#             return hrs


#     except ValueError as e:
#         # Handle missing or invalid request data
#         raise ValueError(str(e))

#     except Exception as e:
#         # Handle any other exceptions
#         # transaction.set_rollback(True) # Rollback the transaction
#         raise Exception(str(e))


@api_view(["GET"])
@permission_classes([AllowAny])
def get_csrf(request):
    response = Response({"detail": "CSRF cookie set"})
    response["X-CSRFToken"] = get_token(request)
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    platform = data.get("platform", "unknown")
    if username is None or password is None:
        raise ValidationError({"detail": "Please provide username and password."})
    user = authenticate(request, username=username, password=password)

    # check_user = Profile.objects.get(user__username=username)
    # if check_user:
    #     if check_user.type == 'hr':
    #         raise AuthenticationFailed({'detail': 'Try login with OTP.'})

    if user is None:
        raise AuthenticationFailed({"detail": "Invalid credentials."})

    last_login = user.last_login
    login(request, user)
    user_data = get_user_data(user)
    if user_data:
        login_timestamp = timezone.now()
        UserLoginActivity.objects.create(
            user=user, timestamp=login_timestamp, platform=platform
        )
        user_token = None
        try:
            user_token = UserToken.objects.get(user_profile__user__username=username)
            if user_token.account_type == "google":
                refresh_google_access_token(user_token)
            else:
                refresh_microsoft_access_token(user_token)

        except ObjectDoesNotExist:
            print("Does not exist")

        return Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
            }
        )
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    if not request.user.is_authenticated:
        raise AuthenticationFailed({"detail": "You're not logged in."})

    logout(request)
    return Response({"detail": "Successfully logged out."})


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def session_view(request):
    user = request.user
    last_login = user.last_login
    user_data = get_user_data(user)
    if user_data:
        return Response(
            {
                "isAuthenticated": True,
                "user": {**user_data, "last_login": last_login},
            }
        )
    else:
        return Response({"error": "Invalid user type"}, status=400)


def get_user_data(user):
    if not user.profile:
        return None
    elif user.profile.roles.count() == 0:
        return None
    user_profile_role = user.profile.roles.all().first().name
    roles = []
    for role in user.profile.roles.all():
        roles.append(role.name)
    if user_profile_role == "coach":
        serializer = CoachDepthOneSerializer(user.profile.coach)
        is_caas_allowed = Project.objects.filter(
            coaches_status__coach=user.profile.coach
        ).exists()
        is_seeq_allowed = SchedularBatch.objects.filter(
            coaches=user.profile.coach
        ).exists()
        return {
            **serializer.data,
            "is_caas_allowed": is_caas_allowed,
            "is_seeq_allowed": is_seeq_allowed,
            "roles": roles,
            "user": {**serializer.data["user"], "type": user_profile_role},
        }
    elif user_profile_role == "pmo":
        serializer = PmoDepthOneSerializer(user.profile.pmo)
    elif user_profile_role == "learner":
        serializer = LearnerDepthOneSerializer(user.profile.learner)
    elif user_profile_role == "hr":
        serializer = HrDepthOneSerializer(user.profile.hr)
    else:
        return None
    return {
        **serializer.data,
        "roles": roles,
        "user": {**serializer.data["user"], "type": user_profile_role},
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_otp(request):
    try:
        user = User.objects.get(username=request.data["email"])
        learner_roles = user.profile.roles.all().filter(name="learner")
        hr_roles = user.profile.roles.all().filter(name="hr")
        # for hr and coachee not allowing login when they are added in caas project where hr and coachee's platform is not provided/needed
        if learner_roles.exists():
            engagements = Engagement.objects.filter(
                learner=user.profile.learner,
                project__enable_emails_to_hr_and_coachee=False,
            )
            if engagements.exists():
                return Response(
                    {"error": "User with the given email does not exist."}, status=400
                )
        elif hr_roles.exists():
            projects = Project.objects.filter(
                hr=user.profile.hr, enable_emails_to_hr_and_coachee=False
            )
            if projects.exists():
                return Response(
                    {"error": "User with the given email does not exist."}, status=400
                )
        try:
            # Check if OTP already exists for the user
            otp_obj = OTP.objects.get(user=user)
            otp_obj.delete()
        except OTP.DoesNotExist:
            pass

        # Generate OTP and save it to the database
        otp = get_random_string(length=6, allowed_chars="0123456789")
        created_otp = OTP.objects.create(user=user, otp=otp)
        user_data = get_user_data(user)
        name = user_data.get("name") or user_data.get("first_name") or "User"
        # Send OTP on email to learner
        subject = f"Meeraq Login OTP"
        message = (
            f"Dear {name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}"
        )
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.username])
        microsoft_auth_url = (
            f'{env("BACKEND_URL")}/api/microsoft/oauth/{request.data["email"]}/'
        )
        user_token_present = False
        try:
            user_token = UserToken.objects.get(
                user_profile__user__username=request.data["email"]
            )
            if user_token:
                user_token_present = True
        except Exception as e:
            pass
        send_mail_templates(
            "hr_emails/login_with_otp.html",
            [user],
            subject,
            {
                "name": name,
                "otp": created_otp.otp,
                "email": request.data["email"],
                "microsoft_auth_url": microsoft_auth_url,
                "user_token_present": user_token_present,
            },
            [],  # no bcc
        )
        return Response({"message": f"OTP has been sent to {user.username}!"})

    except User.DoesNotExist:
        # Handle the case where the user with the given email does not exist
        return Response(
            {"error": "User with the given email does not exist."}, status=400
        )

    except Exception as e:
        # Handle any other exceptions
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_otp(request):
    otp_obj = (
        OTP.objects.filter(
            user__username=request.data["email"], otp=request.data["otp"]
        )
        .order_by("-created_at")
        .first()
    )
    data = request.data
    platform = data.get("platform", "unknown")

    if otp_obj is None:
        raise AuthenticationFailed("Invalid OTP")

    user = otp_obj.user
    # token, created = Token.objects.get_or_create(user=learner.user.user)
    # Delete the OTP object after it has been validated
    user_email = request.data["email"]
    otp_obj.delete()
    last_login = user.last_login
    login(request, user)
    user_data = get_user_data(user)
    if user_data:
        login_timestamp = timezone.now()
        UserLoginActivity.objects.create(
            user=user, timestamp=login_timestamp, platform=platform
        )
        user_token = None
        try:
            user_token = UserToken.objects.get(user_profile__user__username=user_email)
            if user_token.account_type == "google":
                refresh_google_access_token(user_token)
            else:
                refresh_microsoft_access_token(user_token)
        except ObjectDoesNotExist:
            print("Does not exist")

        return Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
            }
        )
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)

    # learner_data = {'id':learner.id,'name':learner.name,'email': learner.email,'phone': learner.email,'last_login': learner.user.user.last_login ,'token': token.key}
    # updateLastLogin(learner.email)
    # return Response({ 'learner': learner_data},status=200)


@api_view(["GET"])
def get_organisation(request):
    orgs = Organisation.objects.all()
    serializer = OrganisationSerializer(orgs, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def add_organisation(request):
    print(request.data.get("image_url", ""))
    org = Organisation.objects.create(
        name=request.data.get("name", ""), image_url=request.data.get("image_url", "")
    )
    orgs = Organisation.objects.all()
    serializer = OrganisationSerializer(orgs, many=True)
    return Response(
        {"message": "Organisation added successfully.", "details": serializer.data},
        status=200,
    )


@api_view(["PUT"])
def update_organisation(request, org_id):
    try:
        org = Organisation.objects.get(id=org_id)
    except Organisation.DoesNotExist:
        return Response({"error": "Organization not found"}, status=404)

    serializer = OrganisationSerializer(org, data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Organization updated successfully", "data": serializer.data}
        )

    return Response(serializer.errors, status=400)


@api_view(["POST"])
def add_hr(request):
    try:
        email = request.data.get("email", "").strip()
        with transaction.atomic():
            user = User.objects.filter(email=email).first()
            if not user:
                temp_password = "".join(
                    random.choices(
                        string.ascii_uppercase + string.ascii_lowercase + string.digits,
                        k=8,
                    )
                )
                user = User.objects.create_user(
                    username=email,
                    password=temp_password,
                    email=email,
                )
                profile = Profile.objects.create(user=user)
            else:
                profile = Profile.objects.get(user=user)

            hr_role, created = Role.objects.get_or_create(name="hr")
            profile.roles.add(hr_role)

            organisation = Organisation.objects.filter(
                id=request.data.get("organisation")
            ).first()

            hr = HR.objects.create(
                user=profile,
                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),
                email=email,
                phone=request.data.get("phone"),
                organisation=organisation,
            )

            hrs = HR.objects.all()
            serializer = HrSerializer(hrs, many=True)
            return Response(
                {"message": "HR added successfully", "details": serializer.data},
                status=200,
            )

    except Exception as e:
        return Response({"error": "User email already exist."}, status=400)


@api_view(["PUT"])
def update_hr(request, hr_id):
    try:
        hr = HR.objects.get(id=hr_id)
    except HR.DoesNotExist:
        return Response({"error": "HR not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get the associated user profile
    with transaction.atomic():
        # Update HR instance
        serializer = HrSerializer(hr, data=request.data, partial=True)
        if serializer.is_valid():
            new_email = request.data.get("email",'').strip()  # Get the new email from the request
            existing_user = (
                User.objects.filter(email=new_email).exclude(username=hr.email).first()
            )
            if existing_user:
                return Response(
                    {"error": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # saving hr
            updated_hr = serializer.save()
            user = updated_hr.user.user

            # if email if getting updated -> updating email in all other user present
            if not updated_hr.email == user.email:
                user.email = new_email
                user.username = new_email
                user.save()
                for role in user.profile.roles.all():
                    if role.name == "pmo":
                        pmo = Pmo.objects.get(user=user.profile)
                        pmo.email = new_email
                        pmo.save()
                    if role.name == "coach":
                        coach = Coach.objects.get(user=user.profile)
                        coach.email = new_email
                        coach.save()
                    if role.name == "learner":
                        learner = Learner.objects.get(user=user.profile)
                        learner.email = new_email
                        learner.save()
                    if role.name == "vendor":
                        vendor = Vendor.objects.get(user=user.profile)
                        vendor.email = new_email
                        vendor.save()
            return Response(
                {"message": "HR updated successfully", "data": serializer.data}
            )

        # Handle serializer errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_hr(request, hr_id):
    try:
        hr = HR.objects.get(id=hr_id)
        user_profile = hr.user
        is_delete_user = True
        for role in user_profile.roles.all():
            if not role.name == "hr":
                is_delete_user = False
            else:
                user_profile.roles.remove(role)
                user_profile.save()
        if is_delete_user:
            user = user_profile.user
            user.delete()
        else:
            hr.delete()
        return Response(
            {"message": "HR deleted successfully"}, status=status.HTTP_200_OK
        )
    except ObjectDoesNotExist:
        return Response(
            {"message": "Failed to delete HR profile"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# Filter API for Coaches
# Expected input "filters": [{"key":"area_of_expertise","value":"test"},...]
# @api_view(['POST'])
# def filter_coach(request):
#     filters=request.data.get('filters',[])
#     temp={}
#     for filter in filters:
#         print(filter)
#         if filter['key'] in ["area_of_expertise", "years_of_coaching_experience", "gender"] and filter['value'] is not None and filter['value']!='':
#             temp[filter['key']] = filter['value']
#     coaches = Coach.objects.filter(**temp).all()
#     serializer = CoachSerializer(coaches, many=True)
#     return Response(serializer.data, status=200)


@api_view(["POST"])
def add_project_struture(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.project_structure = request.data.get("project_structure", [])
    project.currency = request.data.get("currency", "")
    # project.price_per_hour = request.data.get("price", "")
    # project.coach_fees_per_hour = request.data.get("coach_price", "")
    # project.status['project_structure'] = 'complete'
    project.save()
    return Response({"message": "Structure added", "details": ""}, status=200)


@api_view(["POST"])
def send_consent(request):
    # Get the project
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)

    # Get the list of coach IDs
    coach_list = request.data.get("coach_list", [])

    # Initialize a list to store coach status
    coach_status = []

    # Iterate through each coach
    for coach_id in coach_list:
        try:
            coach = Coach.objects.get(id=coach_id)

            # Check if CoachStatus already exists for this coach and project
            coach_status_instance, created = CoachStatus.objects.get_or_create(
                coach=coach,
                project=project,
                defaults={
                    "status": {
                        "consent": {
                            "status": "sent",
                            "response_date": None,
                        },
                        "project_structure": {
                            "status": "sent",
                            "response_date": None,
                        },
                        "hr": {
                            "status": None,
                            "session_id": None,
                            "response_date": None,
                        },
                        "learner": {
                            "status": None,
                            "session_id": None,
                            "response_date": None,
                        },
                    },
                    "consent_expiry_date": request.data["consent_expiry_date"],
                },
            )

            # If CoachStatus was created, add it to the coach_status list
            if created:
                coach_status_instance.save()
                coach_status.append(coach_status_instance)

            # Create or update CoachProfileTemplate
            profile_template, created = CoachProfileTemplate.objects.get_or_create(
                coach=coach,
                project=project,
                defaults={
                    "templates": {
                        # "first_name": coach.first_name,
                        # "last_name": coach.last_name,
                        # "email": coach.email,
                        # "phone": coach.phone,
                        # "linkedin_profile_link": coach.linkedin_profile_link,
                        # "education": coach.education,
                        # "coaching_hours": coach.coaching_hours,
                        # "level": coach.level,
                        # "coaching_years_of_exp": coach.years_of_coaching_experience,
                        # "corporate_years_of_exp": coach.years_of_corporate_experience,
                        "coaching_experience": coach.coaching_experience,
                        "corporate_experience": coach.corporate_experience,
                        # "gender": coach.gender,
                        # "is_approved": coach.is_approved,
                        # "age": coach.age,
                        # "domain": coach.domain,
                        # "room_id": coach.room_id,
                        # "phone_country_code": coach.phone_country_code,
                        # "rating": coach.rating,
                        # "area_of_expertise": coach.area_of_expertise,
                        # "completed_sessions": coach.completed_sessions,
                        # "profile_pic": coach.profile_pic.url
                        # if coach.profile_pic
                        # else "",
                        # "location": coach.location,
                        # "ctt_nctt": coach.ctt_nctt,
                        # "language": coach.language,
                        # "min_fees": coach.min_fees,
                        # "fee_remark": coach.fee_remark,
                        # "job_roles": coach.job_roles,
                        # "created_at": coach.created_at.strftime("%Y-%m-%d"),
                        # "edited_at": coach.edited_at.strftime("%Y-%m-%d"),
                        # "companies_worked_in": coach.companies_worked_in,
                        # "other_certification": coach.other_certification,
                        # "active_inactive": coach.active_inactive,
                        # "currency": coach.currency,
                        # "internal_coach": coach.internal_coach,
                        # "organization_of_coach": coach.organization_of_coach,
                        # "reason_for_inactive": coach.reason_for_inactive,
                        # "client_companies": coach.client_companies,
                        # "educational_qualification": coach.educational_qualification,
                        # # Add other fields here to include all coach details
                    }
                },
            )

            # If the template already exists, update the coach details
            if not created:
                profile_template.templates["templates"] = {
                    # "name": coach.first_name + " " + coach.last_name,
                    # "email": coach.email,
                    # "phone": coach.phone,
                    # "linkedin_profile_link": coach.linkedin_profile_link,
                    # "education": coach.education,
                    # "coaching_hours": coach.coaching_hours,
                    # "level": coach.level,
                    # "coaching_years_of_exp": coach.years_of_coaching_experience,
                    # "corporate_years_of_exp": coach.years_of_corporate_experience,
                    "coaching_experience": coach.coaching_experience,
                    "corporate_experience": coach.corporate_experience,
                    # "gender": coach.gender,
                    # "is_approved": coach.is_approved,
                    # "age": coach.age,
                    # "domain": coach.domain,
                    # "room_id": coach.room_id,
                    # "phone_country_code": coach.phone_country_code,
                    # "rating": coach.rating,
                    # "area_of_expertise": coach.area_of_expertise,
                    # "completed_sessions": coach.completed_sessions,
                    # "profile_pic": coach.profile_pic.url if coach.profile_pic else "",
                    # "location": coach.location,
                    # "ctt_nctt": coach.ctt_nctt,
                    # "language": coach.language,
                    # "min_fees": coach.min_fees,
                    # "fee_remark": coach.fee_remark,
                    # "job_roles": coach.job_roles,
                    # "created_at": coach.created_at.strftime("%Y-%m-%d"),
                    # "edited_at": coach.edited_at.strftime("%Y-%m-%d"),
                    # "companies_worked_in": coach.companies_worked_in,
                    # "other_certification": coach.other_certification,
                    # "active_inactive": coach.active_inactive,
                    # "currency": coach.currency,
                    # "internal_coach": coach.internal_coach,
                    # "organization_of_coach": coach.organization_of_coach,
                    # "reason_for_inactive": coach.reason_for_inactive,
                    # "client_companies": coach.client_companies,
                    # "educational_qualification": coach.educational_qualification,
                    # # Add other fields here to include all coach details
                }

            profile_template.save()

        except Coach.DoesNotExist:
            pass

    # Update project's coach_status and steps
    project.coaches_status.add(*coach_status)
    project.steps["coach_list"]["status"] = "complete"
    project.save()

    # Send notifications and emails
    try:
        path = f"/projects"
        message = (
            f"Admin has requested your consent to share profile for a new project."
        )
        for status in coach_status:
            if project.coach_consent_mandatory:
                create_notification(status.coach.user.user, path, message)
            microsoft_auth_url = (
                f'{env("BACKEND_URL")}/api/microsoft/oauth/{coach.email}/'
            )
            user_token_present = False
            try:
                user_token = UserToken.objects.get(
                    user_profile__user__username=coach.email
                )
                if user_token:
                    user_token_present = True
            except Exception as e:
                pass

            send_mail_templates(
                "coach_templates/pmo_ask_for_consent.html",
                [status.coach.email],
                "Meeraq Coaching | New Project!",
                {
                    "name": status.coach.first_name,
                    "email": coach.email,
                    "microsoft_auth_url": microsoft_auth_url,
                    "user_token_present": user_token_present,
                },
                [],  # no bcc
            )
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    for coach_id in coach_list:
        if not project.coach_consent_mandatory:
            for coach_status in project.coaches_status.all():
                if coach_status.coach.id == coach_id:
                    coach_status.status["consent"]["status"] = "select"
                    if project.steps["project_structure"]["status"] == "complete":
                        coach_status.status["project_structure"]["status"] = "select"
                    coach_status.save()
    return Response({"message": "Consent sent successfully", "details": ""}, status=200)


# @api_view(['POST'])
# def select_coaches(request):
#     # Get all the Coach objects
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     coaches = Coach.objects.filter(id__in=request.data.get('coach_list',[])).all()
#     coach_status = []
#     for coach in coaches:
#         status = project.coaches_status.get(coach=coach)
#         status.status['hr'] = "Selected"
#         status.save()
#     # project.coaches = coach_list
#     project.status['coach_list_to_hr'] = 'complete'
#     project.save()
#     return Response({"message":"Coaches selected successfully"},status=200)


@api_view(["GET"])
def get_project_details(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        serializer = ProjectDepthTwoSerializer(project)
        return Response(serializer.data)
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)


# Filter API for Coaches
# Expected input
# "project_id": 1
# "coach_id": 1
# "status": Consent Approved/Consent Rejected
@api_view(["POST"])
def receive_coach_consent(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    for coach_status in project.coaches_status.all():
        try:
            if coach_status.coach.id == request.data.get("coach_id", ""):
                # coach_status.status[request.data.get('status','').split(" ")[0].lower()]=request.data.get('status','').split(" ")[1].lower()
                # if request.data.get('status','').split(" ")[0].lower()=='contract':
                #     coach_status.status['consent'] = "approved"
                # coach_status.save()
                coach_status.status["consent"]["status"] = request.data["status"]
                if project.steps["project_structure"]["status"] == "complete":
                    coach_status.status["project_structure"]["status"] = request.data[
                        "status"
                    ]
                coach_status.save()
                try:
                    pmo_user = User.objects.filter(profile__roles__name="pmo").first()
                    pmo = Pmo.objects.get(email=pmo_user.email)
                    if request.data["status"] == "select":
                        if pmo_user:
                            path = f"/projects/caas/progress/{project.id}"
                            coach_name = (
                                coach_status.coach.first_name
                                + " "
                                + coach_status.coach.last_name
                            )
                            message = f"{coach_name.title() } has accepted your consent request for Project - {project.name}"
                            create_notification(pmo_user, path, message)

                            send_mail_templates(
                                "pmo_emails/coach_agrees-rejects_consent.html",
                                [pmo_user.email],
                                f"Meeraq Coaching | Coach {coach_status.coach.first_name} agreed to consent",
                                {
                                    "projectname": project.name,
                                    "name": pmo.name,
                                    "coachname": coach_status.coach.first_name,
                                    "agreeddisagreed": request.data["status"],
                                },
                                [],  # no bcc
                            )
                    if request.data["status"] == "reject":
                        send_mail_templates(
                            "pmo_emails/coach_agrees-rejects_consent.html",
                            [pmo_user.email],
                            f"Meeraq Coaching | Coach {coach_status.coach.first_name} reject to consent",
                            {
                                "projectname": project.name,
                                "name": pmo.name,
                                "coachname": coach_status.coach.first_name,
                                "agreeddisagreed": request.data["status"],
                            },
                            [],  # no bcc
                        )

                except Exception as e:
                    print(f"Error occurred while creating notification: {str(e)}")
                    continue

        except Exception as e:
            print(e)
            return Response({"message": "Coach not Found"}, status=400)
    return Response({"message": request.data.get("status", "")}, status=200)


@api_view(["POST"])
def update_project_structure_consent_by_coach(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    for coach_status in project.coaches_status.all():
        try:
            if coach_status.coach.id == request.data.get("coach_id", ""):
                # coach_status.status[request.data.get('status','').split(" ")[0].lower()]=request.data.get('status','').split(" ")[1].lower()
                # if request.data.get('status','').split(" ")[0].lower()=='contract':
                #     coach_status.status['consent'] = "approved"
                # coach_status.save()
                coach_status.status["project_structure"]["status"] = request.data[
                    "status"
                ]
                coach_status.save()
                try:
                    if request.data["status"] == "select":
                        pmo_user = User.objects.filter(
                            profile__roles__name="pmo"
                        ).first()
                        if pmo_user:
                            path = f"/projects/caas/progress/{project.id}"
                            coach_name = (
                                coach_status.coach.first_name
                                + " "
                                + coach_status.coach.last_name
                            )
                            message = f"{coach_name.title() } has agreed to the project structure for Project - {project.name}"
                            create_notification(pmo_user, path, message)
                except Exception as e:
                    print(f"Error occurred while creating notification: {str(e)}")
                    continue

        except Exception as e:
            print(e)
            return Response({"message": "Coach not Found"}, status=400)
    return Response({"message": "Status updated."}, status=200)


@api_view(["POST"])
def complete_coach_consent(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.status["coach_consent"] = "complete"
    project.save()
    return Response({"message": "Coach list sent to HR", "details": ""}, status=200)


@api_view(["POST"])
def complete_coach_list_to_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["coach_list_to_hr"]["status"] = "complete"
    project.steps["coach_consent"]["status"] = "complete"
    if not project.empanelment:
        for coach_status in project.coaches_status.all():
            if coach_status.status["hr"]["status"] == "select":
                coach_status.status["learner"]["status"] = "sent"
                coach_status.save()
    project.save()
    return Response({"message": "Step marked as complete.", "details": {}}, status=200)


@api_view(["POST"])
def complete_interviews_step(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["interviews"]["status"] = "complete"
    project.steps["coach_consent"]["status"] = "complete"
    if not project.empanelment:
        for coach_status in project.coaches_status.all():
            if coach_status.status["hr"]["status"] == "select":
                coach_status.status["learner"]["status"] = "sent"
                coach_status.save()
    project.save()
    return Response({"message": "Step marked as complete.", "details": {}}, status=200)


@api_view(["POST"])
def complete_empanelment(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["add_learners"]["status"] = "complete"
    project.save()
    return Response({"message": "Empanelement completed.", "details": ""}, status=200)


# @api_view(['POST'])
# def complete_interview(request):
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     project.steps['interviews']['status'] = 'complete'
#     project.save()
#     return Response({'message': "Interviews completed."},status=200)


@api_view(["POST"])
def complete_project_structure(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.status["project_structure"] = "complete"
    project.save()
    return Response({"message": "Project structure approved."}, status=200)


# @api_view(['POST'])
# def complete_coach_approval(request):
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     project.status['coach_approval'] = 'complete'
#     project.save()
#     return Response({'message': "Coach approval completed."},status=200)


# @api_view(['POST'])
# def complete_chemistry_sessions(request):
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     project.steps['chemistry_session']['status'] = 'complete'
#     project.save()
#     return Response({'message': "Chemistry sessions completed."},status=200)


@api_view(["GET"])
def get_interview_data(request, project_id):
    sessions = SessionRequestCaas.objects.filter(
        project__id=project_id, session_type="interview"
    ).all()
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_chemistry_session_data(request, project_id):
    sessions = SessionRequestCaas.objects.filter(
        project__id=project_id, session_type="chemistry"
    ).exclude(status="pending")
    serializer = SessionRequestCaasDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_session_requests_of_hr(request, hr_id):
    sessions = SessionRequestCaas.objects.filter(hr__id=hr_id).all()
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_session_requests_of_learner(request, learner_id):
    sessions = SessionRequestCaas.objects.filter(learner__id=learner_id).all()
    print(sessions, "session")
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_upcoming_booked_session_of_coach(request, coach_id):
    current_time = int(timezone.now().timestamp() * 1000)
    # convert current time to milliseconds
    sessions = SessionRequestCaas.objects.filter(
        coach__id=coach_id,
        is_booked=True,
        confirmed_availability__start_time__gt=current_time,
    ).all()
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def book_session_caas(request):
    session_request = SessionRequestCaas.objects.get(
        id=request.data.get("session_request")
    )

    google_calendar_event = CalendarEvent.objects.filter(
        session=session_request, account_type="google"
    ).first()
    microsoft_calendar_event = CalendarEvent.objects.filter(
        session=session_request, account_type="microsoft"
    ).first()

    session_request.confirmed_availability = Availibility.objects.get(
        id=request.data.get("confirmed_availability")
    )
    if session_request.learner:
        coachee = session_request.learner
    #     sessionName = str(session_request.session_type).replace('_', ' ')
    #     if( sessionName == "stakeholder without coach"):
    #         sessionName = "tripartite without coach"
    session_request.is_booked = True
    session_request.status = "booked"
    session_request.invitees = get_trimmed_emails(request.data.get("invitees", []))
    session_request.save()

    # if serializer.is_valid():
    #     session = serializer.save()
    #     # Mark the session request as booked
    #     session_request = session.session_request
    #     session_request.is_booked = True
    #     session_request.save()

    #     coach=session.coach
    #     coach_email=coach.email
    #     hr=session.session_request.hr
    #     he_email= hr.email
    # else:
    #     print(serializer.errors)
    #     return Response(serializer.errors,status=400)

    # Send email notification to the coach
    # subject = 'Hello coach your session is booked.'
    # message = f'Dear {session_request.coach.first_name},\n\nThank you booking slots of hr.Please be ready on date and time to complete session. Best of luck!'
    # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [session_request.coach.email])

    # # Send email notification to the learner
    if session_request.session_type == "interview":
        subject = "Hello hr your session is booked."
        message = f"Dear {session_request.hr.first_name},\n\nThank you booking slots of hr.Please be ready on date and time to complete session. Best of luck!"
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [session_request.hr.email])
    if session_request.session_type == "chemistry":
        subject = "Hello learner your session is booked."
        message = f"Dear {session_request.learner.name},\n\nThank you booking slots of hr.Please be ready on date and time to complete session. Best of luck!"
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [session_request.learner.email])
    try:
        pmo_user = User.objects.filter(profile__roles__name="pmo").first()
        project = session_request.project
        coach = session_request.coach
        pmo = Pmo.objects.get(email=pmo_user)

        if pmo_user:
            path = f"/projects/caas/progress/{project.id}"
            coach_name = coach.first_name + " " + coach.last_name
            start_time = format_timestamp(
                int(session_request.confirmed_availability.start_time)
            )
            end_time = format_timestamp(
                int(session_request.confirmed_availability.end_time)
            )
            slot_message = f"{start_time} - {end_time}"

            session_date = get_date(
                int(session_request.confirmed_availability.start_time)
            )
            start_time = get_time(
                int(session_request.confirmed_availability.start_time)
            )
            end_time = get_time(int(session_request.confirmed_availability.end_time))

            session_time = f"{start_time} - {end_time} IST"

            if session_request.session_type == "interview":
                hr_user = session_request.hr.user.user
                # message = f"{coach_name.title()} has booked the interview session for Project - {project.name}.The booked slot is "
                message_for_hr = f"{coach_name.title()} has booked the slot {slot_message} from your interview request. You can join the meeting on scheduled time."
                create_notification(hr_user, path, message_for_hr)
            if session_request.session_type == "chemistry":
                learner_user = session_request.learner.user.user
                message_for_learner = f"{coach_name.title()} has booked the slot {slot_message} from your chemistry session request. You can join the meeting on scheduled time."
                message_for_hr = f"{coach_name.title()} has booked the slot {slot_message} as per the request from {session_request.learner.name.title()} for the project - {session_request.project.name}"
                create_notification(learner_user, path, message_for_learner)
            message = f"{coach_name.title()} has booked the {SESSION_TYPE_VALUE[session_request.session_type]} for Project - {project.name}.The booked slot is "
            message += slot_message
            create_notification(pmo_user, path, message)
            if coachee:
                microsoft_auth_url = (
                    f'{env("BACKEND_URL")}/api/microsoft/oauth/{coachee.email}/'
                )
                user_token_present = False
                try:
                    user_token = UserToken.objects.get(
                        user_profile__user__username=coachee.email
                    )
                    if user_token:
                        user_token_present = True
                except Exception as e:
                    pass
                if session_request.project.enable_emails_to_hr_and_coachee:
                    send_mail_templates(
                        "coachee_emails/session_booked.html",
                        [coachee.email],
                        "Meeraq Coaching | Session Booked",
                        {
                            "projectName": session_request.project.name,
                            "name": coachee.name,
                            "sessionName": SESSION_TYPE_VALUE[
                                session_request.session_type
                            ],
                            "slot_date": session_date,
                            "slot_time": session_time,
                            "email": coachee.email,
                            "microsoft_auth_url": microsoft_auth_url,
                            "user_token_present": user_token_present,
                        },
                        [],  # no bcc
                    )
                # add microsoft auth url before uncommenting

                # send_mail_templates(
                #     "pmo_emails/session_scheduled.html",
                #     [pmo.email],
                #     "Meeraq Coaching | Session Booked",
                #     {
                #         "projectName": session_request.project.name,
                #         "name": pmo.name,
                #         "coachee_name": coachee.name,
                #         "coach_name": coach_name,
                #         "sessionName": SESSION_TYPE_VALUE[session_request.session_type],
                #         "slot_date": session_date,
                #         "slot_time": session_time,
                # "email": pmo.email,
                #     },
                #     [],  # no bcc
                # )

                event_detail = {
                    "title": f"{SESSION_TYPE_VALUE[session_request.session_type]} Session",
                    "description": "Session Scheduled",
                    "startDate": session_date,
                    "startTime": start_time,
                    "endDate": session_date,
                    "endTime": end_time,
                }
                try:
                    coach_user_token = UserToken.objects.get(
                        user_profile__user__username=coach.email
                    )
                    coach_access_token = coach_user_token.access_token
                    if coach_user_token.account_type == "google":
                        coach_access_token = refresh_google_access_token(
                            coach_user_token
                        )

                        if google_calendar_event:
                            delete_google_calendar_event(
                                coach_access_token, google_calendar_event.event_id
                            )
                            google_calendar_event.delete()

                        create_google_calendar_event(
                            coach_access_token,
                            event_detail,
                            coachee.email,
                            session_request,
                        )
                    else:
                        coach_access_token = refresh_microsoft_access_token(
                            coach_user_token
                        )
                        if microsoft_calendar_event:
                            delete_microsoft_calendar_event(
                                coach_access_token, microsoft_calendar_event.event_id
                            )
                            microsoft_calendar_event.delete()

                        create_microsoft_calendar_event(
                            coach_access_token,
                            event_detail,
                            {"address": coachee.email, "name": coachee.name},
                            session_request,
                        )

                except Exception as e:
                    print(f"Coach calendar error {str(e)}")
                if session_request.project.enable_emails_to_hr_and_coachee:
                    try:
                        coachee_user_token = UserToken.objects.get(
                            user_profile__user__username=coachee.email
                        )
                        coachee_access_token = coachee_user_token.access_token
                        if coachee_user_token.account_type == "google":
                            coachee_access_token = refresh_google_access_token(
                                coachee_user_token
                            )
                            if google_calendar_event:
                                delete_google_calendar_event(
                                    coachee_access_token, google_calendar_event.event_id
                                )
                                google_calendar_event.delete()
                            create_google_calendar_event(
                                coachee_access_token,
                                event_detail,
                                coach.email,
                                session_request,
                            )
                        else:
                            coachee_access_token = refresh_microsoft_access_token(
                                coachee_user_token
                            )
                            if microsoft_calendar_event:
                                delete_microsoft_calendar_event(
                                    coachee_access_token,
                                    microsoft_calendar_event.event_id,
                                )
                                microsoft_calendar_event.delete()
                            create_microsoft_calendar_event(
                                coachee_access_token,
                                event_detail,
                                {"address": coach.email, "name": coach_name},
                                session_request,
                            )
                    except Exception as e:
                        print(f"Coachee calendar error {str(e)}")

    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")

    return Response({"message": "Session booked successfully!"}, status=201)


def create_time_arr(availability):
    time_arr = []
    for time in availability:
        availibility_serilizer = AvailibilitySerializer(data=time)
        if availibility_serilizer.is_valid():
            avil_id = availibility_serilizer.save()
            time_arr.append(avil_id.id)
        else:
            return Response(
                {
                    "message": str(availibility_serilizer.errors),
                },
                status=401,
            )
    return time_arr


def get_slot_message(availability):
    slot_message = ""
    for i, slot in enumerate(availability):
        start_time = format_timestamp(slot["start_time"])
        end_time = format_timestamp(slot["end_time"])
        slot_message += f"Slot {i+1}: {start_time} - {end_time}"
        if i == (len(availability) - 1):
            slot_message += ". "
        elif i == (len(availability) - 2):
            slot_message += " and "
        else:
            slot_message += ", "
    return slot_message


@api_view(["POST"])
def create_session_request_caas(request):
    time_arr = create_time_arr(request.data["availibility"])

    try:
        if request.data["session_type"] == "chemistry":
            session = SessionRequestCaas.objects.get(
                learner__id=request.data["learner_id"],
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        else:
            session = SessionRequestCaas.objects.get(
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        session.availibility.set(time_arr)
        session.save()
        return Response({"message": "Session updated successfully."}, status=201)
    except SessionRequestCaas.DoesNotExist:
        session = {
            "project": request.data["project_id"],
            "availibility": time_arr,
            "coach": request.data["coach_id"],
            "session_type": request.data["session_type"],
        }
        if session["session_type"] == "interview":
            session["hr"] = request.data["hr_id"]
        elif session["session_type"] == "chemistry":
            session["learner"] = request.data["learner_id"]
        session_serilizer = SessionRequestCaasSerializer(data=session)
        if session_serilizer.is_valid():
            session_created = session_serilizer.save()
            try:
                pmo_user = User.objects.filter(profile__roles__name="pmo").first()
                project = Project.objects.get(id=request.data["project_id"])
                coach = Coach.objects.get(id=request.data["coach_id"])
                if pmo_user:
                    path = f"/projects/caas/progress/{project.id}"
                    path_for_coach = f"/sessions"
                    coach_name = coach.first_name + " " + coach.last_name
                    slot_message = get_slot_message(request.data["availibility"])
                    if session["session_type"] == "interview":
                        message = f"HR has requested interview session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                        message_for_coach = f"HR has requested for {slot_message} for Interview for Project - {project.name}. Please book one of the requested slots now"
                    elif session["session_type"] == "chemistry":
                        hr_user_in_project = (
                            session_created.project.hr.first().user.user
                        )
                        message_for_hr = f"{session_created.learner.name.title()} has requested for Chemistry session to the Coach - {coach_name.title()} for {slot_message} for the Project - {project.name}"
                        message_for_coach = f"Coachee has requested {slot_message} for Chemistry session for the Project - {project.name}. Please book one of the requested slots now"
                        for hr_user in hr_user_in_project:
                            create_notification(hr_user, path, message_for_hr)
                        message = f"Coachee has requested chemistry session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                    message += " " + slot_message
                    create_notification(pmo_user, path, message)
                    create_notification(
                        coach.user.user, path_for_coach, message_for_coach
                    )
            except Exception as e:
                print(f"Error occurred while creating notification: {str(e)}")
            return Response({"message": "Session sequested successfully."}, status=201)
        else:
            return Response(
                {
                    "message": str(session_serilizer.errors),
                },
                status=401,
            )


@api_view(["GET"])
def get_session_requests_of_coach(request, coach_id):
    sessions = SessionRequestCaas.objects.filter(coach__id=coach_id).all()
    serializer = SessionRequestCaasDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def accept_coach_caas_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    coaches_selected_count = 0
    for coach in project.coaches_status.all():
        if coach.coach_id == request.data.get("coach_id"):
            if (
                coach.status["consent"]["status"] == "select"
                and coach.status["hr"]["status"] == "sent"
            ):
                coach.status["hr"]["status"] = request.data["status"]
                coach.save()

            else:
                return Response({"error": "Failed to update status."}, status=400)
            # print(coach.id)
            # print(coach.status)
            # if coach.status not in ["HR Selected","HR Rejected"]:
            #     coach.status['hr']=request.data.get('status').split(" ")[1].lower()
            #     coach.save()
            #     print("->")
            #     print(coach.status)
            # else:
            #     return Response({"error": "Status Already Updated"}, status=400)

        if coach.status["hr"]["status"] == "select":
            coaches_selected_count += 1

    project.save()
    try:
        userId = request.data.get("user_id")
        coachId = request.data.get("coach_id")
        user_who_finalized = User.objects.get(id=userId)
        coach_who_got_finalized = Coach.objects.get(id=coachId)
        project = project
        timestamp = timezone.now()

        finalizeCoach = FinalizeCoachActivity.objects.create(
            user_who_finalized=user_who_finalized,
            coach_who_got_finalized=coach_who_got_finalized,
            project=project,
            timestamp=timestamp,
        )

        finalizeCoach.save()
    except Exception as e:
        pass
    # for i in range(0,len(project.coaches_status)):
    #     print(project.coaches_status[i])
    #     status=project.coaches_status[i].status.hr.status
    #     if status=="select":
    #         coach_count=coach_count+1

    message = ""
    if request.data.get("status") == "select":
        # Project
        try:
            contract = ProjectContract.objects.get(project=project.id)
            coach_for_contract = Coach.objects.get(id=request.data["coach_id"])
            contract_data = {}
            if not project.coach_consent_mandatory:
                contract_data = {
                    "project_contract": contract.id,
                    "project": project.id,
                    "status": "approved",
                    "coach": request.data["coach_id"],
                    "name_inputed": coach_for_contract.first_name
                    + " "
                    + coach_for_contract.last_name,
                    "response_date": timezone.now().date(),
                }
            else:
                contract_data = {
                    "project_contract": contract.id,
                    "project": project.id,
                    "status": "pending",
                    "coach": request.data["coach_id"],
                }

            contract_serializer = CoachContractSerializer(data=contract_data)

            if contract_serializer.is_valid():
                contract_serializer.save()
        except Exception as e:
            print(str(e))

        try:
            pmo_user = User.objects.filter(profile__roles__name="pmo").first()
            pmo = Pmo.objects.get(email=pmo_user.email)
            coach = Coach.objects.get(id=request.data["coach_id"])
            if pmo_user:
                path = f"/projects/caas/progress/{project.id}"
                coach_name = coach.first_name + " " + coach.last_name
                message = f"HR has selected {coach_name.title()} for the Project - {project.name}"
                message_for_coach = f"Congratulations! You have been selected by HR for the Project - {project.name}"
                create_notification(pmo_user, path, message)
                create_notification(coach.user.user, path, message)

                send_mail_templates(
                    "pmo_emails/hr_selects_a_coach.html",
                    [pmo_user.email],
                    f"Meeraq Coaching | HR selected {coach_name}",
                    {
                        "projectname": project.name,
                        "name": pmo.name,
                        "coaches_selected_count": coaches_selected_count,
                        "coachname": coach_name,
                    },
                    [],  # no bcc
                )
                microsoft_auth_url = (
                    f'{env("BACKEND_URL")}/api/microsoft/oauth/{coach.email}/'
                )
                user_token_present = False
                try:
                    user_token = UserToken.objects.get(
                        user_profile__user__username=coach.email
                    )
                    if user_token:
                        user_token_present = True
                except Exception as e:
                    pass
                send_mail_templates(
                    "coach_templates/intro_mail_to_coach.html",
                    [coach.email],
                    f"Meeraq Coaching | {project.organisation.name} has selected you",
                    {
                        "name": coach.first_name,
                        "orgName": project.organisation.name,
                        "email": coach.email,
                        "microsoft_auth_url": microsoft_auth_url,
                        "user_token_present": user_token_present,
                    },
                    [env("BCC_EMAIL")],
                )

        except Exception as e:
            print(f"Error occurred while creating notification: {str(e)}")
        message = "Coach selected."
    elif request.data.get("status") == "reject":
        try:
            coach = Coach.objects.get(id=request.data["coach_id"])
            path = f"/projects/caas/progress/{project.id}"
            message_for_coach = f"Unfortunately, your profile is not selected for the Project - {project.name}"
            create_notification(coach.user.user, path, message_for_coach)

        except Exception as e:
            print(f"Error occurred while creating notification: {str(e)}")
        message = "Coach rejected."
    return Response({"message": message}, status=200)


@api_view(["POST"])
def add_learner_to_project(request):
    coacheeCounts = int(0)
    try:
        project = Project.objects.get(id=request.data["project_id"])
    except Project.DoesNotExist:
        return Response({"error": "Project does not exist."}, status=404)
    try:
        learners = create_learners(request.data["learners"])
        for learner in learners:
            create_engagement(learner, project)
            if project.enable_emails_to_hr_and_coachee:
                try:
                    path = f"/projects/caas/progress/{project.id}"
                    message = f"You have been added to Project - {project.name}"
                    create_notification(learner.user.user, path, message)
                    coacheeCounts = coacheeCounts + 1
                    microsoft_auth_url = (
                        f'{env("BACKEND_URL")}/api/microsoft/oauth/{learner.email}/'
                    )
                    user_token_present = False
                    try:
                        user_token = UserToken.objects.get(
                            user_profile__user__username=learner.email
                        )
                        if user_token:
                            user_token_present = True
                    except Exception as e:
                        pass
                    send_mail_templates(
                        "coachee_emails/add_coachee.html",
                        [learner.email],
                        "Meeraq Coaching | Welcome to Meeraq",
                        {
                            "name": learner.name,
                            "orgname": project.organisation.name,
                            "email": learner.email,
                            "microsoft_auth_url": microsoft_auth_url,
                            "user_token_present": user_token_present,
                        },
                        [],
                    )
                except Exception as e:
                    print(f"Error occurred while creating notification: {str(e)}")
                continue
    except Exception as e:
        # Handle any exceptions from create_learners
        return Response({"error": str(e)}, status=500)
    try:
        pmo_user = User.objects.filter(profile__roles__name="pmo").first()
        pmo = Pmo.objects.get(email=pmo_user.email)

        if pmo_user:
            path = f"/projects/caas/progress/{project.id}"
            message = f"HR has added Coachees to the Project - {project.name}"
            create_notification(pmo_user, path, message)
            send_mail_templates(
                "pmo_emails/hr_adding_coachees.html",
                [pmo_user.email],
                "Meeraq Coaching | Coachees added",
                {
                    "projectName": project.name,
                    "name": pmo.name,
                    "coacheeCount": str(coacheeCounts),
                },
                [],  # no bcc
            )
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Coachee added succesfully", "details": ""}, status=201)


def transform_project_structure(sessions):
    # convert project level
    #  to engagement level project structure
    # argument
    # sessions - array of objects where object has price, no. of sessions, session type, session durations
    # returns:
    # sessions - array of objects where object has - session type, session name (session type + n (numbered)) , session duration, status (pending)
    session_counts = {}
    transformed_sessions = []
    billable_session_number = 0

    for session in sessions:
        session_type = session["session_type"]
        session_duration = session["session_duration"]
        is_billable = session["billable"]
        if session_type not in session_counts:
            session_counts[session_type] = 1

        for i in range(session["no_of_sessions"]):
            session_name = f"{session_type}_{session_counts[session_type]}"
            if is_billable:
                billable_session_number = billable_session_number + 1

            transformed_session = {
                "session_name": session_name,
                "session_number": session_counts[session_type],
                "session_type": session_type,
                "session_duration": session_duration,
                "billable_session_number": billable_session_number
                if is_billable
                else None,
                "status": "pending",
            }
            print(transformed_session)
            transformed_sessions.append(transformed_session)
            session_counts[session_type] += 1

    return transformed_sessions


def create_engagement(learner, project):
    existing_engagement = Engagement.objects.filter(
        learner__id=learner.id, project__id=project.id
    )
    if len(existing_engagement) == 0:
        engagemenet_project_structure = transform_project_structure(
            project.project_structure
        )
        for index, session in enumerate(engagemenet_project_structure):
            session_data = SessionRequestCaas.objects.create(
                learner=learner,
                project=project,
                session_duration=session["session_duration"],
                session_number=session["session_number"],
                session_type=session["session_type"],
                billable_session_number=session["billable_session_number"],
                status="pending",
                order=index + 1,
            )
        engagement = Engagement(learner=learner, project=project, status="active")
        engagement.save()
        return engagement
    return existing_engagement


@api_view(["POST"])
def accept_coach_caas_learner(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    cnt = len(
        project.coaches_status.filter(
            learner_id__contains=request.data.get("learner_id")
        )
    )
    if cnt == 0:
        for coach in project.coaches_status.filter(
            coach__id=request.data.get("coach_id")
        ):
            coach.status["learner"]["status"] = request.data.get("status")
            if request.data.get("status") == "select":
                learner = Learner.objects.get(id=request.data.get("learner_id"))
                engagement = Engagement.objects.get(
                    learner__id=request.data.get("learner_id"), project__id=project.id
                )
                engagement.coach = coach.coach
                engagement.save()
                sessions = SessionRequestCaas.objects.filter(
                    learner__id=request.data.get("learner_id"),
                    session_type="chemistry_session",
                    project=project,
                ).exclude(coach=coach.coach)
                for session in sessions:
                    session.is_archive = True
                    session.save()
                coach.learner_id.append(request.data.get("learner_id"))
            coach.save()
    else:
        return Response({"error": "Coach Already Selected"}, status=400)
    message = ""
    if request.data.get("status") == "select":
        try:
            pmo_user = User.objects.filter(profile__roles__name="pmo").first()
            coach = Coach.objects.get(id=request.data["coach_id"])
            if pmo_user:
                path = f"/projects/caas/progress/{project.id}"
                coach_name = coach.first_name + " " + coach.last_name
                message = f"Coachee has selected {coach_name.title()} for the Project - {project.name}"
                create_notification(pmo_user, path, message)
                learner = Learner.objects.get(id=request.data.get("learner_id"))
                message_for_hr = f"{learner.name.title()} has selected {coach_name.title()} as their coach for the project - {project.name} "
                create_notification(learner.user.user, path, message_for_hr)
                message_for_coach = f"Congratulations! Coachee has selected you as their coach for the Project - {project.name}"
                create_notification(coach.user.user, path, message_for_coach)
        except Exception as e:
            print(f"Error occurred while creating notification: {str(e)}")
        message = "Coach selected succesfully."
    else:
        message = "Coach rejected."
    return Response({"message": message}, status=200)


# @api_view(['POST'])
# def send_contract(request):
#     # Get all the Coach objects
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)

#     coach_statuses = project.coaches_status.filter(coach__id__in=request.data.get('coach_list',[]))
#     for status in coach_statuses:
#         status.status['contract']="sent"
#         status.save()

#     return Response({"message":"Contract sent successfully",'details':''},status=200)


# @api_view(['POST'])
# def approve_contract(request):
#     # Get all the Coach objects
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)

#     status = project.coaches_status.get(coach__id=request.data.get('coach_id',[]))
#     status.status['contract']="approved"
#     status.save()
#     return Response({"message":"Contract approved.",'details':''},status=200)


@api_view(["POST"])
def complete_cass_step(request):
    try:
        step = request.data.get("step")
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps[step]["status"] = "complete"
    project.save()
    return Response({"message": "Marked as completed."}, status=200)


@api_view(["POST"])
def mark_as_incomplete(request):
    stepList = [
        "coach_list",
        "coach_consent",
        "coach_list_to_hr",
        "interviews",
        "add_learners",
        "chemistry_session",
        "coach_selected",
        "final_coaches",
    ]
    try:
        step = request.data.get("step")
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    flag = False
    steps = project.steps
    for item in stepList:
        print(item == step)
        print(flag)
        if step == item:
            flag = True
        if flag:
            if (steps[item]["status"]) == "complete":
                steps[item]["status"] = "incomplete"
    # print(statuses)
    project.steps = steps
    project.save()
    return Response({"message": "Marked as Incomplete."}, status=200)


@api_view(["POST"])
def send_project_strure_to_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["project_structure"]["status"] = "complete"
    project.save()
    if not project.coach_consent_mandatory:
        for coach_status in project.coaches_status.all():
            if not coach_status.status["consent"]["status"] == "reject":
                coach_status.status["consent"]["status"] = "select"
                if project.steps["project_structure"]["status"] == "complete":
                    coach_status.status["project_structure"]["status"] = "select"
            coach_status.save()
    try:
        path = f"/projects/caas/progress/{project.id}"
        message = f"Project structure has been added to the project - {project.name}."
        for hr_user in project.hr.all():
            create_notification(hr_user.user.user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Sent to HR."}, status=200)


@api_view(["POST"])
def send_reject_reason(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["project_structure"]["status"] = "pending"
    rejection = dict(
        reason=request.data.get("reject_reason", ""),
        project_structure=request.data.get("project_structure", []),
    )
    if "details" not in project.steps["project_structure"]:
        project.steps["project_structure"]["details"] = []
    project.steps["project_structure"]["details"].append(rejection)
    project.save()
    return Response({"message": "Rejected."}, status=200)


@api_view(["POST"])
def project_structure_agree_by_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["project_structure"]["status"] = "complete"
    project.save()
    return Response({"message": "Agreed."}, status=200)


@api_view(["POST"])
def request_more_profiles_by_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    if (
        request.data["step"] == "coach_list_to_hr"
        or request.data["step"] == "interviews"
    ):
        if "request_details" in project.steps["coach_consent"]:
            project.steps["coach_consent"]["request_details"].append(
                {"message": request.data["message"]}
            )
        else:
            project.steps["coach_consent"]["request_details"] = [
                {"message": request.data["message"]}
            ]
    project.steps["coach_consent"]["status"] = "incomplete"
    project.save()
    try:
        pmo_user = User.objects.filter(profile__roles__name="pmo").first()
        if pmo_user:
            path = f"/projects/caas/progress/{project.id}"
            message = (
                f"HR has requested for more coach profiles for Project - {project.name}"
            )
            create_notification(pmo_user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Request sent successfully"})


@api_view(["POST"])
def edit_learner(request):
    try:
        learner = Learner.objects.get(id=request.data.get("learner_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Learner does not exist"}, status=400)
    user = learner.user.user
    user.username = request.data["email"]
    user.email = request.data["email"]
    user.save()
    learner.email = request.data["email"]
    learner.name = request.data["name"]
    learner.phone = request.data["phone"]
    learner.save()
    return Response({"message": "Learner details updated.", "details": ""}, status=200)


@api_view(["POST"])
def mark_finalized_list_complete(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["final_coaches"]["status"] = "complete"
    project.save()
    return Response({"message": "Step marked as Complete", "details": ""}, status=200)


@api_view(["POST"])
def send_list_to_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    # project.status['coach_list_to_hr'] = 'pending'

    coaches = []

    for coach_id in request.data["coach_list"]:
        coach_status = project.coaches_status.get(coach__id=coach_id)
        coach_status.status["hr"]["status"] = "sent"
        coaches.append(Coach.objects.get(id=coach_id))
        coach_status.save()

    project.save()
    try:
        user_who_shared = User.objects.get(id=request.data.get("user_id", ""))
        project_name = project
        coaches = coaches
        timestamp = timezone.now()
        shareCoachProfile = ShareCoachProfileActivity.objects.create(
            user_who_shared=user_who_shared, project=project_name, timestamp=timestamp
        )

        shareCoachProfile.coaches.set(coaches)
        shareCoachProfile.save()
    except Exception as e:
        pass
    if project.enable_emails_to_hr_and_coachee:
        try:
            path = f"/projects/caas/progress/{project.id}"
            message = f"Admin has shared {len(request.data['coach_list'])} coach profile with you for the Project - {project.name}."
            hr_users = project.hr.all()
            for hr_user in hr_users:
                hr_email = hr_user.email
                hr_name = hr_user.first_name
                microsoft_auth_url = (
                    f'{env("BACKEND_URL")}/api/microsoft/oauth/{hr_email}/'
                )
                user_token_present = False
                try:
                    user_token = UserToken.objects.get(
                        user_profile__user__username=hr_email
                    )
                    if user_token:
                        user_token_present = True
                except Exception as e:
                    pass
                send_mail_templates(
                    "hr_emails/pmo_share_coach_list.html",
                    [hr_email],
                    "Welcome to the Meeraq Platform",
                    {
                        "name": hr_name,
                        "email": hr_email,
                        "microsoft_auth_url": microsoft_auth_url,
                        "user_token_present": user_token_present,
                    },
                    json.loads(env("BCC_EMAIL_SALES_TEAM")),  # bcc
                )
            for hr_user in project.hr.all():
                create_notification(hr_user.user.user, path, message)
        except Exception as e:
            print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Sent Successfully", "details": {}}, status=200)


@api_view(["POST"])
def finalized_coach_from_coach_consent(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)

    for coach_id in request.data["coach_list"]:
        coach_status = project.coaches_status.get(coach__id=coach_id)
        coach_status.status["hr"]["status"] = "select"
        coach_status.save()

    project.steps["coach_consent"]["status"] = "complete"
    project.save()

    return Response({"message": "Sent Successfully", "details": {}}, status=200)


@api_view(["GET"])
def get_coach_field_values(request):
    job_roles = set()
    languages = set()
    locations = set()
    companies_worked_in = set()
    other_certifications = set()
    industries = set()
    functional_domain = set()
    institute = set()
    for coach in Coach.objects.all():
        # 1st coach
        for role in coach.job_roles:
            job_roles.add(role)
        for language in coach.language:
            languages.add(language)
        for location in coach.location:
            locations.add(location)
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

        # domains.add(coach.domain)
        # educations.add(coach.education)
    return Response(
        {
            "job_roles": list(job_roles),
            "languages": list(languages),
            "educations": list(institute),
            "locations": list(locations),
            "companies_worked_in": list(companies_worked_in),
            "other_certifications": list(other_certifications),
            "domains": list(functional_domain),
            "industries": list(industries),
        },
        status=200,
    )


@api_view(["POST"])
def add_mulitple_coaches(request):
    # Get data from request
    coaches = request.data.get("coaches")

    # Check if coaches data is provided
    if not coaches or not isinstance(coaches, list):
        return Response(
            {"error": "Coaches data must be provided as a list."}, status=400
        )

    try:
        for coach_data in coaches:
            with transaction.atomic():
                # Extract coach details from the coach_data dictionary
                coach_id = coach_data.get("coach_id")
                first_name = coach_data.get("first_name")
                last_name = coach_data.get("last_name")
                age = coach_data.get("age", "")
                gender = coach_data.get("gender")
                level = coach_data.get("level")
                min_fees = coach_data.get("min_fees", "")
                active_inactive = coach_data.get("active_inactive")
                corporate_yoe = coach_data.get("corporate_yoe", "")
                coaching_yoe = coach_data.get("coaching_yoe", "")
                domain = coach_data.get("functional_domain", [])
                email = coach_data.get("email","").strip()
                phone = coach_data.get("mobile")
                phone_country_code = coach_data.get("phone_country_code")
                job_roles = coach_data.get("job_roles", [])
                companies_worked_in = coach_data.get("companies_worked_in", [])
                language = coach_data.get("language", [])
                area_of_expertise = coach_data.get("industries", [])
                location = coach_data.get("location", [])
                linkedin_profile_link = coach_data.get("linkedin_profile", "")
                coaching_hours = coach_data.get("coaching_hours", "")
                fee_remark = coach_data.get("fee_remark", "")
                client_companies = coach_data.get("client_companies", [])
                educational_qualification = coach_data.get(
                    "educational_qualification", []
                )
                corporate_experience = coach_data.get("corporate_experience", "")
                coaching_experience = coach_data.get("coaching_experience", "")
                education = coach_data.get("education", [])
                if coach_data.get("ctt_nctt") == "Yes":
                    ctt_nctt = True
                else:
                    ctt_nctt = False
                if coach_data.get("active_inactive") == "Yes":
                    active_inactive = True
                else:
                    active_inactive = False

                # Perform validation on required fields
                if not all(
                    [
                        coach_id,
                        first_name,
                        last_name,
                        gender,
                        level,
                        email,
                        phone,
                        phone_country_code,
                    ]
                ):
                    return Response(
                        {
                            "error": "All required fields must be provided for each coach."
                        },
                        status=400,
                    )

                # Create the Django User
                if coach_exists(coach_id):
                    return Response(
                        {"error": f"Coach with ID {coach_id} already exists."},
                        status=400,
                    )
                user = User.objects.filter(email=email).first()
                if not user:
                    temp_password = "".join(
                        random.choices(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits,
                            k=8,
                        )
                    )
                    user = User.objects.create_user(
                        username=email, password=temp_password, email=email
                    )
                    profile = Profile.objects.create(user=user)
                else:
                    profile = Profile.objects.get(user=user)

                coach_role, created = Role.objects.get_or_create(name="coach")
                profile.roles.add(coach_role)
                profile.save()

                # api call
                room_id = ""
                management_token = generateManagementToken()
                try:
                    response_from_100ms = requests.post(
                        "https://api.100ms.live/v2/rooms",
                        headers={
                            "Authorization": f"Bearer {management_token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "name": email.replace(".", "-").replace("@", ""),
                            "description": "This is a sample description for the room",
                            "region": "in",
                        },
                    )
                    if response_from_100ms.status_code == 200:
                        room_id = response_from_100ms.json().get("id")
                except Exception as e:
                    print(f"Error while generating meeting link, {str(e)}")

                # Create the Coach User using the Profile
                coach_user = Coach.objects.create(
                    user=profile,
                    coach_id=coach_id,
                    first_name=first_name,
                    last_name=last_name,
                    age=age,
                    gender=gender,
                    level=level,
                    room_id=room_id,
                    min_fees=min_fees,
                    fee_remark=fee_remark,
                    ctt_nctt=ctt_nctt,
                    active_inactive=active_inactive,
                    years_of_corporate_experience=corporate_yoe,
                    years_of_coaching_experience=coaching_yoe,
                    domain=domain,
                    email=email,
                    phone=phone,
                    phone_country_code=phone_country_code,
                    job_roles=job_roles,
                    companies_worked_in=companies_worked_in,
                    language=language,
                    area_of_expertise=area_of_expertise,
                    location=location,
                    linkedin_profile_link=linkedin_profile_link,
                    coaching_hours=coaching_hours,
                    client_companies=client_companies,
                    educational_qualification=educational_qualification,
                    corporate_experience=corporate_experience,
                    coaching_experience=coaching_experience,
                    education=education,
                )

                # Approve coach
                coach = Coach.objects.get(id=coach_user.id)
                coach.is_approved = True
                coach.save()

        return Response({"message": "Coaches added successfully."}, status=201)
    except IntegrityError as e:
        print(e)
        return Response(
            {"error": "A coach user with this email already exists."}, status=400
        )

    except Exception as e:
        # Return error response if any other exception occurs
        print(e)
        return Response(
            {"error": "An error occurred while creating the coach user."}, status=500
        )


@api_view(["GET"])
def get_notifications(request, user_id):
    notifications = Notification.objects.filter(user__id=user_id).order_by(
        "-created_at"
    )
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(["PUT"])
def mark_all_notifications_as_read(request):
    notifications = Notification.objects.filter(
        read_status=False, user__id=request.data["user_id"]
    )
    notifications.update(read_status=True)
    return Response("Notifications marked as read.")


@api_view(["PUT"])
def mark_notifications_as_read(request):
    user_id = request.data.get("user_id")
    notification_ids = request.data.get("notification_ids")

    if user_id is None or notification_ids is None:
        return Response("Both user_id and notification_ids are required.", status=400)

    print("abcd")

    notifications = Notification.objects.filter(
        id=notification_ids, user__id=user_id, read_status=False
    )

    notifications.update(read_status=True)
    return Response("Notifications marked as read.")


@api_view(["GET"])
def unread_notification_count(request, user_id):
    count = Notification.objects.filter(user__id=user_id, read_status=False).count()
    return Response({"count": count})


@api_view(["POST"])
def mark_project_as_sold(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.updated_to_sold = True
    project.steps["project_structure"]["status"] = "complete"
    project.save()
    try:
        path = f"/projects/caas/progress/{project.id}"
        message = f"Project structure has been added to the project - {project.name}."
        message_for_coach = f"Admin has added project structure. Please agree to the project structure to go forward with the Project - {project.name}"
        for hr_user in project.hr.all():
            create_notification(hr_user.user.user, path, message)
        for coach_status in project.coaches_status.all():
            create_notification(coach_status.coach.user.user, path, message_for_coach)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Project marked as sold"}, status=200)


@api_view(["GET"])
def get_session_requests_of_user_on_date(request, user_type, user_id, date):
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    start_time = date_obj.replace(hour=0, minute=0, second=0)
    # Set the end time of the given date at 23:59:59
    end_time = date_obj.replace(hour=23, minute=59, second=59)
    # Convert the datetime objects to timestamps
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())

    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            hr__id=user_id,
            availibility__start_time__range=(start_timestamp, end_timestamp),
        )
    elif user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            learner__id=user_id,
            availibility__start_time__range=(start_timestamp, end_timestamp),
        )
    elif user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            coach__id=user_id,
            availibility__start_time__range=(start_timestamp, end_timestamp),
        )
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def request_reschedule(request, session_id):
    session = SessionRequestCaas.objects.get(id=session_id)
    session.reschedule_request.append(
        {
            "requested_by": "coach",
            "requested_on_timestamp": request.data["requested_on"],
            "message": request.data["message"],
        }
    )
    session.save()
    return Response({"message": "Requested for reschedule"})


@api_view(["POST"])
def reschedule_session(request):
    existing_session = SessionRequestCaas.objects.get(
        id=request.data["existing_session_id"]
    )
    existing_session.is_archive = True
    existing_session.save()
    time_arr = create_time_arr(request.data["availibility"])

    try:
        if request.data["session_type"] == "chemistry":
            session = SessionRequestCaas.objects.get(
                learner__id=request.data["learner_id"],
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        else:
            session = SessionRequestCaas.objects.get(
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        session.availibility.set(time_arr)
        session.save()
        return Response({"message": "Session updated successfully."}, status=201)
    except SessionRequestCaas.DoesNotExist:
        session = {
            "project": request.data["project_id"],
            "availibility": time_arr,
            "coach": request.data["coach_id"],
            "session_type": request.data["session_type"],
        }
        if session["session_type"] == "interview":
            session["hr"] = request.data["hr_id"]
        elif session["session_type"] == "chemistry":
            session["learner"] = request.data["learner_id"]
        session_serilizer = SessionRequestCaasSerializer(data=session)
        if session_serilizer.is_valid():
            session_created = session_serilizer.save()
            try:
                pmo_user = User.objects.filter(profile__roles__name="pmo").first()
                project = Project.objects.get(id=request.data["project_id"])
                coach = Coach.objects.get(id=request.data["coach_id"])
                if pmo_user:
                    path = f"/projects/caas/progress/{project.id}"
                    coach_name = coach.first_name + " " + coach.last_name
                    slot_message = get_slot_message(request.data["availibility"])
                    if session["session_type"] == "interview":
                        message = f"HR has requested interview session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                        message_for_coach = f"HR has requested for {slot_message} for Interview for Project - {project.name}. Please book one of the requested slots now"
                    elif session["session_type"] == "chemistry":
                        hr_user_in_project = (
                            session_created.project.hr.first().user.user
                        )
                        message_for_hr = f"{session_created.learner.name.title()} has requested for Chemistry session to the Coach - {coach_name.title()} for {slot_message} for the Project - {project.name}"
                        message_for_coach = f"Coachee has requested {slot_message} for Chemistry session for the Project - {project.name}. Please book one of the requested slots now"
                        for hr_user in hr_user_in_project:
                            create_notification(hr_user, path, message_for_hr)
                        message = f"Coachee has requested chemistry session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                    message += " " + slot_message
                    create_notification(pmo_user, path, message)
                    create_notification(coach.user.user, path, message_for_coach)
            except Exception as e:
                print(f"Error occurred while creating notification: {str(e)}")
            return Response({"message": "Session sequested successfully."}, status=201)
        else:
            return Response(
                {
                    "message": str(session_serilizer.errors),
                },
                status=401,
            )


@api_view(["GET"])
def get_engagement_in_projects(request, project_id):
    engagements = Engagement.objects.filter(project__id=project_id)
    engagements_data = []

    for engagement in engagements:
        completed_sessions_count = SessionRequestCaas.objects.filter(
            status="completed",
            project__id=engagement.project.id,
            learner__id=engagement.learner.id,
        ).count()

        total_sessions_count = SessionRequestCaas.objects.filter(
            project__id=engagement.project.id,
            learner__id=engagement.learner.id,
            is_archive=False,
        ).count()

        serializer = EngagementDepthOneSerializer(engagement)
        data = serializer.data
        data["completed_sessions_count"] = completed_sessions_count
        data["total_sessions_count"] = total_sessions_count
        engagements_data.append(data)

    return Response(engagements_data, status=200)


@api_view(["GET"])
def get_engagements_of_hr(request, user_id):
    engagements = Engagement.objects.filter(project__hr__id=user_id)
    engagements_data = []
    current_time = int(timezone.now().timestamp() * 1000)
    for engagement in engagements:
        completed_sessions_count = SessionRequestCaas.objects.filter(
            status="completed",
            project__id=engagement.project.id,
            learner__id=engagement.learner.id,
        ).count()

        total_sessions_count = SessionRequestCaas.objects.filter(
            project__id=engagement.project.id,
            learner__id=engagement.learner.id,
            is_archive=False,
        ).count()
        upcoming_session = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            Q(project__hr__id=user_id),
            Q(project__id=engagement.project.id),
            Q(learner__id=engagement.learner.id),
            Q(is_archive=False),
            ~Q(status="completed"),
        ).aggregate(Min("confirmed_availability__end_time"))
        serializer = EngagementDepthOneSerializer(engagement)
        data = serializer.data
        data["completed_sessions_count"] = completed_sessions_count
        data["total_sessions_count"] = total_sessions_count
        data["next_session_time"] = upcoming_session.get(
            "confirmed_availability__end_time__min"
        )
        engagements_data.append(data)

    return Response(engagements_data, status=200)


class SessionCountsForAllLearners(APIView):
    def get(self, request, user_type, user_id, format=None):
        try:
            if user_type == "pmo":
                learners = Learner.objects.all()
            elif user_type == "coach":
                learners = Learner.objects.filter(
                    engagement__coach__id=user_id
                ).distinct()
            elif user_type == "hr":
                learners = Learner.objects.filter(
                    engagement__project__hr__id=user_id
                ).distinct()

            engagements = Engagement.objects.all()
            learner_session_counts = {}

            for engagement in engagements:
                learner_id = engagement.learner.id

                completed_sessions_count = SessionRequestCaas.objects.filter(
                    status="completed",
                    billable_session_number__isnull=False,
                    learner__id=learner_id,
                    is_archive=False,
                ).count()

                total_sessions_count = SessionRequestCaas.objects.filter(
                    learner__id=learner_id,
                    # project_id = engagement.project_id
                    billable_session_number__isnull=False,
                    is_archive=False,
                ).count()

                if learner_id in learners.values_list("id", flat=True):
                    if learner_id not in learner_session_counts:
                        learner_data = {
                            "completed_sessions_count": completed_sessions_count,
                            "total_sessions_count": total_sessions_count,
                        }
                        learner_session_counts[learner_id] = learner_data

            return Response(learner_session_counts, status=status.HTTP_200_OK)

        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(["GET"])
def get_learner_engagement_of_project(request, project_id, learner_id):
    engagement = Engagement.objects.get(learner__id=learner_id, project__id=project_id)
    serializer = EngagementDepthOneSerializer(engagement)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_learners_engagement(request, learner_id):
    engagements = Engagement.objects.filter(learner__id=learner_id)
    serializer = EngagementDepthOneSerializer(engagements, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def create_session_request_by_learner(request, session_id):
    # print(request.user)
    # if request.user.profile.type != "learner":
    #     return Response({"message": "Unauthorized"}, status=401)
    time_arr = create_time_arr(request.data["availibility"])
    session = SessionRequestCaas.objects.get(id=session_id)
    session.availibility.set(time_arr)
    session.status = "requested"
    session.save()
    return Response({"message": "Session requested successfully"})


@api_view(["GET"])
def get_session_requests_of_user(request, user_type, user_id):
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None) & ~Q(status="pending")
        )
    if user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None)
            & Q(learner__id=user_id)
            & ~Q(session_type="chemistry")
            & ~Q(status="pending")
        )
    if user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None) & Q(coach__id=user_id) & ~Q(status="pending")
        )
    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None)
            & Q(project__hr__id=user_id)
            & ~Q(status="pending")
        )
    session_requests = session_requests.annotate(
        engagement_status=Subquery(
            Engagement.objects.filter(
                project=OuterRef("project"),
                learner=OuterRef("learner"),
            ).values("status")[:1]
        )
    )
    serializer = SessionRequestWithEngagementCaasDepthOneSerializer(
        session_requests, many=True
    )
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_session_pending_of_user(request, user_type, user_id):
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None)
            & Q(status="pending")
            & ~Q(session_type="interview")
        )
    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None),
            Q(project__hr__id=user_id),
            Q(status="pending"),
            Q(is_archive=False),
            ~Q(session_type="interview"),
        )

    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    res = []
    for session in serializer.data:
        engagement = Engagement.objects.filter(
            learner__id=session["learner"]["id"], project__id=session["project"]["id"]
        )
        if len(engagement) > 0 and engagement[0].coach:
            coach_serializer = CoachSerializer(engagement[0].coach)
            res.append({**session, "coach": coach_serializer.data})
        else:
            res.append({**session})
    return Response(res, status=200)


# used for pmo and hr report section
@api_view(["GET"])
def get_all_sessions_of_user(request, user_type, user_id):
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            ~Q(session_type="interview"),
            ~Q(session_type="chemistry", billable_session_number=None),
            # ~Q(billable_session_number=None),
            is_archive=False,
        )
    elif user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            ~Q(session_type="interview"),
            ~Q(session_type="chemistry", billable_session_number=None),
            # ~Q(billable_session_number=None),
            is_archive=False,
            project__hr__id=user_id,
        )
    sessions_serializer = SessionRequestCaasDepthOneSerializer(
        session_requests, many=True
    )
    res = []
    for session in sessions_serializer.data:
        engagement = Engagement.objects.filter(
            learner__id=session["learner"]["id"], project__id=session["project"]["id"]
        )
        if len(engagement) > 0 and engagement[0].coach:
            coach_serializer = CoachSerializer(engagement[0].coach)
            res.append({**session, "coach": coach_serializer.data})
        else:
            res.append({**session})
    return Response(res, status=200)


@api_view(["GET"])
def get_upcoming_sessions_of_user(request, user_type, user_id):
    current_time = int(timezone.now().timestamp() * 1000)
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            ~Q(status="completed"),
        )
    if user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            Q(learner__id=user_id),
            ~Q(session_type="chemistry"),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    if user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            Q(coach__id=user_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            Q(project__hr__id=user_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )

    session_requests = session_requests.annotate(
        engagement_status=Subquery(
            Engagement.objects.filter(
                project=OuterRef("project"),
                learner=OuterRef("learner"),
            ).values("status")[:1]
        )
    )
    serializer = SessionRequestWithEngagementCaasDepthOneSerializer(
        session_requests, many=True
    )
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_past_sessions_of_user(request, user_type, user_id):
    current_time = int(timezone.now().timestamp() * 1000)
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
        )
    if user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
            Q(learner__id=user_id),
            ~Q(session_type="chemistry"),
            Q(is_archive=False),
        )
    if user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
            Q(coach__id=user_id),
            Q(is_archive=False),
        )
    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
            Q(project__hr__id=user_id),
            Q(is_archive=False),
        )

    session_requests = session_requests.annotate(
        engagement_status=Subquery(
            Engagement.objects.filter(
                project=OuterRef("project"),
                learner=OuterRef("learner"),
            ).values("status")[:1]
        )
    )
    for session_request in session_requests:
        print(session_request.engagement_status)
    serializer = SessionRequestWithEngagementCaasDepthOneSerializer(
        session_requests, many=True
    )
    return Response(serializer.data, status=200)


@api_view(["POST"])
def edit_session_status(request, session_id):
    try:
        session_request = SessionRequestCaas.objects.get(id=session_id)
    except SessionRequestCaas.DoesNotExist:
        return Response({"error": "Session request not found."}, status=404)
    new_status = request.data.get("status")
    if not new_status:
        return Response({"error": "Status field is required."}, status=400)
    session_request.status = new_status
    current_time = datetime.now()
    session_request.status_updated_at = current_time
    session_request.save()
    return Response({"message": "Session status updated successfully."}, status=200)


@api_view(["POST"])
def edit_session_availability(request, session_id):
    time_arr = create_time_arr(request.data["availibility"])
    try:
        # changing availability - edit request.
        session = SessionRequestCaas.objects.get(id=session_id)
        google_calendar_event = CalendarEvent.objects.filter(
            session=session, account_type="google"
        ).first()
        microsoft_calendar_event = CalendarEvent.objects.filter(
            session=session, account_type="microsoft"
        ).first()
        if session.is_booked:
            return Response({"message": "Session edit failed."}, status=401)
        session.availibility.set(time_arr)
        session.save()
        if google_calendar_event:
            google_calendar_event.session = session
            google_calendar_event.save()
        if microsoft_calendar_event:
            microsoft_calendar_event.session = session
            microsoft_calendar_event.save()
        return Response({"message": "Session updated successfully."}, status=201)
    except:
        return Response({"message": "Session edit failed."}, status=401)


@api_view(["GET"])
def get_coachee_of_user(request, user_type, user_id):
    learners_data = []
    if user_type == "pmo":
        learners = Learner.objects.all()
    elif user_type == "coach":
        learners = Learner.objects.filter(engagement__coach__id=user_id).distinct()
    elif user_type == "hr":
        learners = Learner.objects.filter(
            engagement__project__hr__id=user_id
        ).distinct()
    for learner in learners:
        learner_dict = {
            "id": learner.id,
            "name": learner.name,
            "email": learner.email,
            "phone": learner.phone,
            "area_of_expertise": learner.area_of_expertise,
            "years_of_experience": learner.years_of_experience,
            "projects": [],
            "organisation": set(),
        }
        if user_type == "pmo":
            projects = Project.objects.filter(engagement__learner=learner)
        elif user_type == "coach":
            projects = Project.objects.filter(
                Q(engagement__learner=learner) & Q(engagement__coach__id=user_id)
            )
        elif user_type == "hr":
            projects = Project.objects.filter(
                Q(engagement__learner=learner) & Q(hr__id=user_id)
            )
        # project_data = []
        # organisation = set()
        for project in projects:
            project_dict = {
                "name": project.name,
            }
            learner_dict["organisation"].add(project.organisation.name)
            learner_dict["projects"].append(project_dict)
        learners_data.append(learner_dict)
    # serializer = LearnerSerializer(learners,many=True)
    return Response(learners_data)


@api_view(["GET"])
def get_learner_data(request, learner_id):
    learner = Learner.objects.get(id=learner_id)
    serializer = LearnerSerializer(learner)
    return Response(serializer.data)


# updating the availability and coach in the first pending chemistry available for learner
@api_view(["POST"])
def request_chemistry_session(request, project_id, learner_id):
    session = SessionRequestCaas.objects.filter(
        learner__id=learner_id,
        project__id=project_id,
        session_type="chemistry",
        status="pending",
    )
    print(session)
    if len(session) == 0:
        return Response({"error": "Max sessions exceeded."}, status=400)
    else:
        coach = Coach.objects.get(id=request.data["coach_id"])
        time_arr = create_time_arr(request.data["availibility"])
        session_to_update = session[0]
        session_to_update.availibility.set(time_arr)
        session_to_update.coach = coach
        session_to_update.status = "requested"
        session_to_update.save()
        path_for_coach = f"/sessions"
        slot_message = get_slot_message(request.data["availibility"])
        message_for_coach = f"Coachee has requested {slot_message} for Chemistry session for the Project - {session_to_update.project.name}. Please book one of the requested slots now"
        create_notification(coach.user.user, path_for_coach, message_for_coach)

        project = Project.objects.get(id=project_id)
        time_of_request = timezone.now()
        coachee = Learner.objects.get(id=learner_id)
        session_name = "chemistry"

        session_request = SessionRequestedActivity.objects.create(
            project=project,
            time_of_request=time_of_request,
            coach=coach,
            coachee=coachee,
            session_name=session_name,
        )

    session_request.save()

    return Response({"message": "Session requested successfully"}, status=200)


@api_view(["GET"])
def get_learner_sessions_in_project(request, project_id, learner_id):
    sessions = SessionRequestCaas.objects.filter(
        project__id=project_id, learner__id=learner_id
    ).order_by("order")
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def request_session(request, session_id, coach_id):
    session = SessionRequestCaas.objects.get(id=session_id)
    coach = Coach.objects.get(id=coach_id)
    time_arr = create_time_arr(request.data["availibility"])
    session.availibility.set(time_arr)
    session.coach = coach
    session.status = "requested"
    session.save()

    project = session.project
    time_of_request = timezone.now()
    coachee = session.learner
    session_name = session.session_type

    session_request = SessionRequestedActivity.objects.create(
        project=project,
        time_of_request=time_of_request,
        coach=coach,
        coachee=coachee,
        session_name=session_name,
    )

    session_request.save()

    return Response({"message": "Session requested successfully"}, status=200)


@api_view(["POST"])
def reschedule_session_of_coachee(request, session_id):
    session = SessionRequestCaas.objects.get(id=session_id)

    google_calendar_event = CalendarEvent.objects.filter(
        session=session, account_type="google"
    ).first()
    microsoft_calendar_event = CalendarEvent.objects.filter(
        session=session, account_type="microsoft"
    ).first()

    session.is_archive = True

    time_arr = create_time_arr(request.data["availibility"])
    new_session = SessionRequestCaas.objects.create(
        learner=session.learner,
        project=session.project,
        coach=session.coach,
        session_type=session.session_type,
        status="requested",
        session_number=session.session_number,
        session_duration=session.session_duration,
        order=session.order,
    )
    new_session.availibility.set(time_arr)
    new_session.save()
    session.save()

    if google_calendar_event:
        google_calendar_event.session = new_session
        google_calendar_event.save()
    if microsoft_calendar_event:
        microsoft_calendar_event.session = new_session
        microsoft_calendar_event.save()

    return Response({"message": "Session reschedule successfully"}, status=200)


@api_view(["POST"])
def create_goal(request):
    user_email = request.data.get("email")
    serializer = GoalSerializer(data=request.data)
    goal_name = request.data["name"]
    engagement_id = request.data.get("engagement")

    if not Goal.objects.filter(name=goal_name, engagement__id=engagement_id).exists():
        if Goal.objects.filter(engagement__id=engagement_id).count() < 10:
            if serializer.is_valid():
                serializer.save()
                try:
                    user_instance = User.objects.get(username=user_email)
                    AddGoalActivity.objects.create(
                        user=user_instance,
                        timestamp=timezone.now(),
                    )
                except Exception as e:
                    print("AddGoalActivity error", str(e))

                return Response({"message": "Goal created successfully."}, status=201)
            return Response(serializer.errors, status=400)
        else:
            return Response(
                {"error": "The project already has 10 goals. Cannot add more."},
                status=400,
            )
    else:
        return Response({"error": "Goal already exists for the project."}, status=400)


@api_view(["GET"])
def get_engagement_goals(request, engagement_id):
    goals = Goal.objects.filter(engagement__id=engagement_id)
    serializer = GetGoalSerializer(goals, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def edit_goal(request, goal_id):
    try:
        goal = Goal.objects.get(id=goal_id)
    except Goal.DoesNotExist:
        return Response({"error": "Goal not found."}, status=404)

    serializer = GoalSerializer(instance=goal, data=request.data)
    goal_name = request.data.get("name", goal.name)
    engagement_id = request.data.get("engagement", goal.engagement.id)

    if (
        not Goal.objects.filter(name=goal_name, engagement_id=engagement_id)
        .exclude(id=goal_id)
        .exists()
    ):
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Goal updated successfully."}, status=200)
        return Response(serializer.errors, status=400)
    else:
        return Response(
            {
                "error": "Another goal with the same name already exists in the engagement."
            },
            status=400,
        )


@api_view(["DELETE"])
def delete_goal(request, goal_id):
    try:
        goal = Goal.objects.get(id=goal_id)
    except Goal.DoesNotExist:
        return Response({"error": "Goal not found."}, status=404)
    goal.delete()
    return Response({"message": "Goal deleted successfully."}, status=204)


@api_view(["POST"])
def create_competency(request):
    serializer = CompetencySerializer(data=request.data)
    goal_id = request.data.get("goal")
    competency_count = Competency.objects.filter(goal__id=goal_id).count()

    if competency_count < 10:
        if serializer.is_valid():
            competency = serializer.save()
            return Response({"message": "Competency added successfully"}, status=201)
        return Response(serializer.errors, status=400)
    else:
        return Response(
            {"error": "The goal already has 10 competencies. Cannot add more."},
            status=400,
        )


@api_view(["POST"])
def edit_competency(request, competency_id):
    try:
        competency = Competency.objects.get(id=competency_id)
    except Competency.DoesNotExist:
        return Response({"error": "Competency not found."}, status=404)

    serializer = CompetencySerializer(instance=competency, data=request.data)
    competency_name = request.data["name"]
    if (
        not Competency.objects.filter(name=competency_name, goal__id=competency.goal.id)
        .exclude(id=competency.goal.id)
        .exists()
    ):
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Competency updated successfully."}, status=200)
        return Response(serializer.errors, status=400)
    else:
        return Response(
            {
                "error": "Another competency with the same name already exists in the goal."
            },
            status=400,
        )


@api_view(["DELETE"])
def delete_competency(request, competency_id):
    try:
        competency = Competency.objects.get(id=competency_id)
    except Competency.DoesNotExist:
        return Response({"error": "Competency not found."}, status=404)
    competency.delete()
    return Response({"message": "Goal deleted successfully."}, status=204)


@api_view(["GET"])
def get_engagement_competency(request, engagement_id):
    competentcy = Competency.objects.filter(goal__engagement__id=engagement_id)
    serializer = CompetencyDepthOneSerializer(competentcy, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def add_score_to_competency(request, competency_id):
    try:
        competency = Competency.objects.get(id=competency_id)
        scoring_data = {
            "date": request.data.get("date"),
            "score": request.data.get("score"),
        }
        if len(competency.scoring) >= 20:
            return Response(
                {
                    "error": "The maximum number of scores (20) for this competency has been reached."
                },
                status=400,
            )

        competency.scoring.append(scoring_data)
        competency.save()
        return Response(
            {"message": "Competency scoring updated successfully."}, status=201
        )
    except Competency.DoesNotExist:
        return Response({"error": "Competency not found."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
def get_competency_by_goal(request, goal_id):
    competentcy = Competency.objects.filter(goal__id=goal_id)
    serializer = CompetencyDepthOneSerializer(competentcy, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def create_action_item(request):
    serializer = ActionItemSerializer(data=request.data)
    competency_id = request.data.get("competency")

    if ActionItem.objects.filter(competency__id=competency_id).count() < 20:
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Action created successfully."}, status=201)
        return Response(serializer.errors, status=400)
    else:
        return Response(
            {"error": "The competency already has 20 action items. Cannot add more."},
            status=400,
        )


@api_view(["GET"])
def get_engagement_action_items(request, engagement_id):
    action_items = ActionItem.objects.filter(
        competency__goal__engagement__id=engagement_id
    )
    serializer = GetActionItemDepthOneSerializer(action_items, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_action_items_by_competency(request, competency_id):
    action_items = ActionItem.objects.filter(competency__id=competency_id)
    serializer = GetActionItemDepthOneSerializer(action_items, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def edit_action_item(request, action_item_id):
    try:
        action_item = ActionItem.objects.get(id=action_item_id)
    except ActionItem.DoesNotExist:
        return Response({"error": "Action item not found."}, status=404)
    serializer = ActionItemSerializer(instance=action_item, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Action item updated successfully."}, status=200)
    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
def delete_action_item(request, action_item_id):
    try:
        action_item = ActionItem.objects.get(id=action_item_id)
    except ActionItem.DoesNotExist:
        return Response({"error": "Action item not found."}, status=404)
    action_item.delete()
    return Response({"message": "Action item deleted successfully"}, status=204)


@api_view(["POST"])
def mark_session_as_complete(request, session_id):
    try:
        session = SessionRequestCaas.objects.get(id=session_id)
    except ActionItem.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)
    session.status = "completed"
    session.save()
    return Response({"message": "Session marked as complete."}, status=201)


@api_view(["POST"])
def update_engagement_status(request, status, engagement_id):
    try:
        engagement = Engagement.objects.get(id=engagement_id)
    except Engagement.DoesNotExist:
        return Response({"error": "Engagement not found."}, status=404)
    engagement.status = status
    engagement.save()
    return Response({"message": f"Engagement marked as {status}."}, status=201)


@api_view(["GET"])
def get_all_competencies(request):
    goals_with_competencies = Goal.objects.prefetch_related("competency_set").all()

    competency_list = []

    for goal in goals_with_competencies:
        goal_name = goal.name
        project_name = (
            goal.engagement.project.name
            if goal.engagement and goal.engagement.project
            else "N/A"
        )
        coachee_name = (
            goal.engagement.learner.name
            if goal.engagement and goal.engagement.learner
            else "N/A"
        )
        coach_name = (
            goal.engagement.coach.first_name + " " + goal.engagement.coach.last_name
            if goal.engagement and goal.engagement.coach
            else "N/A"
        )

        # Include goals without competencies
        if goal.competency_set.exists():
            for competency in goal.competency_set.all():
                competency_data = {
                    "id": competency.id,
                    "goal_id": goal_name,
                    "name": competency.name,
                    "scoring": competency.scoring,
                    "created_at": competency.created_at.isoformat(),
                    "project_name": project_name,
                    "learner_name": coachee_name,
                    "coach_name": coach_name,
                }
                competency_list.append(competency_data)
        else:
            # Include goals with no competencies
            competency_data = {
                "id": None,
                "goal_id": goal_name,
                "name": "-",
                "scoring": [],
                "created_at": None,
                "project_name": project_name,
                "learner_name": coachee_name,
                "coach_name": coach_name,
            }
            competency_list.append(competency_data)

    return Response({"competencies": competency_list})


@api_view(["GET"])
def get_current_session(request, user_type, room_id, user_id):
    five_minutes_in_milliseconds = 300000
    current_time = int(timezone.now().timestamp() * 1000)
    five_minutes_plus_current_time = current_time + five_minutes_in_milliseconds
    if user_type == "coach":
        sessions = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
            & Q(confirmed_availability__end_time__gt=current_time),
            Q(coach__id=user_id),
            Q(coach__room_id=room_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    elif user_type == "learner":
        sessions = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
            & Q(confirmed_availability__end_time__gt=current_time),
            Q(learner__id=user_id),
            (Q(coach__room_id=room_id) | Q(pmo__room_id=room_id)),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    elif user_type == "hr":
        sessions = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
            & Q(confirmed_availability__end_time__gt=current_time),
            Q(hr__id=user_id),
            (Q(coach__room_id=room_id) | Q(pmo__room_id=room_id)),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    elif user_type == "pmo":
        sessions = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
            & Q(confirmed_availability__end_time__gt=current_time),
            Q(pmo__id=user_id),
            (Q(coach__room_id=room_id) | Q(pmo__room_id=room_id)),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    if len(sessions) == 0:
        return Response({"error": "You don't have any sessions right now."}, status=404)
    return Response({"message": "success"}, status=200)


# @api_view(["POST"])
# def get_current_session_of_stakeholder(request, room_id):
#     five_minutes_in_milliseconds = 300000
#     current_time = int(timezone.now().timestamp() * 1000)
#     five_minutes_plus_current_time = current_time + five_minutes_in_milliseconds
#     sessions = SessionRequestCaas.objects.filter(
#         Q(is_booked=True),
#         Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
#         & Q(confirmed_availability__end_time__gt=current_time),
#         Q(coach__room_id=room_id),
#         Q(session_type="tripartite")
#         | Q(session_type="mid_review")
#         | Q(session_type="end_review"),
#         Q(invitees__contains=request.data["email"]),
#         Q(is_archive=False),
#         ~Q(status="completed"),
#     )
#     if len(sessions) == 0:
#         return Response({"error": "You don't have any sessions right now."}, status=404)
#     return Response({"message": "success"}, status=200)


@api_view(["POST"])
def get_current_session_of_stakeholder(request, room_id):
    five_minutes_in_milliseconds = 300000
    current_time = int(timezone.now().timestamp() * 1000)
    five_minutes_plus_current_time = current_time + five_minutes_in_milliseconds
    sessions = SessionRequestCaas.objects.filter(
        Q(is_booked=True),
        Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
        & Q(confirmed_availability__end_time__gt=current_time),
        (Q(coach__room_id=room_id) | Q(pmo__room_id=room_id)),
        Q(session_type="tripartite")
        | Q(session_type="mid_review")
        | Q(session_type="end_review")
        | Q(session_type="stakeholder_without_coach")
        | Q(session_type="stakeholder_interview"),
        Q(invitees__contains=request.data["email"]),
        Q(is_archive=False),
        ~Q(status="completed"),
    )
    if len(sessions) == 0:
        return Response({"error": "You don't have any sessions right now."}, status=404)
    return Response({"message": "success"}, status=200)


@api_view(["POST"])
def schedule_session_directly(request, session_id):
    try:
        session = SessionRequestCaas.objects.get(id=session_id)
    except SessionRequestCaas.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)

    google_calendar_event = CalendarEvent.objects.filter(
        session=session, account_type="google"
    ).first()
    microsoft_calendar_event = CalendarEvent.objects.filter(
        session=session, account_type="microsoft"
    ).first()

    if session.learner:
        coachee = session.learner

        sessionName = str(session.session_type).replace("_", " ")
        if sessionName == "stakeholder without coach":
            sessionName = "tripartite without coach"
    time_arr = create_time_arr(request.data.get("availability", []))
    if len(time_arr) == 0:
        return Response({"error": "Please provide the availability."}, status=404)

    availability = Availibility.objects.get(id=time_arr[0])
    if request.data["user_type"] == "pmo":
        pmo = Pmo.objects.get(id=request.data["user_id"])
        session.pmo = pmo

    if request.data["user_type"] == "coach":
        coach = Coach.objects.get(id=request.data["user_id"])
        session.coach = coach

    if session.session_type == "stakeholder_interview":
        engagement = Engagement.objects.get(
            learner=session.learner, project=session.project
        )
        session.coach = engagement.coach
        session.hr = session.project.hr.first()

    session.availibility.add(availability)
    session.confirmed_availability = availability
    start_time = format_timestamp(int(session.confirmed_availability.start_time))
    end_time = format_timestamp(int(session.confirmed_availability.end_time))
    slot_message = f"{start_time} - {end_time}"

    session_date = get_date(int(session.confirmed_availability.start_time))
    start_time = get_time(int(session.confirmed_availability.start_time))
    end_time = get_time(int(session.confirmed_availability.end_time))

    session_time = f"{start_time} - {end_time} IST"

    session.is_booked = True

    session.status = "booked"
    session.invitees = get_trimmed_emails(request.data.get("invitees", []))
    session.save()
    coach = None
    if request.data["user_type"] == "coach":
        coach = Coach.objects.get(id=request.data["user_id"])
    if coachee:
        event_detail = {
            "title": f"{SESSION_TYPE_VALUE[session.session_type]} Session",
            "description": "Session Scheduled",
            "startDate": session_date,
            "startTime": start_time,
            "endDate": session_date,
            "endTime": end_time,
        }
        if session.project.enable_emails_to_hr_and_coachee:
            microsoft_auth_url = (
                f'{env("BACKEND_URL")}/api/microsoft/oauth/{coachee.email}/'
            )
            user_token_present = False
            try:
                user_token = UserToken.objects.get(
                    user_profile__user__username=coachee.email
                )
                if user_token:
                    user_token_present = True
            except Exception as e:
                pass

            send_mail_templates(
                "coachee_emails/session_booked.html",
                [coachee.email],
                "Meeraq Coaching | Session Booked",
                {
                    "projectName": session.project.name,
                    "name": coachee.name,
                    "sessionName": SESSION_TYPE_VALUE[session.session_type],
                    "slot_date": session_date,
                    "slot_time": session_time,
                    "email": coachee.email,
                    "microsoft_auth_url": microsoft_auth_url,
                    "user_token_present": user_token_present,
                },
                [],  # no bcc
            )

            try:
                coachee_user_token = UserToken.objects.get(
                    user_profile__user__username=coachee.email
                )

                coachee_access_token = coachee_user_token.access_token
                if coachee_user_token.account_type == "google":
                    coachee_access_token = refresh_google_access_token(
                        coachee_user_token
                    )

                    if google_calendar_event:
                        delete_google_calendar_event(
                            coachee_access_token, google_calendar_event.event_id
                        )
                        google_calendar_event.delete()

                    if request.data["user_type"] == "coach":
                        create_google_calendar_event(
                            coachee_access_token,
                            event_detail,
                            coach.email,
                            session,
                        )
                    else:
                        create_google_calendar_event(
                            coachee_access_token,
                            event_detail,
                            "No Data",
                            session,
                        )
                else:
                    coachee_access_token = refresh_microsoft_access_token(
                        coachee_user_token
                    )

                    if microsoft_calendar_event:
                        delete_microsoft_calendar_event(
                            coachee_access_token, microsoft_calendar_event.event_id
                        )
                        microsoft_calendar_event.delete()

                    if request.data["user_type"] == "coach":
                        create_microsoft_calendar_event(
                            coachee_access_token,
                            event_detail,
                            {
                                "address": coach.email,
                                "name": coach.first_name + " " + coach.last_name,
                            },
                            session,
                        )
                    else:
                        create_microsoft_calendar_event(
                            coachee_access_token,
                            event_detail,
                            {"address": "No Data", "name": "No Data"},
                            session,
                        )
            except Exception as e:
                print(f"Coachee calendar error {str(e)}")

        if request.data["user_type"] == "coach":
            coach = Coach.objects.get(id=request.data["user_id"])

            try:
                coach_user_token = UserToken.objects.get(
                    user_profile__user__username=coach.email
                )
                coach_access_token = coach_user_token.access_token
                if coach_user_token.account_type == "google":
                    coach_access_token = refresh_google_access_token(coach_user_token)

                    if google_calendar_event:
                        delete_google_calendar_event(
                            coach_access_token, google_calendar_event.event_id
                        )
                        google_calendar_event.delete()

                    create_google_calendar_event(
                        coach_access_token,
                        event_detail,
                        coachee.email,
                        session,
                    )
                else:
                    coach_access_token = refresh_microsoft_access_token(
                        coach_user_token
                    )
                    if microsoft_calendar_event:
                        delete_microsoft_calendar_event(
                            coach_access_token, microsoft_calendar_event.event_id
                        )
                        microsoft_calendar_event.delete()

                    create_microsoft_calendar_event(
                        coach_access_token,
                        event_detail,
                        {"address": coachee.email, "name": coachee.name},
                        session,
                    )
            except Exception as e:
                print(f"Coach calendar error {str(e)}")

    return Response({"message": "Session booked successfully."})


@api_view(["POST"])
def delete_learner_from_project(request, engagement_id):
    try:
        engagement = Engagement.objects.get(id=engagement_id)
    except Engagement.DoesNotExist:
        return Response({"error": "Learner not found in project."}, status=404)
    try:
        print("outside the for loop ")
        # removing the learner id from the project coaches statuses
        for coach_statuses in engagement.project.coaches_status.all():
            print("inside for loop")
            if engagement.learner.id in coach_statuses.learner_id:
                coach_statuses.learner_id.remove(engagement.learner.id)
            coach_statuses.save()
        sessions_to_delete = SessionRequestCaas.objects.filter(
            learner__id=engagement.learner.id, project__id=engagement.project.id
        )
        sessions_to_delete.delete()
        engagement.delete()
        return Response({"message": "Learner deleted successfully"})
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to remove learner from the project."}, status=400
        )


@api_view(["POST"])
def reset_consent(request):
    try:
        coach_status = get_object_or_404(
            CoachStatus, id=request.data.get("coach_status_id")
        )
    except CoachStatus.DoesNotExist:
        return Response({"error": "Could not find coach consent"}, status=404)

    if request.data.get("type") == "consent":
        coach_status.status["consent"]["status"] = "sent"
        coach_status.consent_expiry_date = request.data["consent_expiry_date"]
        # coach_status.consent_expiry_date = datetime.strptime(
        #     request.data.get("consent_expiry_date"), "%Y-%m-%d"
        # ).date()

    coach_status.status["project_structure"]["status"] = "sent"
    coach_status.save()

    return Response({"message": "Consent reset successfully"})


@api_view(["GET"])
def get_competency_averages(request, hr_id):
    # Step 1: Retrieve the data from the Competency model
    competencies = Competency.objects.filter(goal__engagement__project__hr__id=hr_id)
    # Step 2 and 3: Calculate the average score for each competency and store in a dictionary
    competency_averages = defaultdict(lambda: {"total_score": 0, "count": 0})

    for competency in competencies:
        competency_name = competency.name
        scoring_data = competency.scoring
        if scoring_data and len(scoring_data) > 0:
            # taking only the latest score
            total_score = scoring_data[-1]["score"]
            # sum(entry["score"] for entry in scoring_data)
            # count = len(scoring_data)
            competency_averages[competency_name]["total_score"] += total_score
            competency_averages[competency_name]["count"] += 1
    # Step 4: Calculate the final average for each competency, on their latest score
    final_averages = {}
    for competency_name, data in competency_averages.items():
        total_score = data["total_score"]
        count = data["count"]
        average_score = total_score / count if count > 0 else 0
        final_averages[competency_name] = average_score
    top_5_competencies = dict(
        sorted(final_averages.items(), key=lambda item: item[1], reverse=True)[:5]
    )
    return Response(top_5_competencies, status=200)


@api_view(["GET"])
def get_learner_competency_averages(request, learner_id):
    competencies = Competency.objects.filter(goal__engagement__learner__id=learner_id)
    serializer = CompetencyDepthOneSerializer(competencies, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_upcoming_session_count(request, hr_id):
    current_time = int(timezone.now().timestamp() * 1000)
    session_requests = []
    # Get the start and end of the current month
    # current_month = timezone.now().replace(
    #     day=1, hour=0, minute=0, second=0, microsecond=0
    # )
    # current_month_timestamp = int(current_month.timestamp() * 1000)
    # next_month = current_month.replace(month=current_month.month + 1, day=1)
    # if current_month.month == 12:  # Handle December case
    #     next_month = next_month.replace(year=current_month.year + 1)
    # next_month_timestamp = int(next_month.timestamp() * 1000)
    session_requests = SessionRequestCaas.objects.filter(
        Q(is_booked=True),
        Q(confirmed_availability__end_time__gt=current_time),
        Q(project__hr__id=hr_id),
        Q(is_archive=False),
        ~Q(status="completed"),
    )
    upcoming_session_count = session_requests.count()
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(
        {
            "upcoming_sessions": serializer.data,
            "upcoming_session_count": upcoming_session_count,
        },
        status=200,
    )


@api_view(["GET"])
def get_requests_count(request, hr_id):
    session_requests = SessionRequestCaas.objects.filter(
        Q(confirmed_availability=None) & Q(project__hr__id=hr_id) & ~Q(status="pending")
    )
    requests_count = session_requests.count()
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(
        {
            "requestes": serializer.data,
            "requests_count": requests_count,
        },
        status=200,
    )


@api_view(["GET"])
def get_completed_sessions_count(request, hr_id):
    session_requests = SessionRequestCaas.objects.filter(
        Q(project__hr__id=hr_id) & Q(status="completed")
    )
    sessions_count = session_requests.count()
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(
        {
            "sessions": serializer.data,
            "sessions_count": sessions_count,
        },
        status=200,
    )


@api_view(["GET"])
def get_completed_learner_sessions_count(request, learner_id):
    learner_session_requests = SessionRequestCaas.objects.filter(
        Q(learner__id=learner_id) & Q(status="completed")
    )
    sessions_count = learner_session_requests.count()
    serializer = SessionRequestCaasDepthOneSerializer(
        learner_session_requests, many=True
    )
    return Response(
        {
            "sessions": serializer.data,
            "sessions_count": sessions_count,
        },
        status=200,
    )


@api_view(["GET"])
def get_total_goals_for_learner(request, learner_id):
    try:
        total_goals = Goal.objects.filter(engagement__learner_id=learner_id).count()
        return Response(
            {"total_goals": total_goals},
            status=200,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=400,
        )


@api_view(["GET"])
def get_total_competencies_for_learner(request, learner_id):
    try:
        total_competencies = Competency.objects.filter(
            goal__engagement__learner_id=learner_id
        ).count()
        return Response(
            {"total_competency": total_competencies},
            status=200,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=400,
        )


@api_view(["GET"])
def get_learners_without_sessions(request, hr_id):
    # Get the learners associated with the given hr_id who don't have any sessions with status = "requested" or "booked".
    learners = (
        Learner.objects.filter(engagement__project__hr__id=hr_id)
        .exclude(sessionrequestcaas__status__in=["requested", "booked"])
        .distinct()
    )
    # Serialize the filtered learner data.
    learners_count = learners.count()
    serializer = LearnerSerializer(learners, many=True)
    return Response(
        {"learners": serializer.data, "learners_count": learners_count}, status=200
    )


@api_view(["POST"])
def select_coach_for_coachee(request):
    try:
        coach_status = CoachStatus.objects.get(id=request.data["coach_status_id"])
    except CoachStatus.DoesNotExist:
        return Response({"error": "Coach not found"}, status=404)
    try:
        engagement = Engagement.objects.get(id=request.data["engagement_id"])
    except Engagement.DoesNotExist:
        return Response({"error": "Unable to find learner"}, status=404)
    coach_status.learner_id.append(engagement.learner.id)
    coach_status.save()
    engagement.coach = coach_status.coach
    engagement.save()
    return Response({"message": "Coach finalized for coachee"}, status=201)


@api_view(["POST"])
def add_past_session(request, session_id):
    # print("request data",request.data)
    try:
        session = SessionRequestCaas.objects.get(id=session_id)
    except SessionRequestCaas.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)

    time_arr = create_time_arr(request.data.get("availability", []))

    if len(time_arr) == 0:
        return Response({"error": "Please provide the availability."}, status=404)
    availability = Availibility.objects.get(id=time_arr[0])
    session.availibility.add(availability)
    session.confirmed_availability = availability
    session.is_booked = True
    if session.session_type != "stakeholder_without_coach":
        coach_id = request.data.get("coach_id")
        if coach_id:
            try:
                coach = Coach.objects.get(id=coach_id)
                session.coach = coach

            except Coach.DoesNotExist:
                return Response({"error": "Coach not found."}, status=404)

    session.status = "completed"
    session.invitees = get_trimmed_emails(request.data.get("invitees", []))
    session.status_updated_at = datetime.now()
    session.save()

    coach = session.coach
    coachee = session.learner
    project = session.project
    timestamp = timezone.now()
    user_id = request.data.get("userId")
    user_who_added = User.objects.get(id=user_id)

    addPastSession = PastSessionActivity.objects.create(
        project=project,
        user_who_added=user_who_added,
        coach=coach,
        coachee=coachee,
        timestamp=timestamp,
        session_name=session.session_type,
    )
    addPastSession.save()

    return Response({"message": "Session booked successfully."})


@api_view(["GET"])
def get_pending_action_items_by_competency(request, learner_id):
    action_items = ActionItem.objects.filter(
        competency__goal__engagement__learner_id=learner_id, status="not_done"
    )
    serializer = PendingActionItemSerializer(action_items, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_all_competencies_of_hr(request, hr_id):
    goals_with_competencies = Goal.objects.prefetch_related("competency_set").filter(
        engagement__project__hr=hr_id
    )

    competency_list = []

    for goal in goals_with_competencies:
        goal_name = goal.name
        project_name = (
            goal.engagement.project.name
            if goal.engagement and goal.engagement.project
            else "N/A"
        )
        coachee_name = (
            goal.engagement.learner.name
            if goal.engagement and goal.engagement.learner
            else "N/A"
        )

        coach_name = (
            goal.engagement.coach.first_name + " " + goal.engagement.coach.last_name
            if goal.engagement and goal.engagement.coach
            else "N/A"
        )

        # Include goals without competencies
        if goal.competency_set.exists():
            for competency in goal.competency_set.all():
                competency_data = {
                    "id": competency.id,
                    "goal_id": goal_name,
                    "name": competency.name,
                    "scoring": competency.scoring,
                    "created_at": competency.created_at.isoformat(),
                    "project_name": project_name,
                    "learner_name": coachee_name,
                    "coach_name": coach_name,
                }
                competency_list.append(competency_data)
        else:
            # Include goals with no competencies
            competency_data = {
                "id": None,
                "goal_id": goal_name,
                "name": "-",
                "scoring": [],
                "created_at": None,
                "project_name": project_name,
                "learner_name": coachee_name,
                "coach_name": coach_name,
            }
            competency_list.append(competency_data)

    return Response({"competencies": competency_list})


class UpdateInviteesView(APIView):
    def put(self, request, session_request_id):
        try:
            session_request = SessionRequestCaas.objects.get(pk=session_request_id)
        except SessionRequestCaas.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            invitee_emails = request.data.get("inviteeEmails", [])
            print(invitee_emails)
            session_request.invitees = get_trimmed_emails(invitee_emails)
            session_request.save()
            return Response(
                {"message": " Invitees Updated Sucessfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                data={"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# @api_view(["GET"])
# def coach_session_list(request, coach_id):
#     try:
#         coach = Coach.objects.get(id=coach_id)
#     except Coach.DoesNotExist:
#         return Response({"error": "Coach not found"}, status=status.HTTP_404_NOT_FOUND)

#     sessions = SessionRequestCaas.objects.filter(coach=coach)
#     serializer = SessionRequestCaasSerializer(sessions, many=True)

#     return Response(serializer.data, status=status.HTTP_200_OK)


# @api_view(["GET"])
# def coach_session_list(request, coach_id):
#     try:
#         coach = Coach.objects.get(id=coach_id)
#     except Coach.DoesNotExist:
#         return Response({"error": "Coach not found"}, status=status.HTTP_404_NOT_FOUND)

#     sessions = SessionRequestCaas.objects.filter(coach=coach)
#     serializer_data = []

#     for session in sessions:
#         print("4575", session)
#         session_data = {
#             "session_id": session.id,
#             "session_status": session.status,
#             "project_id": session.project.id,
#             "project_name": session.project.name,
#             "organisation_name": session.project.organisation.name,
#             # Include other relevant project details here
#         }
#         serializer_data.append(session_data)

#     return Response(serializer_data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def remove_coach_from_project(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        coach_id = request.data.get("coachIdToDelete")
        coach = Coach.objects.get(id=coach_id)
        currentuser_id = request.data.get("currentUserId")
        currentuser = User.objects.get(id=currentuser_id)

    except Project.DoesNotExist:
        return Response(
            {"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Coach.DoesNotExist:
        return Response(
            {"message": "Coach not found"}, status=status.HTTP_404_NOT_FOUND
        )

    engagements_with_coach = Engagement.objects.filter(project=project, coach=coach)

    for engagement in engagements_with_coach:
        sessions = SessionRequestCaas.objects.filter(
            project=project,
            learner=engagement.learner,
        )
        for session in sessions:
            session.status = "pending"
            session.hr = None
            session.pmo = None
            session.coach = None
            session.invitees = []
            session.availibility.clear()
            session.confirmed_availability = None
            session.is_booked = False
            session.reschedule_request = []
            session.is_archive = False
            session.save()

        engagement.coach = None
        engagement.save()

    for coach_status in project.coaches_status.all():
        if coach_status.coach.id == coach_id:
            project.coaches_status.remove(coach_status)
            project.coaches.remove(coach)
            project.save()
            coach_status.delete()

            user = "default user"
            time_of_removal = timezone.now()
            removed_coach = coach
            removed_from_project = project

            removeCoachProfile = RemoveCoachActivity.objects.create(
                user=currentuser,
                time_of_removal=time_of_removal,
                removed_coach=removed_coach,
                removed_from_project=removed_from_project,
            )

            removeCoachProfile.save()

            return Response(
                {"message": "Coach has been removed from the project."},
                status=status.HTTP_201_CREATED,
            )

    return Response(
        {"message": "Coach is not associated with the project"},
        status=status.HTTP_400_BAD_REQUEST,
    )

    # if request.method == "POST":


@api_view(["POST"])
def standard_field_request(request, user_id):
    value = request.data.get("value")

    user_instance = Coach.objects.get(id=user_id)

    field_name = request.data.get("field_name")  # Adjust this based on your field name
    standardized_field, created = StandardizedField.objects.get_or_create(
        field=field_name
    )

    standardized_field_request = StandardizedFieldRequest(
        standardized_field_name=standardized_field,
        coach=user_instance,
        value=value,
        status="pending",
    )
    standardized_field_request.save()

    return Response({"message": "Request sent."}, status=200)


@api_view(["GET"])
def coaches_which_are_included_in_projects(request):
    coachesId = []
    projects = Project.objects.all()

    for project in projects:
        for coach_status in project.coaches_status.all():
            if (
                coach_status.status["hr"]["status"] == "select"
                and coach_status.status["project_structure"]["status"] == "select"
            ):
                coachesId.append(coach_status.coach.id)

    coachesId = set(coachesId)

    return Response(coachesId)


def calculate_session_progress_data_for_hr(user_id):
    session_requests = (
        SessionRequestCaas.objects.filter(project__hr__id=user_id)
        .exclude(
            Q(session_type="chemistry", billable_session_number__isnull=True)
            | Q(session_type="interview")
        )
        .annotate(
            completed_sessions_count=Count(
                Case(When(status="completed", then=1), output_field=IntegerField())
            ),
            total_sessions_count=Count("pk"),
            billable_count=Count(
                Case(
                    When(billable_session_number__isnull=False, then=1),
                    output_field=IntegerField(),
                )
            ),
        )
        .prefetch_related("project", "learner")
    )

    session_data = []
    for session_request in session_requests:
        session_data.append(
            {
                "session_type": session_request.session_type,
                "project_data": ProjectDepthTwoSerializer(session_request.project).data,
                "learner": LearnerDepthOneSerializer(session_request.learner).data,
                "billable": session_request.billable_count > 0,
                "duration": session_request.session_duration,
                "completed_sessions": session_request.completed_sessions_count > 0,
            }
        )
    return session_data


def calculate_and_send_session_data(user_id):
    try:
        filtered_sessions = calculate_session_progress_data_for_hr(user_id)

        session_type_data = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "session_type": None,
                    "billable": "No",
                    "duration": None,
                    "total_sessions": 0,
                    "completed_sessions": 0,
                }
            )
        )

        for session in filtered_sessions:
            project_data = session.get("project_data")
            project_name = project_data.get("name")
            session_type = session.get("session_type")

            session_type_data[project_name][session_type]["session_type"] = session_type
            session_type_data[project_name][session_type]["billable"] = (
                "Yes" if session.get("billable") else "No"
            )
            session_type_data[project_name][session_type]["duration"] = session.get(
                "duration"
            )

            session_type_data[project_name][session_type]["total_sessions"] += 1
            session_type_data[project_name][session_type][
                "completed_sessions"
            ] += session.get("completed_sessions", 0)

        calculated_data = {
            project_name: {
                session_type: {
                    **session,
                    "completion_percentage": format(
                        (session["completed_sessions"] / session["total_sessions"])
                        * 100,
                        ".1f",
                    )
                    if session["total_sessions"] > 0
                    else 0,
                }
                for session_type, session in project_data.items()
            }
            for project_name, project_data in session_type_data.items()
        }

        hr = HR.objects.get(id=user_id)

        email_message = render_to_string(
            "hr_emails/progress_data_excel_send.html",
            {"name": hr.first_name},
        )
        email = EmailMessage(
            f"{env('EMAIL_SUBJECT_INITIAL',default='')}{'Progress Data'}",
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [hr.email],
            bcc=[],
        )

        excel_buffer = io.BytesIO()

        wb = Workbook()

        for project_name, project_data in calculated_data.items():
            ws = wb.create_sheet(title=project_name)

            df = pd.DataFrame.from_dict(project_data, orient="index")
            df.columns = [col.replace("_", " ").capitalize() for col in df.columns]
            # Add column names as the first row in the worksheet
            for c_idx, col_name in enumerate(df.columns, start=1):
                if col_name == "Duration":
                    col_name = "Duration (Min)"
                cell = ws.cell(row=1, column=c_idx, value=col_name)
                cell.font = Font(bold=True)

            # Iterate over DataFrame rows and add data to the worksheet
            for r_idx, row in enumerate(df.iterrows(), start=2):
                for c_idx, value in enumerate(row[1], start=1):
                    if isinstance(value, str):
                        value = str(value).replace("_", " ").capitalize()
                    if value == "Stakeholder without coach":
                        value = "Tripartate without coach"
                    cell = ws.cell(row=r_idx, column=c_idx, value=value)

        default_sheet = wb["Sheet"]
        wb.remove(default_sheet)

        wb.save(excel_buffer)

        email.attach(
            "progress_data.xlsx",
            excel_buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        email.send(fail_silently=False)

    except Exception as e:
        print(f"Error occurred while sending email with attachment: {str(e)}")


class SessionsProgressOfAllCoacheeForAnHr(APIView):
    def get(self, request, user_id, format=None):
        session_data = calculate_session_progress_data_for_hr(user_id)

        return Response({"session_data": session_data})


class AddRegisteredCoach(APIView):
    def post(self, request, *args, **kwargs):
        # Get data from request

        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        is_approved = request.data.get("is_approved")
        phone_country_code = request.data.get("phone_country_code")

        if not all([first_name, last_name, email, phone, phone_country_code]):
            return Response(
                {"error": "All required fields must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create the Django User
            if Coach.objects.filter(email=email).exists():
                return Response(
                    {"error": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                # Check if the user already exists
                user = User.objects.filter(email=email).first()
                if not user:
                    temp_password = "".join(
                        random.choices(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits,
                            k=8,
                        )
                    )
                    user = User.objects.create_user(
                        username=email, password=temp_password, email=email
                    )
                    profile = Profile.objects.create(user=user)
                    print("createing new user and profile.")
                else:
                    print("hello.")
                    profile = Profile.objects.get(user=user)

                coach_role, created = Role.objects.get_or_create(name="coach")
                profile.roles.add(coach_role)
                profile.save()

                # Create the Coach User using the Profile
                coach_user = Coach.objects.create(
                    user=profile,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    phone_country_code=phone_country_code,
                    is_approved=is_approved,
                )

                # Approve coach
                coach = Coach.objects.get(id=coach_user.id)
                # Change the is_approved field to True
                coach.is_approved = False
                coach.save()
                coach_serializer = CoachSerializer(coach)

                path = f"/profile"
                message = f"Welcome to Meeraq. As next step, you need to fill out your details. Admin will look into your profile and contact you for profile approval. Thank You!"

                create_notification(coach.user.user, path, message)
                pmo_user = User.objects.filter(profile__roles__name="pmo").first()
                pmo = Pmo.objects.get(email=pmo_user.username)
                create_notification(
                    pmo_user,
                    f"/registeredcoach",
                    f"{coach.first_name} {coach.last_name} has registered as a coach. Please go through his Profile.",
                )
                send_mail_templates(
                    "pmo_emails/coach_register.html",
                    [pmo_user.username],
                    f"{coach.first_name} {coach.last_name} has Registered as a Coach",
                    {
                        "name": pmo.name,
                        "coachName": f"{coach.first_name} {coach.last_name} ",
                    },
                    json.loads(env("BCC_EMAIL_RAJAT_SUJATA")),
                )
                # Send profile completion tips to the coach
                send_mail_templates(
                    "coach_templates/profile_creation_tips.html",
                    [coach.email],
                    "Profile Completion Tips for Success on Meeraq Platform",
                    {
                        "name": f"{coach.first_name} {coach.last_name}",
                    },
                    [],
                )

            return Response({"coach": coach_serializer.data})

        except IntegrityError as e:
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            # Return error response if any other exception occurs
            print(e)
            return Response(
                {"error": "An error occurred while registering."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
def get_registered_coaches(request):
    try:
        # Filter coaches where isapproved is False
        unapproved_coaches = Coach.objects.filter(is_approved=False)

        # Serialize the unapproved coaches
        serializer = CoachSerializer(unapproved_coaches, many=True)

        # Return the serialized unapproved coaches as the response
        return Response(serializer.data, status=200)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


# @api_view(["GET"])
# def pmo_dashboard(request):
#     try:
#         organisations = Organisation.objects.all()
#         serialized_data = []

#         for organisation in organisations:
#             projects = Project.objects.filter(organisation=organisation)
#             organisation_data = OrganisationSerializer(organisation).data
#             organisation_data["projects"] = []

#             for project in projects:
#                 project_data = ProjectSerializer(project).data

#                 # Get all engagements in the project
#                 engagements = Engagement.objects.filter(project=project)
#                 engagement_data = EngagementSerializer(engagements, many=True).data

#                 project_data["engagements"] = engagement_data
#                 organisation_data["projects"].append(project_data)

#             serialized_data.append(organisation_data)

#         return Response(serialized_data, status=200)
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)


# @api_view(["GET"])
# def get_all_engagements(request):
#     engagements = Engagement.objects.all()
#     serializer = EngagementSerializer(engagements, many=True)
#     return Response(serializer.data)


# @api_view(["GET"])
# def get_all_completed_sessions(request):
#     completed_sessions = SessionRequestCaas.objects.filter(status="completed")
#     serializer = SessionRequestCaasSerializer(completed_sessions, many=True)
#     return Response(serializer.data)


# @api_view(["GET"])
# def get_all_engagements(request):
#     # Get all engagements
#     engagements = Engagement.objects.all()

#     # Create a list to store engagement data with session counts
#     engagement_data_list = []

#     for engagement in engagements:
#         # Get the engagement ID
#         engagement_id = engagement.id

#         # Count completed sessions for the learner in this engagement
#         completed_sessions_count = SessionRequestCaas.objects.filter(
#             status="completed",
#             billable_session_number__isnull=False,
#             learner__id=engagement.learner.id,
#             project__id=engagement.project.id,
#             is_archive=False,
#         ).count()

#         # Count total sessions for the learner in this engagement
#         total_sessions_count = SessionRequestCaas.objects.filter(
#             learner__id=engagement.learner.id,
#             billable_session_number__isnull=False,
#             project__id=engagement.project.id,
#             is_archive=False,
#         ).count()

#         # Create a dictionary with session counts for this engagement
#         engagement_data = {
#             "completed_sessions_count": completed_sessions_count,
#             "total_sessions_count": total_sessions_count,
#         }

#         # Add engagement data to the list
#         engagement_data_list.append(engagement_data)

#     # Serialize the engagements along with session counts
#     serialized_engagements = [
#         {"engagement": engagement, "session_counts": data}
#         for engagement, data in zip(engagements, engagement_data_list)
#     ]

#     # Serialize and return the data
#     serializer = EngagementSerializer(serialized_engagements, many=True)
#     return Response(serializer.data)


@api_view(["GET"])
def get_all_engagements(request):
    # Get all engagements
    engagements = Engagement.objects.all()

    # Create a list to store serialized engagement data with session counts
    engagement_data_list = []

    for engagement in engagements:
        # Get the engagement ID
        engagement_id = engagement.id

        completed_sessions_count = (
            SessionRequestCaas.objects.filter(
                status="completed",
                learner__id=engagement.learner.id,
                project__id=engagement.project.id,
                is_archive=False,
            )
            .exclude(Q(billable_session_number__isnull=True, session_type="chemistry"))
            .count()
        )

        # Count total sessions for the learner in this engagement
        total_sessions_count = SessionRequestCaas.objects.filter(
            learner__id=engagement.learner.id,
            billable_session_number__isnull=False,
            project__id=engagement.project.id,
            is_archive=False,
        ).count()

        completed_sessions = SessionRequestCaas.objects.filter(
            project__id=engagement.project.id,
            learner=engagement.learner,
            status="completed",
            is_archive=False,
        ).exclude(billable_session_number__isnull=True, session_type="chemistry")

        sessions_data = [
            {
                "start_time": datetime.utcfromtimestamp(
                    int(session.confirmed_availability.start_time) / 1000
                ),
                "end_time": datetime.utcfromtimestamp(
                    int(session.confirmed_availability.end_time) / 1000
                ),
            }
            for session in completed_sessions
        ]
        print(sessions_data)

        # Sort the availabilities_data based on start time in descending order
        sorted_availabilities = sorted(
            sessions_data,
            key=lambda availability: availability["start_time"],
            reverse=True,
        )

        # Extract the date of the most recent completed session
        last_session_date = (
            sorted_availabilities[0]["start_time"].date()
            if sorted_availabilities
            else None
        )

        # Serialize the engagement along with session counts
        serialized_engagement = EngagementSerializer(engagement).data
        serialized_engagement["completed_sessions_count"] = completed_sessions_count
        serialized_engagement["total_sessions_count"] = total_sessions_count
        serialized_engagement["last_completed_session_date"] = last_session_date

        # Add serialized engagement data to the list
        engagement_data_list.append(serialized_engagement)

    # Return the list of serialized engagement data with session counts
    # print("engagement_data_list--------------------------------",engagement_data_list)
    return Response(engagement_data_list)


@api_view(["PUT"])
def edit_project_caas(request, project_id):
    organisation = Organisation.objects.filter(
        id=request.data["organisation_id"]
    ).first()

    try:
        # Retrieve the existing project from the database
        project = get_object_or_404(Project, pk=project_id)
        # Update project attributes based on the data in the PUT request
        project.name = request.data.get("project_name", project.name)
        project.approx_coachee = request.data.get(
            "approx_coachee", project.approx_coachee
        )
        project.organisation = organisation
        project.frequency_of_session = request.data.get(
            "frequency_of_session", project.frequency_of_session
        )
        project.interview_allowed = request.data.get(
            "interview_allowed", project.interview_allowed
        )
        project.specific_coach = request.data.get(
            "specific_coach", project.specific_coach
        )
        project.empanelment = request.data.get("empanelment", project.empanelment)
        project.tentative_start_date = request.data.get(
            "tentative_start_date", project.tentative_start_date
        )
        project.mode = request.data.get("mode", project.mode)
        project.sold = request.data.get("sold", project.sold)
        project.location = json.loads(request.data.get("location", "[]"))
        project.project_description = request.data.get(
            "project_description", project.project_description
        )
        project.coach_consent_mandatory = request.data.get(
            "coach_consent_mandatory", project.coach_consent_mandatory
        )
        project.enable_emails_to_hr_and_coachee = request.data.get(
            "enable_emails_to_hr_and_coachee", project.enable_emails_to_hr_and_coachee
        )
        project.hr.clear()
        for hr in request.data["hr"]:
            single_hr = HR.objects.get(id=hr)
            project.hr.add(single_hr)

        # Save the updated project
        project.save()

        # You can return a success response with the updated project details
        return Response(
            {"message": "Project updated successfully", "project_id": project.id}
        )

    except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=404)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["PUT"])
def project_status(request, project_id):
    try:
        # Use get_object_or_404 to retrieve the project or return a 404 response if it doesn't exist
        project = get_object_or_404(Project, id=project_id)
        # Retrieve engagements related to the project
        engagements = Engagement.objects.filter(project=project)
        # Extract the desired status from the request data
        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Status cannot be empty."}, status=400)

        # Check if the new status is "completed" and if any engagement is not completed
        if new_status == "completed" and any(
            engagement.status != "completed" for engagement in engagements
        ):
            return Response(
                {
                    "error": "Cannot set project status to 'completed' if there are active engagements."
                },
                status=400,
            )

        # Update the project status
        project.status = new_status
        # Save the updated project status
        project.save()
        # Return a success response
        return Response(
            {"message": f"Project status updated successfully to {project.status}"},
            status=200,
        )

    except Exception as e:
        # Return a 500 response for other exceptions
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
def completed_projects(request, user_id):
    projects = Project.objects.filter(coaches_status__coach__id=user_id)
    completed_project = []
    for project in projects:
        if project.status == "completed":
            completed_project.append(project)

    print(completed_project)
    project_serializer = ProjectDepthTwoSerializer(completed_project, many=True)
    return Response({"completed_project": project_serializer.data})


class ActivitySummary(APIView):
    def get(self, request):
        try:
            user_login_activities = UserLoginActivity.objects.all()
            total_login_count = user_login_activities.count()
            user_login_serializer = UserLoginActivitySerializer(
                user_login_activities, many=True
            )
        except Exception as e:
            print("user_login_activities", str(e))
            user_login_serializer = []

        try:
            profile_edit_activities = ProfileEditActivity.objects.all()
            total_profile_edit_count = profile_edit_activities.count()
            profile_edit_serializer = ProfileEditActivitySerializer(
                profile_edit_activities, many=True
            )
        except Exception as e:
            print("profile_edit_activities", str(e))
            profile_edit_serializer = []

        try:
            goal_add_activities = AddGoalActivity.objects.all()
            total_goal_add_count = goal_add_activities.count()
            goal_add_serializer = AddGoalActivitySerializer(
                goal_add_activities, many=True
            )
        except Exception as e:
            print("goal_add_activities", str(e))
            goal_add_serializer = []

        try:
            coach_add_activities = AddCoachActivity.objects.all()
            total_coach_add_count = coach_add_activities.count()
            coach_add_serializer = AddCoachActivitySerializer(
                coach_add_activities, many=True
            )
        except Exception as e:
            print("coach_add_activities", str(e))
            coach_add_serializer = []

        try:
            sent_email_activities = SentEmailActivity.objects.all()
            total_sent_email_count = sent_email_activities.count()
            sent_email_serializer = SentEmailActivitySerializer(
                sent_email_activities, many=True
            )
        except Exception as e:
            print("sent_email_activities", str(e))
            sent_email_serializer = []

        try:
            session_requested_activities = SessionRequestedActivity.objects.all()
            total_session_requested_count = session_requested_activities.count()
            session_requested_serializer = SessionRequestedActivitySerializer(
                session_requested_activities, many=True
            )
        except Exception as e:
            print("session_requested_activities", str(e))
            session_requested_serializer = []

        try:
            delete_coach_profile_activities = DeleteCoachProfileActivity.objects.all()
            total_coach_profile_delete_count = delete_coach_profile_activities.count()
            delete_coach_profile_serializer = DeleteCoachProfileActivitySerializer(
                delete_coach_profile_activities, many=True
            )
        except Exception as e:
            print("delete_coach_activities", str(e))
            delete_coach_profile_serializer = []

        try:
            remove_coach_profile_activities = RemoveCoachActivity.objects.all()
            total_remove_coach_count = remove_coach_profile_activities.count()
            remove_coach_profile_serializer = RemoveCoachActivitySerializer(
                remove_coach_profile_activities, many=True
            )
        except Exception as e:
            print("remove_coach_profile_activities", str(e))
            remove_coach_profile_serializer = []

        try:
            add_past_session_activities = PastSessionActivity.objects.all()
            total_past_session_count = add_past_session_activities.count()
            past_session_activity_serializer = PastSessionActivitySerializer(
                add_past_session_activities, many=True
            )
        except Exception as e:
            print("add_past_session_activities", str(e))
            past_session_activity_serializer = []

        try:
            share_coach_profile_activities = ShareCoachProfileActivity.objects.all()
            total_share_coach_profile_count = share_coach_profile_activities.count()
            share_coach_profile_serializer = ShareCoachProfileActivitySerializer(
                share_coach_profile_activities, many=True
            )
        except Exception as e:
            print("share_coach_profile_activities", str(e))
            share_coach_profile_serializer = []

        try:
            create_project_activities = CreateProjectActivity.objects.all()
            total_create_project_count = create_project_activities.count()
            create_project_serializer = CreateProjectActivitySerializer(
                create_project_activities, many=True
            )
        except Exception as e:
            print("share_coach_profile_activities", str(e))
            create_project_serializer = []

        try:
            finalize_coach_activities = FinalizeCoachActivity.objects.all()
            total_finalized_coach_activity_count = finalize_coach_activities.count()
            finalize_coach_serializer = FinalizeCoachActivitySerializer(
                finalize_coach_activities, many=True
            )
        except Exception as e:
            print("share_coach_profile_activities", str(e))
            finalize_coach_serializer = []

        response_data = {
            "user_login": {
                "total_count": total_login_count,
                "activity": user_login_serializer.data,
            },
            "profile_edit": {
                "total_count": total_profile_edit_count,
                "activity": profile_edit_serializer.data,
            },
            "goal_add": {
                "total_count": total_goal_add_count,
                "activity": goal_add_serializer.data,
            },
            "coach_add": {
                "total_count": total_coach_add_count,
                "activity": coach_add_serializer.data,
            },
            "sent_email": {
                "total_count": total_sent_email_count,
                "activity": sent_email_serializer.data,
            },
            "session_requested": {
                "total_count": total_session_requested_count,
                "activity": session_requested_serializer.data,
            },
            "delete_coach_profile": {
                "total_count": total_coach_profile_delete_count,
                "activity": delete_coach_profile_serializer.data,
            },
            "remove_coach_profile": {
                "total_count": total_remove_coach_count,
                "activity": remove_coach_profile_serializer.data,
            },
            "add_past_session": {
                "total_count": total_past_session_count,
                "activity": past_session_activity_serializer.data,
            },
            "share_coach_profile": {
                "total_count": total_share_coach_profile_count,
                "activity": share_coach_profile_serializer.data,
            },
            "create_project": {
                "total_count": total_create_project_count,
                "activity": create_project_serializer.data,
            },
            "finalize_coach": {
                "total_count": total_finalized_coach_activity_count,
                "activity": finalize_coach_serializer.data,
            },
        }

        return Response(response_data)


@api_view(["POST"])
def send_reset_password_link(request):
    # Assuming you are sending a POST request with a list of emails in the body
    users = request.data["users"]
    for user_data in users:
        try:
            user = User.objects.get(email=user_data["email"])
            # Replace YourUserModel with your actual user model
            token = get_token_generator().generate_token()
            # Save the token to the database
            ResetPasswordToken.objects.create(user=user, key=token)
            # def send_mail_templates(file_name, user_email, email_subject, content, bcc_emails):
            reset_password_link = f"https://vendor.meeraq.com/reset-password/{token}"
            send_mail_templates(
                "greeting_email_to_vendor.html",
                [user_data["email"]],
                "Meeraq - Exciting News! New Vendor Platform Launch.",
                {"vendor_name": user_data["name"], "link": reset_password_link},
                [],
            )
        except Exception as e:
            print(f"Error sending link to {user_data['email']}: {str(e)}")
    return Response({"message": "Reset password links sent successfully"})


@api_view(["POST"])
def create_coach_profile_template(request):
    coach_id = request.data.get("coach")
    project_id = request.data.get("project")
    templates = request.data.get("templates")

    coaching_experience = templates.get("coaching_experience")
    corporate_experience = templates.get("corporate_experience")

    try:
        # Fetch the existing CoachProfileTemplate object based on coach and project IDs
        template = CoachProfileTemplate.objects.get(
            coach_id=coach_id, project_id=project_id
        )
    except CoachProfileTemplate.DoesNotExist:
        # If the object doesn't exist, create a new one
        template = CoachProfileTemplate(coach_id=coach_id, project_id=project_id)

    # Get the existing templates data
    existing_templates = template.templates

    if coaching_experience is not None:
        # Update the "coaching_experience" key with the new value
        existing_templates["coaching_experience"] = coaching_experience

    if corporate_experience is not None:
        # Update the "corporate_experience" key with the new value
        existing_templates["corporate_experience"] = corporate_experience

    # Update the "templates" field with the updated data
    template.templates = existing_templates
    template.save()

    return Response("Coach profile template updated successfully")


@api_view(["GET"])
def get_coach_profile_template(request, project_id):
    try:
        coach_profile_templates = CoachProfileTemplate.objects.filter(
            project__id=project_id
        )
        serializer = CoachProfileTemplateSerializer(coach_profile_templates, many=True)
        return Response(serializer.data)
    except CoachProfileTemplate.DoesNotExist:
        return Response(status=404)


class StandardizedFieldAPI(APIView):
    def get(self, request):
        standardized_fields = StandardizedField.objects.all()

        standardized_fields_serializer = StandardizedFieldSerializer(
            standardized_fields, many=True
        )

        field_data = {
            field_data["field"]: field_data["values"]
            for field_data in standardized_fields_serializer.data
        }

        return Response(field_data)


class StandardizedFieldRequestAPI(APIView):
    def get(self, request):
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        today_requests = StandardizedFieldRequest.objects.filter(
            requested_at__gte=today_start, status="pending"
        ).order_by("-requested_at")

        other_requests = StandardizedFieldRequest.objects.filter(
            Q(status="pending") & Q(requested_at__lt=today_start)
        ).order_by("-requested_at")

        today_requests_serializer = StandardizedFieldRequestDepthOneSerializer(
            today_requests, many=True
        )
        other_requests_serializer = StandardizedFieldRequestDepthOneSerializer(
            other_requests, many=True
        )

        return Response(
            {
                "today_requests": today_requests_serializer.data,
                "other_requests": other_requests_serializer.data,
            }
        )


class StandardFieldAddValue(APIView):
    def post(self, request):
        field_name = request.data.get("field_name")
        option_value = request.data.get("optionValue")

        standardized_field, created = StandardizedField.objects.get_or_create(
            field=field_name
        )

        if option_value not in standardized_field.values:
            standardized_field.values.append(option_value)
            standardized_field.save()
        else:
            return Response({"error": "Value already present."}, status=404)

        return Response(
            {"message": f"Value Added to {FIELD_NAME_VALUES[field_name]} field."},
            status=200,
        )


class StandardFieldEditValue(APIView):
    def put(self, request):
        field_name = request.data.get("field_name")
        previous_value = request.data.get("previous_value")
        new_value = request.data.get("new_value")

        try:
            standardized_field = StandardizedField.objects.get(field=field_name)

            if previous_value in standardized_field.values:
                index = standardized_field.values.index(previous_value)
                standardized_field.values[index] = new_value

                standardized_field.save()

                return Response(
                    {
                        "message": f"Value Updated in {FIELD_NAME_VALUES[field_name]} field."
                    },
                    status=200,
                )
            else:
                return Response(
                    {
                        "message": f"{previous_value} not found in {FIELD_NAME_VALUES[field_name]} field."
                    },
                    status=404,
                )
        except StandardizedField.DoesNotExist:
            return Response(
                {"error": f"{FIELD_NAME_VALUES[field_name]} not found."}, status=404
            )


class StandardizedFieldRequestAcceptReject(APIView):
    def put(self, request):
        status = request.data.get("status")
        request_id = request.data.get("request_id")

        try:
            request_instance = StandardizedFieldRequest.objects.get(id=request_id)

            if status == "accepted":
                request_instance.status = status
                request_instance.save()

                field_name = request_instance.standardized_field_name.field
                value = request_instance.value

                standardized_field, created = StandardizedField.objects.get_or_create(
                    field=field_name
                )

                if value not in standardized_field.values:
                    standardized_field.values.append(value)
                    standardized_field.save()
                else:
                    return Response({"error": "Value already present."}, status=404)
                return Response({"message": f"Request {status}"}, status=200)
            else:
                request_instance.status = status
                request_instance.save()

                return Response({"message": f"Request {status}"}, status=200)
        except StandardizedFieldRequest.DoesNotExist:
            return Response({"error": f"Request not found."}, status=404)


class StandardFieldDeleteValue(APIView):
    def delete(self, request):
        field_name = request.data.get("field_name")
        option_value = request.data.get("optionValue")

        standardized_field = StandardizedField.objects.get(field=field_name)

        if option_value in standardized_field.values:
            standardized_field.values.remove(option_value)
            standardized_field.save()
        else:
            return Response({"error": "Value not present."}, status=404)

        return Response(
            {"message": f"Value deleted from {FIELD_NAME_VALUES[field_name]} field."},
            status=200,
        )


@api_view(["GET", "POST"])
def template_list_create_view(request):
    if request.method == "GET":
        templates = Template.objects.all()
        serializer = TemplateSerializer(templates, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = TemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def template_retrieve_update_destroy_view(request, pk):
    try:
        template = Template.objects.get(pk=pk)
    except Template.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = TemplateSerializer(template)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = TemplateSerializer(template, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def create_project_contract(request):
    serializer = ProjectContractSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Contract Assigned Successfully."})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectContractAPIView(APIView):
    def get(self, request, format=None):
        contracts = ProjectContract.objects.all()
        serializer = ProjectContractSerializer(contracts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectContractDetailView(APIView):
    def get(self, request, project_id, format=None):
        print(project_id)
        try:
            project_contract = ProjectContract.objects.get(project=project_id)
        except ProjectContract.DoesNotExist:
            return Response(
                {"error": "Project contract not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProjectContractSerializer(project_contract)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoachContractList(APIView):
    def get(self, request, format=None):
        contracts = CoachContract.objects.all()
        serializer = CoachContractSerializer(contracts, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CoachContractSerializer(data=request.data)
        if serializer.is_valid():
            coach = serializer.validated_data["coach"]
            project = serializer.validated_data["project"]

            if CoachContract.objects.filter(coach=coach, project=project).exists():
                return Response(
                    {
                        "message": f"Coach {coach.username} already has a contract for {project.name}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()
            return Response(
                {"message": "Contract created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "Invalid data", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CoachContractDetail(APIView):
    def get_object(self, pk):
        try:
            return CoachContract.objects.get(pk=pk)
        except CoachContract.DoesNotExist:
            return None

    def get(self, request, pk, format=None):
        contract = self.get_object(pk)
        if contract is not None:
            serializer = CoachContractSerializer(contract)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, format=None):
        contract = self.get_object(pk)
        if contract is not None:
            serializer = CoachContractSerializer(contract, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Contract updated successfully",
                        "data": serializer.data,
                    }
                )
            return Response(
                {"message": "Invalid data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND
        )

    def delete(self, request, pk, format=None):
        contract = self.get_object(pk)
        if contract is not None:
            contract.delete()
            return Response(
                {"message": "Contract deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND
        )


class UpdateCoachContract(APIView):
    def put(self, request, format=None):
        coach_id = request.data.get("coach")
        project_id = request.data.get("project")
        try:
            contract = CoachContract.objects.get(coach=coach_id, project=project_id)
        except CoachContract.DoesNotExist:
            return Response(
                {"error": "Coach Contract not found."}, status=status.HTTP_404_NOT_FOUND
            )

        coach_name = (
            f"{contract.coach.first_name.strip()} {contract.coach.last_name.strip()}"
        )
        provided_name_inputed = request.data.get("name_inputed").strip()

        if provided_name_inputed.lower() != coach_name.lower():
            return Response(
                {"error": "Provided name input does not match coach's name."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CoachContractSerializer(contract, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Contract Accepted Successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignCoachContractAndProjectContract(APIView):
    def post(self, request, format=None):
        project_id = request.data.get("project")
        existing_contract = ProjectContract.objects.filter(project=project_id).first()

        if not existing_contract:
            serializer = ProjectContractSerializer(data=request.data)
            if serializer.is_valid():
                contract = serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            contract = existing_contract

        current_date = timezone.now().date()

        project_id = request.data.get("project")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"message": "Project not found."}, status=status.HTTP_404_NOT_FOUND
            )

        coaches = project.coaches_status.all()

        for coach_status in coaches:
            hr_status = coach_status.status.get("hr", {}).get("status")

            if hr_status == "select":
                coach = coach_status.coach

                existing_coach_contract = CoachContract.objects.filter(
                    project=project_id, coach=coach.id
                ).exists()

                if not existing_coach_contract:
                    contract_data = {}
                    if not project.coach_consent_mandatory:
                        contract_data = {
                            "project_contract": contract.id,
                            "project": project_id,
                            "status": "approved",
                            "coach": coach.id,
                            "name_inputed": coach.first_name + " " + coach.last_name,
                            "response_date": timezone.now().date(),
                        }
                    else:
                        contract_data = {
                            "project_contract": contract.id,
                            "project": project_id,
                            "status": "pending",
                            "coach": coach.id,
                        }
                    contract_serializer = CoachContractSerializer(data=contract_data)

                    if contract_serializer.is_valid():
                        contract_serializer.save()
                    else:
                        return Response(
                            contract_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST,
                        )

        return Response(
            {
                "message": "Project Contract Saved and Coach contracts assigned successfully."
            },
            status=status.HTTP_201_CREATED,
        )


class ApprovedCoachContract(APIView):
    def get(self, request, project_id, coach_id, format=None):
        try:
            coach_contract = CoachContract.objects.get(
                project=project_id, coach=coach_id, status="approved"
            )
        except CoachContract.DoesNotExist:
            return Response(
                {"error": "Coach contract not found1."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CoachContractSerializer(coach_contract)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoachWithApprovedContractsInProject(APIView):
    def get(self, request, project_id, format=None):
        try:
            coach_contracts = CoachContract.objects.filter(
                project=project_id, status="approved"
            )

            coach_ids = [contract.coach.id for contract in coach_contracts]

            coaches = Coach.objects.filter(id__in=coach_ids)

            serializer = CoachSerializer(coaches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CoachContract.DoesNotExist:
            return Response(
                {"error": "Coach contracts not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class SendContractReminder(APIView):
    def post(self, request, format=None):
        try:
            coachs_data = request.data["pending_coaches"]

            timestamp = request.data["timestamp"]

            project_id = request.data["project_id"]

            if not coachs_data:
                raise ValueError("No pending coaches available")

            for coach_data in coachs_data:
                coach = Coach.objects.get(id=coach_data["id"])

                send_mail_templates(
                    "coach_templates/contract_reminder.html",
                    [coach.email],
                    "Meeraq Coaching | Coach Contract Reminder",
                    {"name": coach.first_name},
                    [],  # no bcc emails
                )

            notification_message = "This is a reminder to accept the Coach contract."
            create_notification(coach.user.user, "/projects", notification_message)

            project_contract = ProjectContract.objects.get(project=project_id)
            project_contract.reminder_timestamp = timestamp
            project_contract.save()

            return Response(
                {"message": "Emails and notifications sent successfully"},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["POST"])
def change_user_role(request, user_id):
    user_role = request.data.get("user_role", "")
    user = User.objects.get(id=user_id)
    if not user.profile:
        print("hello")
        return Response({"error": "No user profile."}, status=400)
    elif user.profile.roles.count() == 0:
        print("second")
        return Response({"error": "No user role."}, status=400)
    try:
        user_profile_role = user.profile.roles.all().get(name=user_role).name
    except Exception as e:
        print(e)
        return Response({"error": "User role not found."}, status=400)
    roles = []
    for role in user.profile.roles.all():
        roles.append(role.name)
    if user_profile_role == "coach":
        serializer = CoachDepthOneSerializer(user.profile.coach)
        is_caas_allowed = Project.objects.filter(
            coaches_status__coach=user.profile.coach
        ).exists()
        is_seeq_allowed = SchedularBatch.objects.filter(
            coaches=user.profile.coach
        ).exists()
        return Response(
            {
                **serializer.data,
                "is_caas_allowed": is_caas_allowed,
                "is_seeq_allowed": is_seeq_allowed,
                "roles": roles,
                "user": {**serializer.data["user"], "type": user_profile_role},
                "last_login": user.last_login,
                "message": "Role changed to Coach",
            }
        )
    elif user_profile_role == "pmo":
        serializer = PmoDepthOneSerializer(user.profile.pmo)
    elif user_profile_role == "learner":
        serializer = LearnerDepthOneSerializer(user.profile.learner)
    elif user_profile_role == "hr":
        serializer = HrDepthOneSerializer(user.profile.hr)
    else:
        return Response({"error": "Unknown user role."}, status=400)
    return Response(
        {
            **serializer.data,
            "roles": roles,
            "user": {**serializer.data["user"], "type": user_profile_role},
            "last_login": user.last_login,
            "message": f"Role changed to {user_profile_role}",
        }
    )


@api_view(["GET"])
def get_users(request):
    user_profiles = Profile.objects.all()
    res = []
    for profile in user_profiles:
        existing_roles = [item.name for item in profile.roles.all()]
        email = profile.user.email
        res.append({"id": profile.id, "email": email, "roles": existing_roles})
    return Response(res)


def get_weeks_for_current_month():
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_date = datetime.now()
    first_day_of_current_month = current_date.replace(day=1)
    cal = calendar.monthcalendar(current_year, current_month)
    weeks = []

    for week in cal:
        days_in_week = [day for day in week if day != 0]
        if days_in_week:
            start_day = min(days_in_week)
            end_day = max(days_in_week)

            # Check if Saturday is the last day of the week
            if (
                calendar.weekday(current_year, current_month, end_day)
                == calendar.SATURDAY
            ):
                end_day += 1

            start_date = datetime(current_year, current_month, start_day)
            end_date = datetime(current_year, current_month, end_day)

            weeks.append(
                {
                    "start_day": start_day,
                    "end_day": end_day,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

    return weeks


class SessionData(APIView):
    def get(self, request, format=None):
        now = date.today()
        current_datetime = datetime.now()
        first_day_of_current_month = datetime(
            current_datetime.year, current_datetime.month, 1
        )
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = datetime(
            last_day_of_previous_month.year, last_day_of_previous_month.month, 1
        )
        start_timestamp_prev_month = int(first_day_of_previous_month.timestamp() * 1000)
        end_timestamp_prev_month = int(
            last_day_of_previous_month.timestamp() * 1000 + 86400000
        )
        if now.month == 12:
            last_day_of_current_month = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day_of_current_month = datetime(
                now.year, now.month + 1, 1
            ) - timedelta(days=1)

        start_timestamp_current_month = int(
            first_day_of_current_month.timestamp() * 1000
        )
        end_timestamp_current_month = int(last_day_of_current_month.timestamp() * 1000)

        start_str_prev_mon = str(start_timestamp_prev_month)
        end_str_prev_mon = str(end_timestamp_prev_month)

        start_str_current_mon = str(start_timestamp_current_month)
        end_str_current_mon = str(end_timestamp_current_month)

        projects = Project.objects.all()
        sessiondata = []
        weeks = get_weeks_for_current_month()
        for project in projects:
            res_obj = {}
            is_involved_in_sessions = SessionRequestCaas.objects.filter(
                project=project, is_booked=True
            ).exists()
            if is_involved_in_sessions:
                res_obj["project_name"] = project.name
            else:
                continue
            previous_month_sessions = SessionRequestCaas.objects.filter(
                confirmed_availability__start_time__gte=start_str_prev_mon,
                confirmed_availability__end_time__lte=end_str_prev_mon,
                project__id=project.id,
            )
            res_obj["last_month"] = previous_month_sessions.count()

            current_month_sessions = SessionRequestCaas.objects.filter(
                confirmed_availability__start_time__gte=start_str_current_mon,
                confirmed_availability__end_time__lte=end_str_current_mon,
                project__id=project.id,
            )
            res_obj["current_month"] = current_month_sessions.count()

            for i, week in enumerate(weeks, start=1):
                start_timestamp = int(week["start_date"].timestamp())
                end_timestamp = int(week["end_date"].timestamp())
                start_day_of_ith_week_of_curr_month = str(start_timestamp)
                last_day_of_ith_week_of_curr_month = str(end_timestamp)
                weekly_sessions = SessionRequestCaas.objects.filter(
                    confirmed_availability__start_time__gte=start_day_of_ith_week_of_curr_month,
                    confirmed_availability__end_time__lte=last_day_of_ith_week_of_curr_month,
                    project__id=project.id,
                )
                key = f"current_month_week_{i}"
                res_obj[key] = weekly_sessions.count()
            actual_sessions_in_current_month = SessionRequestCaas.objects.filter(
                confirmed_availability__start_time__gte=start_str_current_mon,
                confirmed_availability__end_time__lte=end_str_current_mon,
                project__id=project.id,
                status="completed",
            )
            res_obj["total_actuals"] = actual_sessions_in_current_month.count()
            balance = (
                current_month_sessions.count()
                - actual_sessions_in_current_month.count()
            )
            res_obj["balance"] = balance
            sessiondata.append(res_obj)

        return Response(
            {"sessiondata": sessiondata, "weeks": weeks},
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
def google_oauth(request, user_email):
    oauth2_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"

    auth_params = {
        "client_id": env("GOOGLE_OAUTH2_CLIENT_ID"),
        "redirect_uri": env("GOOGLE_OAUTH2_REDIRECT_URI"),
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email",
        "access_type": "offline",
        "login_hint": user_email,
    }

    auth_url = f"{oauth2_endpoint}?{urlencode(auth_params)}"

    return HttpResponseRedirect(auth_url)


@api_view(["GET"])
def google_auth_callback(request):
    code = request.GET.get("code")

    if code:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": env("GOOGLE_OAUTH2_CLIENT_ID"),
            "client_secret": env("GOOGLE_OAUTH2_CLIENT_SECRET"),
            "redirect_uri": env("GOOGLE_OAUTH2_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }

        response = requests.post(token_url, data=token_data)
        token_json = response.json()

        if "access_token" in token_json and "refresh_token" in token_json:
            access_token = token_json["access_token"]
            refresh_token = token_json["refresh_token"]
            expires_in = token_json["expires_in"]
            auth_code = code
            user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            user_info_response = requests.get(user_info_url, headers=headers)

            if user_info_response.status_code == 200:
                user_info_data = user_info_response.json()

                user_email = user_info_data.get("email", "")

                user = User.objects.get(username=user_email)
                user_profile = Profile.objects.get(user=user)

                user_token, created = UserToken.objects.get_or_create(
                    user_profile=user_profile
                )
                user_token.access_token = access_token
                user_token.refresh_token = refresh_token
                user_token.access_token_expiry = expires_in
                user_token.authorization_code = auth_code
                user_token.account_type = "google"
                user_token.save()

            return HttpResponseRedirect(env("APP_URL"))
        else:
            return JsonResponse({"error": "Token exchange failed."}, status=400)
    else:
        return JsonResponse(
            {"error": "Authentication failed. Code not found."}, status=400
        )


@api_view(["GET"])
def microsoft_auth(request, user_mail_address):
    oauth2_endpoint = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"

    auth_params = {
        "client_id": env("MICROSOFT_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": env("MICROSOFT_REDIRECT_URI"),
        "response_mode": "query",
        "scope": "openid offline_access User.Read Calendars.ReadWrite profile email",
        "state": "shashankmeeraq",
        "login_hint": user_mail_address,
    }

    auth_url = f"{oauth2_endpoint}?{urlencode(auth_params)}"

    return HttpResponseRedirect(auth_url)


@api_view(["POST", "GET"])
def microsoft_callback(request):
    try:
        authorization_code = request.GET.get("code")

        token_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            "client_id": env("MICROSOFT_CLIENT_ID"),
            "scope": "User.Read",
            "code": authorization_code,
            "redirect_uri": env("MICROSOFT_REDIRECT_URI"),
            "grant_type": "authorization_code",
            "client_secret": env("MICROSOFT_CLIENT_SECRET"),
        }

        response = requests.post(token_url, data=token_data)

        token_json = response.json()

        if "access_token" in token_json and "refresh_token" in token_json:
            access_token = token_json["access_token"]
            refresh_token = token_json["refresh_token"]
            expires_in = token_json["expires_in"]
            auth_code = authorization_code
            user_email_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}

            user_email_response = requests.get(user_email_url, headers=headers)

            if user_email_response.status_code == 200:
                user_info_data = user_email_response.json()
                user_email = user_info_data.get("mail", "")
                user = User.objects.get(username=user_email)
                user_profile = Profile.objects.get(user=user)
                user_token, created = UserToken.objects.get_or_create(
                    user_profile=user_profile
                )
                user_token.access_token = access_token
                user_token.refresh_token = refresh_token
                user_token.access_token_expiry = expires_in
                user_token.authorization_code = auth_code
                user_token.account_type = "microsoft"
                user_token.save()
            return HttpResponseRedirect(env("APP_URL"))
        else:
            error_json = response.json()
            return JsonResponse(error_json, status=response.status_code)

    except Exception as e:
        # Handle exceptions here, you can log the exception for debugging
        print(f"An exception occurred: {str(e)}")
        # You might want to return an error response or redirect to an error page.
        return JsonResponse({"error": "An error occurred"}, status=500)


class UserTokenAvaliableCheck(APIView):
    def get(self, request, user_mail, format=None):
        user_token_present = False
        try:
            user_token = UserToken.objects.get(user_profile__user__username=user_mail)
            if user_token:
                user_token_present = True
        except Exception as e:
            pass
        return Response({"user_token_present": user_token_present})


class DownloadCoachContract(APIView):
    def get(self, request, coach_contract_id, format=None):
        try:
            coach_contract = CoachContract.objects.get(id=coach_contract_id)
            coach_contract.project_contract.project.project_structure
            data = coach_contract.project_contract.project.project_structure
            for item in data:
                if (
                    "session_type" in item
                    and item["session_type"] in SESSION_TYPE_VALUE
                ):
                    item["session_type"] = SESSION_TYPE_VALUE[item["session_type"]]

            total_sessions = sum(session["no_of_sessions"] for session in data)
            total_duration = sum(int(session["session_duration"]) for session in data)
            total_coach_fees = sum(int(session["coach_price"]) for session in data)

            html_content = render_to_string(
                "contract/contract_template.html",
                {
                    "name": coach_contract.coach.first_name
                    + " "
                    + coach_contract.coach.last_name,
                    "data": data,
                    "content": coach_contract.project_contract.content,
                    "name_inputed": coach_contract.name_inputed.capitalize(),
                    "signed_date": coach_contract.response_date.strftime("%d-%m-%Y"),
                    "total_sessions": total_sessions,
                    "total_duration": total_duration,
                    "total_coach_fees": total_coach_fees,
                },
            )
            pdf = pdfkit.from_string(
                html_content,
                False,
                configuration=pdfkit_config,
            )
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename={f"Contract.pdf"}'
            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to downlaod Contract."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
