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
from api.models import (
    Coach,
    OTP,
    UserLoginActivity,
    Profile,
    Role,
    CoachStatus,
    Project,
)
from api.serializers import CoachDepthOneSerializer
from openpyxl import Workbook
import json

from rest_framework.views import APIView
import string
import random
from django.db.models import Q
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
    VendorEditSerializer,
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
    fetch_purchase_orders,
    fetch_sales_orders,
    filter_purchase_order_data,
    fetch_customers_from_zoho,
    fetch_client_invoices,
)
from .models import (
    InvoiceData,
    AccessToken,
    Vendor,
    InvoiceStatusUpdate,
    OrdersAndProjectMapping,
)
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
from collections import defaultdict
import re
from schedularApi.models import (
    FacilitatorPricing,
    CoachPricing,
    SchedularBatch,
    Expense,
    SchedularProject,
)
from api.models import Facilitator
from decimal import Decimal
from collections import defaultdict

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
    hsn_or_sac = None
    try:
        hsn_or_sac = Vendor.objects.get(vendor_id=invoice.vendor_id).hsn_or_sac
    except Exception as e:
        pass
    invoice_data = {
        **serializer.data,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "line_items": line_items,
        "sub_total_excluding_tax": get_subtotal_excluding_tax(
            serializer.data["line_items"]
        ),
        "hsn_or_sac": hsn_or_sac if hsn_or_sac else "-",
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
    file_name,
    user_email,
    email_subject,
    content,
    body_message,
    bcc_emails,
    is_send_attatched_invoice,
):
    try:
        datetime_obj = datetime.strptime(
            content["invoice"]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        formatted_date = datetime_obj.strftime("%d-%m-%Y")
        pdf_name = f"{content['invoice']['vendor_name']}_{formatted_date}.pdf"
        email = EmailMessage(
            subject=f"{env('EMAIL_SUBJECT_INITIAL', default='')} {email_subject}",
            body=body_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=user_email,
            bcc=bcc_emails,
        )
        if is_send_attatched_invoice:
            attachment_url = content["invoice"]["attatched_invoice"]
            # attachment_file_name = attachment_url.split('/')[-1].split('?')[0]
            attachment_response = requests.get(attachment_url)
            if attachment_response.status_code == 200:
                email.attach(pdf_name, attachment_response.content, "application/pdf")
            else:
                pass
        else:
            image_url = f"{content['invoice']['signature']}"
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            image_base64 = base64.b64encode(image_response.content).decode("utf-8")
            content["image_base64"] = image_base64
            email_message = render_to_string(file_name, content)
            pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)
            result = BytesIO(pdf)
            email.attach(
                pdf_name,
                result.getvalue(),
                "application/pdf",
            )

        # Convert the downloaded image to base64
        # Attach the PDF to the email
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
    if not user.profile.vendor.active_inactive:
        return None
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
        print(str(e))
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
        print(str(e))
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
                hsn_or_sac = Vendor.objects.get(
                    vendor_id=invoice["vendor_id"]
                ).hsn_or_sac
                matching_bill = next(
                    (
                        bill
                        for bill in bills
                        if (
                            bill.get(env("INVOICE_FIELD_NAME"))
                            == invoice["invoice_number"]
                            and bill.get("vendor_id") == invoice["vendor_id"]
                        )
                    ),
                    None,
                )
                invoice_res.append(
                    {
                        **invoice,
                        "bill": matching_bill,
                        "hsn_or_sac": hsn_or_sac if hsn_or_sac else "",
                    }
                )
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
                    vendor_id = purchase_order.get("vendor_id")
                    if vendor_id:
                        vendor = Vendor.objects.filter(vendor_id=vendor_id).first()
                        hsn_or_sac = vendor.hsn_or_sac if vendor else None
                        line_item["hsn_sac_vendor_modal"] = hsn_or_sac
                    else:
                        line_item["hsn_sac_vendor_modal"] = None
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


def get_subtotal_excluding_tax(line_items):
    res = 0
    for line_item in line_items:
        res += round(line_item["quantity_input"] * line_item["rate"])
    return res


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
    hsn_or_sac = request.data.get("hsn_or_sac", None)
    if hsn_or_sac:
        try:
            vendor = Vendor.objects.get(vendor_id=request.data["vendor_id"])
            vendor.hsn_or_sac = hsn_or_sac
            vendor.save()
        except Exception as e:
            print(str(e))
            return Response({"error": "Vendor not found."}, status=400)

    if invoices.count() > 0:
        return Response({"error": "Invoice number should be unique."}, status=400)

    vendor = Vendor.objects.get(vendor_id=request.data["vendor_id"])

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
        print(serializer.errors)
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
    vendor = Vendor.objects.get(vendor_id=request.data["vendor_id"])

    if serializer.is_valid():
        serializer.save()
        invoice.status = "in_review"
        invoice.save()
        approver_email = invoice.approver_email
        invoice_data = get_invoice_data_for_pdf(invoice)
        send_mail_templates(
            "vendors/edit_invoice.html",
            [
                (
                    approver_email
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else "tech@meeraq.com"
                )
            ],
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
        print(str(e))
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
            serializer = InvoiceDataSerializer(invoice)

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


class DownloadAttatchedInvoice(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            invoice = get_object_or_404(InvoiceData, id=record_id)
            serializer = InvoiceDataSerializer(invoice)
            response = requests.get(serializer.data["attatched_invoice"])
            if response.status_code == 200:
                file_content = response.content
                content_type = response.headers.get("Content-Type", f"application/pdf")
                file_response = HttpResponse(file_content, content_type=content_type)
                file_response["Content-Disposition"] = (
                    f'attachment; filename={f"{invoice.invoice_number}_invoice.pdf"}'
                )
                return file_response
            else:
                return HttpResponse(
                    "Failed to download the file", status=response.status_code
                )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to download invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DownloadAttatchedInvoice(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            invoice = get_object_or_404(InvoiceData, id=record_id)
            serializer = InvoiceDataSerializer(invoice)
            response = requests.get(serializer.data["attatched_invoice"])
            if response.status_code == 200:
                file_content = response.content
                content_type = response.headers.get("Content-Type", f"application/pdf")
                file_response = HttpResponse(file_content, content_type=content_type)
                file_response["Content-Disposition"] = (
                    f'attachment; filename={f"{invoice.invoice_number}_invoice.pdf"}'
                )
                return file_response
            else:
                return HttpResponse(
                    "Failed to download the file", status=response.status_code
                )

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
                user_profile.roles.add(vendor_role)
                user_profile.save()
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
                # user.set_unusable_password()
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
        print(str(e))
        return Response(
            {"detail": f"Error fetching vendors: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_purchase_orders(request):
    try:
        all_purchase_orders = fetch_purchase_orders(organization_id)
        return Response(all_purchase_orders, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_purchase_orders_for_pmo(request):
    try:
        all_purchase_orders = fetch_purchase_orders(organization_id)
        pmos_allowed = json.loads(env("PMOS_ALLOWED_TO_VIEW_ALL_INVOICES_AND_POS"))
        if not request.user.username in pmos_allowed:
            all_purchase_orders = [
                purchase_order
                for purchase_order in all_purchase_orders
                if "cf_invoice_approver_s_email" in purchase_order
                and purchase_order["cf_invoice_approver_s_email"].strip().lower()
                == request.user.username.strip().lower()
            ]
        # filter based on the conditions
        return Response(all_purchase_orders, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def fetch_invoices(organization_id):
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
                if (
                    bill.get(env("INVOICE_FIELD_NAME")) == invoice["invoice_number"]
                    and bill.get("vendor_id") == invoice["vendor_id"]
                )
            ),
            None,
        )
        all_invoices.append({**invoice, "bill": matching_bill})
    return all_invoices


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_invoices(request):
    try:
        all_invoices = fetch_invoices(organization_id)
        return Response(all_invoices, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoices_for_pmo(request):
    try:
        all_invoices = fetch_invoices(organization_id)
        pmos_allowed = json.loads(env("PMOS_ALLOWED_TO_VIEW_ALL_INVOICES_AND_POS"))
        if not request.user.username in pmos_allowed:
            all_invoices = [
                invoice
                for invoice in all_invoices
                if invoice["approver_email"].strip().lower() == request.user.username
            ]
        return Response(all_invoices, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoices_by_status(request, status):
    try:
        all_invoices = fetch_invoices(organization_id)
        res = []
        for invoice_data in all_invoices:
            if status == "approved":
                if invoice_data["bill"]:
                    if (
                        "status" in invoice_data["bill"]
                        and not invoice_data["bill"]["status"] == "paid"
                    ):
                        res.append(invoice_data)
                elif invoice_data["status"] == "approved":
                    res.append(invoice_data)
            elif status == "paid":
                if invoice_data["bill"] and invoice_data["bill"]["status"] == "paid":
                    res.append(invoice_data)

        return Response(res, status=200)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to load"}, status=400)

def get_purchase_order_ids_for_project(project_id):
    coach_pricings = CoachPricing.objects.filter(project__id=project_id)
    facilitator_pricings = FacilitatorPricing.objects.filter(project__id=project_id)
    purchase_order_set = {}
    for coach_pricing in coach_pricings:
        if coach_pricing.purchase_order_id in purchase_order_set:
            continue
        purchase_order_set[coach_pricing.purchase_order_id]
    for facilitator_pricing in facilitator_pricings:
        if facilitator_pricing.purchase_order_id in purchase_order_set:
            continue
        purchase_order_set[facilitator_pricing.purchase_order_id]

    return list(purchase_order_set)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_invoices_by_status_for_founders(request, status):

    try:
        all_invoices = fetch_invoices(organization_id)
        project_id = request.query_params.get("project_id")
        if project_id:
            purchase_order_ids = get_purchase_order_ids_for_project(project_id)

        res = []
        
        for invoice_data in all_invoices:
            if project_id and invoice_data["purchase_order_id"] not in purchase_order_ids:
                continue
            if status == "in_review":
                if not invoice_data["bill"] and invoice_data["status"] == "in_review":
                    res.append(invoice_data)
            elif status == "approved":
                if not invoice_data["bill"] and invoice_data["status"] == "approved":
                    res.append(invoice_data)
            elif status == "rejected":
                if not invoice_data["bill"] and invoice_data["status"] == "rejected":
                    res.append(invoice_data)
            if status == "accepted":
                if invoice_data["bill"]:
                    if (
                        "status" in invoice_data["bill"]
                        and not invoice_data["bill"]["status"] == "paid"
                    ):
                        res.append(invoice_data)
            elif status == "paid":
                if invoice_data["bill"] and invoice_data["bill"]["status"] == "paid":
                    res.append(invoice_data)
        return Response(res, status=200)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to load"}, status=400)


@api_view(["PUT"])
def edit_vendor(request, vendor_id):
    try:
        vendor = Vendor.objects.get(id=vendor_id)

        data = request.data
        name = data.get("name", "")
        email = data.get("email", "").strip().lower()
        vendor_id = data.get("vendor", "")
        phone = data.get("phone", "")
        existing_user = (
            User.objects.filter(username=email).exclude(username=vendor.email).first()
        )
        if existing_user:
            return Response(
                {"error": "User with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vendor.user.user.username = email
        vendor.user.user.email = email
        vendor.user.user.save()
        vendor.email = email
        vendor.name = name
        vendor.phone = phone
        vendor.vendor_id = vendor_id

        vendor.save()

        return Response(
            {"message": "Vendor updated successfully!"}, status=status.HTTP_200_OK
        )
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to update vendor"}, status=status.HTTP_404_NOT_FOUND
        )


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
    vendor = Vendor.objects.get(vendor_id=invoice.vendor_id)
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
            vendor.is_upload_invoice_allowed,
        )
    else:
        send_mail_to = (
            invoice.vendor_email
            if env("ENVIRONMENT") == "PRODUCTION"
            else "tech@meeraq.com"
        )
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_vendor_details_from_zoho(request, vendor_id):
    try:

        vendor = Vendor.objects.get(vendor_id=vendor_id)

        user = vendor.user.user
        user_data = get_user_data(user)
        if user_data:
            organization = get_organization_data()
            zoho_vendor = get_vendor(user_data["vendor_id"])
            res = {
                "vendor": user_data,
                "organization": organization,
                "zoho_vendor": zoho_vendor,
            }
            return Response(res)

    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data."}, status=500)


# creating a PO in zoho and adding the create po id and number in either coach pricing or facilitator pricing
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_purchase_order(request, user_type, facilitator_pricing_id):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if user_type == "facilitator":
            facilitator_pricing = FacilitatorPricing.objects.get(
                id=facilitator_pricing_id
            )
        elif user_type == "coach":
            coach_pricing = CoachPricing.objects.get(id=facilitator_pricing_id)
            coach_pricings = CoachPricing.objects.filter(
                project=coach_pricing.project, coach=coach_pricing.coach
            )
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/purchaseorders?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=auth_header, data=request.data)
        if response.status_code == 201:
            purchaseorder_created = response.json().get("purchaseorder")
            if user_type == "facilitator":
                facilitator_pricing.purchase_order_id = purchaseorder_created[
                    "purchaseorder_id"
                ]
                facilitator_pricing.purchase_order_no = purchaseorder_created[
                    "purchaseorder_number"
                ]
                facilitator_pricing.save()
            elif user_type == "coach":
                for coach_pricing in coach_pricings:
                    coach_pricing.purchase_order_id = purchaseorder_created[
                        "purchaseorder_id"
                    ]
                    coach_pricing.purchase_order_no = purchaseorder_created[
                        "purchaseorder_number"
                    ]
                    coach_pricing.save()
            return Response({"message": "Purchase Order created successfully."})
        else:
            print(response.json())
            return Response(status=401)
    except Exception as e:
        print(str(e))
        return Response(status=404)


def get_current_financial_year():
    today = date.today()
    current_year = today.year
    financial_year_start = date(
        current_year, 4, 1
    )  # Financial year starts from April 1st
    if today < financial_year_start:
        financial_year = str(current_year - 1)[2:] + "-" + str(current_year)[2:]
    else:
        financial_year = str(current_year)[2:] + "-" + str(current_year + 1)[2:]
    return financial_year


def generate_new_po_number(po_list, regex_to_match):
    # pattern to match the purchase order number
    pattern = rf"^{regex_to_match}\d+$"
    # Filter out purchase orders with the desired format
    filtered_pos = [
        po for po in po_list if re.match(pattern, po["purchaseorder_number"])
    ]
    latest_number = 0
    # Finding the latest number for each year
    for po in filtered_pos:
        print(po["purchaseorder_number"].split("/"))
        _, _, _, _, po_number = po["purchaseorder_number"].split("/")
        latest_number = max(latest_number, int(po_number))
    # Generating the new purchase order number
    new_number = latest_number + 1
    new_po_number = f"{regex_to_match}{str(new_number).zfill(4)}"
    return new_po_number


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_po_number_to_create(request):
    try:
        purchase_orders = fetch_purchase_orders(organization_id)
        current_financial_year = get_current_financial_year()
        regex_to_match = f"Meeraq/PO/{current_financial_year}/T/"
        new_po_number = generate_new_po_number(purchase_orders, regex_to_match)
        return Response({"new_po_number": new_po_number})
    except Exception as e:
        print(str(e))
        return Response(status=403)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_purchase_order_status(request, purchase_order_id, status):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/purchaseorders/{purchase_order_id}/status/{status}?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=auth_header)
        print(response.json())
        if response.status_code == 200:
            return Response({"message": f"Purchase Order changed to {status}."})
        else:
            return Response(status=401)
    except Exception as e:
        print(str(e))
        return Response(status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def coching_purchase_order_create(request, coach_id, project_id):
    try:
        coach_status = CoachStatus.objects.get(
            coach__id=coach_id, project__id=project_id
        )

        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/purchaseorders?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=auth_header, data=request.data)
        if response.status_code == 201:
            purchaseorder_created = response.json().get("purchaseorder")

            coach_status.purchase_order_id = purchaseorder_created["purchaseorder_id"]
            coach_status.purchase_order_no = purchaseorder_created[
                "purchaseorder_number"
            ]
            coach_status.save()

            return Response({"message": "Purchase Order created successfully."})
        else:
            print(response.json())
            return Response(status=500)
    except Exception as e:
        print(str(e))
        return Response(status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_coaching_purchase_order(request, purchase_order_id):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/purchaseorders/{purchase_order_id}?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.delete(api_url, headers=auth_header)
        print(response.json())
        if response.status_code == 200:
            CoachStatus.objects.filter(purchase_order_id=purchase_order_id).update(
                purchase_order_id="", purchase_order_no=""
            )
            return Response({"message": "Purchase Order deleted successfully."})
        else:
            return Response(status=401)
    except Exception as e:
        print(str(e))
        return Response(status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def expense_purchase_order_create(request, facilitator_id, batch_id):
    try:
        facilitator = Facilitator.objects.get(id=facilitator_id)
        batch = SchedularBatch.objects.get(id=batch_id)
        expenses = Expense.objects.filter(facilitator=facilitator, batch=batch)
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/purchaseorders?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=auth_header, data=request.data)
        if response.status_code == 201:
            purchaseorder_created = response.json().get("purchaseorder")
            for expense in expenses:
                expense.purchase_order_id = purchaseorder_created["purchaseorder_id"]
                expense.purchase_order_no = purchaseorder_created[
                    "purchaseorder_number"
                ]
                expense.save()

            return Response({"message": "Purchase Order created successfully."})
        else:
            print(response.json())
            return Response(status=500)
    except Exception as e:
        print(str(e))
        return Response(status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_coach_wise_finances(request):
    try:
        # Fetch all invoices and purchase orders
        all_invoices = fetch_invoices(organization_id)
        all_purchase_orders = fetch_purchase_orders(organization_id)
        # Filter vendors who are coaches
        vendors = Vendor.objects.filter(user__roles__name="coach")
        # Calculate purchase order amounts
        vendor_po_amounts = {}
        for po in all_purchase_orders:
            if po["status"] not in ["draft", "cancelled"]:
                vendor_id = po["vendor_id"]
                total_amount = Decimal(po["total"])
                if vendor_id in vendor_po_amounts:
                    vendor_po_amounts[vendor_id] += total_amount
                else:
                    vendor_po_amounts[vendor_id] = total_amount

        # Calculate invoice amounts and paid amounts
        vendor_invoice_amounts = {}
        for invoice in all_invoices:
            vendor_id = invoice["vendor_id"]
            invoiced_amount = Decimal(invoice["total"])
            paid_amount = (
                Decimal(invoice["total"])
                if invoice["bill"] and invoice["bill"]["status"] == "paid"
                else Decimal(0)
            )
            if vendor_id in vendor_invoice_amounts:
                vendor_invoice_amounts[vendor_id]["invoiced_amount"] += invoiced_amount
                vendor_invoice_amounts[vendor_id]["paid_amount"] += paid_amount
                vendor_invoice_amounts[vendor_id]["currency_symbol"] = (
                    invoice["currency_symbol"]
                    if not vendor_invoice_amounts[vendor_id]["currency_symbol"]
                    else vendor_invoice_amounts[vendor_id]["currency_symbol"]
                )
            else:
                vendor_invoice_amounts[vendor_id] = {
                    "invoiced_amount": invoiced_amount,
                    "paid_amount": paid_amount,
                    "currency_symbol": invoice["currency_symbol"],
                }

        # Prepare response
        res = []
        for vendor in vendors:
            vendor_id = vendor.vendor_id
            res.append(
                {
                    "id": vendor.id,
                    "vendor_id": vendor_id,
                    "vendor_name": vendor.name,
                    "po_amount": vendor_po_amounts.get(vendor_id, Decimal(0)),
                    "invoiced_amount": vendor_invoice_amounts.get(
                        vendor_id, {"invoiced_amount": Decimal(0)}
                    )["invoiced_amount"],
                    "paid_amount": vendor_invoice_amounts.get(
                        vendor_id, {"paid_amount": Decimal(0)}
                    )["paid_amount"],
                    "currency_symbol": vendor_invoice_amounts[vendor_id][
                        "currency_symbol"
                    ],
                }
            )
        return Response(res)
    except Exception as e:
        print(str(e))
        return Response(status=403)


def create_purchase_order_project_mapping():
    coach_pricings = CoachPricing.objects.all()
    facilitator_pricings = FacilitatorPricing.objects.all()

    # Create a dictionary to store the mapping of purchase_order_id to project_id
    purchase_order_project_mapping = {}

    # Iterate over CoachPricing instances and add purchase_order_id to project_id mapping
    for coach_pricing in coach_pricings:
        purchase_order_id = coach_pricing.purchase_order_id
        project_id = coach_pricing.project.id
        purchase_order_project_mapping[purchase_order_id] = project_id

    # Iterate over FacilitatorPricing instances and add purchase_order_id to project_id mapping
    for facilitator_pricing in facilitator_pricings:
        purchase_order_id = facilitator_pricing.purchase_order_id
        project_id = facilitator_pricing.project.id
        purchase_order_project_mapping[purchase_order_id] = project_id

    return purchase_order_project_mapping


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_wise_finances(request):
    try:
        purchase_order_project_mapping = create_purchase_order_project_mapping()
        all_invoices = fetch_invoices(organization_id)
        all_purchase_orders = fetch_purchase_orders(organization_id)

        # Filter vendors who are coaches
        schedular_projects = SchedularProject.objects.all()

        # Calculate purchase order amounts
        project_po_amounts = {}
        for po in all_purchase_orders:

            if (
                po["status"] not in ["draft", "cancelled"]
                and po["purchaseorder_id"] in purchase_order_project_mapping
            ):
                project_id = purchase_order_project_mapping[po["purchaseorder_id"]]
                total_amount = Decimal(po["total"])
                if project_id in project_po_amounts:
                    project_po_amounts[project_id] += total_amount
                else:
                    project_po_amounts[project_id] = total_amount

        # Calculate invoice amounts and paid amounts
        project_invoice_amounts = {}
        for invoice in all_invoices:
            if invoice["purchase_order_id"] in purchase_order_project_mapping:
                project_id = purchase_order_project_mapping[
                    invoice["purchase_order_id"]
                ]
                invoiced_amount = Decimal(invoice["total"])
                paid_amount = (
                    Decimal(invoice["total"])
                    if invoice["bill"] and invoice["bill"]["status"] == "paid"
                    else Decimal(0)
                )
                if project_id in project_invoice_amounts:
                    project_invoice_amounts[project_id][
                        "invoiced_amount"
                    ] += invoiced_amount
                    project_invoice_amounts[project_id]["paid_amount"] += paid_amount
                    project_invoice_amounts[project_id]["currency_symbol"] = (
                        invoice["currency_symbol"]
                        if not project_invoice_amounts[project_id]["currency_symbol"]
                        else project_invoice_amounts[project_id]["currency_symbol"]
                    )
                else:
                    project_invoice_amounts[project_id] = {
                        "invoiced_amount": invoiced_amount,
                        "paid_amount": paid_amount,
                        "currency_symbol": invoice.get("currency_symbol", ""),
                    }

        # Prepare response
        res = []
        for project in schedular_projects:
            project_id = project.id
            if (
                project_id in project_po_amounts
                or project_id in project_invoice_amounts
            ):
                res.append(
                    {
                        "id": project_id,
                        "project_name": project.name,
                        "po_amount": project_po_amounts.get(project_id, Decimal(0)),
                        "invoiced_amount": project_invoice_amounts.get(
                            project_id, {"invoiced_amount": Decimal(0)}
                        )["invoiced_amount"],
                        "paid_amount": project_invoice_amounts.get(
                            project_id, {"paid_amount": Decimal(0)}
                        )["paid_amount"],
                        "currency_symbol": project_invoice_amounts.get(
                            project_id, {}
                        ).get("currency_symbol", ""),
                    }
                )

        return Response(res)
    except Exception as e:
        print(str(e))
        return Response(status=403)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_expense_purchase_order(request, purchase_order_id):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/purchaseorders/{purchase_order_id}?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.delete(api_url, headers=auth_header)
        print(response.json())
        if response.status_code == 200:
            Expense.objects.filter(purchase_order_id=purchase_order_id).update(
                purchase_order_id="", purchase_order_no=""
            )
            return Response({"message": "Purchase Order deleted successfully."})
        else:
            return Response(status=401)
    except Exception as e:
        print(str(e))
        return Response(status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_sales_orders(request):
    try:
        all_sales_orders = fetch_sales_orders(organization_id)
        return Response(all_sales_orders, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_sales_order_data_pdf(request, salesorder_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        api_url = f"{base_url}/salesorders/{salesorder_id}?print=true&accept=pdf&organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            pdf_content = response.content
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="sales_order.pdf"'
            return response
        else:
            return Response(
                {"error": "Failed to fetch sales order data"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sales_order_data(request, salesorder_id):
    access_token_sales_order = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token_sales_order:
        api_url = (
            f"{base_url}/salesorders/{salesorder_id}?organization_id={organization_id}"
        )
        auth_header = {"Authorization": f"Bearer {access_token_sales_order}"}
        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            sales_order = response.json().get("salesorder")
            return Response(sales_order, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to fetch sales order data"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_customers_from_zoho(request):
    try:
        customers = fetch_customers_from_zoho(organization_id)
        return Response(customers, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_customer_details_from_zoho(request, customer_id):
    try:
        zoho_vendor = get_vendor(customer_id)
        return Response(zoho_vendor)
    except Exception as e:
        print(str(e))
        return Response({"error": "Failed to get data."}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_invoice(request):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/invoices?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=auth_header, data=request.data)
        print(response.json())
        if response.status_code == 201:
            return Response({"message": "Invoice created successfully."})
        else:
            print(response.json())
            return Response(status=401)
    except Exception as e:
        print(str(e))
        return Response(status=404)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def edit_so_invoice(request,invoice_id):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/invoices/{invoice_id}?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=auth_header, data=request.data)
        print(response.json())
        if response.status_code == 201:
            return Response({"message": "Invoice created successfully."})
        else:
            print(response.json())
            return Response(status=401)
    except Exception as e:
        print(str(e))
        return Response(status=404)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sales_order(request):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if not access_token:
            raise Exception(
                "Access token not found. Please generate an access token first."
            )
        api_url = f"{base_url}/salesorders?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=auth_header, data=request.data)
        print(response.json())
        if response.status_code == 201:
            salesorder_created = response.json().get("salesorder")
            project_id = request.data.get("project_id", "")
            project_type = request.data.get("project_type", "")
            project = None
            schedular_project = None
            orders_and_project_mapping = None

            if project_id:
                if project_type == "caas":
                    project = Project.objects.get(id=project_id)
                    orders_and_project_mapping = OrdersAndProjectMapping.objects.filter(
                        Q(project=project)
                    )
                elif project_type == "skill_training":
                    schedular_project = SchedularProject.objects.get(id=project_id)
                    orders_and_project_mapping = OrdersAndProjectMapping.objects.filter(
                        Q(schedular_project=schedular_project)
                    )

            if (
                not orders_and_project_mapping
                or not orders_and_project_mapping.exists()
            ):
                OrdersAndProjectMapping.objects.create(
                    project=project,
                    schedular_project=schedular_project,
                    sales_order_ids=[salesorder_created["salesorder_id"]],
                )
            else:
                mapping = orders_and_project_mapping.first()
                mapping.project = project
                mapping.schedular_project = schedular_project
                mapping.sales_order_ids = [
                    *mapping.sales_order_ids,
                    salesorder_created["salesorder_id"],
                ]
                mapping.save()
            # add the mapping for sales order here
            return Response({"message": "Sales Order created successfully."})
        else:
            print(response.json())
            return Response(status=401)
    except Exception as e:
        print(str(e))
        return Response(status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_client_invoices(request):
    try:
        all_client_invoices = fetch_client_invoices(organization_id)
        return Response(all_client_invoices, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_client_invoice_data(request, invoice_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        api_url = f"{base_url}/invoices/{invoice_id}?organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            client_invoice = response.json().get("invoice")
            return Response(client_invoice, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to fetch invoices data"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_client_invoice_data_pdf(request, invoice_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        api_url = f"{base_url}/invoices/{invoice_id}?print=true&accept=pdf&organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            pdf_content = response.content
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="invoice.pdf"'
            return response
        else:
            return Response(
                {"error": "Failed to fetch invoice data"},
                status=response.status_code,
            )
    else:
        return Response(
            {"error": "Access token not found. Please generate an access token first."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_sales_orders(request, project_id):
    try:
        orders_and_project_mapping = OrdersAndProjectMapping.objects.filter(
            project=project_id
        )
        res = {}
        res["sales_orders"] = []
        if orders_and_project_mapping.exists():
            salesorder_ids = orders_and_project_mapping.first().sales_order_ids
            sales_orders = []
            if salesorder_ids:
                ids = ",".join(salesorder_ids)
                sales_orders = fetch_sales_orders(
                    organization_id, f"&salesorder_ids={ids}"
                )
                return Response(
                    {"sales_orders": sales_orders, "salesorder_ids": salesorder_ids}
                )
        return Response({"sales_orders": [], "salesorder_ids": []})
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_so_to_project(request, project_id):
    try:
        orders_and_project_mapping = OrdersAndProjectMapping.objects.filter(
            project=project_id
        )
        project = Project.objects.get(id=project_id)
        sales_order_ids = request.data.get("sales_order_ids", [])
        if not orders_and_project_mapping.exists():
            for id in sales_order_ids:
                orders_and_project_mapping = OrdersAndProjectMapping.objects.filter(
                    sales_order_ids__contains=id
                )
                if orders_and_project_mapping.exists():
                    mapping = orders_and_project_mapping.first()
                    if mapping.project and mapping.project.id != project.id:
                        return Response(
                            {
                                "error": f"SO already exist in project: {mapping.project.name}"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    break
        if orders_and_project_mapping.exists():
            mapping = orders_and_project_mapping.first()
            existing_sales_order_ids = mapping.sales_order_ids
            set_of_sales_order_ids = set(existing_sales_order_ids)
            for id in sales_order_ids:
                set_of_sales_order_ids.add(id)
            final_list_of_sales_order_ids = list(set_of_sales_order_ids)
            mapping.sales_order_ids = final_list_of_sales_order_ids
            mapping.project = project
            mapping.save()
        else:
            OrdersAndProjectMapping.objects.create(
                project=project, sales_order_ids=sales_order_ids
            )
        return Response({"message": "Sales orders added to project"})
    except Exception as e:
        print(str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



