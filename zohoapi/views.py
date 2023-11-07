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
from rest_framework.permissions import AllowAny
from api.models import (
    Coach,
    OTP,
    UserLoginActivity,
)
from api.serializers import (
    CoachDepthOneSerializer,
)
from openpyxl import Workbook


from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from django.http import HttpResponse
from .serializers import InvoiceDataEditSerializer, InvoiceDataSerializer
from .models import InvoiceData, AccessToken
import base64
from django.core.mail import EmailMessage
from io import BytesIO
from xhtml2pdf import pisa

import environ
import os

env = environ.Env()

base_url = os.environ.get("ZOHO_API_BASE_URL")
organization_id = os.environ.get("ZOHO_ORGANIZATION_ID")


def get_line_items_details(invoices):
    res = {}
    for invoice in invoices:
        for line_item in invoice.line_items:
            if line_item["line_item_id"] in res:
                res[line_item["line_item_id"]] += line_item["quantity_input"]
            else:
                res[line_item["line_item_id"]] = line_item["quantity_input"]
    return res


class EmailSendingError(Exception):
    pass


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


def get_access_token(refresh_token):
    try:
        access_token_object = AccessToken.objects.get(refresh_token=refresh_token)
        if not access_token_object.is_expired():
            return access_token_object.access_token
        else:
            new_access_token = generate_access_token_from_refresh_token(refresh_token)
            if new_access_token:
                access_token_object.access_token = new_access_token
                access_token_object.created_at = timezone.now()
                access_token_object.save()
            return new_access_token
    except:
        new_access_token = generate_access_token_from_refresh_token(refresh_token)
        if new_access_token:
            access_token_instance = AccessToken(
                access_token=new_access_token,
                refresh_token=refresh_token,
                expires_in=3600,
            )
            access_token_instance.save()
        return new_access_token


def send_mail_templates(file_name, user_email, email_subject, content):
    email_message = render_to_string(file_name, content)

    try:
        # Attempt to send the email
        send_mail_result = send_mail(
            f"{env('EMAIL_SUBJECT_INITIAL', default='')} {email_subject}",
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            user_email,
            fail_silently=False,
            html_message=email_message,
        )

        if not send_mail_result:
            print(
                "send_mail function returned False. There may be an issue with sending the email."
            )
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")
        raise EmailSendingError(f"Error occurred while sending emails: {str(e)}")


def send_mail_templates_with_attachment(
    file_name, user_email, email_subject, content, body_message
):
    image_url = f"{content['invoice']['signature']}"
    try:
        # Attempt to send the email
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        # Convert the downloaded image to base64
        image_base64 = base64.b64encode(image_response.content).decode("utf-8")
        content["image_base64"] = image_base64
        email_message = render_to_string(file_name, content)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(email_message.encode("ISO-8859-1")), result)
        email = EmailMessage(
            subject=f"{env('EMAIL_SUBJECT_INITIAL', default='')} {email_subject}",
            body=body_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=user_email,
        )
        # Attach the PDF to the email
        email.attach("invoice.pdf", result.getvalue(), "application/pdf")
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
    elif user.profile.type == "coach" and user.profile.coach.vendor_id:
        serializer = CoachDepthOneSerializer(user.profile.coach)
    # elif user.profile.type == "pmo":
    #     serializer = PmoDepthOneSerializer(user.profile.pmo)
    # elif user.profile.type == "learner":
    #     serializer = LearnerDepthOneSerializer(user.profile.learner)
    # elif user.profile.type == "hr":
    #     serializer = HrDepthOneSerializer(user.profile.hr)
    else:
        return None
    return serializer.data


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_otp(request):
    try:
        user = User.objects.get(username=request.data["email"])
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
                [user],
                subject,
                {"name": name, "otp": created_otp.otp},
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
    platform = data.get("platform","unknown")
    


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
        UserLoginActivity.objects.create(user=user, timestamp=login_timestamp,platform=platform)
        return Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
                "organization": organization,
                "zoho_vendor": zoho_vendor,
            }
        )
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
        return Response(
            {
                "isAuthenticated": True,
                "user": {**user_data, "last_login": last_login},
                "organization": organization,
                "zoho_vendor": zoho_vendor,
            }
        )
    else:
        logout(request)
        return Response({"error": "Invalid user type."}, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    platform = data.get("platform","unknown")
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
        UserLoginActivity.objects.create(user=user, timestamp=login_timestamp,platform=platform)
        return Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
                "organization": organization,
                "zoho_vendor": zoho_vendor,
            }
        )
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)


@api_view(["GET"])
def get_purchase_orders(request, vendor_id):
    access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token_purchase_data:
        api_url = f"{base_url}/purchaseorders/?organization_id={organization_id}&vendor_id={vendor_id}"
        auth_header = {"Authorization": f"Bearer {access_token_purchase_data}"}
        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            purchase_orders = response.json().get("purchaseorders", [])

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
def get_invoices_with_status(request, vendor_id, purchase_order_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        if purchase_order_id == "all":
            invoices = InvoiceData.objects.filter(vendor_id=vendor_id)
            url = f"{base_url}/bills?organization_id={env('ZOHO_ORGANIZATION_ID')}&vendor_id={vendor_id}"
            bills_response = requests.get(url, headers=headers)
        else:
            invoices = InvoiceData.objects.filter(purchase_order_id=purchase_order_id)
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
def get_purchase_order_data_pdf(request, purchaseorder_id):
    access_token_purchase_order = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token_purchase_order:
        api_url = f"{base_url}/purchaseorders/{purchaseorder_id}?print=true&accept=pdf&organization_id={organization_id}"
        auth_header = {"Authorization": f"Bearer {access_token_purchase_order}"}

        response = requests.get(api_url, headers=auth_header)
        if response.status_code == 200:
            pdf_content = response.content
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="purchase_order.pdf"'
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


@api_view(["POST"])
def add_invoice_data(request):
    invoices = InvoiceData.objects.filter(
        vendor_id=request.data["vendor_id"],
        invoice_number=request.data["invoice_number"],
    )

    if invoices.count() > 0:
        return Response({"error": "Invoice number should be unique."}, status=400)

    serializer = InvoiceDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        line_items = serializer.data["line_items"]
        for line_item in line_items:
            line_item["quantity_mul_rate"] = (
                line_item["quantity_input"] * line_item["rate"]
            )
            line_item["quantity_mul_rate_include_tax"] = (
                line_item["quantity_input"]
                * line_item["rate"]
                * (1 + line_item["tax_percentage"] / 100)
            )
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
        send_mail_templates_with_attachment(
            "invoice_pdf.html",
            [env("FINANCE_EMAIL")],
            f"Invoice raised by a Vendor - {invoice_data['vendor_name']} ",
            {"invoice": invoice_data},
            f"A new invoice: {invoice_data['invoice_number']} is raised by the vendor: {invoice_data['vendor_name']}",
        )
        return Response({"message": "Invoice generated successfully"}, status=201)
    else:
        return Response(serializer.errors, status=400)


@api_view(["PUT"])
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
        line_items = serializer.data["line_items"]
        for line_item in line_items:
            line_item["quantity_mul_rate"] = (
                line_item["quantity_input"] * line_item["rate"]
            )
            line_item["quantity_mul_rate_include_tax"] = (
                line_item["quantity_input"]
                * line_item["rate"]
                * (1 + line_item["tax_percentage"] / 100)
            )
        invoice_serializer = InvoiceDataSerializer(invoice)
        invoice_date = datetime.strptime(
            serializer.data["invoice_date"], "%Y-%m-%d"
        ).strftime("%d-%m-%Y")
        due_date = datetime.strptime(
            add_45_days(serializer.data["invoice_date"]), "%Y-%m-%d"
        ).strftime("%d-%m-%Y")
        invoice_data = {
            **invoice_serializer.data,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "line_items": line_items,
        }
        send_mail_templates_with_attachment(
            "invoice_pdf.html",
            [env("FINANCE_EMAIL")],
            f"Invoice edited by a Vendor - {invoice_data['vendor_name']}",
            {"invoice": invoice_data},
            f"Invoice: {invoice_data['invoice_number']} has been edited by the vendor: {invoice_data['vendor_name']}",
        )
        return Response({"message": "Invoice edited successfully."}, status=201)
    else:
        return Response({"error": "Invalid data."}, status=400)


@api_view(["DELETE"])
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


@api_view(["GET"])
def update_vendor_id(request):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/contacts?organization_id={env('ZOHO_ORGANIZATION_ID')}&contact_type=vendor"
        vendor_response = requests.get(url, headers=headers)
        if vendor_response.json()["message"] == "success":
            for vendor in vendor_response.json()["contacts"]:
                if vendor["email"]:
                    try:
                        coach = Coach.objects.get(email=vendor["email"])
                        coach.vendor_id = vendor["contact_id"]
                        coach.save()
                    except Coach.DoesNotExist:
                        print(vendor["email"], "coach doesnt exist")
                        pass
            return Response(vendor_response.json())
        else:
            return Response({"error": "Failed to get vendors."}, status=400)
    else:
        return Response({"error": "Unauthorized	."}, status=400)


@api_view(["GET"])
def get_coach_exists_and_not_existing_emails(request):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/contacts?organization_id={env('ZOHO_ORGANIZATION_ID')}&contact_type=vendor"
        vendor_response = requests.get(url, headers=headers)
        if vendor_response.json()["message"] == "success":
            existing_coaches = []
            not_existing_coaches = []
            for vendor in vendor_response.json()["contacts"]:
                if vendor["email"]:
                    try:
                        coach = Coach.objects.get(email=vendor["email"])
                        existing_coaches.append(vendor["email"])
                    except Coach.DoesNotExist:
                        not_existing_coaches.append(vendor["email"])
                        pass
            return Response(
                {
                    "vendors": vendor_response.json()["contacts"],
                    "existing_coaches": existing_coaches,
                    "not_existing_coaches": not_existing_coaches,
                },
                status=200,
            )
        else:
            return Response({"error": "Failed to get vendors."}, status=400)
    else:
        return Response({"error": "Unauthorized	."}, status=400)


@api_view(["GET"])
def import_invoices_from_zoho(request):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        coaches = Coach.objects.exclude(vendor_id__isnull=True).exclude(vendor_id="")
        res = []
        bill_details_res = []
        for coach in coaches:
            purchase_orders_url = f"{base_url}/purchaseorders/?organization_id={organization_id}&vendor_id={coach.vendor_id}"
            response = requests.get(purchase_orders_url, headers=headers)
            if response.status_code == 200:
                purchase_orders = response.json().get("purchaseorders", [])
                for purchase_order in purchase_orders:
                    bills_url = f"{base_url}/bills?organization_id={env('ZOHO_ORGANIZATION_ID')}&purchaseorder_id={purchase_order['purchaseorder_id']}"
                    bills_response = requests.get(bills_url, headers=headers)
                    if bills_response.status_code == 200:
                        bills = bills_response.json().get("bills", [])
                        res.append(bills_response.json().get("bills", []))
                        for bill in bills:
                            bill_url = f"{base_url}/bills/{bill['bill_id']}?organization_id={env('ZOHO_ORGANIZATION_ID')}"
                            bill_response = requests.get(bill_url, headers=headers)
                            if (
                                env("INVOICE_FIELD_NAME") in bill
                                and bill_response.status_code == 200
                            ):
                                bill_details = bill_response.json().get("bill")
                                bill_details_res.append(bill_details)
                                line_items_res = []

                                for line_item in bill_details["line_items"]:
                                    if line_item["quantity"] > 0:
                                        line_items_res.append(
                                            {
                                                **line_item,
                                                "line_item_id": line_item[
                                                    "purchaseorder_item_id"
                                                ],
                                                "quantity_input": line_item["quantity"],
                                            }
                                        )
                                if InvoiceData.objects.filter(
                                    vendor_id=coach.vendor_id,
                                    invoice_number=bill[env("INVOICE_FIELD_NAME")],
                                ).exists():
                                    print(
                                        "invoice already exists",
                                        bill[env("INVOICE_FIELD_NAME")],
                                    )
                                else:
                                    invoice = InvoiceData.objects.create(
                                        invoice_number=bill[env("INVOICE_FIELD_NAME")],
                                        vendor_id=coach.vendor_id,
                                        vendor_name=coach.first_name,
                                        vendor_email=coach.email,
                                        vendor_billing_address="",
                                        vendor_gst="",
                                        vendor_phone=coach.phone,
                                        customer_name="",
                                        customer_gst="",
                                        customer_notes="",
                                        is_oversea_account=False,
                                        tin_number="",
                                        invoice_date=bill["date"],
                                        purchase_order_id=purchase_order[
                                            "purchaseorder_id"
                                        ],
                                        purchase_order_no=purchase_order[
                                            "purchaseorder_number"
                                        ],
                                        line_items=line_items_res,
                                        total=bill["total"],
                                    )
                            else:
                                print("bill details couldn't get")
                    else:
                        print("bills didn't fetched")
                print(coach.email, purchase_orders)
            else:
                print(
                    {"error": "Failed to fetch purchase orders", "email": coach.email}
                )
        return Response({"res": res, "bill_details_res": bill_details_res}, status=200)
    else:
        return Response({"error": "Invalid invoices"}, status=400)


@api_view(["GET"])
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
