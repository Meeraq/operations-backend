from datetime import date
import uuid
import requests
import uuid
from os import name
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from operationsBackend import settings
import jwt
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_celery_beat.models import PeriodicTask, ClockedSchedule


from django.shortcuts import render
from api.models import Organisation, HR,Coach
from .serializers import (
    SchedularProjectSerializer,
    SchedularBatchSerializer,
    SchedularParticipantsSerializer,
    SessionItemSerializer,
    LearnerDataUploadSerializer,
    EmailTemplateSerializer,
    SentEmailDepthOneSerializer,
    BatchSerializer,
    LiveSessionSerializer,
    CoachingSessionSerializer,
    GetSchedularParticipantsSerializer,
    CoachSchedularAvailibiltySerializer,
    CoachSchedularAvailibiltySerializer2,
    CoachBasicDetailsSerializer
)
from .models import (
    SchedularBatch,
    LiveSession,
    CoachingSession,
    SchedularProject,
    SchedularParticipants,
    SentEmail,
    EmailTemplate,
    CoachSchedularAvailibilty,
    RequestAvailibilty
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
    existing_projects_with_same_name = SchedularProject.objects.filter(name=request.data["project_name"])
    if existing_projects_with_same_name.exists():
        return Response({"error": "Project with same name already exists."},status=400)
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
        participants = SchedularParticipants.objects.filter(schedularbatch__id=batch_id)
        participants_serializer = GetSchedularParticipantsSerializer(
            participants, many=True
        )
        coaches = Coach.objects.filter(schedularbatch__id=batch_id)
        coaches_serializer = CoachBasicDetailsSerializer(coaches, many=True)
        sessions = [*live_sessions_serializer.data, *coaching_sessions_serializer.data]
        sorted_sessions = sorted(sessions, key=lambda x: x["order"])
        return Response(
            {"sessions": sorted_sessions, "participants": participants_serializer.data, "coaches" : coaches_serializer.data}
        )
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )


@api_view(["PUT"])
def update_live_session(request, live_session_id):
    try:
        live_session = LiveSession.objects.get(id=live_session_id)
    except LiveSession.DoesNotExist:
        return Response(
            {"error": "LiveSession not found"}, status=status.HTTP_404_NOT_FOUND
        )

    serializer = LiveSessionSerializer(live_session, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
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


@api_view(["GET"])
def participants_list(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
    except SchedularBatch.DoesNotExist:
        return Response({"detail": "Batch not found"}, status=404)

    participants = batch.participants.all()
    serializer = SchedularParticipantsSerializer(participants, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def getSavedTemplates(request):
    emailTemplate = EmailTemplate.objects.all()
    serilizer = EmailTemplateSerializer(emailTemplate, many=True)
    return Response({"status": "success", "data": serilizer.data}, status=200)


@api_view(["GET"])
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
                task="base.tasks.send_email_to_recipients",
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
def get_all_schedular_availabilities(request):
    availabilities = RequestAvailibilty.objects.all()
    serializer = CoachSchedularAvailibiltySerializer2(availabilities, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def create_coach_schedular_availibilty(request):
    if request.method == "POST":
        serializer = CoachSchedularAvailibiltySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def add_batch(request,project_id):
    participants_data = request.data.get('participants', [])
    project = SchedularProject.objects.get(id=project_id)

    for participant_data in participants_data:
        name = participant_data.get('name')
        email = participant_data.get('email').strip()
        phone = participant_data.get('phone')
        batch_name = participant_data.get('batch').strip().upper()
         # Assuming 'project_id' is in your request data
        
        # Check if batch with the same name exists
        batch = SchedularBatch.objects.filter(name=batch_name, project=project).first()

        if not batch:
            # If batch does not exist, create a new batch
            batch = SchedularBatch.objects.create(name=batch_name, project=project)

            # Create Live Sessions and Coaching Sessions based on project structure
            for session_data in project.project_structure:
                order = session_data.get('order')
                duration = session_data.get('duration')
                session_type = session_data.get('session_type')

                if session_type == 'live_session':
                    live_session_number = LiveSession.objects.filter(batch=batch).count() + 1
                    live_session = LiveSession.objects.create(
                        batch=batch,
                        live_session_number=live_session_number,
                        order=order,
                        duration=duration,
                    )
                elif session_type == 'laser_coaching_session':
                    coaching_session_number = CoachingSession.objects.filter(batch=batch).count() + 1
                    booking_link =  f"{env('SCHEUDLAR_APP_URL')}/coaching/book/{str(uuid.uuid4())}"    # Generate a unique UUID for the booking link
                    coaching_session = CoachingSession.objects.create(
                        batch=batch,
                        coaching_session_number=coaching_session_number,
                        order=order,
                        duration=duration,
                        booking_link=booking_link,
                    )

        # Check if participant with the same email exists
        participant, participant_created = SchedularParticipants.objects.get_or_create(
            email=email,
            defaults={'name': name, 'phone': phone}
        )

        # Add participant to the batch if not already added
        if participant not in batch.participants.all():
            batch.participants.add(participant)

    return Response({'message': 'Batch created successfully.'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_coaches(request):
    coaches = Coach.objects.filter(is_approved=True)
    serializer = CoachBasicDetailsSerializer(coaches,many=True)
    return Response(serializer.data)


@api_view(["PUT"])
def update_batch(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
    except SchedularBatch.DoesNotExist:
        return Response(
            {"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND
        )
    serializer = SchedularBatchSerializer(
        batch, data=request.data, partial=True
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
