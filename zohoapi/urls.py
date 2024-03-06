from django.urls import path, include
from . import views
from .views import DownloadInvoice, DownloadAttatchedInvoice
import environ

env = environ.Env()

urlpatterns = [
    path("login/", views.login_view, name="zoho-login"),
    path("session/", views.session_view, name="zoho-session"),
    path("otp/generate/", views.generate_otp),
    path(
        f"{env('GENERATE_OTP')}/<str:email>/",
        views.generate_otp_send_mail_fixed,
    ),
    path("otp/validate/", views.validate_otp),
    path(
        "get-purchase-orders/<int:vendor_id>/",
        views.get_purchase_orders,
        name="get_purchase_orders",
    ),
    path(
        "get_invoices_with_status/<str:vendor_id>/<str:purchase_order_id>/",
        views.get_invoices_with_status,
    ),
    path(
        "get-purchase-order-data/<int:purchaseorder_id>/",
        views.get_purchase_order_data,
        name="get_purchase_order_data",
    ),
    path(
        "get-purchase-order-data-pdf/<int:purchaseorder_id>/",
        views.get_purchase_order_data_pdf,
        name="get_purchase_order_data",
    ),
    path("add-invoice-data/", views.add_invoice_data, name="add_invoice_data"),
    path("edit-invoice/<int:invoice_id>/", views.edit_invoice),
    path(
        "delete-invoice/<int:invoice_id>/",
        views.delete_invoice,
        name="get_invoice_data",
    ),
    path(
        "po-and-invoices/<str:purchase_order_id>/",
        views.get_purchase_order_and_invoices,
    ),
    path(
        "get-bank-data/<str:vendor_id>/<str:bank_account_id>/",
        views.get_bank_account_data,
    ),
    # path("update-vendor-id-to-coaches/", views.update_vendor_id),
    path(
        "get-vendors-existing-and-non-existing/",
        views.get_vendor_exists_and_not_existing_emails,
    ),
    path("import-invoices/", views.import_invoices_from_zoho),
    path("export-invoice-data/", views.export_invoice_data),
    path("download-invoice/<int:record_id>/", DownloadInvoice.as_view()),
    path(
        "download-attatched-invoice/<int:record_id>/",
        DownloadAttatchedInvoice.as_view(),
    ),
    path("add/vendor/", views.add_vendor),
    path("vendors/", views.get_all_vendors),
    path(
        "get-all-purchase-orders/",
        views.get_all_purchase_orders,
        name="get_all_purchase_orders",
    ),
    path(
        "get-all-invoices/",
        views.get_all_invoices,
        name="get_all_invoices",
    ),
    path("vendors/<int:vendor_id>/", views.edit_vendor, name="edit_vendor"),
    path(
        "invoices/<int:invoice_id>/update_status/",
        views.update_invoice_status,
    ),
    path(
        "invoices/<int:invoice_id>/updates/",
        views.get_invoice_updates,
        name="get_invoice_updates",
    ),
    path(
        "vendor/<str:vendor_id>/",
        views.get_vendor_details_from_zoho,
        name="get_vendor_details_from_zoho",
    ),
    path(
        "purchase-order/create/<str:user_type>/<int:facilitator_pricing_id>/",
        views.create_purchase_order,
        name="create_purchase_order",
    ),
    path(
        "po-number/meeraq/",
        views.get_po_number_to_create,
        name="get_po_number_to_create",
    ),
    path(
        "purchase-order/status/<str:purchase_order_id>/<str:status>/",
        views.update_purchase_order_status,
        name="update_purchase_order_status",
    ),
]
