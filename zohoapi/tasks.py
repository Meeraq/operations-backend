from celery import shared_task
from .models import Vendor, AccessToken, InvoiceData
import requests
from django.utils import timezone
import os
import environ


base_url = os.environ.get("ZOHO_API_BASE_URL")
organization_id = os.environ.get("ZOHO_ORGANIZATION_ID")
env = environ.Env()


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
                            invoice = InvoiceData.objects.create(
                                invoice_number=bill[env("INVOICE_FIELD_NAME")],
                                vendor_id=vendor.vendor_id,
                                vendor_name=vendor.name,
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
