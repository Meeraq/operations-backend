from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from zohoapi.tasks import (
    fetch_customers_from_zoho,
    organization_id,
    fetch_sales_orders,
    fetch_client_invoices,
)
from django.template.loader import render_to_string
from zohoapi.models import SalesOrder
from collections import defaultdict
from django.utils import timezone
from .serializers import (
    BatchSerializer,
    FacultiesSerializer,
    SessionsSerializerDepthOne,
)
from django.http import HttpResponse
import pandas as pd
from io import BytesIO
import base64
from .models import (
    Batches,
    BatchUsers,
    Sessions,
    BatchFaculty,
    Faculties,
    BatchMentorCoach,
    UserAssignments,
    Assignments,
    MentorCoachSessions,
    Users,
)
from zohoapi.models import SalesOrder, ClientInvoice, PurchaseOrder
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import (
    Count,
    Prefetch,
    OuterRef,
    Subquery,
    Case,
    When,
    Value,
    F,
    Q,
    CharField,
    Sum,
)

from zohoapi.models import InvoiceData, Vendor, ZohoVendor
from zohoapi.views import fetch_invoices_db
from courses.models import CttSessionAttendance, CttCalendarInvites
from api.views import refresh_microsoft_access_token
from api.models import UserToken
import requests
import environ

env = environ.Env()

import json


def create_ctt_outlook_calendar_invite(
    subject,
    description,
    start_time_stamp,
    end_time_stamp,
    attendees,
    user_email,
    ctt_session_id,
    ctt_user_id,
    meeting_location,
    start_date,
    end_date,
    recurrence_type=None,  # Added recurrence type parameter
):
    event_create_url = "https://graph.microsoft.com/v1.0/me/events"
    try:
        user_token = UserToken.objects.get(user_profile__user__username=user_email)
        new_access_token = refresh_microsoft_access_token(user_token)
        if not new_access_token:
            new_access_token = user_token.access_token
        headers = {
            "Authorization": f"Bearer {new_access_token}",
            "Content-Type": "application/json",
        }
        start_datetime_obj = datetime.fromtimestamp(int(start_time_stamp) / 1000)
        end_datetime_obj = datetime.fromtimestamp(int(end_time_stamp) / 1000)
        start_datetime = start_datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
        end_datetime = end_datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")

        event_payload = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": description},
            "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
            "attendees": attendees,
            "location": {"displayName": meeting_location if meeting_location else ""},
        }

        if recurrence_type:
            event_payload["recurrence"] = {
                "pattern": {
                    "type": "weekly",
                    "interval": 1,
                    "daysOfWeek": [start_datetime_obj.strftime("%A").capitalize()],
                },
                "range": {
                    "type": "endDate",
                    "startDate": start_date,
                    "endDate": end_date,
                    "recurrenceTimeZone": "Asia/Kolkata",
                },
            }

        response = requests.post(event_create_url, json=event_payload, headers=headers)
        if response.status_code == 201:
            microsoft_response_data = response.json()
            calendar_invite = CttCalendarInvites(
                event_id=microsoft_response_data.get("id"),
                title=subject,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                attendees=attendees,
                creator=user_email,
                ctt_session=ctt_session_id,
                ctt_user=ctt_user_id,
            )
            calendar_invite.save()
            print("Calendar invite sent successfully.")
            return True
        else:
            print(f"Calendar invitation failed. Status code: {response.status_code}")
            print(response.text, response)
            return False

    except UserToken.DoesNotExist:
        print(f"User token not found for email: {user_email}")
        return False

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def get_month_start_end_dates():
    today = datetime.today()
    month_start_date = today.replace(day=1)
    next_month = month_start_date.replace(month=month_start_date.month + 1)
    month_end_date = next_month - timedelta(days=1)
    return month_start_date, month_end_date


def get_current_quarter_dates():
    today = datetime.today()
    quarter_month = (today.month - 1) // 3 + 1
    quarter_start_date = datetime(today.year, 3 * quarter_month - 2, 1)
    quarter_end_date = datetime(today.year, 3 * quarter_month, 1) - timedelta(days=1)
    return quarter_start_date, quarter_end_date


def get_current_financial_year_dates():
    today = datetime.today()
    financial_year_start_month = 4  # Assuming financial year starts in April
    if today.month < financial_year_start_month:
        financial_year_start_date = datetime(
            today.year - 1, financial_year_start_month, 1
        )
    else:
        financial_year_start_date = datetime(today.year, financial_year_start_month, 1)
    financial_year_end_date = datetime(
        today.year + 1, financial_year_start_month, 1
    ) - timedelta(days=1)
    return financial_year_start_date, financial_year_end_date


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_batches(request):
    batches = Batches.objects.using("ctt").all().order_by("-created_at")
    serializer = BatchSerializer(batches, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def batch_details(request):
    batches = Batches.objects.using("ctt").all().order_by("-created_at")
    data = []
    index = 1
    for batch in batches:
        total_participants = (
            BatchUsers.objects.using("ctt")
            .filter(batch=batch, deleted_at__isnull=True)
            .count()
        )
        no_of_sessions = Sessions.objects.using("ctt").filter(batch=batch).count()
        faculty_ids = (
            BatchFaculty.objects.using("ctt")
            .filter(batch=batch)
            .values_list("faculty_id", flat=True)
        )
        faculties = Faculties.objects.using("ctt").filter(id__in=faculty_ids)
        faculty_names = [f.first_name + " " + f.last_name for f in faculties]
        mentor_coach_ids = (
            BatchMentorCoach.objects.using("ctt")
            .filter(batch=batch)
            .values_list("faculty_id", flat=True)
        )
        mentor_coaches = Faculties.objects.using("ctt").filter(id__in=mentor_coach_ids)
        mentor_coach_names = [
            mc.first_name + " " + mc.last_name for mc in mentor_coaches
        ]

        batch_data = {
            "id": batch.id,
            "index": index,
            "batch_name": batch.name,
            "program_name": batch.program.name,
            "start_date": batch.start_date,
            "total_participants": total_participants,
            "no_of_sessions": no_of_sessions,
            "faculty": faculty_names,
            "mentor_coaches": mentor_coach_names,
            "created_at": batch.created_at,
        }
        index = index + 1
        data.append(batch_data)

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def participant_details(request):
    try:
        batch_users = (
            BatchUsers.objects.using("ctt")
            .filter(deleted_at__isnull=True)
            .order_by("-created_at")
        )
        data = []
        index = 1

        for batch_user in batch_users:
            try:
                batch_name = batch_user.batch.name
                batch = batch_user.batch
                batch_start_date = batch_user.batch.start_date
                program_name = batch_user.batch.program.name
                assignment_completion = (
                    UserAssignments.objects.using("ctt")
                    .filter(user=batch_user.user, assignment__batch=batch)
                    .count()
                )
                total_assignments_in_batch = (
                    Assignments.objects.using("ctt").filter(batch=batch).count()
                )
                certificate_status = (
                    "released" if batch_user.certificate else "not released"
                )
                organization_name = batch_user.user.current_organisation_name
                salesorders = SalesOrder.objects.filter(
                    zoho_customer__email=batch_user.user.email,
                    custom_field_hash__cf_ctt_batch=batch_user.batch.name,
                )
                sales_order = salesorders.first()
                payment_status = None
                total = 0
                invoiced_amount = 0
                paid_amount = 0
                currency_code = None
                for sales_order in salesorders:
                    total += sales_order.total
                    currency_code = sales_order.currency_code
                    for invoice in sales_order.invoices:
                        invoiced_amount += invoice["total"]
                        if invoice["status"] == "paid":
                            paid_amount += invoice["total"]

                    if sales_order.invoiced_status != "invoiced":
                        if sales_order.invoiced_status == "partially_invoiced":
                            payment_status = "Partially Invoiced"
                            break
                        elif sales_order.invoiced_status == "not_invoiced":
                            payment_status = "Not Invoiced"
                            break
                    else:
                        payment_status = "Invoiced"

                pending_amount = invoiced_amount - paid_amount

                user_data = {
                    "index": index,
                    "name": batch_user.user.first_name
                    + " "
                    + batch_user.user.last_name,
                    "email": batch_user.user.email,
                    "phone_number": batch_user.user.phone,
                    "batch": batch_name,
                    "program": program_name,
                    "assignment_completion": assignment_completion,
                    "total_assignments_in_batch": total_assignments_in_batch,
                    "program_start_date": batch_user.batch.start_date,
                    "total": total,
                    "invoiced_amount": invoiced_amount,
                    "pending_amount": pending_amount,
                    "paid_amount": paid_amount,
                    "currency_code": currency_code,
                    "certificate_status": certificate_status,
                    "organisation": organization_name,
                    "payment_status": payment_status,
                }

                index += 1
                data.append(user_data)
            except Exception as e:
                print(str(e))

        return Response(data)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=500)


def find_customer_by_email(customers, email):
    for customer in customers:
        if email == customer.get("email"):
            return customer
    return None


def filter_sales_orders_by_batch(sales_orders, batch):
    res = []
    for so in sales_orders:
        if batch == so.get("cf_ctt_batch"):
            res.append(so)
    return res


def filter_client_invoices_by_batch(invoices, batch):
    res = []
    for invoice in invoices:
        if batch == invoice.get("cf_ctt_batch"):
            res.append(invoice)
    return res


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def participant_so_in_batch(request, email):
    batch = request.query_params.get("batch", "")
    if not batch:
        return Response(
            {"message": "Customer not found in ZOHO", "customer_found": False}
        )
    customers = fetch_customers_from_zoho(organization_id, f"&email_contains={email}")
    customer = find_customer_by_email(customers, email)
    if customer:
        # fetch invoices
        sales_orders = fetch_sales_orders(
            organization_id, f"&customer_ids={customer['contact_id']}"
        )
        filtered_sales_orders = filter_sales_orders_by_batch(sales_orders, batch)
        return Response({"sales_orders": filtered_sales_orders, "customer_found": True})
    else:
        return Response(
            {"message": "Customer not found in ZOHO", "customer_found": False}
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def participant_so_and_invoices_in_batch(request, email):
    batch = request.query_params.get("batch", "")
    if not batch:
        return Response(
            {"message": "Customer not found in ZOHO", "customer_found": False}
        )
    customers = fetch_customers_from_zoho(organization_id, f"&email_contains={email}")
    customer = find_customer_by_email(customers, email)
    if customer:
        # fetch invoices
        sales_orders = fetch_sales_orders(
            organization_id, f"&customer_ids={customer['contact_id']}"
        )
        filtered_sales_orders = filter_sales_orders_by_batch(sales_orders, batch)
        invoices = fetch_client_invoices(
            organization_id, f"&customer_ids={customer['contact_id']}"
        )
        filtered_invoices = filter_client_invoices_by_batch(invoices, batch)
        return Response(
            {
                "sales_orders": filtered_sales_orders,
                "invoices": filtered_invoices,
                "customer_found": True,
            }
        )
    else:
        return Response(
            {"message": "Customer not found in ZOHO", "customer_found": False}
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_persons_finances(request):
    start_date = request.query_params.get("start_date", "")
    end_date = request.query_params.get("end_date", "")
    all_batches = Batches.objects.using("ctt").all().order_by("-created_at")
    l1_batches = []
    l2_batches = []
    l3_batches = []
    actc_batches = []

    month_start_date, month_end_date = get_month_start_end_dates()
    quarter_start_date, quarter_end_date = get_current_quarter_dates()
    financial_year_start_date, financial_year_end_date = (
        get_current_financial_year_dates()
    )
    for batch in all_batches:
        if batch.program.certification_level.name == "Level 1":
            l1_batches.append(batch.name)
        elif batch.program.certification_level.name == "Level 2":
            l2_batches.append(batch.name)
        elif batch.program.certification_level.name == "Level 3":
            l3_batches.append(batch.name)
        elif batch.program.certification_level.name == "ACTC":
            actc_batches.append(batch.name)

    if start_date and end_date:
        sales_orders = SalesOrder.objects.filter(
            salesorder_number__startswith="CTT",
            date__gte=start_date,
            date__lte=end_date,
        )
    else:
        sales_orders = SalesOrder.objects.filter(salesorder_number__startswith="CTT")
    # query_params = f"&salesorder_number_contains=CTT{date_query}"
    # sales_orders = fetch_sales_orders(organization_id, query_params)
    salesperson_totals = defaultdict(
        lambda: {
            "l1": 0,
            "l2": 0,
            "l3": 0,
            "monthly": 0,
            "quarterly": 0,
            "yearly": 0,
            "actc": 0,
            "total": 0,
            "salesperson": "",
        }
    )
    for order in sales_orders:
        batch = order.custom_field_hash.get("cf_ctt_batch", "")
        if not batch:
            continue
        salesperson = order.salesperson_name
        salesperson_id = order.salesperson_id
        salesperson_totals[salesperson_id]["salesperson"] = salesperson
        salesperson_totals[salesperson_id]["total"] += 1

        if batch in l1_batches:
            salesperson_totals[salesperson_id]["l1"] += 1
        elif batch in l2_batches:
            salesperson_totals[salesperson_id]["l2"] += 1
        elif batch in l3_batches:
            salesperson_totals[salesperson_id]["l3"] += 1
        elif batch in actc_batches:
            salesperson_totals[salesperson_id]["actc"] += 1

        if month_start_date.date() <= order.date <= month_end_date.date():
            salesperson_totals[salesperson_id]["monthly"] += 1
        if quarter_start_date.date() <= order.date <= quarter_end_date.date():
            salesperson_totals[salesperson_id]["quarterly"] += 1
        if (
            financial_year_start_date.date()
            <= order.date
            <= financial_year_end_date.date()
        ):
            salesperson_totals[salesperson_id]["yearly"] += 1

    res_list = [
        {"index": index, "salesperson_id": salesperson_id, **totals}
        for index, (salesperson_id, totals) in enumerate(
            salesperson_totals.items(), start=1
        )
    ]
    return Response(res_list)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def participant_finances(request):
    query_params = "&reference_number_contains=CTT"
    client_invoices = fetch_client_invoices(organization_id, query_params)
    # salesorders = fetch_sales_orders(
    #     organization_id, f"&salesorder_number_contains=CTT"
    # )
    # salesorders_dict = {}
    # for so in salesorders:
    #     salesorders_dict[so.get("salesorder_number", "")] = so
    batches = Batches.objects.using("ctt").all()
    batch_program_details = {}
    for batch in batches:
        batch_program_details[batch.name] = {
            "start_date": batch.start_date,
            "program_name": batch.program.name,
        }
    res = {}
    for invoice in client_invoices:
        batch = invoice.get("cf_ctt_batch", "")
        if batch:
            key = invoice["customer_id"] + batch
            if key in res:
                res[key]["invoices"].append(invoice)
            else:
                res[key] = {
                    "customer_name": invoice["customer_name"],
                    "batch": batch,
                    "program": batch_program_details[batch]["program_name"],
                    "start_date": batch_program_details[batch]["start_date"],
                    "sales_person": invoice["salesperson_name"],
                    "invoices": invoice,
                    # "so": salesorders_dict[invoice["reference_number"]],
                }
    result = res.items()
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_faculties(request):

    faculty_id = request.query_params.get("faculty_id")
    batch_faculties = None
    if faculty_id:
        batch_faculties = (
            BatchFaculty.objects.using("ctt")
            .select_related("faculty", "batch", "batch__program")
            .filter(faculty__id=int(faculty_id))
        )
    else:

        batch_faculties = (
            BatchFaculty.objects.using("ctt")
            .select_related("faculty", "batch", "batch__program")
            .all()
        )

    batch_ids = batch_faculties.values_list("batch_id", flat=True)

    participant_counts = (
        BatchUsers.objects.using("ctt")
        .filter(batch_id__in=batch_ids, deleted_at__isnull=True)
        .values("batch_id")
        .annotate(count=Count("id"))
    )
    total_assignments_counts = (
        Assignments.objects.using("ctt")
        .filter(batch_id__in=batch_ids)
        .values("batch_id")
        .annotate(count=Count("id"))
    )
    assignments_counts = (
        UserAssignments.objects.using("ctt")
        .filter(assignment__batch_id__in=batch_ids)
        .values("assignment__batch_id")
        .annotate(count=Count("id"))
    )
    mentor_coaching_counts = (
        MentorCoachSessions.objects.using("ctt")
        .filter(batch_id__in=batch_ids)
        .values("batch_id")
        .annotate(count=Count("id"))
    )
    current_date = timezone.now().date()
    total_sessions_counts = (
        Sessions.objects.using("ctt")
        .filter(batch_id__in=batch_ids)
        .values("batch_id")
        .annotate(count=Count("id"))
    )
    completed_sessions_counts = (
        Sessions.objects.using("ctt")
        .filter(batch_id__in=batch_ids, date__lt=current_date)
        .values("batch_id")
        .annotate(count=Count("id"))
    )
    salesorders_counts = (
        SalesOrder.objects.filter(
            invoiced_status="invoiced",
            custom_field_hash__cf_ctt_batch__in=[
                bf.batch.name for bf in batch_faculties
            ],
        )
        .values("custom_field_hash__cf_ctt_batch")
        .annotate(count=Count("id"))
    )

    participant_counts_dict = {
        item["batch_id"]: item["count"] for item in participant_counts
    }
    total_assignments_counts_dict = {
        item["batch_id"]: item["count"] for item in total_assignments_counts
    }
    assignments_counts_dict = {
        item["assignment__batch_id"]: item["count"] for item in assignments_counts
    }
    mentor_coaching_counts_dict = {
        item["batch_id"]: item["count"] for item in mentor_coaching_counts
    }
    total_sessions_counts_dict = {
        item["batch_id"]: item["count"] for item in total_sessions_counts
    }
    completed_sessions_counts_dict = {
        item["batch_id"]: item["count"] for item in completed_sessions_counts
    }
    salesorders_counts_dict = {
        item["custom_field_hash__cf_ctt_batch"]: item["count"]
        for item in salesorders_counts
    }

    res = []
    index = 1
    for batch_faculty in batch_faculties:
        batch_id = batch_faculty.batch.id
        batch_name = batch_faculty.batch.name
        vendor = Vendor.objects.filter(email=batch_faculty.faculty.email).first()
        total_invoiced = 0
        if vendor:
            total_invoiced = (
                InvoiceData.objects.filter(vendor__id=vendor.id).aggregate(
                    Sum("total")
                )["total__sum"]
                or 0
            )

        obj = {
            "index": index,
            "id": batch_faculty.id,
            "name": f"{batch_faculty.faculty.first_name} {batch_faculty.faculty.last_name}",
            "email": batch_faculty.faculty.email,
            "phone": batch_faculty.faculty.phone,
            "batch": batch_faculty.batch.name,
            "program": batch_faculty.batch.program.name,
            "participant_count": participant_counts_dict.get(batch_id, 0),
            "total_assignments": total_assignments_counts_dict.get(batch_id, 0),
            "assignments_count": assignments_counts_dict.get(batch_id, 0),
            "mentor_coaching_sessions": mentor_coaching_counts_dict.get(batch_id, 0),
            "total_sessions_count": total_sessions_counts_dict.get(batch_id, 0),
            "completed_sessions_count": completed_sessions_counts_dict.get(batch_id, 0),
            "salesorders": salesorders_counts_dict.get(batch_name, 0),
            "created_at": batch_faculty.batch.created_at,
            "total_invoiced": total_invoiced,
        }
        index += 1
        res.append(obj)

    return Response(res)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_faculties(request):
    try:
        faculties = Faculties.objects.using("ctt").all().order_by("-created_at")
        serializer = FacultiesSerializer(faculties, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_finance(request):
    try:
        salesperson_id = request.query_params.get("salesperson_id", None)
        salesperson_id_sales = request.query_params.get("salesperson_id_sales", None)

        batch_users = (
            BatchUsers.objects.using("ctt")
            .select_related("user", "batch__program")
            .filter(deleted_at__isnull=True)
            .order_by("-created_at")
        )

        # Convert batch_users emails to a list to avoid subquery across different databases
        user_emails = list(batch_users.values_list("user__email", flat=True))
        if salesperson_id or salesperson_id_sales:
            salesorders = SalesOrder.objects.filter(
                zoho_customer__email__in=user_emails, salesperson_id=salesperson_id
            ).select_related("zoho_customer")
        else:
            salesorders = SalesOrder.objects.filter(
                zoho_customer__email__in=user_emails
            ).select_related("zoho_customer")

        data = []
        index = 1
        # user_assignments = UserAssignments.objects.using("ctt").all()
        assignments = Assignments.objects.using("ctt").all()
        for batch_user in batch_users:
            if salesperson_id_sales:
                salesorders.filter(zoho_customer__email=batch_user.user.email)
                if salesorders.count() == 0:
                    continue

            user_email = batch_user.user.email
            batch_name = batch_user.batch.name
            user_salesorders = [
                so
                for so in salesorders
                if so.zoho_customer.email == user_email
                and so.custom_field_hash.get("cf_ctt_batch") == batch_name
            ]

            total = sum(Decimal(str(so.total or 0)) for so in user_salesorders)
            invoiced_amount = sum(
                Decimal(str(invoice["total"]))
                for so in user_salesorders
                for invoice in so.invoices
            )
            paid_amount = sum(
                Decimal(str(invoice["total"]))
                for so in user_salesorders
                for invoice in so.invoices
                if invoice.get("status") == "paid"
            )
            sales_persons = {so.salesperson_name for so in user_salesorders}
            background = (
                user_salesorders[0].background
                if len(user_salesorders) > 0 and user_salesorders[0]
                else ""
            )
            currency_code = (
                user_salesorders[0].currency_code if user_salesorders else None
            )

            pending_amount = total - paid_amount

            if not user_salesorders:
                payment_status = "N/A"
            elif paid_amount == 0:
                payment_status = "Not Paid"
            elif total == paid_amount:
                payment_status = "Paid"
            else:
                payment_status = "Partially Paid"

            # assignment_completion = user_assignments.filter(
            #     user=batch_user.user, assignment__batch=batch_user.batch
            # ).count()
            total_assignments_in_batch = assignments.filter(
                batch=batch_user.batch
            ).count()

            certificate_status = (
                "released" if batch_user.certificate else "not released"
            )
            temp = {
                "index": index,
                "participant_name": f"{batch_user.user.first_name} {batch_user.user.last_name}",
                "participant_email": batch_user.user.email,
                "participant_id": batch_user.user.id,
                "participant_phone": batch_user.user.phone,
                "batch_name": batch_user.batch.name,
                "batch_id": batch_user.batch.id,
                "program_name": batch_user.batch.program.name,
                "payment_status": payment_status,
                "program_start_date": batch_user.batch.start_date,
                "salesperson_name": list(sales_persons),
                "total": total,
                "invoiced_amount": invoiced_amount,
                "pending_amount": pending_amount,
                "paid_amount": paid_amount,
                "currency_code": currency_code,
                "total_assignments_in_batch": total_assignments_in_batch,
                "no_of_sales_orders": len(user_salesorders),
                "organisation": batch_user.user.current_organisation_name,
                "certificate_status": certificate_status,
                "background": background,
            }
            index += 1
            # assuming that the user is the salespersons user only if sales order exists
            if salesperson_id:
                if len(user_salesorders) > 0:
                    data.append(temp)
            else:
                data.append(temp)

        return Response(data)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_client_invoice_of_participant_for_batch(request, participant_id, batch_id):
    try:
        data = []
        user = Users.objects.using("ctt").get(id=participant_id)
        batch = Batches.objects.using("ctt").get(id=batch_id)
        client_invoices = ClientInvoice.objects.filter(
            custom_field_hash__cf_ctt_batch=batch.name,
            zoho_customer__email=user.email,
            sales_order__custom_field_hash__cf_ctt_batch=batch.name,
        )
        for client_invoice in client_invoices:
            payment_status = "Paid" if client_invoice.status == "paid" else "Not Paid"
            temp = {
                "invoice_number": client_invoice.invoice_number,
                "so_number": (
                    client_invoice.sales_order.salesorder_number
                    if client_invoice.sales_order
                    else None
                ),
                "due_date": client_invoice.due_date,
                "date": client_invoice.date,
                "payment_status": payment_status,
            }
            data.append(temp)
        return Response(data)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_participants_of_that_batch(request, batch_id):
    try:
        batch_users = BatchUsers.objects.using("ctt").filter(
            batch__id=batch_id, deleted_at__isnull=True
        )
        data = []
        index = 1
        for batch_user in batch_users:
            batch_name = batch_user.batch.name
            batch_start_date = batch_user.batch.start_date
            program_name = batch_user.batch.program.name
            salesorders = (
                SalesOrder.objects.filter(zoho_customer__email=batch_user.user.email)
                .select_related("zoho_customer")
                .first()
            )
            background = salesorders.background if salesorders else ""

            assignment_completion = (
                UserAssignments.objects.using("ctt")
                .filter(user=batch_user.user, assignment__batch=batch_user.batch)
                .count()
            )
            total_assignments_in_batch = (
                Assignments.objects.using("ctt").filter(batch=batch_user.batch).count()
            )
            certificate_status = (
                "released" if batch_user.certificate else "not released"
            )
            organization_name = batch_user.user.current_organisation_name
            salesorders = SalesOrder.objects.filter(
                zoho_customer__email=batch_user.user.email,
                custom_field_hash__cf_ctt_batch=batch_user.batch.name,
            )
            payment_status = None

            for sales_order in salesorders:
                if sales_order.invoiced_status != "invoiced":
                    if sales_order.invoiced_status == "partially_invoiced":
                        payment_status = "Partially Invoiced"
                        break
                    elif sales_order.invoiced_status == "not_invoiced":
                        payment_status = "Not Invoiced"
                        break
                else:
                    payment_status = "Invoiced"

            user_data = {
                "index": index,
                "batch_user_id": batch_user.id,
                "user_id": batch_user.user.id,
                "name": f"{batch_user.user.first_name} {batch_user.user.last_name}",
                "email": batch_user.user.email,
                "phone_number": batch_user.user.phone,
                "batch": batch_name,
                "program": program_name,
                "assignment_completion": assignment_completion,
                "total_assignments_in_batch": total_assignments_in_batch,
                "certificate_status": certificate_status,
                "organisation": organization_name,
                "payment_status": payment_status,
                "background": background,
            }

            index += 1
            data.append(user_data)
        return Response(data)
    except Exception as e:
        print(str(e))
        return Response(
            {"message": "Batch users not found for the given batch ID"}, status=500
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_ctt_salesperson_individual(request, salesperson_id):
    try:
        batch_users = (
            BatchUsers.objects.using("ctt")
            .filter(deleted_at__isnull=True)
            .order_by("-created_at")
        )
        data = []
        index = 1
        for batch_user in batch_users:
            salesorders = SalesOrder.objects.filter(
                zoho_customer__email=batch_user.user.email,
                custom_field_hash__cf_ctt_batch=batch_user.batch.name,
                salesperson_id=salesperson_id,
            )
            if salesorders.exists():
                total = 0
                invoiced_amount = 0
                paid_amount = 0
                currency_code = None
                sales_persons = set()
                all_invoices_paid = []

                for sales_order in salesorders:
                    total += Decimal(str(sales_order.total))
                    currency_code = sales_order.currency_code
                    sales_persons.add(sales_order.salesperson_name)
                    for invoice in sales_order.invoices:
                        invoiced_amount += Decimal(str(invoice["total"]))
                        if invoice["status"] == "paid":
                            paid_amount += Decimal(str(invoice["total"]))
                            all_invoices_paid.append(True)
                        else:
                            all_invoices_paid.append(False)

                pending_amount = total - paid_amount
                if salesorders.count() == 0:
                    payment_status = "N/A"
                else:
                    if paid_amount == 0:
                        payment_status = "Not Paid"
                    elif total == paid_amount:
                        payment_status = "Paid"
                    else:
                        payment_status = "Partially Paid"

                temp = {
                    "index": index,
                    "participant_name": batch_user.user.first_name
                    + " "
                    + batch_user.user.last_name,
                    "participant_email": batch_user.user.email,
                    "participant_id": batch_user.user.id,
                    "participant_phone": batch_user.user.phone,
                    "batch_name": batch_user.batch.name,
                    "batch_id": batch_user.batch.id,
                    "program_name": batch_user.batch.program.name,
                    "payment_status": payment_status,
                    "program_start_date": batch_user.batch.start_date,
                    "salesperson_name": list(sales_persons),
                    "total": total,
                    "invoiced_amount": invoiced_amount,
                    "pending_amount": pending_amount,
                    "paid_amount": paid_amount,
                    "currency_code": currency_code,
                    "no_of_sales_orders": len(salesorders),
                }
                index += 1
                data.append(temp)
        return Response(data)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_card_data_for_dashboard_ctt(request):
    try:
        batches = Batches.objects.using("ctt").all().count()
        unique_users_count = (
            BatchUsers.objects.using("ctt")
            .filter(deleted_at__isnull=True)
            .distinct()
            .count()
        )
        faculties = Faculties.objects.using("ctt").all().count()

        return Response(
            {
                "total_number_of_batches": batches,
                "total_number_of_participants": unique_users_count,
                "total_number_of_faculty": faculties,
            }
        )
    except Exception as e:
        print(str(e))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_ctt_faculties(request):
    try:
        faculties = Faculties.objects.using("ctt").all()
        faculties_data = []

        for faculty in faculties:
            vendor = Vendor.objects.filter(email=faculty.email).first()
            total_invoiced = 0
            if vendor:
                all_invoices = fetch_invoices_db()
                for invoice in all_invoices:
                    total_invoiced += invoice["total"] * (
                        invoice["bill"]["exchange_rate"] if invoice["bill"] else 1
                    )

            batch_faculties = BatchFaculty.objects.using("ctt").filter(faculty=faculty)
            total_batches = batch_faculties.count()
            batch_names = list(batch_faculties.values_list("batch__name", flat=True))

            faculties_data.append(
                {
                    "index": faculty.id,
                    "name": faculty.first_name + " " + faculty.last_name,
                    "email": faculty.email,
                    "phone": faculty.phone,
                    "total_invoiced": total_invoiced,
                    "total_batches": total_batches,
                    "batch_names": batch_names,
                }
            )

        return Response(faculties_data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_the_profitability_of_a_batch(request, batch_id):
    try:
        batch_user = Batches.objects.using("ctt").get(id=batch_id)
        salesorders = SalesOrder.objects.filter(
            custom_field_hash__cf_ctt_batch=batch_user.name
        )
        purchase_orders = PurchaseOrder.objects.filter(
            custom_field_hash__cf_ctt_batch=batch_user.name
        )

        total = Decimal("0.0")
        invoiced_amount = Decimal("0.0")
        paid_amount = Decimal("0.0")
        currency_code = None
        all_invoices_paid = []

        if salesorders.exists():
            for sales_order in salesorders:
                total += Decimal(str(sales_order.total)) * sales_order.exchange_rate
                currency_code = sales_order.currency_code
                for invoice in sales_order.invoices:
                    invoiced_amount += (
                        Decimal(str(invoice["total"])) * sales_order.exchange_rate
                    )
                    if invoice["status"] == "paid":
                        paid_amount += Decimal(str(invoice["total"]))
                        all_invoices_paid.append(True)
                    else:
                        all_invoices_paid.append(False)

        purchase_total = Decimal("0.0")
        purchase_billed_amount = Decimal("0.0")
        purchase_paid_amount = Decimal("0.0")
        purchase_currency_code = None
        purchase_all_bills_paid = []

        if purchase_orders.exists():
            for purchase_order in purchase_orders:
                purchase_total += (
                    Decimal(str(purchase_order.total)) * purchase_order.exchange_rate
                )
                purchase_currency_code = purchase_order.currency_code
                for bill in purchase_order.bills:
                    purchase_billed_amount += (
                        Decimal(str(bill["total"])) * purchase_order.exchange_rate
                    )
                    if bill["status"] == "paid":
                        purchase_paid_amount += Decimal(str(bill["total"]))
                        purchase_all_bills_paid.append(True)
                    else:
                        purchase_all_bills_paid.append(False)

        response_data = {
            "total_amount": total,
            "invoiced_amount": invoiced_amount,
            "paid_amount": paid_amount,
            "purchase_total": purchase_total,
            "purchase_billed_amount": purchase_billed_amount,
            "purchase_paid_amount": purchase_paid_amount,
            "currency_code": currency_code,
            "purchase_currency_code": purchase_currency_code,
            "all_invoices_paid": all_invoices_paid,
            "purchase_all_bills_paid": purchase_all_bills_paid,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    except BatchUsers.DoesNotExist:
        return Response(
            {"error": "Batch user not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_upcoming_sessions(request):
    try:
        batch_id = request.query_params.get("batch_id")
        faculty_email = request.query_params.get("faculty_email")
        now = datetime.now()
        upcoming_sessions = (
            Sessions.objects.using("ctt")
            .filter(
                Q(date__gt=now.date())
                | (Q(date=now.date()) & Q(start_time__gte=now.time())),
                deleted_at__isnull=True,
            )
            .order_by("date", "start_time")
            .distinct()
        )
        if faculty_email:
            upcoming_sessions = upcoming_sessions.filter(
                batch__batchfaculty__faculty__email=faculty_email
            )

        if batch_id:
            upcoming_sessions = upcoming_sessions.filter(
                batch__id=int(batch_id)
            ).order_by("date", "start_time")

        all_sessions = []
        for session in upcoming_sessions:
            session_attendance = CttSessionAttendance.objects.filter(
                session=session.id
            ).first()
            user_names = None
            if session_attendance:
                users = (
                    Users.objects.using("ctt")
                    .filter(batchusers__id__in=session_attendance.attendance)
                    .distinct()
                )
                user_names = [user.first_name + " " + user.last_name for user in users]
            all_sessions.append(
                {
                    "id": session.id,
                    "batch_name": session.batch.name,
                    "batch_id": session.batch.id,
                    "program_name": session.batch.program.name,
                    "date": session.date,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "session_no": session.session_no,
                    "description": session.description,
                    "type": session.type,
                    "session_attendance": (user_names if user_names else []),
                }
            )

        return Response(all_sessions)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_past_sessions(request):
    try:
        batch_id = request.query_params.get("batch_id")
        faculty_email = request.query_params.get("faculty_email")
        now = datetime.now()
        past_sessions = (
            Sessions.objects.using("ctt")
            .filter(
                Q(date__lt=now.date())
                | (Q(date=now.date()) & Q(start_time__lt=now.time())),
                deleted_at__isnull=True,
            )
            .order_by("-date", "-start_time")
            .distinct()
        )
        if faculty_email:
            past_sessions = past_sessions.filter(
                batch__batchfaculty__faculty__email=faculty_email
            )

        if batch_id:
            past_sessions = past_sessions.filter(batch__id=int(batch_id)).order_by(
                "-date", "-start_time"
            )

        all_sessions = []

        for session in past_sessions:
            session_attendance = CttSessionAttendance.objects.filter(
                session=session.id
            ).first()
            user_names = None
            if session_attendance:
                users = (
                    Users.objects.using("ctt")
                    .filter(batchusers__id__in=session_attendance.attendance)
                    .distinct()
                )
                user_names = [user.first_name + " " + user.last_name for user in users]
            all_sessions.append(
                {
                    "id": session.id,
                    "batch_name": session.batch.name,
                    "batch_id": session.batch.id,
                    "program_name": session.batch.program.name,
                    "date": session.date,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "session_no": session.session_no,
                    "description": session.description,
                    "type": session.type,
                    "session_attendance": (user_names if user_names else []),
                }
            )

        return Response(all_sessions)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_sessions(request, batch_id):
    try:
        now = datetime.now()
        sessions = (
            Sessions.objects.using("ctt")
            .filter(
                Q(date__gt=now.date())
                | (Q(date=now.date()) & Q(start_time__gte=now.time())),
                deleted_at__isnull=True,
            )
            .order_by("date", "start_time")
            .distinct()
        )
        serializer = SessionsSerializerDepthOne(sessions, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_attendance_of_session(request):
    try:
        participants = request.data.get("participants", [])
        session = request.data.get("session")

        existing_session_attendance, created = (
            CttSessionAttendance.objects.get_or_create(session=session)
        )

        existing_session_attendance.attendance = participants

        existing_session_attendance.save()

        return Response({"message": "Attendance Added Successfully!"}, status=200)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to add attendance"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_attendance_of_session(request, session_id):
    try:
        session_attendance = CttSessionAttendance.objects.get(session=session_id)

        return Response(
            {
                "session": session_attendance.session,
                "attendance": session_attendance.attendance,
            }
        )
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=500)


def get_the_meeting_details_based_on_level(certification_name):
    try:
        image_path = None
        template = None
        if certification_name == "Level 1":
            image_path = "templates/ctt_images/level_1_image.png"
            template = "ctt_templates/level_1.html"
        elif certification_name == "Level 2 / PCC Bridge":
            image_path = "templates/ctt_images/level_2_image.png"
            template = "ctt_templates/level_2.html"
        elif certification_name == "MCCP":
            image_path = "templates/ctt_images/mccp_image.png"
            template = "ctt_templates/actc.html"
        elif certification_name == "ACTC":
            image_path = "templates/ctt_images/actc_image.png"
            template = "ctt_templates/mccp.html"

        image_base64 = None
        if image_path:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

        return image_base64, template
    except Exception as e:
        print(str(e))
        return None, None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_calendar_invites(request):
    try:
        batch_id = request.data.get("batch_id", [])
        meeting_link = request.data.get("meeting_link", None)
        meeting_id = request.data.get("meeting_id", None)
        meeting_passcode = request.data.get("meeting_passcode", None)
        if meeting_link:
            all_sessions = Sessions.objects.using("ctt").filter(
                batch__id=batch_id, deleted_at__isnull=True
            )
            all_sessions_array = [
                {
                    "name": f"Session {session.session_no}",
                    "date": session.date.strftime("%d/%m/%Y"),
                    "timing": f"{session.start_time.strftime('%I:%M %p')} to {session.end_time.strftime('%I:%M %p')} IST",
                }
                for session in all_sessions
            ]
            session = all_sessions.first()

            if session:
                batch = session.batch
                certification_name = session.batch.program.certification_level.name
                course_start_date = session.batch.start_date.strftime("%d/%m/%Y")
                course_end_date = session.batch.end_date.strftime("%d/%m/%Y")
                batch_name = session.batch.name
                program_name = session.batch.program.name
                session_timing = f"{session.start_time.strftime('%I:%M %p')} to {session.end_time.strftime('%I:%M %p')} IST"
                total_sessions_to_book = len(all_sessions)
                faculty_ids = (
                    BatchFaculty.objects.using("ctt")
                    .filter(batch=batch)
                    .values_list("faculty_id", flat=True)
                )
                faculties = Faculties.objects.using("ctt").filter(id__in=faculty_ids)
                faculty_names = [f.first_name + " " + f.last_name for f in faculties]
                faculty_names_str = ", ".join(faculty_names)

                start_datetime = datetime.combine(session.date, session.start_time)
                end_datetime = datetime.combine(session.date, session.end_time)
                start_time_stamp = int(start_datetime.timestamp()) * 1000
                end_time_stamp = int(end_datetime.timestamp()) * 1000

                image_base64, selected_template = (
                    get_the_meeting_details_based_on_level(certification_name)
                )
                batch_userss = BatchUsers.objects.using("ctt").filter(
                    batch=batch, deleted_at__isnull=True
                )
                for batch_users in batch_userss:
                    description = render_to_string(
                        selected_template,
                        {
                            "faculty_names_str": faculty_names_str,
                            "course_start_date": course_start_date,
                            "course_end_date": course_end_date,
                            "batch_name": batch_name,
                            "program_name": program_name,
                            "session_timing": session_timing,
                            "total_sessions_to_book": total_sessions_to_book,
                            "all_sessions_array": all_sessions_array,
                            "image_base64": image_base64,
                            "meeting_link": meeting_link,
                            "day_of_week": start_datetime.strftime("%A").capitalize(),
                            "name": batch_users.user.first_name,
                            "meeting_id": meeting_id,
                            "meeting_passcode": meeting_passcode,
                        },
                    )

                    if description:

                        try:
                            create_ctt_outlook_calendar_invite(
                                f"Coach-To-Transformation| {batch_name} | Calendar Invite",
                                description,
                                start_time_stamp,
                                end_time_stamp,
                                [
                                    {
                                        "emailAddress": {
                                            "address": batch_users.user.email,
                                        },
                                        "type": "required",
                                    }
                                ],
                                env("CTT_CALENDAR_INVITATION_ORGANIZER"),
                                session.id,
                                batch_users.user.id,
                                meeting_link if meeting_link else None,
                                session.batch.start_date.strftime("%Y-%m-%d"),
                                session.batch.end_date.strftime("%Y-%m-%d"),
                                "weekly",
                            )

                        except Exception as e:
                            print(str(e))

                return Response({"message": "Invites sent successfully!"}, status=200)
            return Response({"error": "Upcoming Sessions are not present."}, status=500)
        return Response({"error": "Failed to send invites"}, status=500)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to send invites"}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def download_training_attendance_data(request, batch_id):
    try:
        batch = Batches.objects.using("ctt").get(id=batch_id)
        sessions = Sessions.objects.using("ctt").filter(
            batch=batch,
            deleted_at__isnull=True,
        )
        batch_users = BatchUsers.objects.using("ctt").filter(
            batch=batch,
            deleted_at__isnull=True,
        )
        data = []

        for batch_user in batch_users:
            temp = {
                "Participant Name": batch_user.user.first_name
                + " "
                + batch_user.user.last_name
            }
            for session in sessions:
                ctt_attendance = CttSessionAttendance.objects.filter(
                    session=session.id
                ).first()
                is_present = False
                if ctt_attendance:
                    if batch_user.id in ctt_attendance.attendance:
                        is_present = True

                temp[f"Session {session.session_no}"] = (
                    "Attended" if is_present else "Not Attended"
                )

            data.append(temp)

        df = pd.DataFrame(data)
        excel_writer = BytesIO()
        df.to_excel(excel_writer, index=False)
        excel_writer.seek(0)
        response = HttpResponse(
            excel_writer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="Report.xlsx"'
        return response

    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=500)
