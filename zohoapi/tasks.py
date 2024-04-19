from celery import shared_task
from .models import Vendor, AccessToken, InvoiceData, OrdersAndProjectMapping
from .serializers import InvoiceDataSerializer
import requests
from django.utils import timezone
import os
import environ
from datetime import datetime
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
from operationsBackend import settings
from rest_framework.response import Response


base_url = os.environ.get("ZOHO_API_BASE_URL")
organization_id = os.environ.get("ZOHO_ORGANIZATION_ID")
env = environ.Env()

purchase_orders_allowed = [
    "Meeraq/PO/CaaS/23-24/0024",
    "Meeraq/PO/CaaS/23-24/0025",
    "Meeraq/PO/CaaS/23-24/0026",
    "Meeraq/PO/CaaS/23-24/0067",
    "Meeraq/PO/CaaS/23-24/0068",
    "Meeraq/PO/CaaS/23-24/0069",
    "Meeraq/PO/CaaS/23-24/0070",
    "Meeraq/PO/CaaS/23-24/0061",
    "Meeraq/PO/CaaS/23-24/0062",
    "Meeraq/PO/CaaS/23-24/0063",
    "Meeraq/PO/CaaS/23-24/0084",
    "Meeraq/PO/CaaS/23-24/0085",
    "Meeraq/PO/CaaS/23-24/0086",
    "Meeraq/PO/CaaS/23-24/0087",
    "Meeraq/PO/CaaS/23-24/0088",
    "Meeraq/PO/CaaS/23-24/0042",
    "Meeraq/PO/CaaS/23-24/0043",
    "Meeraq/PO/CaaS/23-24/0044",
    "Meeraq/PO/CaaS/23-24/0045",
    "Meeraq/PO/CaaS/23-24/0046",
    "Meeraq/PO/CaaS/23-24/0047",
    "Meeraq/PO/CaaS/23-24/0048",
    "Meeraq/PO/CaaS/23-24/0049",
    "Meeraq/PO/CaaS/23-24/0050",
    "Meeraq/PO/CaaS/23-24/0051",
    "Meeraq/PO/CaaS/23-24/0052",
    "Meeraq/PO/CaaS/23-24/0053",
    "Meeraq/PO/CaaS/23-24/0054",
    "Meeraq/PO/CaaS/23-24/0055",
    "Meeraq/PO/CaaS/23-24/0056",
    "Meeraq/PO/CaaS/23-24/0057",
    "Meeraq/PO/CaaS/23-24/0058",
    "Meeraq/PO/CaaS/23-24/0064",
    "Meeraq/PO/CaaS/23-24/0096",
    "Meeraq/PO/CaaS/23-24/0097",
    "Meeraq/PO/CaaS/23-24/0098",
    "Meeraq/PO/CaaS/23-24/0099",
    "Meeraq/PO/23-24/T/0030",
    "Meeraq/PO/23-24/T/0039",
    "Meeraq/PO/23-24/T/0023",
    "Meeraq/PO/23-24/T/0024",
    "Meeraq/PO/23-24/T/0033",
    "Meeraq/PO/23-24/T/0034",
    "Meeraq/PO/23-24/T/0035",
    "Meeraq/PO/23-24/T/0036",
    "Meeraq/PO/23-24/T/0038",
    "Meeraq/PO/23-24/T/0013",
    "Meeraq/PO/23-24/T/0032",
    "Meeraq/PO/23-24/T/0005",
    "Meeraq/PO/23-24/T/0007",
    "Meeraq/PO/23-24/T/0008",
    "Meeraq/PO/23-24/T/0009",
    "Meeraq/PO/23-24/T/0002",
    "Meeraq/PO/23-24/T/0006",
    "Meeraq/PO/23-24/T/0001",
    "Meeraq/PO/23-24/T/0003",
    "Meeraq/PO/23-24/T/0004",
    "Meeraq/PO/23-24/T/0010",
    "Meeraq/PO/23-24/T/0031",
    "Meeraq/PO/23-24/T/0012",
    "Meeraq/PO/23-24/T/0029",
    "Meeraq/PO/23-24/T/0015",
    "Meeraq/PO/23-24/T/0014",
    "Meeraq/PO/23-24/T/0028",
    "Meeraq/PO/23-24/T/0037",
    "Meeraq/PO/23-24/T/0021",
    "Meeraq/PO/23-24/T/0016",
    "Meeraq/PO/23-24/T/0017",
    "Meeraq/PO/23-24/T/0018",
    "Meeraq/PO/23-24/T/0022",
    "Meeraq/PO/23-24/T/0019",
    "Meeraq/PO/23-24/T/0020",
    "CTT/PO/23-24/008",
    "CTT/PO/23-24/006",
    "CTT/PO/23-24/0018",
    "CTT/PO/23-24/0017",
    "CTT/PO/23-24/0016",
    "CTT/PO/23-24/0015",
    "CTT/PO/23-24/005",
    "CTT/PO/23-24/004",
    "CTT/PO/23-24/0012",
    "CTT/PO/23-24/0011",
    "CTT/PO/23-24/0014",
    "CTT/PO/23-24/0013",
    "Meeraq/PO/CaaS/23-24/0077",
    "Meeraq/PO/22-23/0041",
    "CTT/PO/22-23/058",
    "CTT/PO/22-23/059",
    "CTT/PO/22-23/060",
    "CTT/PO/22-23/061",
    "CTT/PO/22-23/065",
    "CTT/PO/22-23/066",
    "CTT/PO/22-23/067",
    "CTT/PO/23-24/003",
    "Meeraq/PO/CaaS/23-24/0066",
    "Meeraq/PO/CaaS/23-24/0094",
    "Meeraq/PO/22-23/0045",
    "Meeraq/PO/CaaS/23-24/0101",
    "Meeraq/PO/CaaS/23-24/0060",
    "Meeraq/PO/CaaS/23-24/0004",
    "Meeraq/PO/CaaS/23-24/0102",
    "Meeraq/PO/22-23/0045",
    "Meeraq/PO/22-23/0002",
    "Meeraq/PO/22-23/0014",
    "Meeraq/PO/22-23/0017",
    "Meeraq/PO/22-23/0021",
    "Meeraq/PO/22-23/0034",
    "Meeraq/PO/22-23/0036",
    "Meeraq/PO/Caas/23-24/0021",
    "Meeraq/PO/23-24/T/0014",
    "Meeraq/PO/23-24/T/0018",
    "Meeraq/PO/Caas/23-24/0079",
]


def get_all_so_of_po(purchase_order_id):
    try:
        mapping_instance = None
        for order_project_mapping in OrdersAndProjectMapping.objects.all():
            if str(purchase_order_id) in order_project_mapping.purchase_order_ids:

                mapping_instance = order_project_mapping
                break
        return mapping_instance

    except Exception as e:
        print(str(e))


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


def filter_purchase_order_data(purchase_orders):
    try:
        filtered_purchase_orders = []
        for order in purchase_orders:
            purchaseorder_number = order.get("purchaseorder_number", "").strip()
            mapping_instance = get_all_so_of_po(
                order.get("purchaseorder_id", "").strip()
            )
            if mapping_instance:
                order["assigned_sales_order_ids"] = mapping_instance.sales_order_ids
            else:
                order["assigned_sales_order_ids"] = []
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


def fetch_sales_orders(organization_id, queryParams=""):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if not access_token:
        raise Exception(
            "Access token not found. Please generate an access token first."
        )

    all_sales_orders = []
    has_more_page = True
    page = 1

    while has_more_page:
        api_url = f"{base_url}/salesorders/?organization_id={organization_id}&page={page}{queryParams}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(api_url, headers=auth_header)

        if response.status_code == 200:
            sales_orders = response.json().get("salesorders", [])
            # sales_orders = filter_sales_order_data(sales_orders)
            all_sales_orders.extend(sales_orders)

            page_context = response.json().get("page_context", {})
            has_more_page = page_context.get("has_more_page", False)
            page += 1
        else:
            raise Exception("Failed to fetch sales orders")

    return all_sales_orders


def fetch_client_invoices(organization_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if not access_token:
        raise Exception(
            "Access token not found. Please generate an access token first."
        )

    all_client_invoices = []
    has_more_page = True
    page = 1

    while has_more_page:
        api_url = f"{base_url}/invoices/?organization_id={organization_id}&page={page}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(api_url, headers=auth_header)

        if response.status_code == 200:
            client_invoices = response.json().get("invoices", [])
            all_client_invoices.extend(client_invoices)

            page_context = response.json().get("page_context", {})
            has_more_page = page_context.get("has_more_page", False)
            page += 1
        else:
            raise Exception("Failed to fetch client invoices.")

    return all_client_invoices


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
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")


def fetch_bills(organization_id):
    access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if not access_token_purchase_data:
        raise Exception(
            "Access token not found. Please generate an access token first."
        )

    all_bills = []
    has_more_page = True
    page = 1

    while has_more_page:
        api_url = f"{base_url}/bills/?organization_id={organization_id}&page={page}"
        auth_header = {"Authorization": f"Bearer {access_token_purchase_data}"}
        response = requests.get(api_url, headers=auth_header)

        if response.status_code == 200:
            bills = response.json().get("bills", [])
            all_bills.extend(bills)
            page_context = response.json().get("page_context", {})
            has_more_page = page_context.get("has_more_page", False)
            page += 1
        else:
            raise Exception("Failed to fetch bills")

    return all_bills


def fetch_customers_from_zoho(organization_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if not access_token:
        raise Exception(
            "Access token not found. Please generate an access token first."
        )

    all_customers = []
    has_more_page = True
    page = 1

    while has_more_page:
        api_url = f"{base_url}/customers/?organization_id={organization_id}&page={page}"
        auth_header = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(api_url, headers=auth_header)

        if response.status_code == 200:
            customers = response.json().get("contacts", [])
            all_customers.extend(customers)
            page_context = response.json().get("page_context", {})
            has_more_page = page_context.get("has_more_page", False)
            page += 1
        else:
            raise Exception("Failed to fetch customers")

    return all_customers


def filter_invoice_data(invoices):
    try:
        filtered_invoices = []
        for invoice in invoices:
            if (
                invoice.created_at.year >= 2024
                or invoice.purchase_order_no.strip() in purchase_orders_allowed
            ):
                filtered_invoices.append(invoice)
        return filtered_invoices
    except Exception as e:
        print(str(e))
        return None


def import_invoices_for_vendor_from_zoho(vendor, headers, res, bill_details_res):
    purchase_orders_url = f"{base_url}/purchaseorders/?organization_id={organization_id}&vendor_id={vendor.vendor_id}"
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
                            vendor_id=vendor.vendor_id,
                            invoice_number=bill[env("INVOICE_FIELD_NAME")],
                        ).exists():
                            print(
                                "invoice already exists",
                                bill[env("INVOICE_FIELD_NAME")],
                            )
                        else:
                            vendor_details = get_vendor(vendor.vendor_id)
                            name = vendor_details["contact_name"]
                            invoice = InvoiceData.objects.create(
                                invoice_number=bill[env("INVOICE_FIELD_NAME")],
                                vendor_id=vendor.vendor_id,
                                vendor_name=name,
                                vendor_email=vendor.email,
                                vendor_billing_address="",
                                vendor_gst="",
                                vendor_phone=vendor.phone,
                                customer_name="",
                                customer_gst="",
                                customer_notes="",
                                customer_address="",
                                is_oversea_account=False,
                                tin_number="",
                                invoice_date=bill["date"],
                                purchase_order_id=purchase_order["purchaseorder_id"],
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
        print(vendor.email, purchase_orders)
    else:
        print({"error": "Failed to fetch purchase orders", "email": vendor.email})


@shared_task
def import_invoice_for_new_vendor(id):
    try:
        access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            vendor = Vendor.objects.get(id=id)
            res = []
            bill_details_res = []
            import_invoices_for_vendor_from_zoho(vendor, headers, res, bill_details_res)
        else:
            print(access_token)
            pass
    except Exception as e:
        print(str(e))


@shared_task
def weekly_invoice_approval_reminder():
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
                        if (
                            bill.get(env("INVOICE_FIELD_NAME"))
                            == invoice["invoice_number"]
                            and bill.get("vendor_id") == invoice["vendor_id"]
                        )
                    ),
                    None,
                )
                all_invoices.append({**invoice, "bill": matching_bill})
            invoices_in_review = []
            for invoice in all_invoices:
                if invoice["status"] == "in_review" and not invoice["bill"]:
                    datetime_obj = datetime.strptime(
                        invoice["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                    generated_date = datetime_obj.strftime("%d-%m-%Y")
                    invoices_in_review.append(
                        {**invoice, "generated_date": generated_date}
                    )
            if len(invoices_in_review) > 0:
                send_mail_templates(
                    "vendors/weekly_invoice_approval_reminder.html",
                    [
                        (
                            "pmocoaching@meeraq.com"
                            if env("ENVIRONMENT") == "PRODUCTION"
                            else "tech@meeraq.com"
                        )
                    ],
                    "Pending Invoices: Your Approval Needed",
                    {"invoices": invoices_in_review, "link": env("CAAS_APP_URL")},
                    [env("BCC_EMAIL_RAJAT_SUJATA")],
                )
    except Exception as e:
        print(str(e))
        pass
