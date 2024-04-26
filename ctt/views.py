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
from collections import defaultdict


from .serializers import BatchSerializer, FacultiesSerializer
from .models import (
    Batches,
    BatchUsers,
    Sessions,
    BatchFaculty,
    Faculties,
    BatchMentorCoach,
    UserAssignments,
    Assignments,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_batches(request):
    batches = Batches.objects.using("ctt").all()
    serializer = BatchSerializer(batches, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def batch_details(request):
    batches = Batches.objects.using("ctt").all()
    data = []

    for batch in batches:
        total_participants = BatchUsers.objects.using("ctt").filter(batch=batch).count()
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
            "batch_name": batch.name,
            "program_name": batch.program.name,
            "start_date": batch.start_date,
            "total_participants": total_participants,
            "no_of_sessions": no_of_sessions,
            "faculty": faculty_names,
            "mentor_coaches": mentor_coach_names,
        }
        data.append(batch_data)

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def participant_details(request):
    batch_users = BatchUsers.objects.using("ctt").all()
    data = []
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
            user_data = {
                "name": batch_user.user.first_name + " " + batch_user.user.last_name,
                "email": batch_user.user.email,
                "phone_number": batch_user.user.phone,
                "batch": batch_name,
                "program": program_name,
                "assignment_completion": assignment_completion,
                "total_assignments_in_batch": total_assignments_in_batch,
                "certificate_status": certificate_status,
                "organisation": organization_name,
            }
            data.append(user_data)
        except Exception as e:
            print(str(e))
            pass
    return Response(data)


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
    all_batches = Batches.objects.using("ctt").all()
    l1_batches = []
    l2_batches = []
    l3_batches = []
    actc_batches = []
    for batch in all_batches:
        print(batch.name)
        if batch.program.certification_level.name == "Level 1":
            l1_batches.append(batch.name)
        elif batch.program.certification_level.name == "Level 2":
            l2_batches.append(batch.name)
        elif batch.program.certification_level.name == "Level 3":
            l3_batches.append(batch.name)
        elif batch.program.certification_level.name == "ACTC":
            actc_batches.append(batch.name)
    date_query = ""
    if start_date and end_date:
        date_query = f"&date_start={start_date}&date_end={end_date}"
    query_params = f"&salesorder_number_contains=CTT{date_query}"
    sales_orders = fetch_sales_orders(organization_id, query_params)
    print(sales_orders)
    salesperson_totals = defaultdict(lambda: {"l1": 0, "l2": 0, "l3": 0, "actc": 0})
    for order in sales_orders:
        batch = order.get("cf_ctt_batch", "")
        if not batch:
            continue
        salesperson = order["salesperson_name"]
        # amount = order["total"]
        if batch in l1_batches:
            salesperson_totals[salesperson]["l1"] += 1
        elif batch in l2_batches:
            salesperson_totals[salesperson]["l2"] += 1
        elif batch in l3_batches:
            salesperson_totals[salesperson]["l3"] += 1
        elif batch in actc_batches:
            salesperson_totals[salesperson]["actc"] += 1

    res_dict = dict(salesperson_totals)
    res_list = [
        {"salesperson": salesperson, **totals}
        for salesperson, totals in salesperson_totals.items()
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
def get_all_faculties(request):
    try:
        faculties = Faculties.objects.using("ctt").all()
        serializer = FacultiesSerializer(faculties, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(str(e))
        return Response({"error":"Failed to get data"},status=500)



