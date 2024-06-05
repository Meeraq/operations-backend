from datetime import date, datetime, timedelta
from collections import defaultdict
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
    Count,
    Q,
    BooleanField,
    CharField,
    Count,
    ExpressionWrapper,
    FloatField,
    Sum,
)
from time import sleep
import json
from django.core.exceptions import ObjectDoesNotExist
from api.views import (
    get_date,
    get_time,
    add_contact_in_wati,
    add_so_to_project,
    create_task,
)
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
    CoachStatus,
    Project,
    SessionRequestCaas,
    Sales,
)
from decimal import Decimal

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
    SchedularProjectSerializerArchiveCheck,
    HandoverDetailsSerializer,
    TaskSerializer,
    BenchmarkSerializer,
    GmSheetSerializer,
    OfferingSerializer,
    HandoverDetailsSerializerWithOrganisationName,
    AssetsSerializer,
    GmSheetDetailedSerializer,
    AssetsDetailedSerializer,
    EmployeeSerializer,
    GmSheetSalesOrderExistsSerializer,
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
    CoachContract,
    ProjectContract,
    CoachPricing,
    FacilitatorPricing,
    Expense,
    HandoverDetails,
    Task,
    Offering,
    GmSheet,
    Benchmark,
    Assets,
    Employee,
)
from api.serializers import (
    FacilitatorSerializer,
    FacilitatorSerializerIsVendor,
    FacilitatorBasicDetailsSerializer,
    CoachSerializer,
    FacilitatorDepthOneSerializer,
    ProjectSerializer,
    FacilitatorSerializerWithNps,
    CoachContractSerializer,
)

from courses.models import (
    FeedbackLessonResponse,
    QuizLessonResponse,
    FeedbackLesson,
    QuizLesson,
    LaserCoachingSession,
    LiveSessionLesson,
    Lesson,
    Certificate,
    Answer,
    Assessment as AssessmentLesson,
)
from courses.models import Course, CourseEnrollment
from courses.serializers import (
    CourseSerializer,
    LessonSerializer,
    CourseEnrollmentDepthOneSerializer,
)
from django.core.serializers import serialize

from courses.views import (
    add_question_to_feedback_lesson,
    nps_default_feed_questions,
    create_lessons_for_batch,
)
from assessmentApi.models import (
    Assessment,
    ParticipantUniqueId,
    ParticipantObserverMapping,
    ParticipantResponse,
    Competency,
    Behavior,
    ActionItem,
    BatchCompetencyAssignment,
)
from io import BytesIO
from api.serializers import LearnerSerializer
from api.views import (
    create_notification,
    send_mail_templates,
    create_outlook_calendar_invite,
    delete_outlook_calendar_invite,
    create_teams_meeting,
    delete_teams_meeting,
    create_learner,
)
from django.db.models import Max
import io
from time import sleep
from assessmentApi.views import (
    delete_participant_from_assessments,
    add_multiple_participants_for_project,
)
from assessmentApi.serializers import (
    CompetencySerializerDepthOne,
    ActionItemSerializer,
    ActionItemDetailedSerializer,
    CompetencySerializer,
    BehaviorSerializer,
    AssessmentSerializer,
)
from schedularApi.tasks import (
    celery_send_unbooked_coaching_session_mail,
    celery_send_unbooked_coaching_session_whatsapp_message,
    get_current_date_timestamps,
    get_coaching_session_according_to_time,
    get_live_session_according_to_time,
    send_emails_in_bulk,
    add_batch_to_project,
    create_or_get_learner,
)
from django.db.models import BooleanField, F, Exists, OuterRef

# Create your views here.
from itertools import chain
import environ
import re
from rest_framework.views import APIView
from api.views import get_user_data
from zohoapi.models import (
    Vendor,
    InvoiceData,
    OrdersAndProjectMapping,
    SalesOrder,
    PurchaseOrder,
)
from zohoapi.views import (
    fetch_purchase_orders,
    organization_id,
    fetch_sales_persons,
    filter_purchase_order_data,
)
from zohoapi.tasks import organization_id, fetch_sales_orders, purchase_orders_allowed
from zohoapi.serializers import (
    SalesOrderSerializer,
    PurchaseOrderSerializer,
    SalesOrderGetSerializer,
    PurchaseOrderGetSerializer,
)
from courses.views import calculate_nps
from api.permissions import IsInRoles

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
    elif session_type == "pre_study":
        session_name = "Pre Study"
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
@transaction.atomic
def create_project_schedular(request):
    project_details = request.data
    organisation = Organisation.objects.filter(
        id=project_details["organisation_name"]
    ).first()
    junior_pmo = None
    if "junior_pmo" in project_details:
        junior_pmo = Pmo.objects.filter(id=project_details["junior_pmo"]).first()
    if not organisation:
        organisation = Organisation(
            name=project_details["organisation_name"],
            image_url=project_details["image_url"],
        )
    organisation.save()
    existing_projects_with_same_name = SchedularProject.objects.filter(
        name=project_details["project_name"]
    )
    if existing_projects_with_same_name.exists():
        return Response({"error": "Project with same name already exists."}, status=400)
    try:
        schedularProject = SchedularProject(
            name=project_details["project_name"],
            organisation=organisation,
            email_reminder=project_details["email_reminder"],
            whatsapp_reminder=project_details["whatsapp_reminder"],
            calendar_invites=project_details["calendar_invites"],
            nudges=project_details["nudges"],
            pre_assessment=project_details["pre_assessment"],
            post_assessment=project_details["post_assessment"],
            is_finance_enabled=project_details["finance"],
            teams_enabled=project_details["teams_enabled"],
            project_type=project_details["project_type"],
            junior_pmo=junior_pmo,
        )
        schedularProject.save()
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to create project."}, status=400)

    for hr in project_details["hr"]:
        single_hr = HR.objects.get(id=hr)
        schedularProject.hr.add(single_hr)

    try:
        create_task(
            {
                "task": "add_project_structure",
                "schedular_project": schedularProject.id,
                "project_type": "skill_training",
                "priority": "high",
                "status": "pending",
                "remarks": [],
            },
            1,
        )
        create_task(
            {
                "task": "add_batches",
                "schedular_project": schedularProject.id,
                "project_type": "skill_training",
                "priority": "high",
                "status": "pending",
                "remarks": [],
            },
            1,
        )

    except Exception as e:
        print("Error", str(e))

    handover_id = project_details.get("handover")
    if handover_id:
        handover = HandoverDetails.objects.get(id=handover_id)
        handover.schedular_project = schedularProject
        handover.save()
        schedularProject.project_structure = handover.project_structure
        schedularProject.save()
        add_so_to_project("SEEQ", schedularProject.id, handover.sales_order_ids)
    else:
        sales_order_ids = project_details["sales_order_ids"]
        if sales_order_ids:
            add_so_to_project("SEEQ", schedularProject.id, sales_order_ids)
        # raise Exception("No handover found")

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


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "sales")])
@transaction.atomic
def create_handover(request):
    handover_details = json.loads(request.data.get("payload"))
    serializer = HandoverDetailsSerializer(data=handover_details)
    if serializer.is_valid():
        organisation_name = handover_details.get("organisation_name")
        # create or get organisation
        organisation, created = Organisation.objects.get_or_create(
            name=organisation_name
        )
        # for saving gm_sheets and proposals
        handover_instance = serializer.save()
        handover_instance.organisation = organisation
        handover_instance.save()

        serializer = HandoverDetailsSerializer(
            handover_instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)

        res_serializer = HandoverDetailsSerializer(handover_instance)
        return Response(
            {
                "message": (
                    "The Handover has been saved as draft successfully"
                    if handover_instance.is_drafted
                    else "Handover created successfully. Please contact the PMO team for acceptance of the handover."
                ),
                "handover": res_serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    else:
        print(serializer.errors)
        return Response({"error": "Failed to add handover. "}, status=500)


PROJECT_TYPE_VALUES = {"caas": "CAAS", "skill_training": "Skill Training", "COD": "COD"}

PROJECT_TYPE_VALUES = {
    "caas": "CAAS",
    "skill_training": "Skill Training",
    "COD": "COD",
    "assessment": "Assessment",
}


from django.utils import timezone


@api_view(["GET"])
def get_current_or_next_year(request):
    try:
        latest_benchmark = Benchmark.objects.latest("created_at")
        if latest_benchmark:
            current_year = int(latest_benchmark.year.split("-")[0])
            print("curr", current_year)
            next_year = f"{current_year + 1}-{str(current_year + 2)[2:]}"
            print(next_year)
            return Response({"year": next_year})
    except Benchmark.DoesNotExist:
        # If no benchmark exists, return the current year
        current_year = timezone.now().year
        next_year = f"{current_year}-{str(current_year + 1)[2:]}"
        return Response({"year": next_year}, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_benchmark(request):
    year = request.data.get("year", None)  # Extract year from request data
    benchmark_data = request.data.get(
        "benchmark", None
    )  # Extract benchmark data from request data

    if year is None:
        return Response(
            {"error": "Year is required in the payload"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        benchmark = Benchmark.objects.get(year=year)
    except Benchmark.DoesNotExist:
        return Response(
            {"error": f"Benchmark for year {year} does not exist"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "PUT":
        serializer = BenchmarkSerializer(
            benchmark, data={"project_type": benchmark_data}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def create_benchmark(request):
    year = request.data.get("year")
    if not year:
        return Response(
            {"error": "Year is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Fetch all existing benchmarks
    existing_benchmarks = Benchmark.objects.all()

    # Gather project_type keys from existing benchmarks
    project_type_keys = set()
    for benchmark in existing_benchmarks:
        project_type_keys.update(benchmark.project_type.keys())

    # Create new project_type with keys and empty string values
    project_type = {key: "" for key in project_type_keys}

    data = {
        "year": year,
        "project_type": project_type,
    }

    serializer = BenchmarkSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(["POST"])
# @permission_classes([IsAuthenticated, IsInRoles("leader")])
# def create_benchmark(request):
#     try:
#         benchmarks_data = request.data.get("lineItems")
#         created_benchmarks = []

#         with transaction.atomic():
#             for benchmark_data in benchmarks_data:
#                 serializer = BenchmarkSerializer(data=benchmark_data)
#                 if serializer.is_valid():
#                     serializer.save()
#                     created_benchmarks.append(serializer.data)
#                 else:
#                     # If any benchmark data is invalid, return the errors
#                     return Response(serializer.errors, status=400)

#         return Response(created_benchmarks, status=201)  # Return the created benchmarks
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes(
    [IsAuthenticated]
)  # Assuming authenticated users can access all benchmarks
def get_all_benchmarks(request):
    if request.method == "GET":
        try:
            benchmarks = Benchmark.objects.all()
            serializer = BenchmarkSerializer(benchmarks, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@transaction.atomic
def create_gmsheet(request):
    try:
        if request.method == "POST":
            gmsheet_data = request.data.get("gmsheet")
            gm_sheet_serializer = GmSheetSerializer(data=gmsheet_data)
            if gm_sheet_serializer.is_valid():
                gm_sheet = gm_sheet_serializer.save()
                offerings_data = request.data.get("offerings")
                if offerings_data:
                    for offering_data in offerings_data:
                        offering_data["gm_sheet"] = gm_sheet.id
                        offering_serializer = OfferingSerializer(data=offering_data)
                        if offering_serializer.is_valid():
                            offering_serializer.save()
                        else:
                            return Response(
                                offering_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                # Sending email notification
                send_mail_templates(
                    "leader_emails/gm_sheet_created.html",
                    (
                        ["sujata@meeraq.com"]
                        if env("ENVIRONMENT") == "PRODUCTION"
                        else ["naveen@meeraq.com"]
                    ),  # Update with the recipient's email address
                    "New GM Sheet created",
                    {
                        "projectName": gm_sheet.project_name,
                        "clientName": gm_sheet.client_name,
                        "startdate": gm_sheet.start_date,
                        "projectType": gm_sheet.project_type,
                        "salesName": gm_sheet.sales.name,
                    },
                    [],  # No BCC
                )

                return Response(
                    gm_sheet_serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                gm_sheet_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        # Handle any exceptions here
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
def update_is_accepted_status(request, pk):
    try:
        gm_sheet = GmSheet.objects.get(pk=pk)
    except GmSheet.DoesNotExist:
        return Response(
            {"error": "GmSheet not found"}, status=status.HTTP_404_NOT_FOUND
        )
    data = {}
    # Check if is_accepted is present in request data
    if "is_accepted" in request.data:
        data["is_accepted"] = request.data.get("is_accepted")
        # Call send_mail_templates if is_accepted is True
        if data["is_accepted"]:
            template_name = "gm_sheet_approved.html"
            subject = "GM Sheet approved"
            context_data = {
                "projectName": gm_sheet.project_name,
                "clientName": gm_sheet.client_name,
                "startdate": gm_sheet.start_date,
                "projectType": gm_sheet.project_type,
                "salesName": gm_sheet.sales.name,
            }
            bcc_list = []  # No BCC
            send_mail_templates(
                template_name,
                (
                    [gm_sheet.sales.email]
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else ["naveen@meeraq.com"]
                ),
                subject,
                context_data,
                bcc_list,
            )

    # Check if deal_status is present in request data
    if "deal_status" in request.data:
        data["deal_status"] = request.data.get("deal_status")
        all_offerings = Offering.objects.filter(gm_sheet=gm_sheet)
        all_offerings.update(is_won=False)
        if data["deal_status"].lower() == "won":
            offering_id = request.data.get("offering_id")
            if not offering_id:
                return Response(
                    {"error": "Offering ID not provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                offering = Offering.objects.get(pk=offering_id)
                offering.is_won = True
                offering.save()
            except Offering.DoesNotExist:
                return Response(
                    {"error": "Offering not found"}, status=status.HTTP_404_NOT_FOUND
                )

    gm_sheet_serializer = GmSheetSerializer(gm_sheet, data=data, partial=True)
    if gm_sheet_serializer.is_valid():
        gm_sheet_serializer.save()
        return Response(gm_sheet_serializer.data, status=status.HTTP_200_OK)
    return Response(gm_sheet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@transaction.atomic
def update_gmsheet(request, id):
    try:
        gm_sheet = GmSheet.objects.get(id=id)
        gmsheet_data = request.data.get("gmsheet")
        gm_sheet_serializer = GmSheetSerializer(
            gm_sheet, data=gmsheet_data, partial=True
        )

        if gm_sheet_serializer.is_valid():
            gm_sheet = gm_sheet_serializer.save()

            # Handle offerings update
            offerings_data = request.data.get("offerings", [])

            for offering_data in offerings_data:
                offering_id = offering_data.get("id")
                if offering_id:
                    try:
                        offering_instance = Offering.objects.get(
                            id=offering_id, gm_sheet=gm_sheet
                        )
                        offering_serializer = OfferingSerializer(
                            offering_instance, data=offering_data, partial=True
                        )
                        if offering_serializer.is_valid():
                            offering_serializer.save()
                        else:
                            print(offering_serializer.errors)
                            return Response(
                                offering_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    except Offering.DoesNotExist:
                        return Response(
                            {"error": "Offering not found"},
                            status=status.HTTP_404_NOT_FOUND,
                        )
                else:
                    offering_data["gm_sheet"] = gm_sheet.id
                    offering_serializer = OfferingSerializer(data=offering_data)
                    if offering_serializer.is_valid():
                        offering_serializer.save()
                    else:
                        print("he2", offering_serializer.errors)
                        return Response(
                            offering_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            return Response(
                {"message": "Update Successfully"}, status=status.HTTP_200_OK
            )
        else:
            print("hey", gm_sheet_serializer.errors)
            return Response(
                gm_sheet_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to update data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "sales")])
def update_handover(request):
    handover_details = json.loads(request.data.get("payload"))
    try:
        handover_instance = HandoverDetails.objects.get(id=request.data.get("id"))
    except HandoverDetails.DoesNotExist:
        return Response({"error": "Handover not found."}, status=404)

    serializer = HandoverDetailsSerializer(
        handover_instance, data=handover_details, partial=True
    )
    if serializer.is_valid():
        handover_instance = serializer.save()
        try:
            files_saving_serializer = HandoverDetailsSerializer(
                handover_instance, data=request.data, partial=True
            )
            if files_saving_serializer.is_valid():
                handover_instance = files_saving_serializer.save()
            else:
                print(files_saving_serializer.errors)
        except Exception as e:
            pass

        # when handover is being edited and the project is already created, sending the mails
        if handover_instance.caas_project or handover_instance.schedular_project:
            # junior pmo and pmo training and coaching if a handover is edited by the sales person
            if handover_instance.caas_project:
                junior_pmo = handover_instance.caas_project.junior_pmo
                project_name = handover_instance.caas_project.name
            elif handover_instance.schedular_project:
                junior_pmo = handover_instance.schedular_project.junior_pmo
                project_name = handover_instance.schedular_project.name
            else:
                junior_pmo = None
                project_name = ""
            emails = ["pmocoaching@meeraq.com", "pmotraining@meeraq.com"]
            if junior_pmo:
                emails.append(junior_pmo.email)

            send_mail_templates(
                "pmo_emails/edit_handover.html",
                emails if env("ENVIRONMENT") == "PRODUCTION" else ["tech@meeraq.com"],
                "Meeraq Platform | Handover Details Updated",
                {"project_name": project_name},
                [],  # no bcc
            )
        if request.query_params.get("handover", "") == "accepted":
            bcc_emails = [
                "pmocoaching@meeraq.com",
                "pmotraining@meeraq.com",
                "rajat@meeraq.com",
                "sujata@meeraq.com",
                "sales@meeraq.com",
            ]
            project_name = handover_instance.project_name
            send_mail_templates(
                "pmo_emails/accept_handover.html",
                [
                    (
                        handover_instance.sales.email
                        if handover_instance.sales
                        else "sales@meeraq.com"
                    )
                ],
                f"Handover Accepted: {PROJECT_TYPE_VALUES[handover_instance.project_type]}",
                {
                    "project_name": project_name,
                    "project_type": PROJECT_TYPE_VALUES[handover_instance.project_type],
                    "pmo_name": "PMO",
                    "sales_name": handover_instance.sales.name,
                    "sales_number": handover_instance.sales_order_ids,
                },
                (
                    bcc_emails
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else ["tech@meeraq.com", "naveen@meeraq.com"]
                ),
            )

        return Response(
            {
                "message": "Handover updated successfully.",
                "handover": serializer.data,
            },
            status=200,
        )
    else:
        print(serializer.errors)
        return Response({"error": "Failed to update handover."}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "sales")])
def get_handover_salesorders(request, handover_id):
    try:
        handover = HandoverDetails.objects.get(id=handover_id)
        sales_orders_ids_str = ",".join(handover.sales_order_ids)
        all_sales_orders = []
        if sales_orders_ids_str:
            all_sales_orders = fetch_sales_orders(
                organization_id, f"&salesorder_ids={sales_orders_ids_str}"
            )
        return Response(all_sales_orders)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_handover(request, project_type, project_id):
    if project_type == "skill_training":
        handover = HandoverDetails.objects.get(schedular_project=project_id)
    elif project_type == "caas":
        handover = HandoverDetails.objects.get(caas_project=project_id)
    serializer = HandoverDetailsSerializer(handover)
    return Response(serializer.data)


@api_view(["POST"])
def create_asset(request):
    serializer = AssetsSerializer(data=request.data)
    if serializer.is_valid():
        instance = serializer.save()
        # Set default values for update_entry
        update_entry = {
            "date": str(datetime.now()),
            "status": instance.status,
        }

        if instance.assigned_to is not None:
            update_entry["assigned_to"] = instance.assigned_to.id
            update_entry["assigned_to_name"] = (
                instance.assigned_to.first_name + " " + instance.assigned_to.last_name
            )
        else:
            update_entry["assigned_to"] = None
            update_entry["assigned_to_name"] = None

        instance.updates.append(update_entry)
        instance.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_all_assets(request):
    if request.method == "GET":
        assets = Assets.objects.all().order_by("-update_at")
        serializer = AssetsDetailedSerializer(assets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_asset(request):
    id = request.data.get("id")
    if not id:
        return Response({"error": "ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        asset = Assets.objects.get(pk=id)
    except Assets.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    asset.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
def update_asset(request):
    payload = request.data
    values = payload.get("values")
    asset_id = payload.get("id")

    if not asset_id:
        return Response(
            {"error": "Asset ID is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        asset = Assets.objects.get(id=asset_id)
    except Assets.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = AssetsSerializer(
        asset, data=values, partial=True
    )  # Use partial=True for partial updates

    if serializer.is_valid():
        instance = serializer.save()

        update_entry = {
            "date": datetime.now().isoformat(),
            "status": instance.status,
            "assigned_to": instance.assigned_to.id if instance.assigned_to else None,
            "assigned_to_name": (
                f"{instance.assigned_to.first_name} {instance.assigned_to.last_name}"
                if instance.assigned_to
                else None
            ),
        }

        # Ensure updates field is a list before appending
        if not isinstance(instance.updates, list):
            instance.updates = []

        instance.updates.append(update_entry)
        instance.save()

        # Use AssetsDetailedSerializer to include assigned_to_name in the response
        detailed_serializer = AssetsDetailedSerializer(instance)
        return Response(detailed_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def update_status(request):
    if request.method == "PUT":
        asset_id = request.data.get("id")
        if asset_id is None:
            return Response(
                {"error": "Asset ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            asset = Assets.objects.get(pk=asset_id)
        except Assets.DoesNotExist:
            return Response(
                {"error": "Asset does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")
        if new_status not in [choice[0] for choice in Assets.STATUS_CHOICES]:
            return Response(
                {"error": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST
            )

        asset.status = new_status
        if new_status == "idle":
            asset.assigned_to = None

        # Serialize the assigned_to field
        assigned_to = asset.assigned_to.id if asset.assigned_to else None

        # Append the update to the updates field
        update_entry = {
            "date": str(datetime.now()),
            "status": new_status,
            "assigned_to": assigned_to,
        }
        if not hasattr(asset, "updates"):
            asset.updates = []  # Initialize if 'updates' field does not exist
        asset.updates.append(update_entry)

        asset.save()
        return Response({"success": "Status updated successfully"})
    return Response(
        {"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@api_view(["GET"])
@permission_classes(
    [
        IsAuthenticated,
        IsInRoles("hr", "pmo", "coach", "facilitator", "learner", "sales"),
    ]
)
def get_all_Schedular_Projects(request):
    status = request.query_params.get("status")
    pmo_id = request.query_params.get("pmo")
    coach_id = request.query_params.get("coach_id")
    finance = request.query_params.get("finance")
    projects = None
    if finance:
        projects = SchedularProject.objects.all()
    elif pmo_id:
        pmo = Pmo.objects.get(id=int(pmo_id))

        if pmo.sub_role == "junior_pmo":
            projects = SchedularProject.objects.filter(junior_pmo=pmo)
        else:
            projects = SchedularProject.objects.all()
    elif coach_id:
        coach = Coach.objects.get(id=int(coach_id))
        projects = SchedularProject.objects.filter(
            Q(schedularbatch__coaches=coach)
        ).distinct()
    else:
        projects = SchedularProject.objects.all()

    if status:
        projects = projects.exclude(status="completed")

    projects = projects.annotate(
        is_archive_enabled=Case(
            When(
                Exists(SchedularBatch.objects.filter(project=OuterRef("id"))),
                then=False,
            ),
            default=True,
            output_field=BooleanField(),
        )
    )
    serializer = SchedularProjectSerializerArchiveCheck(projects, many=True)
    for project_data in serializer.data:

        latest_update = (
            SchedularUpdate.objects.filter(project__id=project_data["id"])
            .order_by("-created_at")
            .first()
        )
        project_data["latest_update"] = latest_update.message if latest_update else None
        handover = HandoverDetails.objects.filter(
            schedular_project__id=project_data["id"]
        ).first()
        project_data["is_handover_present"] = True if handover else False
    return Response(serializer.data, status=200)


def create_facilitator_pricing(batch, facilitator):
    project_structure = batch.project.project_structure

    for session in project_structure:

        if session["session_type"] in [
            "check_in_session",
            "in_person_session",
            "pre_study",
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
                facilitator_pricing.price = session.get("price", 0)
                facilitator_pricing.save()


def delete_facilitator_pricing(batch, facilitator):
    project_structure = batch.project.project_structure

    for session in project_structure:

        if session["session_type"] in [
            "check_in_session",
            "in_person_session",
            "pre_study",
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


def create_coach_pricing(batch, coach):
    project_structure = batch.project.project_structure
    for session in project_structure:
        if session["session_type"] in [
            "laser_coaching_session",
            "mentoring_session",
            "action_coaching_session",
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
                coach_pricing.price = session.get("price", 0)
                coach_pricing.save()
                create_task(
                    {
                        "task": "create_purchase_order",
                        "schedular_project": batch.project.id,
                        "coach": coach_pricing.coach.id,
                        "project_type": "skill_training",
                        "priority": "low",
                        "status": "pending",
                        "remarks": [],
                    },
                    7,
                )


def create_batch_calendar(batch):
    for session_data in batch.project.project_structure:
        order = session_data.get("order")
        duration = session_data.get("duration")
        session_type = session_data.get("session_type")

        if session_type in [
            "live_session",
            "check_in_session",
            "in_person_session",
            "pre_study",
            "kickoff_session",
            "virtual_session",
        ]:
            session_number = (
                LiveSession.objects.filter(
                    batch=batch, session_type=session_type
                ).count()
                + 1
            )
            if session_type == "pre_study":
                facilitator = Facilitator.objects.filter(
                    email=env("PRE_STUDY_FACILITATOR")
                ).first()

                live_session = LiveSession.objects.create(
                    batch=batch,
                    live_session_number=session_number,
                    order=order,
                    duration=duration,
                    session_type=session_type,
                    facilitator=facilitator,
                )
            else:
                live_session = LiveSession.objects.create(
                    batch=batch,
                    live_session_number=session_number,
                    order=order,
                    duration=duration,
                    session_type=session_type,
                )
            create_task(
                {
                    "task": "add_session_details",
                    "schedular_project": batch.project.id,
                    "project_type": "skill_training",
                    "live_session": live_session.id,
                    "priority": "medium",
                    "status": "pending",
                    "remarks": [],
                },
                3,
            )
        elif session_type in [
            "laser_coaching_session",
            "mentoring_session",
            "action_coaching_session",
        ]:
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
            create_task(
                {
                    "task": "add_dates",
                    "schedular_project": batch.project.id,
                    "project_type": "skill_training",
                    "coaching_session": coaching_session.id,
                    "priority": "medium",
                    "status": "pending",
                    "remarks": [],
                },
                7,
            )


def delete_sessions_and_create_new_batch_calendar_and_lessons(project):
    # deletion of related details
    lessons = Lesson.objects.filter(
        lesson_type="feedback",
        feedbacklesson__live_session__isnull=False,
        course__batch__project=project,
    )
    lessons.delete()
    lessons = Lesson.objects.filter(
        lesson_type="live_session", course__batch__project=project
    )
    lessons.delete()
    lessons = Lesson.objects.filter(
        lesson_type="laser_coaching", course__batch__project=project
    )
    lessons.delete()
    coach_pricings = CoachPricing.objects.filter(project=project)
    coach_pricings.delete()
    facilitator_pricings = FacilitatorPricing.objects.filter(project=project)
    facilitator_pricings.delete()
    calendar_invites = CalendarInvites.objects.filter(
        live_session__batch__project=project
    )
    for calendar_invite in calendar_invites:
        delete_outlook_calendar_invite(calendar_invite)

    live_sessions = LiveSession.objects.filter(batch__project=project)
    live_sessions.delete()
    coaching_sessions = CoachingSession.objects.filter(batch__project=project)
    coaching_sessions.delete()

    # create new batch calendar for all batches
    batches = SchedularBatch.objects.filter(project=project)
    for batch in batches:
        create_batch_calendar(batch)
        # dont change the order of create batch calendar and create lessons -> lessons will be created after batch calendar
        create_lessons_for_batch(batch)

        for coach in batch.coaches.all():
            create_coach_pricing(batch, coach)

    return None


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
@transaction.atomic
def create_project_structure(request, project_id):
    try:
        project = get_object_or_404(SchedularProject, id=project_id)
        serializer = SessionItemSerializer(data=request.data, many=True)
        if serializer.is_valid():
            is_editing = len(project.project_structure) > 0
            project.project_structure = serializer.data
            project.save()
            # updating task status
            try:
                tasks = Task.objects.filter(
                    task="add_project_structure",
                    status="pending",
                    schedular_project=project,
                )
                tasks.update(status="completed")
            except Exception as e:
                print(str(e))
                pass

            batches = SchedularBatch.objects.filter(project=project)
            if batches.exists():
                delete_sessions_and_create_new_batch_calendar_and_lessons(project)

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
@permission_classes(
    [
        IsAuthenticated,
        IsInRoles("hr", "pmo", "coach", "facilitator", "learner", "sales"),
    ]
)
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

        # Check if a contract exists for the project
        is_contract_present = ProjectContract.objects.filter(
            schedular_project__id=project_id
        ).exists()

        serializer = SchedularProjectSerializer(project)
        # Add the 'is_contract_present' field to the serializer data

        return Response({**serializer.data, "is_contract_present": is_contract_present})
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."},
            status=status.HTTP_400_BAD_REQUEST,
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
@permission_classes(
    [IsAuthenticated, IsInRoles("hr", "pmo", "coach", "facilitator", "learner")]
)
def get_batch_calendar(request, batch_id):
    try:
        fetch_po = request.query_params.get("fetch_po")
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
            )
        )

        coaches_serializer = CoachSerializer(coaches, many=True)
        facilitator_serializer = FacilitatorSerializerIsVendor(facilitator, many=True)
        if fetch_po == "True":
            try:
                purchase_orders = PurchaseOrderGetSerializer(
                    PurchaseOrder.objects.filter(
                        Q(created_time__year__gte=2024)
                        | Q(purchaseorder_number__in=purchase_orders_allowed)
                    ),
                    many=True,
                ).data
                # filter_purchase_order_data(PurchaseOrderGetSerializer(PurchaseOrder.objects.all(), many=True).data)
                # fetch_purchase_orders(organization_id)
                for facilitator_item in facilitator_serializer.data:
                    expense = Expense.objects.filter(
                        batch__id=batch_id, facilitator__id=facilitator_item["id"]
                    ).first()
                    facilitator_item["purchase_order_id"] = expense.purchase_order_id
                    facilitator_item["purchase_order_no"] = expense.purchase_order_no
                    is_delete_purchase_order_allowed = True
                    if facilitator_item["purchase_order_id"]:
                        purchase_order = get_purchase_order(
                            purchase_orders, facilitator_item["purchase_order_id"]
                        )
                        if not purchase_order:
                            Expense.objects.filter(
                                batch__id=batch_id,
                                facilitator__id=facilitator_item["id"],
                            ).update(purchase_order_id="", purchase_order_no="")
                            facilitator_item["purchase_order_id"] = None
                            facilitator_item["purchase_order_no"] = None
                        else:
                            invoices = InvoiceData.objects.filter(
                                purchase_order_id=facilitator_item["purchase_order_id"]
                            )
                            if invoices.exists():
                                is_delete_purchase_order_allowed = False
                        facilitator_item["is_delete_purchase_order_allowed"] = (
                            is_delete_purchase_order_allowed
                        )
                        facilitator_item["purchase_order"] = purchase_order
                    else:
                        facilitator_item["purchase_order"] = None
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
        certificate = Certificate.objects.filter(courses=course).first()
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
                "project_name": batch_for_response.project.name,
                "certificate_present": True if certificate else False,
            }
        )
    except SchedularProject.DoesNotExist:
        return Response(
            {"error": "Couldn't find project to add project structure."}, status=400
        )
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=400)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def update_live_session(request, live_session_id):
    try:
        with transaction.atomic():
            change_in_all_batches = request.query_params.get("change_in_all_batches")
            change_in_all_batches_bool = bool(change_in_all_batches)
            main_live_session = LiveSession.objects.get(id=live_session_id)
            batches = []
            if change_in_all_batches:
                batches = SchedularBatch.objects.filter(
                    project=main_live_session.batch.project
                )
            else:
                batches = SchedularBatch.objects.filter(id=main_live_session.batch.id)
            count = 0
            for batch in batches:

                live_session = LiveSession.objects.get(
                    batch=batch, order=main_live_session.order
                )
                data = request.data
                if change_in_all_batches and count >= 1:
                    if "attendees" in request.data:
                        del request.data["attendees"]
                existing_date_time = live_session.date_time
                serializer = LiveSessionSerializer(
                    live_session, data=data, partial=True
                )
                count += 1
                if serializer.is_valid():
                    update_live_session = serializer.save()
                    try:
                        tasks = Task.objects.filter(
                            task="add_session_details",
                            status="pending",
                            live_session=live_session,
                        )
                        tasks.update(status="completed")
                    except Exception as e:
                        print(str(e))
                        pass
                    current_time = timezone.now()
                    days_difference = (
                        update_live_session.date_time - current_time
                    ).days
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
                            periodic_task = PeriodicTask.objects.create(
                                name=f"send_live_session_link_whatsapp_to_facilitators_30_min_before{uuid.uuid1()}",
                                task="schedularApi.tasks.send_live_session_link_whatsapp_to_facilitators_30_min_before",
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
                    if live_session_lesson:
                        lesson = live_session_lesson.lesson

                        lesson.drip_date = live_session.date_time + timedelta(
                            hours=5, minutes=30
                        )

                        lesson.save()
                if update_live_session.batch.project.teams_enabled:
                    if (
                        existing_date_time
                        and existing_date_time.strftime("%d-%m-%Y %H:%M")
                        != update_live_session.date_time.strftime("%d-%m-%Y %H:%M")
                        and update_live_session.teams_meeting_id
                        and update_live_session.batch.project.teams_enabled
                    ):
                        delete_teams_meeting(
                            env("CALENDAR_INVITATION_ORGANIZER"),
                            update_live_session,
                        )
                if (
                    update_live_session.batch.project.teams_enabled
                    and update_live_session.session_type != "in_person_session"
                    and (
                        not existing_date_time
                        or existing_date_time.strftime("%d-%m-%Y %H:%M")
                        != update_live_session.date_time.strftime("%d-%m-%Y %H:%M")
                    )
                ):

                    start_time = update_live_session.date_time
                    end_date = start_time + timedelta(
                        minutes=int(update_live_session.duration)
                    )
                    start_time_str_for_teams = start_time.strftime(
                        "%Y-%m-%dT%H:%M:%S.%f-07:00"
                    )
                    end_time_str_for_teams = end_date.strftime(
                        "%Y-%m-%dT%H:%M:%S.%f-07:00"
                    )
                    create_teams_meeting(
                        env("CALENDAR_INVITATION_ORGANIZER"),
                        update_live_session.id,
                        f"{update_live_session.session_type} {update_live_session.live_session_number}",
                        start_time_str_for_teams,
                        end_time_str_for_teams,
                    )

                if update_live_session.status == "completed":
                    tasks = Task.objects.filter(
                        task="update_status_of_virtual_session",
                        live_session=update_live_session,
                    )
                    tasks.update(status="completed")
                    if len(update_live_session.attendees) == 0:
                        create_task(
                            {
                                "task": "add_attendance",
                                "schedular_project": update_live_session.batch.project.id,
                                "project_type": "skill_training",
                                "live_session": update_live_session.id,
                                "priority": "low",
                                "status": "pending",
                                "remarks": [],
                            },
                            3,
                        )
                    elif len(update_live_session.attendees) > 0:
                        try:
                            tasks = Task.objects.filter(
                                task="add_attendance",
                                status="pending",
                                live_session=update_live_session,
                            )
                            tasks.update(status="completed")
                        except Exception as e:
                            print(str(e))
                            pass

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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def update_coaching_session(request, coaching_session_id):
    try:
        with transaction.atomic():
            coaching_session = CoachingSession.objects.get(id=coaching_session_id)

            serializer = CoachingSessionSerializer(
                coaching_session, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                try:
                    tasks = Task.objects.filter(
                        task="add_dates",
                        status="pending",
                        coaching_session=coaching_session,
                    )
                    tasks.update(status="completed")
                except Exception as e:
                    print(str(e))
                    pass

                coaching_session_lesson = LaserCoachingSession.objects.filter(
                    coaching_session=coaching_session
                ).first()
                if coaching_session_lesson:
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "learner")])
def participants_list(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
    except SchedularBatch.DoesNotExist:
        return Response({"detail": "Batch not found"}, status=404)
    learners = batch.learners.all()
    serializer = LearnerSerializer(learners, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_learner_by_project(request, project_type, project_id):
    if project_type == "caas":
        learners = Learner.objects.filter(engagement__project__id=project_id).distinct()
    elif project_type == "skill_training":
        learners = Learner.objects.filter(
            schedularbatch__project__id=project_id
        ).distinct()
    else:
        return Response(
            {"error": "Failed to get learners"}, status=status.HTTP_400_BAD_REQUEST
        )
    serializer = LearnerSerializer(learners, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def getSavedTemplates(request):
    emailTemplate = EmailTemplate.objects.all()
    serilizer = EmailTemplateSerializer(emailTemplate, many=True)
    return Response({"status": "success", "data": serilizer.data}, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "learner")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "coach")])
def get_all_schedular_availabilities(request):
    coach_id = request.GET.get("coach_id")
    if coach_id:
        availabilities = RequestAvailibilty.objects.filter(coach__id=coach_id)
    else:
        availabilities = RequestAvailibilty.objects.all()
    serializer = CoachSchedularAvailibiltySerializer2(availabilities, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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

                try:
                    create_task(
                        {
                            "task": "remind_coach_availability",
                            "priority": "medium",
                            "status": "pending",
                            "coach": coach.id,
                            "request": serializer.data["id"],
                            "remarks": [],
                        },
                        1,
                    )
                except Exception as e:
                    print(str(e))

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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def add_batch(request, project_id):
    try:
        data = {
            "participants": request.data.get("participants", []),
            "project_id": project_id,
            "user_email": request.user.username,
        }

        add_batch_to_project.delay(data)

        return Response(
            {
                "message": "Hooray! Your participant data is now in the upload queue. It's like ordering pizza; just sit back, relax, and soon you'll receive a notification by email with fresh, insightful data at your fingertips!"
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to add participants."},
            status=500,
        )


@api_view(["GET"])
@permission_classes(
    [IsAuthenticated, IsInRoles("pmo", "hr", "coach", "facilitator", "leanrer")]
)
def get_coaches(request):
    coaches = Coach.objects.filter(is_approved=True)
    serializer = CoachBasicDetailsSerializer(coaches, many=True)
    return Response(serializer.data)


# use to add coaches to a batch
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
                    create_coach_pricing(batch, coach)

            serializer = SchedularBatchSerializer(
                batch, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                contracts = ProjectContract.objects.filter(
                    schedular_project__id=batch.project.id
                )
                if contracts.exists():
                    contract = contracts.first()
                    for coach in batch.coaches.all():
                        existing_coach_contract = CoachContract.objects.filter(
                            schedular_project=batch.project, coach=coach.id
                        ).exists()
                        if not existing_coach_contract:
                            contract_data = {
                                "project_contract": contract.id,
                                "schedular_project": batch.project.id,
                                "status": "pending",
                                "coach": coach.id,
                            }
                            contract_serializer = CoachContractSerializer(
                                data=contract_data
                            )
                            if contract_serializer.is_valid():
                                contract_serializer.save()
                            else:
                                return Response(
                                    {"error": "Failed to perform task."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                )
                try:
                    tasks = Task.objects.filter(
                        task="add_coach", status="pending", schedular_batch=batch
                    )
                    tasks.update(status="complete")
                except Exception as e:
                    print(str(e))

                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to perform task."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_batch(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)
    except SchedularBatch.DoesNotExist:
        return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = SchedularBatchSerializer(batch)
    return Response({**serializer.data, "is_nudge_enabled": batch.project.nudges})


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

            language_coaches = {}
            for coach_instance in coaches_in_batch:
                for language in coach_instance.language:
                    if language in language_coaches:
                        language_coaches[language].append(coach_instance.id)
                    else:
                        language_coaches[language] = [coach_instance.id]

            return Response(
                {
                    "project_status": coaching_session.batch.project.status,
                    "slots": serializer.data,
                    "session_duration": session_duration,
                    "session_type": session_type,
                    "coaches": coaches_serializer.data if coaches_serializer else None,
                    "language_coaches": language_coaches,
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
                        else (
                            "Meeraq - Mentoring Session Booked"
                            if session_type == "mentoring_session"
                            else (
                                "Meeraq - Action Coaching Booked"
                                if session_type == "action_coaching_session"
                                else "Meeraq - Session Booked"
                            )
                        )
                    ),
                    {
                        "name": learner.name,
                        "date": date_for_mail,
                        "time": session_time,
                        "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                        "session_type": (
                            "Mentoring"
                            if session_type == "mentoring_session"
                            else (
                                "Action Coaching"
                                if session_type == "action_coaching_session"
                                else "Laser Coaching"
                            )
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
            existing_session_of_coach_at_same_time = SchedularSessions.objects.filter(
                Q(availibility__coach_id=coach_id),
                Q(
                    availibility__start_time__gt=timestamp,
                    availibility__start_time__lte=end_time,
                )
                | Q(
                    availibility__start_time__lt=timestamp,
                    availibility__end_time__gte=timestamp,
                )
                | Q(availibility__start_time=timestamp)
                | Q(availibility__end_time=end_time),
            )
            if existing_session_of_coach_at_same_time.exists():
                return Response(
                    {
                        "error": "Sorry! This slot has just been booked. Please refresh and try selecting a different time."
                    },
                    status=401,
                )
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
                    else (
                        "mentoring"
                        if session_type == "mentoring_session"
                        else (
                            "action coaching"
                            if session_type == "action_coaching_session"
                            else ""
                        )
                    )
                )
                booking_id = coach_availability.coach.room_id
                meeting_location = f"{env('CAAS_APP_URL')}/call/{booking_id}"
                # tasks = Task.objects.filter(
                #     task="coachee_book_session",
                #     status="pending",
                # )
                # if tasks:
                #     tasks.update(status="completed")
                try:
                    create_task(
                        {
                            "task": "schedular_update_session_status",
                            "priority": "medium",
                            "status": "pending",
                            "coach_id": coach_id,
                            "remarks": [],
                        },
                        1,
                    )
                except Exception as e:
                    print(str(e))
                # Only send email if project status is ongoing
                if coaching_session.batch.project.status == "ongoing":
                    attendees = None
                    if coaching_session.batch.calendar_invites:
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
                            else (
                                "Meeraq - Mentoring Session Booked"
                                if session_type == "mentoring_session"
                                else (
                                    "Meeraq - Action Coaching Booked"
                                    if session_type == "action_coaching_session"
                                    else "Meeraq - Session Booked"
                                )
                            )
                        ),
                        {
                            "name": learner.name,
                            "date": date_for_mail,
                            "time": session_time,
                            "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                            "session_type": (
                                "Mentoring"
                                if session_type == "mentoring_session"
                                else (
                                    "Action Coaching"
                                    if session_type == "action_coaching_session"
                                    else "Laser Coaching"
                                )
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
                    else (
                        "mentoring"
                        if session_type == "mentoring_session"
                        else (
                            "action coaching"
                            if session_type == "action_coaching_session"
                            else ""
                        )
                    )
                )

                booking_id = coach_availability.coach.room_id
                meeting_location = f"{env('CAAS_APP_URL')}/call/{booking_id}"
                # Only send email if project status is ongoing
                if coaching_session.batch.project.status == "ongoing":
                    attendees = None
                    if coaching_session.batch.calendar_invites:
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
                            else (
                                "Meeraq - Mentoring Session Booked"
                                if session_type == "mentoring_session"
                                else (
                                    "Meeraq - Action Coaching Booked"
                                    if session_type == "action_coaching_session"
                                    else "Meeraq - Session Booked"
                                )
                            )
                        ),
                        {
                            "name": learner.name,
                            "date": date_for_mail,
                            "time": session_time,
                            "meeting_link": f"{env('CAAS_APP_URL')}/call/{coach_availability.coach.room_id}",
                            "session_type": (
                                "Mentoring"
                                if session_type == "mentoring_session"
                                else (
                                    "Action Coaching"
                                    if session_type == "action_coaching_session"
                                    else "Laser Coaching"
                                )
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "coach")])
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
            tasks = Task.objects.filter(
                task="remind_coach_availability", status="pending"
            )
            if tasks:
                tasks.update(status="completed")
            # try:

            #     create_task(
            #         {
            #             "task": "coachee_book_session",
            #             "priority": "medium",
            #             "status": "pending",
            #             "engagement": engagement.id,
            #             "coach_id": coach_id,
            #         },
            #         3,
            #     )
            # except Exception as e:
            #     print(str(e))
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "coach")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "coach")])
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
@permission_classes([IsAuthenticated, IsInRoles("coach")])
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
@permission_classes([IsAuthenticated, IsInRoles("coach","pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "coach")])
def get_upcoming_slots_of_coach(request, coach_id):
    current_time = timezone.now()
    timestamp_milliseconds = str(int(current_time.timestamp() * 1000))
    availabilities = CoachSchedularAvailibilty.objects.filter(
        coach__id=coach_id, start_time__gt=timestamp_milliseconds
    )
    serializer = CoachSchedularAvailibiltySerializer(availabilities, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "coach")])
def delete_slots(request):
    slot_ids = request.data.get("slot_ids", [])
    # Assuming slot_ids is a list of integers
    slots_to_delete = CoachSchedularAvailibilty.objects.filter(id__in=slot_ids)
    if not slots_to_delete.exists():
        return Response({"error": "No matching slots found."}, status=404)

    slots_to_delete.delete()
    return Response({"detail": "Slots deleted successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def send_unbooked_coaching_session_mail(request):
    try:
        celery_send_unbooked_coaching_session_mail.delay(request.data)

        return Response({"message": "Emails sent to participants."}, status.HTTP_200_OK)

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to send emails."}, status.HTTP_400_BAD_REQUEST
        )
    
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def send_unbooked_coaching_session_whatsapp_message(request):
    try:
        celery_send_unbooked_coaching_session_whatsapp_message(request.data)
        return Response({"message": "Whatsapp message sent to participants."}, status.HTTP_200_OK)
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "coach")])
def send_live_session_link(request):
    live_session = LiveSession.objects.get(id=request.data.get("live_session_id"))
    email_contents = []
    for learner in live_session.batch.learners.all():
        # Only send email if project status is ongoing
        is_not_in_person_session = (
            False if live_session.session_type == "in_person_session" else True
        )
        if live_session.batch.project.status == "ongoing":
            email_contents.append(
                {
                    "file_name": "send_live_session_link.html",
                    "user_email": learner.email,
                    "email_subject": "Meeraq - Live Session",
                    "content": {
                        "participant_name": learner.name,
                        "live_session_name": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                        "project_name": live_session.batch.project.name,
                        "description": (
                            live_session.description if live_session.description else ""
                        ),
                        "meeting_link": live_session.meeting_link,
                        "is_not_in_person_session": is_not_in_person_session,
                    },
                    "bcc_emails": [],
                }
            )
    send_emails_in_bulk.delay(email_contents)
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
                elif session.session_type == "mentoring_session":
                    session_type_name = "Mentoring Session"
                elif session.session_type == "action_coaching_session":
                    session_type_name = "Action Coaching Session"

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
                participant_email = learner.email
                data = {
                    "Participant name": participant_name,
                    "Email": participant_email,
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
            elif session.session_type == "action_coaching_session":
                session_name = "Action Coaching session"
            session_key = f"{session_name} {session.coaching_session_number}"
            if session_key not in dfs:
                dfs[session_key] = []

            for learner in session.batch.learners.all():
                session_exist = SchedularSessions.objects.filter(
                    coaching_session=session, learner=learner
                ).first()

                participant_name = learner.name
                participant_email = learner.email

                if session_exist:
                    attendance = "YES" if session_exist.status == "completed" else "NO"
                    data = {
                        "Participant name": participant_name,
                        "Email": participant_email,
                        "Batch name": session.batch.name,
                        "Completed": attendance,
                    }
                else:
                    data = {
                        "Participant name": participant_name,
                        "Email": participant_email,
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def add_facilitator(request):
    first_name = request.data.get("first_name", "").strip().title()
    last_name = request.data.get("last_name", "").strip().title()
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def get_facilitators(request):
    try:
        # Get all the Coach objects
        all_fac = []
        facilitators = Facilitator.objects.filter(is_approved=True)
        for facilitator in facilitators:
            overall_answer = Answer.objects.filter(
                question__type="rating_0_to_10",
                question__feedbacklesson__live_session__facilitator__id=facilitator.id,
            )
            overall_nps = calculate_nps_from_answers(overall_answer)
            serializer = FacilitatorSerializer(facilitator)
            all_fac.append(
                {
                    **serializer.data,
                    "overall_nps": overall_nps,
                }
            )
        # Serialize the Coach objects

        # Return the serialized Coach objects as the response
        return Response(all_fac, status=200)

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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "facilitator")])
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


# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def delete_facilitator(request):
#     data = request.data
#     facilitator_id = data.get("facilitator_id")

#     if facilitator_id is None:
#         return Response(
#             {"error": "Facilitator ID is missing in the request data"},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     try:
#         facilitator = Facilitator.objects.get(pk=facilitator_id)
#     except Facilitator.DoesNotExist:
#         return Response(
#             {"error": "Facilitator not found"}, status=status.HTTP_404_NOT_FOUND
#         )

#     facilitator.delete()
#     return Response(
#         {"message": "Facilitator deleted successfully"},
#         status=200,
#     )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "facilitator")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
@transaction.atomic
def edit_schedular_project(request, project_id):
    try:
        with transaction.atomic():
            project = SchedularProject.objects.get(pk=project_id)

            prev_pre_assessment = project.pre_assessment
            prev_post_assessment = project.post_assessment
            project_details = request.data
            junior_pmo = None
            if "junior_pmo" in project_details:
                junior_pmo = Pmo.objects.filter(
                    id=project_details["junior_pmo"]
                ).first()

            project_name = project_details.get("project_name")
            organisation_id = project_details.get("organisation_id")
            hr_ids = project_details.get("hr", [])
            if project_name:
                project.name = project_name
            if organisation_id:
                try:
                    organisation = Organisation.objects.get(pk=organisation_id)
                    project.organisation = organisation

                except Organisation.DoesNotExist:
                    return Response(
                        {"error": "Organisation not found"},
                        status=status.HTTP_404_NOT_FOUND,
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
            project.email_reminder = project_details.get("email_reminder")
            project.whatsapp_reminder = project_details.get("whatsapp_reminder")
            project.calendar_invites = project_details.get("calendar_invites")
            project.nudges = project_details.get("nudges")
            project.pre_assessment = project_details.get("pre_assessment")
            project.post_assessment = project_details.get("post_assessment")
            project.is_finance_enabled = project_details.get("finance")
            project.junior_pmo = junior_pmo
            project.teams_enabled = request.data.get("teams_enabled")
            project.project_type = request.data.get("project_type")
            project.save()

            pre_assessment = None
            post_assessment = None

            batches = SchedularBatch.objects.filter(project=project)

            if not prev_pre_assessment == project.pre_assessment:
                for batch in batches:
                    course = Course.objects.filter(batch=batch).first()
                    if course:

                        max_order = (
                            Lesson.objects.filter(course=course).aggregate(
                                Max("order")
                            )["order__max"]
                            or 0
                        )

                        lesson1 = Lesson.objects.create(
                            course=course,
                            name="Pre Assessment",
                            status="draft",
                            lesson_type="assessment",
                            # Duplicate specific lesson types
                            order=max_order + 1,
                        )
                        assessment1 = AssessmentLesson.objects.create(
                            lesson=lesson1, type="pre"
                        )
                        post_assessment_lesson = AssessmentLesson.objects.filter(
                            lesson__course=course, type="post"
                        ).first()

                        pre_assessment = Assessment.objects.create(
                            name=batch.name + " " + "Pre",
                            participant_view_name=batch.name + " " + "Pre",
                            assessment_type="self",
                            organisation=batch.project.organisation,
                            assessment_timing="pre",
                            unique_id=str(uuid.uuid4()),
                            batch=batch,
                        )
                        pre_assessment.hr.set(batch.project.hr.all())
                        pre_assessment.save()
                        for learner in batch.learners.all():

                            if pre_assessment.participants_observers.filter(
                                participant__email=learner.email
                            ).exists():
                                continue
                            new_participant = create_learner(name, learner.email)
                            if learner.phone:
                                new_participant.phone = learner.phone
                            new_participant.save()
                            mapping = ParticipantObserverMapping.objects.create(
                                participant=new_participant
                            )
                            if learner.phone:
                                add_contact_in_wati(
                                    "learner",
                                    new_participant.name,
                                    new_participant.phone,
                                )
                            unique_id = uuid.uuid4()  # Generate a UUID4
                            # Creating a ParticipantUniqueId instance with a UUID as unique_id
                            unique_id_instance = ParticipantUniqueId.objects.create(
                                participant=new_participant,
                                assessment=pre_assessment,
                                unique_id=unique_id,
                            )
                            mapping.save()
                            pre_assessment.participants_observers.add(mapping)
                            pre_assessment.save()

                        if post_assessment_lesson:
                            pre_assessment.questionnaire = (
                                post_assessment_lesson.assessment_modal.questionnaire
                            )
                            pre_assessment.email_reminder = (
                                post_assessment_lesson.assessment_modal.email_reminder
                            )
                            pre_assessment.whatsapp_reminder = (
                                post_assessment_lesson.assessment_modal.whatsapp_reminder
                            )

                            pre_assessment.save()

                            post_assessment_lesson.assessment_modal.pre_assessment = (
                                pre_assessment
                            )

                            post_assessment_lesson.assessment_modal.save()

                        assessment1.assessment_modal = pre_assessment
                        assessment1.save()

            if not prev_post_assessment == project.post_assessment:
                for batch in batches:
                    course = Course.objects.filter(batch=batch).first()
                    if course:
                        max_order = (
                            Lesson.objects.filter(course=course).aggregate(
                                Max("order")
                            )["order__max"]
                            or 0
                        )
                        lesson1 = Lesson.objects.create(
                            course=course,
                            name="Post Assessment",
                            status="draft",
                            lesson_type="assessment",
                            # Duplicate specific lesson types
                            order=max_order + 1,
                        )
                        assessment1 = AssessmentLesson.objects.create(
                            lesson=lesson1, type="post"
                        )
                        pre_assessment_lesson = AssessmentLesson.objects.filter(
                            lesson__course=course, type="pre"
                        ).first()
                        post_assessment = Assessment.objects.create(
                            name=batch.name + " " + "Post",
                            participant_view_name=batch.name + " " + "Post",
                            assessment_type="self",
                            organisation=batch.project.organisation,
                            assessment_timing="post",
                            unique_id=str(uuid.uuid4()),
                            batch=batch,
                        )
                        post_assessment.hr.set(batch.project.hr.all())
                        post_assessment.save()
                        for learner in batch.learners.all():

                            if post_assessment.participants_observers.filter(
                                participant__email=learner.email
                            ).exists():
                                continue
                            new_participant = create_learner(name, learner.email)
                            if learner.phone:
                                new_participant.phone = learner.phone
                            new_participant.save()
                            mapping = ParticipantObserverMapping.objects.create(
                                participant=new_participant
                            )
                            if learner.phone:
                                add_contact_in_wati(
                                    "learner",
                                    new_participant.name,
                                    new_participant.phone,
                                )
                            unique_id = uuid.uuid4()  # Generate a UUID4
                            # Creating a ParticipantUniqueId instance with a UUID as unique_id
                            unique_id_instance = ParticipantUniqueId.objects.create(
                                participant=new_participant,
                                assessment=post_assessment,
                                unique_id=unique_id,
                            )
                            mapping.save()
                            post_assessment.participants_observers.add(mapping)
                            post_assessment.save()

                        if pre_assessment_lesson:
                            post_assessment.questionnaire = (
                                pre_assessment_lesson.assessment_modal.questionnaire
                            )
                            post_assessment.email_reminder = (
                                pre_assessment_lesson.assessment_modal.email_reminder
                            )
                            post_assessment.whatsapp_reminder = (
                                pre_assessment_lesson.assessment_modal.whatsapp_reminder
                            )
                            post_assessment.pre_assessment = (
                                pre_assessment_lesson.assessment_modal
                            )
                            post_assessment.save()
                        assessment1.assessment_modal = post_assessment
                        assessment1.save()

            if not project.pre_assessment and not project.post_assessment:
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
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to updated project"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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

    learner_id = request.query_params.get("learner_id", None)
    if learner_id:
        queryset = queryset.filter(batch__learners__id=learner_id)

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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
                    "pre_study",
                    "virtual_session",
                ]:
                    session_number = (
                        LiveSession.objects.filter(
                            batch=batch, session_type=session_type
                        ).count()
                        + 1
                    )

                    if session_type == "pre_study":
                        facilitator = Facilitator.objects.filter(
                            email=env("PRE_STUDY_FACILITATOR")
                        ).first()

                        live_session = LiveSession.objects.create(
                            batch=batch,
                            live_session_number=session_number,
                            order=new_session["order"],
                            duration=new_session["duration"],
                            session_type=session_type,
                            facilitator=facilitator,
                        )
                    else:
                        live_session = LiveSession.objects.create(
                            batch=batch,
                            live_session_number=session_number,
                            order=new_session["order"],
                            duration=new_session["duration"],
                            session_type=session_type,
                        )
                    create_task(
                        {
                            "task": "add_session_details",
                            "schedular_project": batch.project.id,
                            "project_type": "skill_training",
                            "live_session": live_session.id,
                            "priority": "medium",
                            "status": "pending",
                            "remarks": [],
                        },
                        3,
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
                        elif live_session.session_type == "pre_study":
                            session_name = "Pre Study"
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
                elif session_type in [
                    "laser_coaching_session",
                    "mentoring_session",
                    "action_coaching_session",
                ]:
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
                    create_task(
                        {
                            "task": "add_dates",
                            "schedular_project": batch.project.id,
                            "project_type": "skill_training",
                            "coaching_session": coaching_session.id,
                            "priority": "medium",
                            "status": "pending",
                            "remarks": [],
                        },
                        7,
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
                        elif coaching_session.session_type == "action_coaching_session":
                            session_name = "Action Coaching Session"
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
@permission_classes(
    [
        IsAuthenticated,
        IsInRoles("pmo", "hr", "facilitator", "coach", "leanrer", "sales"),
    ]
)
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
                    "pre_study",
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

                elif session_type in [
                    "laser_coaching_session",
                    "mentoring_session",
                    "action_coaching_session",
                ]:
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
                    "pre_study",
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

                elif session_type in [
                    "laser_coaching_session",
                    "mentoring_session",
                    "action_coaching_session",
                ]:
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "hr", "facilitator", "coach", "learner"),
    ]

    def get(self, request, project_id):
        try:
            batches = SchedularBatch.objects.filter(project__id=project_id)
            all_coaches = {}
            all_facilitators = {}
            purchase_orders = PurchaseOrderGetSerializer(
                PurchaseOrder.objects.filter(
                    Q(created_time__year__gte=2024)
                    | Q(purchaseorder_number__in=purchase_orders_allowed)
                ),
                many=True,
            ).data
            # filter_purchase_order_data(PurchaseOrderGetSerializer(PurchaseOrder.objects.all(), many=True).data)
            # fetch_purchase_orders(organization_id)
            for batch in batches:
                coaches_data = []
                for coach in batch.coaches.all():
                    coach_data = all_coaches.get(coach.id)
                    if not coach_data:
                        coach_data = CoachSerializer(coach).data
                        coach_data["batchNames"] = set()
                        all_coaches[coach.id] = coach_data
                    coach_data["batchNames"].add(batch.name)

                facilitators_data = []
                for facilitator in Facilitator.objects.filter(
                    livesession__batch=batch
                ).annotate(
                    is_vendor=Case(
                        When(user__vendor__isnull=False, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField(),
                    ),
                    vendor_id=Case(
                        When(
                            user__vendor__isnull=False,
                            then=F("user__vendor__vendor_id"),
                        ),
                        default=None,
                        output_field=CharField(max_length=255, null=True),
                    ),
                ):
                    facilitator_data = all_facilitators.get(facilitator.id)
                    if not facilitator_data:

                        facilitator_data = FacilitatorSerializer(facilitator).data
                        facilitator_data["batchNames"] = set()
                        try:
                            expense = Expense.objects.filter(
                                batch=batch, facilitator__id=facilitator_data["id"]
                            ).first()

                            facilitator_data["purchase_order_id"] = (
                                expense.purchase_order_id
                            )
                            facilitator_data["purchase_order_no"] = (
                                expense.purchase_order_no
                            )
                            is_delete_purchase_order_allowed = True
                            if facilitator_data["purchase_order_id"]:
                                purchase_order = get_purchase_order(
                                    purchase_orders,
                                    facilitator_data["purchase_order_id"],
                                )
                                if not purchase_order:
                                    Expense.objects.filter(
                                        batch=batch,
                                        facilitator__id=facilitator_data["id"],
                                    ).update(purchase_order_id="", purchase_order_no="")
                                    facilitator_data["purchase_order_id"] = None
                                    facilitator_data["purchase_order_no"] = None
                                else:
                                    invoices = InvoiceData.objects.filter(
                                        purchase_order_id=facilitator_data[
                                            "purchase_order_id"
                                        ]
                                    )
                                    if invoices.exists():
                                        is_delete_purchase_order_allowed = False
                                facilitator_data["is_delete_purchase_order_allowed"] = (
                                    is_delete_purchase_order_allowed
                                )
                                facilitator_data["purchase_order"] = purchase_order
                            else:
                                facilitator_data["purchase_order"] = None
                        except Exception as e:
                            print(str(e))
                        all_facilitators[facilitator.id] = facilitator_data
                    facilitator_data["batchNames"].add(batch.name)
            return Response(
                {
                    "unique_coaches": list(all_coaches.values()),
                    "unique_facilitator": list(all_facilitators.values()),
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
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "hr", "facilitator", "coach", "leanrer"),
    ]

    def get(self, request, project_id):
        try:
            batches = SchedularBatch.objects.filter(project__id=project_id)
            facilitator_id = request.query_params.get("facilitator_id")

            if facilitator_id:
                batches = SchedularBatch.objects.filter(
                    livesession__facilitator__id=facilitator_id
                )
            learner_data_dict = {}

            for batch in batches:
                for learner in batch.learners.all():
                    learner_id = learner.id
                    if learner_id not in learner_data_dict:
                        learner_data_dict[learner_id] = {
                            "id": learner_id,
                            "name": learner.name,
                            "email": learner.email,
                            "batchNames": set(),
                            "phone": learner.phone,
                        }
                        learner_data_dict[learner_id]["batchNames"].add(batch.name)
                    else:
                        learner_data_dict[learner_id]["batchNames"].add(batch.name)

            unique_learner_data = [
                {**data, "batchNames": list(data["batchNames"])}  # Convert set to list
                for data in learner_data_dict.values()
            ]

            return Response(unique_learner_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to get learners data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
@permission_classes(
    [IsAuthenticated, IsInRoles("pmo", "hr", "facilitator", "coach", "leanrer")]
)
def coach_inside_skill_training_or_not(request, project_id, batch_id):
    try:
        if batch_id == "all":
            sessions = SchedularSessions.objects.filter(
                coaching_session__batch__project__id=project_id
            )
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
@permission_classes(
    [IsAuthenticated, IsInRoles("pmo", "coach", "facilitator", "hr", "learner")]
)
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
                        "action_coaching_session",
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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


def calculate_nps_from_answers(answers):
    ratings = [answer.rating for answer in answers]
    if ratings:
        return calculate_nps(ratings)
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "hr")])
def get_skill_dashboard_card_data(request, project_id):
    try:
        virtual_nps = 0
        overall_nps = 0
        in_person_nps = 0
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
            if hr_id:
                ongoing_assessment = ongoing_assessment.filter(hr__id=hr_id)

            completed_assessments = Assessment.objects.filter(
                assessment_modal__isnull=False, status="completed"
            )
            if hr_id:
                completed_assessments = completed_assessments.filter(hr__id=hr_id)

            if not hr_id:
                virtual_session_answer = Answer.objects.filter(
                    question__type="rating_0_to_10",
                    question__feedbacklesson__live_session__session_type="virtual_session",
                )
                virtual_nps = calculate_nps_from_answers(virtual_session_answer)

                # In-person session NPS calculation
                in_person_session_answer = Answer.objects.filter(
                    question__type="rating_0_to_10",
                    question__feedbacklesson__live_session__session_type="in_person_session",
                )
                in_person_nps = calculate_nps_from_answers(in_person_session_answer)

                # Overall NPS calculation
                overall_answer = Answer.objects.filter(
                    question__type="rating_0_to_10",
                )
                overall_nps = calculate_nps_from_answers(overall_answer)

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
            if not hr_id:
                virtual_session_answer = Answer.objects.filter(
                    question__type="rating_0_to_10",
                    question__feedbacklesson__live_session__session_type="virtual_session",
                    question__feedbacklesson__live_session__batch__project__id=int(
                        project_id
                    ),
                )

                virtual_nps = calculate_nps_from_answers(virtual_session_answer)

                # In-person session NPS calculation
                in_person_session_answer = Answer.objects.filter(
                    question__type="rating_0_to_10",
                    question__feedbacklesson__live_session__session_type="in_person_session",
                    question__feedbacklesson__live_session__batch__project__id=int(
                        project_id
                    ),
                )
                in_person_nps = calculate_nps_from_answers(in_person_session_answer)

                # Overall NPS calculation
                overall_answer = Answer.objects.filter(
                    question__type="rating_0_to_10",
                    question__feedbacklesson__live_session__batch__project__id=int(
                        project_id
                    ),
                )
                overall_nps = calculate_nps_from_answers(overall_answer)

        return Response(
            {
                "today_coaching_sessions": len(today_sessions),
                "today_live_sessions": len(today_live_sessions),
                "ongoing_assessments": len(ongoing_assessment),
                "completed_assessments": len(completed_assessments),
                "virtual_session_nps": virtual_nps,
                "in_person_session_nps": in_person_nps,
                "overall_nps": overall_nps,
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
def get_skill_dashboard_card_data_for_facilitator(request, project_id, facilitator_id):

    try:
        if project_id == "all":

            virtual_session_answer = Answer.objects.filter(
                question__type="rating_0_to_10",
                question__feedbacklesson__live_session__facilitator__id=facilitator_id,
                question__feedbacklesson__live_session__session_type="virtual_session",
            )
            virtual_nps = calculate_nps_from_answers(virtual_session_answer)

            # In-person session NPS calculation
            in_person_session_answer = Answer.objects.filter(
                question__type="rating_0_to_10",
                question__feedbacklesson__live_session__facilitator__id=facilitator_id,
                question__feedbacklesson__live_session__session_type="in_person_session",
            )
            in_person_nps = calculate_nps_from_answers(in_person_session_answer)

            # Overall NPS calculation
            overall_answer = Answer.objects.filter(
                question__type="rating_0_to_10",
                question__feedbacklesson__live_session__facilitator__id=facilitator_id,
            )
            overall_nps = calculate_nps_from_answers(overall_answer)

        else:

            virtual_session_answer = Answer.objects.filter(
                question__type="rating_0_to_10",
                question__feedbacklesson__live_session__facilitator__id=facilitator_id,
                question__feedbacklesson__live_session__session_type="virtual_session",
                question__feedbacklesson__live_session__batch__project__id=int(
                    project_id
                ),
            )
            virtual_nps = calculate_nps_from_answers(virtual_session_answer)

            # In-person session NPS calculation
            in_person_session_answer = Answer.objects.filter(
                question__type="rating_0_to_10",
                question__feedbacklesson__live_session__facilitator__id=facilitator_id,
                question__feedbacklesson__live_session__session_type="in_person_session",
                question__feedbacklesson__live_session__batch__project__id=int(
                    project_id
                ),
            )
            in_person_nps = calculate_nps_from_answers(in_person_session_answer)

            # Overall NPS calculation
            overall_answer = Answer.objects.filter(
                question__type="rating_0_to_10",
                question__feedbacklesson__live_session__facilitator__id=facilitator_id,
                question__feedbacklesson__live_session__batch__project__id=int(
                    project_id
                ),
            )
            overall_nps = calculate_nps_from_answers(overall_answer)

        return Response(
            {
                "virtual_session_nps": virtual_nps,
                "in_person_session_nps": in_person_nps,
                "overall_nps": overall_nps,
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "hr")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "hr")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "hr")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "hr")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def add_facilitator_to_batch(request, batch_id):
    try:
        batch = SchedularBatch.objects.get(id=batch_id)

        facilitator_id = request.data.get("facilitator_id", "")
        facilitator = Facilitator.objects.get(id=facilitator_id)

        live_sessions = LiveSession.objects.filter(batch=batch)
        for live_session in live_sessions:
            live_session.facilitator = facilitator
            live_session.save()

        try:
            tasks = Task.objects.filter(
                task="add_facilitator", status="pending", schedular_batch=batch
            )
            tasks.update(status="complete")
        except Exception as e:
            print(str(e))

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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
            "pre_study",
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
        elif session_type in [
            "laser_coaching_session",
            "mentoring_session",
            "action_coaching_session",
        ]:
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

                temp = {
                    "participant_name": participant.name,
                    "Email": participant.email,
                    "batch_name": batch.name,
                }

                pre_participant_response = ParticipantResponse.objects.filter(
                    assessment=pre_assessment, participant=participant
                ).first()
                post_participant_response = ParticipantResponse.objects.filter(
                    assessment=post_assessment, participant=participant
                ).first()

                if project and project.pre_assessment:
                    temp["pre_assessment"] = "Yes" if pre_participant_response else "No"

                for session in project.project_structure:
                    session_type = session["session_type"]
                    if session_type in [
                        "live_session",
                        "check_in_session",
                        "in_person_session",
                        "pre_study",
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
                        "action_coaching_session",
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

                if project and project.post_assessment:
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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
                    "pre_study",
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
                    "action_coaching_session",
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def get_facilitators_and_pricing_for_project(request, project_id):
    try:
        facilitators = Facilitator.objects.filter(
            livesession__batch__project__id=project_id
        ).distinct()
        facilitators_pricing = FacilitatorPricing.objects.filter(project__id=project_id)
        facilitators_data = []
        purchase_orders = PurchaseOrderGetSerializer(
            PurchaseOrder.objects.filter(
                Q(created_time__year__gte=2024)
                | Q(purchaseorder_number__in=purchase_orders_allowed)
            ),
            many=True,
        ).data
        # filter_purchase_order_data(PurchaseOrderGetSerializer(PurchaseOrder.objects.all(), many=True).data)
        # fetch_purchase_orders(organization_id)
        for facilitator in facilitators:
            serializer = FacilitatorBasicDetailsSerializer(facilitator)
            is_vendor = facilitator.user.roles.filter(name="vendor").exists()
            vendor_id = None
            if is_vendor:
                vendor_id = Vendor.objects.get(user=facilitator.user).vendor_id
            facilitator_data = serializer.data
            pricing = facilitators_pricing.filter(facilitator__id=facilitator.id)
            is_delete_purchase_order_allowed = True
            purchase_order = None
            if pricing.exists():
                first_pricing = pricing.first()
                if first_pricing.purchase_order_id:
                    purchase_order = get_purchase_order(
                        purchase_orders, first_pricing.purchase_order_id
                    )
                    # when no po found remove po number and id from fac. pricings
                    if not purchase_order:
                        first_pricing.purchase_order_id = ""
                        first_pricing.purchase_order_no = ""
                        first_pricing.save()
                    else:
                        invoices = InvoiceData.objects.filter(
                            purchase_order_id=first_pricing.purchase_order_id
                        )
                        if invoices.exists():
                            is_delete_purchase_order_allowed = False
                pricing_serializer = FacilitatorPricingSerializer(first_pricing)
            else:
                pricing_serializer = None
            facilitator_data["pricing_details"] = (
                pricing_serializer.data if pricing_serializer else None
            )
            facilitator_data["is_delete_purchase_order_allowed"] = (
                is_delete_purchase_order_allowed
            )
            facilitator_data["vendor_id"] = vendor_id
            facilitator_data["purchase_order"] = purchase_order
            facilitators_data.append(facilitator_data)
        return Response(facilitators_data)
    except Exception as e:
        print(str(e))
        return Response(status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def get_coaches_and_pricing_for_project(request, project_id):
    try:
        coaches = Coach.objects.filter(
            schedularbatch__project__id=project_id
        ).distinct()
        coaches_data = []
        purchase_orders = PurchaseOrderGetSerializer(
            PurchaseOrder.objects.filter(
                Q(created_time__year__gte=2024)
                | Q(purchaseorder_number__in=purchase_orders_allowed)
            ),
            many=True,
        ).data
        # filter_purchase_order_data(PurchaseOrderGetSerializer(PurchaseOrder.objects.all(), many=True).data)
        # fetch_purchase_orders(organization_id)
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
            is_delete_purchase_order_allowed = True
            if pricing.exists():
                first_pricing = pricing.first()
                if first_pricing.purchase_order_id:
                    purchase_order = get_purchase_order(
                        purchase_orders, first_pricing.purchase_order_id
                    )
                    if not purchase_order:
                        CoachPricing.objects.filter(
                            purchase_order_id=first_pricing.purchase_order_id
                        ).update(purchase_order_id="", purchase_order_no="")
                    else:
                        invoices = InvoiceData.objects.filter(
                            purchase_order_id=first_pricing.purchase_order_id
                        )
                        if invoices.exists():
                            is_delete_purchase_order_allowed = False
                pricing_serializer = CoachPricingSerializer(pricing.first())
            else:
                pricing_serializer = None
            coach_data["pricing_details"] = (
                pricing_serializer.data if pricing_serializer else None
            )
            coach_data["is_delete_purchase_order_allowed"] = (
                is_delete_purchase_order_allowed
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
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def add_facilitator_pricing(request):
    serializer = FacilitatorPricingSerializer(data=request.data)
    if serializer.is_valid():
        facilitator_pricing = serializer.save()
        create_task(
            {
                "task": "create_purchase_order_facilitator",
                "schedular_project": facilitator_pricing.project.id,
                "facilitator": facilitator_pricing.facilitator.id,
                "project_type": "skill_training",
                "priority": "low",
                "status": "pending",
                "remarks": [],
            },
            7,
        )
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def edit_facilitator_pricing(request, facilitator_pricing_id):
    try:
        pricing_instance = get_object_or_404(
            FacilitatorPricing, id=facilitator_pricing_id
        )
        pricing_instance.price = request.data.get("price")
        pricing_instance.save()
        serializer = FacilitatorPricingSerializer(pricing_instance)

        return Response(serializer.data, status=200)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to create expense"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "facilitator", "coach")])
def create_expense(request):
    try:
        with transaction.atomic():
            name = request.data.get("name")
            description = request.data.get("description")
            date_of_expense = request.data.get("date_of_expense")
            live_session = request.data.get("live_session")
            session = request.data.get("session")
            coach = request.data.get("coach")
            batch = request.data.get("batch")
            facilitator = request.data.get("facilitator")
            file = request.data.get("file")
            amount = request.data.get("amount")
            if not file:
                return Response(
                    {"error": "Please upload file."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if not session and (not batch or not facilitator):
                return Response(
                    {"error": "Failed to create expense."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            email_name = None
            expense_name = None
            project_name = None

            if name and date_of_expense and description and amount:
                if session:
                    session = SessionRequestCaas.objects.get(id=int(session))
                    coach = Coach.objects.get(id=int(coach))
                    expense = Expense.objects.create(
                        name=name,
                        description=description,
                        date_of_expense=date_of_expense,
                        session=session,
                        coach=coach,
                        file=file,
                        amount=amount,
                    )
                    email_name = f"{coach.first_name} {coach.last_name}"
                    expense_name = expense.name
                    project_name = session.project.name

                else:

                    facilitator = Facilitator.objects.get(id=int(facilitator))
                    batch = SchedularBatch.objects.get(id=int(batch))
                    if live_session:
                        live_session = LiveSession.objects.filter(
                            id=int(live_session)
                        ).first()
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

                    email_name = f"{facilitator.first_name} {facilitator.last_name}"
                    expense_name = expense.name
                    project_name = expense.batch.project.name

                try:
                    emails = [
                        "madhuri@coachtotransformation.com",
                        "nisha@coachtotransformation.com",
                        "pmotraining@meeraq.com",
                        "pmocoaching@meeraq.com",
                    ]
                    if batch.project.junior_pmo:
                        emails.append(batch.project.junior_pmo.email)

                    send_mail_templates(
                        "expenses/expenses_emails.html",
                        emails,
                        (
                            "Verification Required: Coaches Expenses"
                            if session
                            else "Verification Required: Facilitators Expenses"
                        ),
                        {
                            "facilitator_name": email_name,
                            "expense_name": expense_name,
                            "project_name": project_name,
                            "description": expense.description,
                            "amount": expense.amount,
                        },
                    )

                    email_array = json.loads(env("EXPENSE_NOTIFICATION_EMAILS"))
                    if batch.project.junior_pmo:
                        email_array.append(batch.project.junior_pmo.email)
                    for email in email_array:
                        pmo = Pmo.objects.filter(email=email.strip().lower()).first()
                        send_mail_templates(
                            (
                                "pmo_emails/expense_added_by_coach.html"
                                if session
                                else "pmo_emails/expense_added_by_facilitator.html"
                            ),
                            [email],
                            "Meeraq | Expense Upload Notification",
                            {
                                "name": pmo.name if pmo else "User",
                                "project_name": project_name,
                                "facilitator_name": email_name,
                                "description": expense.description,
                                "amount": expense.amount,
                                "date_of_expense": expense.created_at.strftime(
                                    "%d/%m/%Y"
                                ),
                            },
                            [],
                        )
                        sleep(2)
                except Exception as e:
                    print(str(e))

                return Response(
                    {"message": "Expense created successfully!"}, status=201
                )
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
@permission_classes([IsAuthenticated, IsInRoles("pmo", "facilitator")])
def edit_expense(request):
    try:
        data = request.data
        expense_id = data.get("expense_id")

        # Ensure all required fields are present
        required_fields = ["name", "description", "date_of_expense", "file"]
        if not all(field in data for field in required_fields):
            return Response(
                {"error": "Please provide all required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expense = Expense.objects.get(id=int(expense_id))

        # Update expense object
        expense.name = data["name"]
        expense.description = data["description"]
        expense.date_of_expense = data["date_of_expense"]

        # Fetch related instances if provided
        session_id = data.get("session")
        if session_id:
            expense.session = SessionRequestCaas.objects.get(id=int(session_id))
            expense.coach = None
        else:
            expense.live_session = LiveSession.objects.filter(
                id=int(data.get("live_session"))
            ).first()
            expense.batch = SchedularBatch.objects.get(id=int(data.get("batch")))
            expense.facilitator = Facilitator.objects.get(
                id=int(data.get("facilitator"))
            )

        # Update file if provided
        if data["file"] != "null":
            expense.file = data["file"]

        expense.save()

        return Response(
            {"message": "Expense updated successfully!"}, status=status.HTTP_200_OK
        )

    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to update expense."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo", "facilitator")])
def get_expense_for_facilitator(request, batch_or_project_id, usertype, user_id):
    try:
        is_all_batch = request.query_params.get("is_all_batch")
        if is_all_batch:
            batches = SchedularBatch.objects.filter(project__id=batch_or_project_id)
        else:
            batches = SchedularBatch.objects.filter(id=batch_or_project_id)

        all_expenses = []
        for batch in batches:
            if usertype == "facilitator":
                expenses = Expense.objects.filter(batch=batch, facilitator__id=user_id)
            elif usertype == "pmo":
                expenses = Expense.objects.filter(batch=batch)

            all_expenses.extend(expenses)

        po_ids = []  # po ids
        for expense in all_expenses:
            if expense.purchase_order_id:
                po_ids.append(expense.purchase_order_id)
        po_ids_str = ",".join(po_ids)
        purchase_orders = PurchaseOrderGetSerializer(
            PurchaseOrder.objects.filter(
                Q(created_time__year__gte=2024)
                | Q(purchaseorder_number__in=purchase_orders_allowed),
                Q(purchaseorder_id__in=po_ids),
            ),
            many=True,
        ).data
        # filter_purchase_order_data(PurchaseOrderGetSerializer(PurchaseOrder.objects.filter(purchaseorder_id__in=po_ids), many=True).data)
        # fetch_purchase_orders(
        #     organization_id, f"&purchaseorder_ids={po_ids_str}"
        # )
        serializer = ExpenseSerializerDepthOne(all_expenses, many=True)
        for expense in serializer.data:
            if expense["purchase_order_id"]:
                expense["purchase_order"] = get_purchase_order(
                    purchase_orders, expense["purchase_order_id"]
                )
            else:
                expense["purchase_order"] = None
        return Response(serializer.data)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get expense"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_courses_for_all_batches(request, project_id):
    try:
        facilitator_id = request.query_params.get("facilitator_id", None)
        batches = SchedularBatch.objects.filter(
            livesession__facilitator__id=facilitator_id, project__id=project_id
        )
        courses = Course.objects.filter(batch__in=batches)
        course_serializer = CourseSerializer(courses, many=True)
        return Response(course_serializer.data)
    except SchedularBatch.DoesNotExist:
        return Response(
            {"error": "Couldn't find batches with the specified facilitator."},
            status=400,
        )
    except Course.DoesNotExist:
        return Response(
            {"error": "Couldn't find courses for the specified batch and facilitator."},
            status=400,
        )
    except Exception as e:
        print(str(e))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_card_data_for_coach_in_skill_project(request, project_id, coach_id):
    try:
        project = SchedularProject.objects.get(id=project_id)
        coach = Coach.objects.get(id=coach_id)

        # Count total laser coaching sessions and mentoring sessions
        session_counts = (
            CoachingSession.objects.filter(batch__coaches=coach, batch__project=project)
            .values("session_type")
            .annotate(count=Count("id"))
        )

        total_laser_coaching_session = sum(
            s["count"]
            for s in session_counts
            if s["session_type"] == "laser_coaching_session"
        )
        total_mentoring_session = sum(
            s["count"]
            for s in session_counts
            if s["session_type"] == "mentoring_session"
        )
        print(total_laser_coaching_session)
        # Get merged dates for coaching sessions
        batches = SchedularBatch.objects.filter(project=project)
        merged_dates = get_merged_date_of_coaching_session_for_a_batches(batches)
        first_start_date = merged_dates[0][0] if merged_dates else None
        last_end_date = merged_dates[-1][1] if merged_dates else None

        # Convert dates to datetime objects
        first_start_datetime = (
            datetime.combine(first_start_date, datetime.min.time())
            if first_start_date
            else None
        )
        last_end_datetime = (
            datetime.combine(last_end_date, datetime.min.time())
            if last_end_date
            else None
        )

        # Get timestamps for start and end dates
        start_timestamp = (
            first_start_datetime.timestamp() * 1000 if first_start_datetime else None
        )
        end_timestamp = (
            (last_end_datetime + timedelta(days=1)).timestamp() * 1000
            if last_end_datetime
            else None
        )

        avaliable_solts = []

        if start_timestamp and end_timestamp:
            # Count available slots
            avaliable_solts = CoachSchedularAvailibilty.objects.filter(
                coach=coach,
                start_time__gte=start_timestamp,
                end_time__lte=end_timestamp,
                is_confirmed=False,
            )

        booked_slots = SchedularSessions.objects.filter(
            Q(coaching_session__batch__coaches=coach)
            | Q(coaching_session__batch__coaches__isnull=True),
            Q(coaching_session__batch__project=project)
            | Q(coaching_session__batch__project__isnull=True),
            status="pending",
        ).count()

        # Count completed sessions
        completed_sessions = SchedularSessions.objects.filter(
            Q(coaching_session__batch__coaches=coach)
            | Q(coaching_session__batch__coaches__isnull=True),
            Q(coaching_session__batch__project=project)
            | Q(coaching_session__batch__project__isnull=True),
            status="completed",
        ).count()

        return Response(
            {
                "total_laser_coaching_session": total_laser_coaching_session,
                "total_mentoring_session": total_mentoring_session,
                "first_start_date": (
                    first_start_date.strftime("%d-%m-%Y") if first_start_date else None
                ),
                "last_end_date": (
                    last_end_date.strftime("%d-%m-%Y") if last_end_date else None
                ),
                "available_slots": len(avaliable_solts),
                "booked_slots": booked_slots,
                "completed_sessions": completed_sessions,
            },
            status=200,
        )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": f"Failed to get data."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInRoles("pmo")])
def check_if_project_structure_edit_allowed(request, project_id):
    try:
        current_time_seeq = timezone.now()
        is_allowed = True
        past_live_sessions = LiveSession.objects.filter(
            date_time__lt=current_time_seeq, batch__project__id=project_id
        )
        scheduler_sessions = SchedularSessions.objects.filter(
            coaching_session__batch__project__id=project_id
        )
        if past_live_sessions.exists():
            is_allowed = False
        elif scheduler_sessions.exists():
            is_allowed = False
        return Response({"is_allowed_to_edit": is_allowed})
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get details"}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_coaching_and_live_session_data_for_learner(request, user_id):
    current_time_seeq = timezone.now()
    timestamp_milliseconds = str(int(current_time_seeq.timestamp() * 1000))
    learner = Learner.objects.get(id=user_id)
    schedular_sessions = SchedularSessions.objects.filter(learner=learner)
    available_sessions = schedular_sessions.filter(
        availibility__end_time__gt=timestamp_milliseconds
    )
    live_sessions = LiveSession.objects.filter(
        batch__learners__id=user_id, date_time__gt=current_time_seeq
    )
    upcoming_sessions_data = []

    # LIVE SESSION
    for live_session in live_sessions:
        project_name = live_session.batch.project.name
        session_name = f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}"
        facilitator_names = (
            f"{live_session.facilitator.first_name} {live_session.facilitator.last_name}"
            if live_session.facilitator
            else []
        )
        session_timing = live_session.date_time
        room_id = live_session.meeting_link
        session_data = {
            "project_name": project_name,
            "session_name": session_name,
            "coach_name": facilitator_names,
            "session_timing": session_timing,
            "type": "Live Session",
            "room_id": room_id,
            "start_time": "",
            "end_time": "",
        }
        upcoming_sessions_data.append(session_data)

    # COACHING SESSION
    for available_session in available_sessions:
        project_name = available_session.coaching_session.batch.project.name
        session_name = available_session.coaching_session.session_type
        session_type = available_session.coaching_session.session_type
        session_timing = available_session.availibility.start_time
        coach_name = (
            available_session.availibility.coach.first_name
            + " "
            + available_session.availibility.coach.last_name
        )
        room_id = f"{available_session.availibility.coach.room_id}"
        start_time = available_session.availibility.start_time
        end_time = available_session.availibility.end_time
        session_data = {
            "project_name": project_name,
            "session_name": session_name,
            "coach_name": coach_name,
            "session_timing": session_timing,
            "type": "Coaching Session",
            "room_id": room_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        upcoming_sessions_data.append(session_data)

    return JsonResponse(upcoming_sessions_data, safe=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_assessment_data(request, user_id):
    try:
        current_time = timezone.now()
        upcoming_assessment = Assessment.objects.filter(
            assessment_start_date__gt=current_time,
            participants_observers__participant__id=user_id,
        ).first()

        if upcoming_assessment:
            assessment_data = {
                "assessment_name": upcoming_assessment.participant_view_name,
                "assessment_type": upcoming_assessment.assessment_type,
                "assessment_start_date": upcoming_assessment.assessment_start_date,
            }
            return Response(assessment_data)
        else:
            return Response({"message": "No upcoming assessment found."}, status=400)

    except Exception as e:
        return Response({"message": f"An error occurred: {str(e)}"}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_just_upcoming_session_data(request, user_id):
    try:
        current_time = int(timezone.now().timestamp() * 1000)
        learner = Learner.objects.get(id=user_id)
        sessions = SchedularSessions.objects.filter(
            availibility__end_time__gt=current_time,
            learner=learner,
        ).order_by("availibility__start_time")
        upcoming_session = sessions.first()

        # You can customize the response based on whether an upcoming session is found or not
        if upcoming_session:
            # Customize the response data according to your requirement
            response_data = {
                "session_id": upcoming_session.id,
                "start_time": upcoming_session.availibility.start_time,
                "session_type": upcoming_session.coaching_session.session_type,
                "session_number": upcoming_session.coaching_session.coaching_session_number,
                # Add more fields as needed
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "No upcoming sessions found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Learner.DoesNotExist:
        return Response(
            {"message": "Learner not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_project_purchase_orders_for_finance(request, project_id, project_type):
    try:
        # filter_purchase_order_data(PurchaseOrderGetSerializer(PurchaseOrder.objects.all(), many=True).data)
        # fetch_purchase_orders(organization_id)
        if (
            project_type == "skill_training"
            or project_type == "SEEQ"
            or project_type == "assessment"
        ):
            purchase_orders = PurchaseOrderGetSerializer(
                PurchaseOrder.objects.filter(
                    Q(created_time__year__gte=2024)
                    | Q(purchaseorder_number__in=purchase_orders_allowed),
                    Q(schedular_project__id=project_id),
                ),
                many=True,
            ).data
        elif project_type == "CAAS" or project_type == "COD":
            purchase_orders = PurchaseOrderGetSerializer(
                PurchaseOrder.objects.filter(
                    Q(created_time__year__gte=2024)
                    | Q(purchaseorder_number__in=purchase_orders_allowed),
                    Q(caas_project__id=project_id),
                ),
                many=True,
            ).data
        return Response(purchase_orders)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_and_handover(request):
    project_id = request.GET.get("project_id")
    handover_id = request.GET.get("handover_id")
    project_type = request.GET.get("project_type")
    if project_id:
        try:
            if project_type == "skill_training" or project_type == "assessment":
                project = SchedularProject.objects.get(id=project_id)
                project_serializer = SchedularProjectSerializer(project)
                handover_details = HandoverDetails.objects.filter(
                    schedular_project=project
                )
            elif project_type == "CAAS" or project_type == "COD":
                project = Project.objects.get(id=project_id)
                project_serializer = ProjectSerializer(project)
                handover_details = HandoverDetails.objects.filter(caas_project=project)
            else:
                return Response({"error": "Invalid project type"}, status=400)
        except (SchedularProject.DoesNotExist, Project.DoesNotExist):
            return Response({"error": "Project not found"}, status=404)

        handover_serializer = None
        if handover_details.exists():
            handover_serializer = HandoverDetailsSerializer(handover_details.first())

        return Response(
            {
                "project": project_serializer.data,
                "handover": handover_serializer.data if handover_serializer else None,
                "project_type": project_type,
            }
        )
    elif handover_id:
        try:
            handover = HandoverDetails.objects.get(id=handover_id)
        except HandoverDetails.DoesNotExist:
            return Response({"error": "Handover details not found"}, status=404)

        if handover.schedular_project:
            project_serializer = SchedularProjectSerializer(handover.schedular_project)
            project_type = "skill_training"
        elif handover.caas_project:
            project_serializer = ProjectSerializer(handover.caas_project)
            project_type = "caas"
        else:
            project_type = None
            project_serializer = None
        handover_serializer = HandoverDetailsSerializer(handover)
        return Response(
            {
                "project": project_serializer.data if project_serializer else None,
                "handover": handover_serializer.data,
                "project_type": project_type,
            }
        )
    else:
        return Response({"error": "Invalid query parameters"}, status=400)


def get_formatted_handovers(handovers):
    try:
        serializer = HandoverDetailsSerializerWithOrganisationName(handovers, many=True)
        for handover in serializer.data:
            sales_order_ids = handover["sales_order_ids"]
            salesorders = SalesOrder.objects.filter(salesorder_id__in=sales_order_ids)
            salespersons = []
            added_salespersons = (
                set()
            )  # Keep track of added salespersons for each handover
            for salesorder in salesorders:
                sales_person_name = salesorder.salesperson_name
                if sales_person_name:
                    # Check if sales person has already been added for this handover
                    if sales_person_name not in added_salespersons:
                        sales = Sales.objects.filter(
                            sales_person_id=salesorder.salesperson_id
                        ).first()
                        salespersons.append(
                            {
                                "salesperson_id": salesorder.salesperson_id,
                                "salesperson_name": salesorder.salesperson_name,
                                "salesperson_email": sales.email if sales else None,
                            }
                        )
                        added_salespersons.add(
                            sales_person_name
                        )  # Add the sales person to the set of added salespersons
            handover["salespersons"] = salespersons
        return serializer.data
    except Exception as e:
        print(str(e))
        raise Exception("Failed to get formatted handovers")


# def get_formatted_handovers(handovers):
#     try:
#         sales_order_ids_list = []
#         for handover in handovers:
#             for sales_order_id in handover.sales_order_ids:
#                 sales_order_ids_list.append(sales_order_id)
#         sales_order_ids_str = ",".join(map(str, sales_order_ids_list))
#         serializer = HandoverDetailsSerializerWithOrganisationName(handovers, many=True)
#         # Fetch sales orders for the given sales order IDs
#         if sales_order_ids_str:
#             sales_orders = SalesOrderGetSerializer(SalesOrder.objects.all(),many=True).data
#             # fetch_sales_orders(
#             #     organization_id, f"&salesorder_ids={sales_order_ids_str}"
#             # )
#             if not sales_orders:
#                 raise Exception("Failed to get sales orders.")
#             # Create a dictionary to map sales order ID to sales person ID
#             sales_order_to_sales_person = {
#                 sales_order["salesorder_id"]: sales_order["salesperson_name"]
#                 for sales_order in sales_orders
#             }
#             # Fetch sales persons based on sales person IDs from sales orders
#             sales_persons = fetch_sales_persons(organization_id)
#             if not sales_persons:
#                 raise Exception(
#                     "Failed to get sales persons."
#                 )  # Map sales persons to handovers
#             for handover in serializer.data:
#                 sales_order_ids = handover["sales_order_ids"]
#                 salespersons = []
#                 added_salespersons = (
#                     set()
#                 )  # Keep track of added salespersons for each handover
#                 for sales_order_id in sales_order_ids:
#                     sales_person_name = sales_order_to_sales_person.get(sales_order_id)
#                     if sales_person_name:
#                         # Check if sales person has already been added for this handover
#                         if sales_person_name not in added_salespersons:
#                             for person in sales_persons:
#                                 if person["salesperson_name"] == sales_person_name:
#                                     salespersons.append(person)
#                                     added_salespersons.add(
#                                         sales_person_name
#                                     )  # Add the sales person to the set of added salespersons
#                 handover["salespersons"] = salespersons
#         return serializer.data
#     except Exception as e:
#         print(str(e))
#         raise Exception("Failed to get formatted handovers")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_handovers(request, sales_id):
    try:
        handovers = HandoverDetails.objects.filter(sales__id=sales_id).order_by(
            "-created_at"
        )
        formatted_handovers = get_formatted_handovers(handovers)
        return Response(formatted_handovers, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get handovers."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pmo_handovers(request):
    try:
        handovers = HandoverDetails.objects.filter(
            schedular_project__isnull=True, caas_project__isnull=True, is_drafted=False
        ).order_by("-created_at")
        print(handovers)
        formatted_handovers = get_formatted_handovers(handovers)
        return Response(formatted_handovers, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get handovers."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def max_gmsheet_number(request):
    try:
        # Get the latest gmsheet_number
        latest_gmsheet = GmSheet.objects.latest("created_at")
        latest_number = int(
            latest_gmsheet.gmsheet_number[3:]
        )  # Extract the number part and convert to integer
        next_number = latest_number + 1
        next_gmsheet_number = (
            f"PRO{next_number:03}"  # Format the next number to match 'PRO001' format
        )
    except GmSheet.DoesNotExist:
        # If no GmSheet objects exist, create the first gmsheet_number as 'PRO001'
        next_gmsheet_number = "PRO001"
        # GmSheet.objects.create(gmsheet_number=next_gmsheet_number)

    return JsonResponse({"max_number": next_gmsheet_number})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def max_asset_number(request):
    try:
        # Get the latest gmsheet_number
        latest_asset = Assets.objects.latest("created_at")

        latest_number = int(
            latest_asset.asset_id[3:]
        )  # Extract the number part and convert to integer
        next_number = latest_number + 1
        next_asset_number = (
            f"NUM{next_number:03}"  # Format the next number to match 'PRO001' format
        )
    except Assets.DoesNotExist:
        # If no GmSheet objects exist, create the first gmsheet_number as 'PRO001'
        next_asset_number = "NUM001"
        print(next_asset_number)
    return JsonResponse({"max_number": next_asset_number})


@api_view(["GET"])
def get_employees(request):
    try:
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
        return JsonResponse(serializer.data, safe=False)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Employees not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def create_employee(request):
    serializer = EmployeeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_gmsheet_by_sales(request, sales_person_id):
    try:
        gmsheet = GmSheet.objects.filter(sales__id=sales_person_id).order_by(
            "-created_at"
        )
        serializer = GmSheetSalesOrderExistsSerializer(gmsheet, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get GM Sheets for the specified salesperson."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_employee(request):
    employee_id = request.data.get("id")
    if not employee_id:
        return Response(
            {"error": "Employee ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND
        )

    serializer = EmployeeSerializer(employee, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_employee(request):
    employee_id = request.data.get("id")
    if not employee_id:
        return Response(
            {"error": "Employee ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND
        )

    employee.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_gmsheet(request):
    try:
        gmsheet_id = request.data.get("gmSheetId")
        gmsheet = GmSheet.objects.get(id=gmsheet_id)
        gmsheet.delete()
        return Response(
            {"success": "GM Sheet deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
    except GmSheet.DoesNotExist:
        return Response(
            {"error": "GM Sheet does not exist."}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to delete GM Sheet."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_offerings_by_gmsheet_id(request, gmsheet_id):
    print(gmsheet_id)
    offerings = Offering.objects.filter(gm_sheet=gmsheet_id)
    print(offerings)
    serializer = OfferingSerializer(offerings, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_gmsheet(request):
    try:
        gmsheet = GmSheet.objects.all().order_by("-created_at")
        serializer = GmSheetDetailedSerializer(gmsheet, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get GM Sheet."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_reminder_in_batch(request, batch_id):
    try:
        email_reminder = request.data.get("email_reminder")
        whatsapp_reminder = request.data.get("whatsapp_reminder")
        calendar_invites = request.data.get("calendar_invites")
        batch = SchedularBatch.objects.get(id=batch_id)
        batch.email_reminder = email_reminder
        batch.whatsapp_reminder = whatsapp_reminder
        batch.calendar_invites = calendar_invites
        batch.save()
        return Response({"message": "Reminder Updated successfully!"}, status=200)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_mail_to_coaches(request):
    try:
        template_id = request.data.get("template_id")
        coaches = request.data.get("coaches")
        subject = request.data.get("subject")
        template = EmailTemplate.objects.get(id=template_id)

        temp1 = template.template_data

        for coach_id in coaches:
            coach = Coach.objects.get(id=int(coach_id))
            mail = coach.email
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
                settings.DEFAULT_FROM_EMAIL,
                [mail],
            )
            email.content_subtype = "html"
            email.send()
            sleep(5)
            print("Email sent to:", mail)
        return Response({"message": "Mails Send Successfully!"}, status=200)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to send mail!"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_action_item(request):
    if request.method == "POST":
        serializer = ActionItemSerializer(data=request.data)
        if serializer.is_valid():
            action_item = serializer.save()
            status_updates = (
                [
                    {
                        "status": action_item.initial_status,
                        "updated_at": str(timezone.now()),
                    }
                ]
                if action_item.initial_status
                else []
            )
            action_item.status_updates = status_updates
            action_item.save()
            res_serializer = ActionItemSerializer(action_item)
            return Response(res_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_action_item(request, pk):
    try:
        action_item = ActionItem.objects.get(pk=pk)
    except ActionItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        serializer = ActionItemSerializer(action_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def add_remark_to_action_item(request, pk):
    try:
        action_item = ActionItem.objects.get(pk=pk)
    except ActionItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        remark = request.data.get("remark")
        if not remark:
            return Response(
                {"error": "No remark found"}, status=status.HTTP_400_BAD_REQUEST
            )
        action_item.remarks.append({"text": remark, "created_at": str(timezone.now())})
        action_item.save()
        serializer = ActionItemSerializer(action_item)
        return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_action_item_status(request, pk):
    try:
        action_item = ActionItem.objects.get(pk=pk)
    except ActionItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        new_status = request.data.get("current_status")
        if new_status not in dict(ActionItem.STATUS_CHOICES).keys():
            return Response(
                {"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
            )

        action_item.current_status = new_status
        action_item.status_updates.append(
            {"status": new_status, "updated_at": str(timezone.now())}
        )
        action_item.save()
        serializer = ActionItemSerializer(action_item)
        return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_action_item(request, pk):
    try:
        action_item = ActionItem.objects.get(pk=pk)
    except ActionItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        action_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learner_batches(request, pk):
    try:
        batches = SchedularBatch.objects.filter(
            learners__id=pk, project__is_archive=False
        ).distinct()
        serializer = SchedularBatchSerializer(batches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get batches."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def batch_competencies_and_behaviours(request, batch_id):
    try:
        competency_assignments = BatchCompetencyAssignment.objects.filter(
            batch__id=batch_id
        )
        res = []
        for competency_assignment in competency_assignments:
            competency_serializer = CompetencySerializer(
                competency_assignment.competency
            )
            behaviors_serializer = BehaviorSerializer(
                competency_assignment.selected_behaviors, many=True
            )
            data = competency_serializer.data
            data["behaviors"] = behaviors_serializer.data
            res.append(data)
        return Response(res, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to get competencies."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learner_action_items_in_batch_of_competency_and_behavior(
    request, batch_id, learner_id, competency_id, behavior_id
):
    action_items = ActionItem.objects.filter(
        batch__id=batch_id,
        competency__id=competency_id,
        behavior__id=behavior_id,
        learner__id=learner_id,
    ).order_by("-created_at")
    action_items_serializer = ActionItemSerializer(action_items, many=True)
    return Response(action_items_serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learner_action_items_in_batch(request, batch_id, learner_id):
    action_items = ActionItem.objects.filter(
        batch__id=batch_id, learner__id=learner_id
    ).order_by("-created_at")
    action_items_serializer = ActionItemDetailedSerializer(action_items, many=True)
    return Response(action_items_serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learner_action_items_in_session(request, session_id):
    session = SchedularSessions.objects.get(id=session_id)
    action_items = ActionItem.objects.filter(
        batch__id=session.coaching_session.batch.id, learner__id=session.learner.id
    ).order_by("-created_at")
    action_items_serializer = ActionItemDetailedSerializer(action_items, many=True)
    return Response(action_items_serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def action_items_in_batch(request, batch_id):
    action_items = ActionItem.objects.filter(batch__id=batch_id).order_by("-created_at")
    action_items_serializer = ActionItemDetailedSerializer(action_items, many=True)
    return Response(action_items_serializer.data, status=status.HTTP_200_OK)


status_choices_dict = {
    "not_started": 1,
    "occasionally_doing": 2,
    "regularly_doing": 3,
    "actively_pursuing": 4,
    "consistently_achieving": 5,
}


STATUS_CHOICES = (
    ("not_started", "Not Started"),
    ("occasionally_doing", "Occasionally Doing"),
    ("regularly_doing", "Regularly Doing"),
    ("actively_pursuing", "Actively Pursuing"),
    ("consistently_achieving", "Consistently Achieving"),
)

MOVEMENT_TYPES = {
    0: "No Movement",
    1: "Limited Movement",
    2: "Some Movement",
    3: "Significant Movement",
    4: "Excellent Movement",
}

STATUS_LABELS = {
    "not_started": "Not Started",
    "occasionally_doing": "Occasionally Doing",
    "regularly_doing": "Regularly Doing",
    "actively_pursuing": "Actively Pursuing",
    "consistently_achieving": "Consistently Achieving",
}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def batch_competency_behavior_movement(request, batch_id, competency_id, behavior_id):
    ############### Movement based on current ########################

    # Define initial and current status integer mappings
    initial_status_int = Case(
        *[
            When(initial_status=status, then=Value(status_choices_dict.get(status, 0)))
            for status in status_choices_dict
        ],
        default=Value(0),  # Default value if status not found
        output_field=IntegerField(),
    )
    current_status_int = Case(
        *[
            When(current_status=status, then=Value(status_choices_dict.get(status, 0)))
            for status in status_choices_dict
        ],
        default=Value(0),  # Default value if status not found
        output_field=IntegerField(),
    )

    # Annotate the queryset with the movement between initial and current statuses
    movement_counts = (
        ActionItem.objects.filter(
            batch__id=batch_id, competency__id=competency_id, behavior__id=behavior_id
        )
        .annotate(
            initial_status_int=initial_status_int,
            current_status_int=current_status_int,
            movement=F("current_status_int") - F("initial_status_int"),
        )
        .values("movement")
        .annotate(count=Count("id"))
    )

    # Prepare data for response for movements
    data = [
        {"movement": i, "count": 0}
        for i in range(
            5
        )  # Initialize with default count of 0 for all movements (0 to 4)
    ]
    # Update the counts from the queryset
    for item in movement_counts:
        movement = item["movement"]
        data[movement]["count"] = item["count"]

    ############### Action Item Count ########################

    status_counts_dict = {status[0]: 0 for status in STATUS_CHOICES}

    # Fetch status counts from the database
    status_counts_queryset = (
        ActionItem.objects.filter(
            batch__id=batch_id, competency__id=competency_id, behavior__id=behavior_id
        )
        .values("current_status")
        .annotate(count=Count("id"))
    )

    # Update counts for existing statuses
    for item in status_counts_queryset:
        status_counts_dict[item["current_status"]] = item["count"]

    # Prepare data for response, sorted according to STATUS_CHOICES
    action_item_count = [
        {"status": status, "count": status_counts_dict[status]}
        for status, _ in STATUS_CHOICES
    ]
    ############### Action Item Count - END ########################

    ################ Date Wise Movement ############################

    first_created_item = (
        ActionItem.objects.filter(
            batch__id=batch_id, competency__id=competency_id, behavior__id=behavior_id
        )
        .order_by("created_at")
        .first()
    )
    last_updated_item = (
        ActionItem.objects.filter(
            batch__id=batch_id, competency__id=competency_id, behavior__id=behavior_id
        )
        .order_by("-updated_at")
        .first()
    )

    formatted_data = []
    if first_created_item and last_updated_item:
        # Get start and end dates
        start_date = first_created_item.created_at.date()
        end_date = (
            last_updated_item.updated_at.date()
        )  # Set the end date as the current date

        # Calculate the number of days between start and end dates
        date_difference = (end_date - start_date).days

        # Calculate step value for the date range
        if date_difference < 4:
            step = (
                1  # Keep dates equal to the number of days if difference is less than 4
            )
        else:
            step = date_difference // 4

        # Get dates evenly spaced between start and end dates
        date_range = [
            start_date + timedelta(days=i * step)
            for i in range(min(date_difference, 4) + 1)
        ]

        # Include the current date as the last date in the range
        if end_date not in date_range:
            date_range.append(end_date)

        # Prepare data structure to store movement counts for each date
        date_data = {}

        for date in date_range:
            # Get action items created before or on the mapped date
            filtered_items = ActionItem.objects.filter(
                created_at__date__lte=date,
                batch__id=batch_id,
                competency__id=competency_id,
                behavior__id=behavior_id,
            )

            # Get the most recent status for each action item on the mapped date
            status_data = {}
            for item in filtered_items:
                latest_status = None
                for update in item.status_updates:
                    update_date = datetime.strptime(
                        update["updated_at"], "%Y-%m-%d %H:%M:%S.%f+00:00"
                    ).date()
                    if update_date <= date:
                        latest_status = update["status"]
                    else:
                        break  # Break the loop if update date is after the mapped date
                if latest_status:
                    status_data[item.id] = latest_status

            # Calculate movement counts
            movement_counts = {i: 0 for i in range(5)}
            for status in status_data.values():
                movement = status_choices_dict.get(status, 0) - status_choices_dict.get(
                    "not_started", 0
                )
                movement_counts[movement] += 1

            # Store movement count data for the current date
            date_data[date.strftime("%d-%m-%Y")] = movement_counts

        formatted_data = []
        for date, counts in date_data.items():
            formatted_counts = {MOVEMENT_TYPES[i]: count for i, count in counts.items()}
            formatted_counts["date"] = date
            formatted_data.append(formatted_counts)
    ################ Date Wise Movement - END ############################

    return Response(
        {
            "movements": data,
            "action_item_counts": action_item_count,
            "date_wise_movement": formatted_data,
        },
        status=200,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_action_items(request):
    action_items = ActionItem.objects.all()
    serialized_data = ActionItemDetailedSerializer(action_items, many=True).data
    return Response(serialized_data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_action_items_hr(request, hr_id):
    action_items = ActionItem.objects.filter(batch__project__hr=hr_id)
    serialized_data = ActionItemDetailedSerializer(action_items, many=True).data
    return Response(serialized_data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_assessments_of_batch(request, type, pk):
    try:
        assessments = []
        if type == "project":
            assessments = Assessment.objects.filter(batch__project__id=pk)
        elif type == "batch":
            assessments = Assessment.objects.filter(batch__id=pk)
        assessment_list = []
        for assessment in assessments:
            total_responses_count = ParticipantResponse.objects.filter(
                assessment=assessment
            ).count()
            assessment_data = {
                "id": assessment.id,
                "name": assessment.name,
                "participant_view_name": assessment.participant_view_name,
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
                "created_at": assessment.created_at,
                "batch_name": assessment.batch.name,
            }
            assessment_list.append(assessment_data)

        return Response(assessment_list)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_past_live_session_facilitator(request, user_id):
    print("hello")
    try:
        status = request.query_params.get("status")
        project_id = request.query_params.get("project_id")

        facilitator = Facilitator.objects.get(id=user_id)

        all_live_sessions = LiveSession.objects.all()

        if project_id and not project_id == "all":
            all_live_sessions = all_live_sessions.filter(batch__project__id=project_id)

        if status == "Upcoming":
            live_sessions = all_live_sessions.filter(
                facilitator=facilitator, date_time__gt=timezone.now()
            ).order_by("date_time")
        elif status == "Past":
            live_sessions = all_live_sessions.filter(
                facilitator=facilitator, date_time__lt=timezone.now()
            ).order_by("-date_time")
        # For upcoming live sessions
        live_session_data = []
        for session in live_sessions:
            session_name = get_live_session_name(session.session_type)
            session_data = {
                "batch_name": session.batch.name,
                "project_name": session.batch.project.name,
                "session_name": f"{session_name} {session.live_session_number}",
                "date_time": session.date_time,
                "meeting_link": session.meeting_link,
            }
            live_session_data.append(session_data)

        return Response({"live_session_data": live_session_data})
    except ObjectDoesNotExist:
        return Response({"error": "Facilitator not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def batch_competency_movement(request, batch_id, competency_id):
    # Define initial and current status integer mappings
    initial_status_int = Case(
        *[
            When(initial_status=status, then=Value(status_choices_dict.get(status, 0)))
            for status in status_choices_dict
        ],
        default=Value(0),  # Default value if status not found
        output_field=IntegerField(),
    )
    current_status_int = Case(
        *[
            When(current_status=status, then=Value(status_choices_dict.get(status, 0)))
            for status in status_choices_dict
        ],
        default=Value(0),  # Default value if status not found
        output_field=IntegerField(),
    )

    # Fetch behaviors associated with the competency
    competency_behaviors = []
    batch_competency_assignment = BatchCompetencyAssignment.objects.filter(
        batch__id=batch_id, competency__id=competency_id
    ).first()
    if batch_competency_assignment:
        competency_behaviors = batch_competency_assignment.selected_behaviors.all()
    # Competency.objects.get(id=competency_id).behaviors.all()

    # Annotate the queryset with the movement between initial and current statuses
    movement_counts = (
        ActionItem.objects.filter(
            batch__id=batch_id,
            competency__id=competency_id,
            behavior__in=competency_behaviors,
        )
        .annotate(
            initial_status_int=initial_status_int,
            current_status_int=current_status_int,
            movement=F("current_status_int") - F("initial_status_int"),
        )
        .values("behavior__name", "movement")
        .annotate(count=Count("id"))
    )

    print(movement_counts)

    # Prepare data for response
    data = [
        {"movement": i, **{behavior.name: 0 for behavior in competency_behaviors}}
        for i in range(
            5
        )  # Initialize with default count of 0 for all movements (0 to 4)
    ]

    # Update the counts from the queryset
    for item in movement_counts:
        behavior_name = item["behavior__name"]
        movement = item["movement"]
        count = item["count"]
        # if only +ve movement exist
        if movement >= 0:
            data[movement][behavior_name] += count
        # if someone does negative movemtn than assuming it as 0 movement
        else:
            data[0][behavior_name] += count

    # Fetch behavior names associated with the competency
    behavior_names = {behavior.name: behavior.id for behavior in competency_behaviors}

    # Initialize a dictionary to store counts for each behavior in each status
    behavior_status_counts = {
        behavior_name: {status[0]: 0 for status in STATUS_CHOICES}
        for behavior_name in behavior_names
    }

    # Fetch status counts for each behavior from the database
    for behavior_name, behavior_id in behavior_names.items():
        status_counts_queryset = (
            ActionItem.objects.filter(
                batch__id=batch_id,
                competency__id=competency_id,
                behavior__id=behavior_id,
            )
            .values("current_status")
            .annotate(count=Count("id"))
        )

        # Update counts for existing statuses for the current behavior
        for item in status_counts_queryset:
            behavior_status_counts[behavior_name][item["current_status"]] = item[
                "count"
            ]

    # Prepare data for response
    action_item_counts = [
        {
            "status": STATUS_LABELS[status],
            **{
                behavior_name: counts[status]
                for behavior_name, counts in behavior_status_counts.items()
            },
        }
        for status, _ in STATUS_CHOICES
    ]

    return Response(
        {"action_item_movement": data, "action_item_counts": action_item_counts}
    )


def find_conflicting_sessions():
    coach_conflicts = defaultdict(list)
    current_time = timezone.now()
    current_timestamp_ms = int(current_time.timestamp() * 1000)
    upcoming_sessions = SchedularSessions.objects.filter(
        availibility__start_time__gte=current_timestamp_ms
    )
    for session in upcoming_sessions:
        coach_id = session.availibility.coach_id
        start_time = session.availibility.start_time
        end_time = session.availibility.end_time
        session_id = session.id

        conflicting_sessions = SchedularSessions.objects.filter(
            Q(availibility__coach_id=coach_id),
            Q(
                availibility__start_time__gt=start_time,
                availibility__start_time__lte=end_time,
            )
            | Q(
                availibility__start_time__lt=start_time,
                availibility__end_time__gte=start_time,
            )
            | Q(availibility__start_time=start_time)
            | Q(availibility__end_time=end_time),
        ).exclude(
            id=session_id
        )  # Exclude the current session itself

        for conflicting_session in conflicting_sessions:
            conflicting_session_id = conflicting_session.id
            # Ensure only one of the conflicting pairs is added
            if (
                conflicting_session_id not in coach_conflicts
                or session_id < conflicting_session_id
            ):
                coach_conflicts[session_id].append(conflicting_session_id)
    result = []
    for session_id, conflicts in coach_conflicts.items():
        session_obj = SchedularSessions.objects.get(id=session_id)
        session_coach_name = session_obj.availibility.coach.first_name
        session_start_time = session_obj.availibility.start_time
        session_end_time = session_obj.availibility.end_time
        session_learner_name = session_obj.learner.name
        session_details = {
            "learner_name": session_learner_name,
            "start_time": session_start_time,
            "end_time": session_end_time,
        }
        for conflict_id in conflicts:
            conflict_obj = SchedularSessions.objects.get(id=conflict_id)
            conflict_start_time = conflict_obj.availibility.start_time
            conflict_end_time = conflict_obj.availibility.end_time
            conflict_learner_name = conflict_obj.learner.name
            conflict_details = {
                "learner_name": conflict_learner_name,
                "start_time": conflict_start_time,
                "end_time": conflict_end_time,
            }
            result.append(
                {
                    "id": conflict_id,
                    "session": session_details,
                    "conflicting_with_session": conflict_details,
                    "coach": session_coach_name,
                }
            )
    return result


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_conflicting_sessions(request):
    res = find_conflicting_sessions()
    return Response(res)


def calculate_date_range(d1, d2, interval):
    if not d1 or not d2:
        return []

    date_range = []
    current_date = d1
    while current_date <= d2:
        date_range.append(current_date)
        current_date += timedelta(days=interval)
    return date_range


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def new_graph(request, batch_id, competency_id, behavior_id):
    # Get interval from query parameters
    interval = int(request.query_params.get("interval", 1))

    # Retrieve d1 from the first created action item
    first_created_action_item = (
        ActionItem.objects.filter(
            batch__id=batch_id, competency__id=competency_id, behavior__id=behavior_id
        )
        .order_by("created_at")
        .first()
    )
    d1 = (
        first_created_action_item.created_at.date()
        if first_created_action_item
        else None
    )

    # Retrieve d2 from the last updated action item
    last_updated_action_item = (
        ActionItem.objects.filter(
            batch__id=batch_id, competency__id=competency_id, behavior__id=behavior_id
        )
        .order_by("-updated_at")
        .first()
    )
    d2 = (
        last_updated_action_item.updated_at.date() if last_updated_action_item else None
    )

    # Calculate date range based on interval
    date_range = calculate_date_range(d1, d2, interval)
    graph_data = [{"date": date.strftime("%d/%m/%y")} for date in date_range]
    last_index = len(date_range) - 1
    # outer loop
    for outer_index, date in enumerate(date_range):
        if outer_index < last_index:
            filtered_action_items = ActionItem.objects.filter(
                batch__id=batch_id,
                competency__id=competency_id,
                behavior__id=behavior_id,
                created_at__gte=date,
                created_at__lte=date_range[outer_index + 1],
            )
            for inner_index in range(outer_index, len(graph_data)):
                movements = []
                for action_item in filtered_action_items:
                    movement = 0
                    initial_status = action_item.initial_status
                    latest_status = None
                    for update in action_item.status_updates:
                        update_date = datetime.strptime(
                            update["updated_at"], "%Y-%m-%d %H:%M:%S.%f+00:00"
                        ).date()
                        if update_date <= date_range[outer_index + 1]:
                            latest_status = update["status"]
                        else:
                            break  # Break the loop if update date is after the mapped date
                    if latest_status:
                        movement = (
                            status_choices_dict[latest_status]
                            - status_choices_dict[initial_status]
                        )
                        movements.append(movement)
                average = sum(movements) / len(movements) if movements else 0
                graph_data[inner_index][
                    f"{filtered_action_items.count()} Actions created on "
                    + (date_range[outer_index]).strftime("%d/%m/%y")
                ] = average
    return Response({"graph_data": graph_data})


@api_view(["POST"])
@permission_classes([AllowAny])
def get_booking_id_of_session(request):
    coaching_session_order = request.data.get('coaching_session_order') 
    project_id  = request.data.get('project_id')
    email = request.data.get('email')
    schedular_batches  = SchedularBatch.objects.filter(learners__email = email, project__unique_id = project_id)
    if schedular_batches.exists():
        print(coaching_session_order, type(coaching_session_order), schedular_batches.first())
        coaching_sessions  = CoachingSession.objects.filter(order=coaching_session_order,batch =schedular_batches.first())
        if coaching_sessions.exists():
            booking_link =  coaching_sessions.first().booking_link
            splitted_link = booking_link.split("/")
            return Response({ "booking_unique_id" : splitted_link[-1], "email": email})
        return Response({"error" : "Failed to verify the user."} ,status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error" : "Failed to verify the user."} ,status=status.HTTP_400_BAD_REQUEST)
