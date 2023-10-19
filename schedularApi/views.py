from datetime import date
import requests
from os import name
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
import jwt
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status

from django.shortcuts import render
from api.models import Organisation, HR
from .serializers import (
    SchedularProjectSerializer,
    SchedularBatchSerializer,
    SchedularParticipantsSerializer,
    SessionItemSerializer,
)
from .models import (
    SchedularBatch,
    LiveSession,
    CoachingSession,
    SchedularProject,
    SchedularParticipants,
)


from api.views import create_notification


# Create your views here.

import environ

env = environ.Env()


@api_view(["POST"])
def create_project_schedular(request):
    organisation = Organisation.objects.filter(
        id=request.data["organisation_name"]
    ).first()
    if not organisation:
        organisation = Organisation(
            name=request.data["organisation_name"], image_url=request.data["image_url"]
        )
    organisation.save()
    try:
        schedularProject = SchedularProject(
            name=request.data["project_name"],
            organisation=organisation,
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
        path = f"/projects/caas/progress/{schedularProject.id}"
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
def get_all_Schedular_Projects(request):
    projects = SchedularProject.objects.all()
    serializer = SchedularProjectSerializer(projects, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def create_schedular_participant(request):
    if request.method == "POST":
        serializer = SchedularParticipantsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
def create_project_structure(request, project_id):
    try:
        project = get_object_or_404(SchedularProject, id=project_id)
        serializer = SessionItemSerializer(data=request.data, many=True)
        if serializer.is_valid():
            project.project_structure = serializer.data
            project.save()
            return Response(
                {"message": "Project structure added successfully."}, status=200
            )
        return Response({"error": "Invalid sessions found."}, status=400)
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )


@api_view(["GET"])
def get_schedular_batches(request):
    try:
        batches = SchedularBatch.objects.all()
        serializer = SchedularBatchSerializer(batches, many=True)
        return Response(serializer.data)
    except SchedularBatch.DoesNotExist:
        return Response({"message": "No batches found"}, status=404)


@api_view(["GET"])
def get_schedular_project(request, project_id):
    try:
        project = get_object_or_404(SchedularProject, id=project_id)
        serializer = SchedularProjectSerializer(project)
        return Response(serializer.data)
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )


@api_view(["GET"])
def get_batch_calendar(request, batch_id):
    try:
        live_sessions = LiveSession.objects.filter(batch__id=batch_id)
        coaching_sessions = CoachingSession.objects.filter(batch__id=batch_id)
        live_sessions_serializer = LiveSessionSerializer(live_sessions, many=True)
        coaching_sessions_serializer = CoachingSessionSerializer(
            coaching_sessions, many=True
        )
        return Response(
            {
                "live_sessions": live_sessions_serializer.data,
                "coaching_sessions": coaching_sessions_serializer.data,
            }
        )
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )
