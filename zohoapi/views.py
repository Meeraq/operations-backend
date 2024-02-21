from rest_framework.decorators import api_view, permission_classes
from datetime import date
import requests
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError
from operationsBackend import settings
from django.utils.crypto import get_random_string
from rest_framework.exceptions import AuthenticationFailed
from datetime import datetime, timedelta
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from api.models import Coach, OTP, UserLoginActivity, Profile, Role
from api.serializers import CoachDepthOneSerializer
from openpyxl import Workbook

from rest_framework.views import APIView

from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from django.http import HttpResponse
from .serializers import (
    InvoiceDataEditSerializer,
    InvoiceDataSerializer,
    VendorDepthOneSerializer,
    VendorSerializer,
    InvoiceStatusUpdateGetSerializer,
)
from .tasks import (
    import_invoice_for_new_vendor,
    get_access_token,
    base_url,
    organization_id,
    import_invoices_for_vendor_from_zoho,
    fetch_bills,
    purchase_orders_allowed,
    filter_invoice_data,
    send_mail_templates,
)
from .models import InvoiceData, AccessToken, Vendor, InvoiceStatusUpdate
import base64
from django.core.mail import EmailMessage
from io import BytesIO
from xhtml2pdf import pisa
import environ
import os
import os
from django.http import HttpResponse
import io
import pdfkit
from django.middleware.csrf import get_token
from django.db import transaction


env = environ.Env()

wkhtmltopdf_path = os.environ.get(
    "WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")


def get_line_items_details(invoices):
    res = {}
    for invoice in invoices:
        for line_item in invoice.line_items:
            if line_item["line_item_id"] in res:
                res[line_item["line_item_id"]] += line_item["quantity_input"]
            else:
                res[line_item["line_item_id"]] = line_item["quantity_input"]
    return res


def get_invoice_data_for_pdf(invoice):
    serializer = InvoiceDataSerializer(invoice)
    line_items = get_line_items_for_template(serializer.data["line_items"])
    invoice_date = datetime.strptime(
        serializer.data["invoice_date"], "%Y-%m-%d"
    ).strftime("%d-%m-%Y")
    due_date = datetime.strptime(
        add_45_days(serializer.data["invoice_date"]), "%Y-%m-%d"
    ).strftime("%d-%m-%Y")
    invoice_data = {
        **serializer.data,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "line_items": line_items,
    }
    return invoice_data


def generate_access_token_from_refresh_token(refresh_token):
    token_url = env("ZOHO_TOKEN_URL")
    client_id = env("ZOHO_CLIENT_ID")
    client_secret = env("ZOHO_CLIENT_SECRET")
    # Payload for requesting access token
    token_payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": env("REDIRECT_URI"),
        "grant_type": "refresh_token",
    }
    token_response = requests.post(token_url, params=token_payload)

    token_data = token_response.json()
    if "access_token" in token_data:
        return token_data["access_token"]
    else:
        return None


def send_mail_templates_with_attachment(
    file_name, user_email, email_subject, content, body_message, bcc_emails
):
    try:
        image_url = f"{content['invoice']['signature']}"
        datetime_obj = datetime.strptime(
            content["invoice"]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        formatted_date = datetime_obj.strftime("%d-%m-%Y")
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        # Convert the downloaded image to base64
        image_base64 = base64.b64encode(image_response.content).decode("utf-8")
        content["image_base64"] = image_base64
        email_message = render_to_string(file_name, content)
        pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)
        result = BytesIO(pdf)
        email = EmailMessage(
            subject=f"{env('EMAIL_SUBJECT_INITIAL', default='')} {email_subject}",
            body=body_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=user_email,
            bcc=bcc_emails,
        )
        # Attach the PDF to the email
        email.attach(
            f"{content['invoice']['vendor_name']}_{formatted_date}.pdf",
            result.getvalue(),
            "application/pdf",
        )
        email.content_subtype = "html"
        email.send()

    except Exception as e:
        print(str(e))


def get_organization_data():
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/organizations/{env('ZOHO_ORGANIZATION_ID')}/"
        organization_response = requests.get(
            url,
            headers=headers,
        )
        if (
            organization_response.json()["message"] == "success"
            and organization_response.json()["organization"]
        ):
            return organization_response.json()["organization"]
        return Response({}, status=400)
    else:
        return Response({}, status=400)


def get_vendor(vendor_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/contacts/{vendor_id}?organization_id={env('ZOHO_ORGANIZATION_ID')}"
        vendor_response = requests.get(
            url,
            headers=headers,
        )
        if (
            vendor_response.json()["message"] == "success"
            and vendor_response.json()["contact"]
        ):
            return vendor_response.json()["contact"]
        return Response({}, status=400)
    else:
        return Response({}, status=400)


def add_45_days(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date + timedelta(days=45)
    new_date_str = new_date.strftime("%Y-%m-%d")
    return new_date_str


def get_user_data(user):
    if not user.profile:
        return None
    elif user.profile.roles.count() == 0:
        return None
    user_profile_role = user.profile.roles.filter(name="vendor")
    if user_profile_role.exists() and user.profile.vendor:
        serializer = VendorDepthOneSerializer(user.profile.vendor)
    else:
        return None
    return {
        **serializer.data,
        "user": {**serializer.data["user"], "type": "vendor"},
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_otp(request):
    try:
        user = User.objects.get(username=request.data["email"])
        try:
            otp_obj = OTP.objects.get(user=user)
            otp_obj.delete()
        except OTP.DoesNotExist:
            pass

        # Generate OTP and save it to the database
        user_data = get_user_data(user)
        if user_data:
            otp = get_random_string(length=6, allowed_chars="0123456789")
            created_otp = OTP.objects.create(user=user, otp=otp)
            name = user_data.get("name") or user_data.get("first_name") or "User"
            subject = f"Meeraq Login OTP"
            message = f"Dear {name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}"
            send_mail_templates(
                "hr_emails/login_with_otp.html",
                [user],
                subject,
                {"name": name, "otp": created_otp.otp},
                [],
            )
            return Response({"message": f"OTP has been sent to {user.username}!"})
        else:
            return Response({"error": "Vendor doesn't exist."}, status=400)

    except User.DoesNotExist:
        # Handle the case where the user with the given email does not exist
        return Response(
            {"error": "User with the given email does not exist."}, status=400
        )

    except Exception as e:
        # Handle any other exceptions
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def generate_otp_send_mail_fixed(request, email):
    try:
        user = User.objects.get(username=email)
        try:
            # Check if OTP already exists for the user
            otp_obj = OTP.objects.get(user=user)
            otp_obj.delete()
        except OTP.DoesNotExist:
            pass

        # Generate OTP and save it to the database
        user_data = get_user_data(user)
        if user_data:
            otp = get_random_string(length=6, allowed_chars="0123456789")
            created_otp = OTP.objects.create(user=user, otp=otp)
            name = user_data.get("name") or user_data.get("first_name") or "User"
            subject = f"Meeraq Login OTP"
            message = f"Dear {name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}"
            send_mail_templates(
                "hr_emails/login_with_otp.html",
                ["pankaj@meeraq.com"],
                subject,
                {"name": name, "otp": created_otp.otp},
                [],
            )
            return Response({"message": f"OTP has been sent to {user.username}!"})
        else:
            return Response({"error": "Vendor doesn't exist."}, status=400)

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
    otp_obj.delete()
    last_login = user.last_login
    login(request, user)
    user_data = get_user_data(user)
    if user_data:
        organization = get_organization_data()
        zoho_vendor = get_vendor(user_data["vendor_id"])
        login_timestamp = timezone.now()
        UserLoginActivity.objects.create(
            user=user, timestamp=login_timestamp, platform=platform
        )
        response = Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
                "organization": organization,
                "zoho_vendor": zoho_vendor,
            }
        )
        response["X-CSRFToken"] = get_token(request)
        return response
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def session_view(request):
    user = request.user
    last_login = user.last_login
    user_data = get_user_data(user)
    if user_data:
        organization = get_organization_data()
        zoho_vendor = get_vendor(user_data["vendor_id"])
        response = Response(
            {
                "isAuthenticated": True,
                "user": {**user_data, "last_login": last_login},
                "organization": organization,
                "zoho_vendor": zoho_vendor,
            }
        )
        response["X-CSRFToken"] = get_token(request)
        return response
    else:
        logout(request)
        return Response({"error": "Invalid user type."}, status=400)


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
    if user is None:
        raise AuthenticationFailed({"detail": "Invalid credentials."})

    last_login = user.last_login
    login(request, user)
    user_data = get_user_data(user)
    if user_data:
        organization = get_organization_data()
        zoho_vendor = get_vendor(user_data["vendor_id"])
        login_timestamp = timezone.now()
        UserLoginActivity.objects.create(
            user=user, timestamp=login_timestamp, platform=platform
        )
        response = Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
                "organization": organization,
                "zoho_vendor": zoho_vendor,
            }
        )
        response["X-CSRFToken"] = get_token(request)
        return response
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)


def filter_purchase_order_data(purchase_orders):
    try:
        filtered_purchase_orders = []
        for order in purchase_orders:
            purchaseorder_number = order.get("purchaseorder_number", "").strip()
            created_time_str = order.get("created_time", "").strip()
            if created_time_str:
                created_time = datetime.strptime(
                    created_time_str, "%Y-%m-%dT%H:%M:%S%z"
                )
                if (
                    purchaseorder_number in purchase_orders_allowed
                    or created_time.year >= 2024
                ):
                    filtered_purchase_orders.append(order)
        return filtered_purchase_orders
    except Exception as e:
        print(str(e))
        return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_purchase_orders(request, vendor_id):
    access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token_purchase_data:
        api_url = f"{base_url}/purchaseorders/?organization_id={organization_id}&vendor_id={vendor_id}"
        auth_header = {"Authorization": f"Bearer {access_token_purchase_data}"}
        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            purchase_orders = response.json().get("purchaseorders", [])
            purchase_orders = filter_purchase_order_data(purchase_orders)

            return Response(purchase_orders, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to fetch purchase orders"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoices_with_status(request, vendor_id, purchase_order_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        if purchase_order_id == "all":
            invoices = InvoiceData.objects.filter(vendor_id=vendor_id)

            invoices = filter_invoice_data(invoices)

            url = f"{base_url}/bills?organization_id={env('ZOHO_ORGANIZATION_ID')}&vendor_id={vendor_id}"
            bills_response = requests.get(url, headers=headers)
        else:
            invoices = InvoiceData.objects.filter(purchase_order_id=purchase_order_id)
            invoices = filter_invoice_data(invoices)
            url = f"{base_url}/bills?organization_id={env('ZOHO_ORGANIZATION_ID')}&purchaseorder_id={purchase_order_id}"
            bills_response = requests.get(
                url,
                headers=headers,
            )
        if bills_response.json()["message"] == "success":
            invoice_serializer = InvoiceDataSerializer(invoices, many=True)
            bills = bills_response.json()["bills"]
            invoice_res = []
            for invoice in invoice_serializer.data:
                matching_bill = next(
                    (
                        bill
                        for bill in bills
                        if bill.get(env("INVOICE_FIELD_NAME"))
                        == invoice["invoice_number"]
                    ),
                    None,
                )
                invoice_res.append({**invoice, "bill": matching_bill})
            return Response(invoice_res)
        else:
            return Response({}, status=400)
    else:
        return Response({}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_purchase_order_data(request, purchaseorder_id):
    access_token_purchase_order = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token_purchase_order:
        api_url = f"{base_url}/purchaseorders/{purchaseorder_id}?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token_purchase_order}"}

        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            purchase_order = response.json().get("purchaseorder")

            invoices = InvoiceData.objects.filter(
                purchase_order_no=purchase_order.get("purchaseorder_number")
            )

            line_item_details = get_line_items_details(invoices)
            for line_item in purchase_order["line_items"]:
                if line_item["line_item_id"] in line_item_details:
                    line_item["total_invoiced_quantity"] = line_item_details[
                        line_item["line_item_id"]
                    ]
            return Response(purchase_order, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to fetch purchase order data"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_purchase_order_data_pdf(request, purchaseorder_id):
    access_token_purchase_order = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token_purchase_order:
        api_url = f"{base_url}/purchaseorders/{purchaseorder_id}?print=true&accept=pdf&organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token_purchase_order}"}

        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            pdf_content = response.content
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="purchase_order.pdf"'
            )
            return response
        else:
            return Response(
                {"error": "Failed to fetch purchase order data"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


def get_tax(line_item, taxt_type):
    tax_based_on_type = next(
        (
            item
            for item in line_item.get("line_item_taxes", [])
            if taxt_type in item.get("tax_name", "")
        ),
        None,
    )
    percentage = (
        float(tax_based_on_type["tax_name"].split("(")[-1].split("%")[0])
        if tax_based_on_type
        else 0
    )
    return f"{percentage}%" if percentage else ""


def get_line_items_for_template(line_items):
    res = [*line_items]
    for line_item in res:
        line_item["quantity_mul_rate"] = round(
            line_item["quantity_input"] * line_item["rate"], 2
        )
        line_item["quantity_mul_rate_include_tax"] = round(
            line_item["quantity_input"]
            * line_item["rate"]
            * (1 + line_item["tax_percentage"] / 100),
            2,
        )
        line_item["tax_amount"] = round(
            (
                line_item["quantity_input"]
                * line_item["rate"]
                * line_item["tax_percentage"]
            )
            / 100,
            2,
        )
        line_item["cgst_tax"] = get_tax(line_item, "CGST")
        line_item["sgst_tax"] = get_tax(line_item, "SGST")
        line_item["igst_tax"] = get_tax(line_item, "IGST")
    return res


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_invoice_data(request):
    invoices = InvoiceData.objects.filter(
        vendor_id=request.data["vendor_id"],
        invoice_number=request.data["invoice_number"],
    )

    if invoices.count() > 0:
        return Response({"error": "Invoice number should be unique."}, status=400)

    serializer = InvoiceDataSerializer(data=request.data)
    if serializer.is_valid():
        invoice_instance = serializer.save()
        approver_email = serializer.data["approver_email"]
        invoice_data = get_invoice_data_for_pdf(invoice_instance)
        send_mail_templates(
            "vendors/add_invoice.html",
            [
                (
                    approver_email
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else "tech@meeraq.com"
                )
            ],
            f"Action Needed: Approval Required for Invoice - {invoice_data['vendor_name']}  + {invoice_data['invoice_number']}",
            {**invoice_data, "link": env("CAAS_APP_URL")},
            [],
        )
        return Response({"message": "Invoice generated successfully"}, status=201)
    else:
        return Response(serializer.errors, status=400)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(InvoiceData, id=invoice_id)
    if (
        InvoiceData.objects.filter(
            vendor_id=invoice.vendor_id, invoice_number=request.data["invoice_number"]
        )
        .exclude(id=invoice.id)
        .exists()
    ):
        return Response({"error": "Invoice already exists with the invoice number"})
    serializer = InvoiceDataEditSerializer(data=request.data, instance=invoice)
    if serializer.is_valid():
        serializer.save()
        invoice.status = "in_review"
        invoice.save()
        approver_email = invoice.approver_email
        invoice_data = get_invoice_data_for_pdf(invoice)
        send_mail_templates(
            "vendors/edit_invoice.html",
            [approver_email],
            f"Action Needed: Re-Approval Required for Invoice - {invoice_data['vendor_name']}  + {invoice_data['invoice_number']}",
            {**invoice_data, "link": env("CAAS_APP_URL")},
            [],
        )
        return Response({"message": "Invoice edited successfully."}, status=201)
    else:
        return Response({"error": "Invalid data."}, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_invoice(request, invoice_id):
    try:
        invoice = get_object_or_404(InvoiceData, id=invoice_id)
        invoice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except InvoiceData.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_purchase_order_and_invoices(request, purchase_order_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        api_url = f"{base_url}/purchaseorders/{purchase_order_id}?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            purchase_order = response.json()["purchaseorder"]

            invoices = InvoiceData.objects.filter(purchase_order_id=purchase_order_id)

            invoice_serializer = InvoiceDataSerializer(invoices, many=True)
            return Response(
                {"purchase_order": purchase_order, "invoices": invoice_serializer.data},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Failed to fetch purchase order data"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_bank_account_data(
    request,
    vendor_id,
    bank_account_id,
):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))

    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/contacts/{vendor_id}/bankaccount/editpage?account_id={bank_account_id}&organization_id={env('ZOHO_ORGANIZATION_ID')}"
        bank_response = requests.get(
            url,
            headers=headers,
        )
        if bank_response.json()["message"] == "success":
            return Response(bank_response.json(), status=200)
        return Response({}, status=400)
    else:
        return Response({}, status=400)


# @api_view(["GET"])
# def update_vendor_id(request):
#     access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
#     if access_token:
#         headers = {"Authorization": f"Bearer {access_token}"}
#         url = f"{base_url}/contacts?organization_id={env('ZOHO_ORGANIZATION_ID')}&contact_type=vendor"
#         vendor_response = requests.get(url, headers=headers)
#         if vendor_response.json()["message"] == "success":
#             for vendor in vendor_response.json()["contacts"]:
#                 if vendor["email"]:
#                     try:
#                         coach = Coach.objects.get(email=vendor["email"])
#                         coach.vendor_id = vendor["contact_id"]
#                         coach.save()
#                     except Coach.DoesNotExist:
#                         print(vendor["email"], "coach doesnt exist")
#                         pass
#             return Response(vendor_response.json())
#         else:
#             return Response({"error": "Failed to get vendors."}, status=400)
#     else:
#         return Response({"error": "Unauthorized	."}, status=400)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_vendor_exists_and_not_existing_emails(request):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/contacts?organization_id={env('ZOHO_ORGANIZATION_ID')}&contact_type=vendor"
        vendor_response = requests.get(url, headers=headers)
        if vendor_response.json()["message"] == "success":
            existing_vendors = []
            not_existing_vendors = []
            for vendor in vendor_response.json()["contacts"]:
                if vendor["email"]:
                    try:
                        existing_vendor = Vendor.objects.get(email=vendor["email"])
                        existing_vendors.append(vendor["email"])
                    except Vendor.DoesNotExist:
                        not_existing_vendors.append(vendor["email"])
                        pass
            return Response(
                {
                    "vendors": vendor_response.json()["contacts"],
                    "existing_vendors": existing_vendors,
                    "not_existing_vendors": not_existing_vendors,
                },
                status=200,
            )
        else:
            return Response({"error": "Failed to get vendors."}, status=400)
    else:
        return Response({"error": "Unauthorized	."}, status=400)


@api_view(["GET"])
@permission_classes([AllowAny])
def import_invoices_from_zoho(request):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        vendors = Vendor.objects.all()
        res = []
        bill_details_res = []
        for vendor in vendors:
            import_invoices_for_vendor_from_zoho(vendor, headers, res, bill_details_res)
        return Response({"res": res, "bill_details_res": bill_details_res}, status=200)
    else:
        return Response({"error": "Invalid invoices"}, status=400)


@api_view(["GET"])
@permission_classes([AllowAny])
def export_invoice_data(request):
    # Retrieve all InvoiceData objects
    queryset = InvoiceData.objects.all()

    # Create a new workbook and add a worksheet
    wb = Workbook()
    ws = wb.active

    # Write headers to the worksheet
    headers = [
        "Vendor ID",
        "Vendor Name",
        "Vendor Email",
        "Vendor Billing Address",
        "Vendor GST",
        "Vendor Phone",
        "Purchase Order ID",
        "Purchase Order No",
        "Invoice Number",
        "Customer Name",
        "Customer Notes",
        "Customer GST",
        "Total",
        "Is Oversea Account",
        "TIN Number",
        "Type of Code",
        "IBAN",
        "SWIFT Code",
        "Invoice Date",
        "Beneficiary Name",
        "Bank Name",
        "Account Number",
        "IFSC Code",
    ]

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    # Write data to the worksheet
    for row_num, invoice_data in enumerate(queryset, 2):
        ws.append(
            [
                invoice_data.vendor_id,
                invoice_data.vendor_name,
                invoice_data.vendor_email,
                invoice_data.vendor_billing_address,
                invoice_data.vendor_gst,
                invoice_data.vendor_phone,
                invoice_data.purchase_order_id,
                invoice_data.purchase_order_no,
                invoice_data.invoice_number,
                invoice_data.customer_name,
                invoice_data.customer_notes,
                invoice_data.customer_gst,
                invoice_data.total,
                invoice_data.is_oversea_account,
                invoice_data.tin_number,
                invoice_data.type_of_code,
                invoice_data.iban,
                invoice_data.swift_code,
                invoice_data.invoice_date,
                invoice_data.beneficiary_name,
                invoice_data.bank_name,
                invoice_data.account_number,
                invoice_data.ifsc_code,
            ]
        )

    # Create a response with the Excel file
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=invoice_data.xlsx"
    wb.save(response)

    return response


class DownloadInvoice(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            invoice = get_object_or_404(InvoiceData, id=record_id)
            invoice_data = get_invoice_data_for_pdf(invoice)
            image_base64 = None
            try:
                image_url = f"{invoice_data['signature']}"
                # Attempt to send the email
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                # Convert the downloaded image to base64
                image_base64 = base64.b64encode(image_response.content).decode("utf-8")
            except Exception as e:
                pass
            email_message = render_to_string(
                "invoice_pdf.html",
                {"invoice": invoice_data, "image_base64": image_base64},
            )
            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename={f"{invoice.invoice_number}_invoice.pdf"}'
            )
            return response
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to download invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_vendor(request):
    # Extract data from the request
    with transaction.atomic():
        data = request.data
        name = data.get("name", "")
        email = data.get("email", "").strip().lower()
        vendor_id = data.get("vendor", "")
        phone = data.get("phone", "")

        try:
            # Check if the user with the given email already exists
            user_profile = Profile.objects.get(user__email=email)
            user = user_profile.user

            # Check if the user has the role 'vendor'
            if user_profile.roles.filter(name="vendor").exists():
                return Response(
                    {"detail": "User already exists as a vendor."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # If the user was not a vendor, update the Vendor model
            try:
                vendor = Vendor.objects.get(user=user_profile)
                # Check if the provided vendor_id already exists for another vendor
                if (
                    Vendor.objects.exclude(id=vendor.id)
                    .filter(vendor_id=vendor_id)
                    .exists()
                ):
                    return Response(
                        {"detail": "Vendor with the same vendor_id already exists."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                vendor.name = name
                vendor.phone = phone
                vendor.vendor_id = vendor_id
                vendor.save()

            except Vendor.DoesNotExist:
                # Check if the provided vendor_id already exists for another vendor
                if Vendor.objects.filter(vendor_id=vendor_id).exists():
                    return Response(
                        {"detail": "Vendor with the same vendor_id already exists."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                vendor_role, created = Role.objects.get_or_create(name="vendor")
                vendor = Vendor.objects.create(
                    user=user_profile,
                    name=name,
                    email=email,
                    vendor_id=vendor_id,
                    phone=phone,
                )
                vendor.save()
                import_invoice_for_new_vendor.delay(vendor.id)
            return Response(
                {"detail": 'Role "vendor" assigned to the existing user successfully.'},
                status=status.HTTP_200_OK,
            )

        except Profile.DoesNotExist:
            # User with the given email doesn't exist, create a new Vendor
            try:
                # Check if the provided vendor_id already exists for another vendor
                if Vendor.objects.filter(vendor_id=vendor_id).exists():
                    return Response(
                        {"detail": "Vendor with the same vendor_id already exists."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user = User.objects.create_user(email, email=email)
                user.set_unusable_password()
                user.save()
                vendor_role, created = Role.objects.get_or_create(name="vendor")
                profile = Profile.objects.create(user=user)
                profile.roles.add(vendor_role)
                profile.save()

                vendor = Vendor.objects.create(
                    user=profile,
                    name=name,
                    email=email,
                    vendor_id=vendor_id,
                    phone=phone,
                )
                vendor.save()

                return Response(
                    {"detail": "New vendor created successfully."},
                    status=status.HTTP_201_CREATED,
                )

            except Exception as e:
                return Response(
                    {"detail": f"Error creating vendor: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_vendors(request):
    try:
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"detail": f"Error fetching vendors: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def fetch_purchase_orders(organization_id):
    access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if not access_token_purchase_data:
        raise Exception(
            "Access token not found. Please generate an access token first."
        )

    all_purchase_orders = []
    has_more_page = True
    page = 1

    while has_more_page:
        api_url = (
            f"{base_url}/purchaseorders/?organization_id={organization_id}&page={page}"
        )
        auth_header = {"Authorization": f"Bearer {access_token_purchase_data}"}
        response = requests.get(api_url, headers=auth_header)

        if response.status_code == 200:
            purchase_orders = response.json().get("purchaseorders", [])
            purchase_orders = filter_purchase_order_data(purchase_orders)
            all_purchase_orders.extend(purchase_orders)

            page_context = response.json().get("page_context", {})
            has_more_page = page_context.get("has_more_page", False)
            page += 1
        else:
            raise Exception("Failed to fetch purchase orders")

    return all_purchase_orders


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_purchase_orders(request):
    try:
        all_purchase_orders = fetch_purchase_orders(organization_id)
        return Response(all_purchase_orders, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_invoices(request):
    try:
        access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if access_token_purchase_data:
            all_bills = fetch_bills(organization_id)
            invoices = InvoiceData.objects.all()
            invoices = filter_invoice_data(invoices)
            invoice_serializer = InvoiceDataSerializer(invoices, many=True)
            all_invoices = []
            for invoice in invoice_serializer.data:
                matching_bill = next(
                    (
                        bill
                        for bill in all_bills
                        if bill.get(env("INVOICE_FIELD_NAME"))
                        == invoice["invoice_number"]
                    ),
                    None,
                )
                all_invoices.append({**invoice, "bill": matching_bill})

            return Response(all_invoices, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "error": "Access token not found. Please generate an access token first."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_invoice_status(request, invoice_id):
    try:
        invoice = InvoiceData.objects.get(pk=invoice_id)
    except InvoiceData.DoesNotExist:
        return Response({"error": "Invoice does not exist"}, status=404)
    new_status = request.data.get("status")
    if new_status not in ["rejected", "approved"]:
        return Response({"error": "Invalid status"}, status=400)
    invoice.status = new_status
    invoice.save()
    comment = request.data.get("comment", "")
    approval = InvoiceStatusUpdate.objects.create(
        invoice=invoice,
        status=new_status,
        comment=comment,
        user=request.user,
    )
    approval.save()
    invoice_data = get_invoice_data_for_pdf(invoice)
    if new_status == "approved":
        email_body_message = render_to_string(
            "vendors/approve_invoice.html",
            {**invoice_data, "comment": comment, "approved_by": request.user.username},
        )
        send_mail_templates_with_attachment(
            "invoice_pdf.html",
            [env("FINANCE_EMAIL")],
            f"Meeraq | Invoice Approved - {invoice_data['purchase_order_no']} + {invoice_data['vendor_name']} ",
            {"invoice": invoice_data},
            email_body_message,
            [env("BCC_EMAIL")],
        )
    else:
        send_mail_to = invoice.vendor_email if env("ENVIRONMENT") == "PRODUCTION" else "tech@meeraq.com"
        send_mail_templates(
            "vendors/reject_invoice.html",
            [send_mail_to],
            "Meeraq - Invoice Rejected",
            {"vendor_name": invoice.vendor_name, "comment": comment},
            [],
        )
    return Response({"message": f"Invoice {invoice.invoice_number} {new_status}."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoice_updates(request, invoice_id):
    try:
        updates = InvoiceStatusUpdate.objects.filter(invoice_id=invoice_id).order_by(
            "-created_at"
        )
        serializer = InvoiceStatusUpdateGetSerializer(updates, many=True)
        return Response(serializer.data)
    except InvoiceStatusUpdate.DoesNotExist:
        return Response(status=404)


# cf_invoice_approver_s_email

# Final Task
# Add new option in zoho to add Email of the person who will approve the invoice against the PO. -> Done
# Then Invoice is Generated by vendor
# Disable email to finance -> Done
# Send the email to Approvers email, given in zoho -> Done
# In pmo view  → Only for nisha@meeraq.com  and madhuri@meeraq.com show the options to approve and reject + the approvers email. (Usually they approve)
# Billing → Invoice tab
# New status → In Review for the unapproved invoices
# Approve and Reject buttons for each invoice in In Review status
# Onclick Approve → show a pop up with some commenting feild or feild to add description
# Once confirmed → Finance gets a email with the approved invoice with the description included by the pmo (Ask naveen for email content)
# Once Rejected → show the pop up to enter comment which “will be shared to the vendor”
# Email to vendor , with the comment and the invoice file (Email content connect with naveen)
# Every week , a email to pmocoaching regarding the invoices pending (email content connect with naveen)
# cc rajat and sujata
# invoices to approve
# approvers name
# Invoice generated date
# Link to caas to approve → click here to login to caas inn the email
