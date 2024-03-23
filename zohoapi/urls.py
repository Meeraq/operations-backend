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
        "pmo/purchase-orders/",
        views.get_all_purchase_orders_for_pmo,
        name="get_all_purchase_orders",
    ),
    path(
        "get-all-invoices/",
        views.get_all_invoices,
        name="get_all_invoices",
    ),
    path(
        "pmo/invoices/",
        views.get_invoices_for_pmo,
        name="get_all_invoices",
    ),
    path("vendors/<int:vendor_id>/", views.edit_vendor, name="edit_vendor"),
    path(
        "invoices/<str:status>/",
        views.get_invoices_by_status,
        name="get_invoices_by_status",
    ),
    path(
        "invoices/founders/<str:status>/",
        views.get_invoices_by_status_for_founders,
        name="get_invoices_by_status_for_founders",
    ),
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
    path(
        "coching-purchase-order/create/<int:coach_id>/<int:project_id>/",
        views.coching_purchase_order_create,
    ),
    path(
        "purchase-order/coaching/delete/<int:purchase_order_id>/",
        views.delete_coaching_purchase_order,
        name="delete_coaching_purchase_order",
    ),
    path("coach/finances/", views.get_coach_wise_finances),
    path("project/finances/", views.get_project_wise_finances),
    path(
        "expense-purchase-order/create/<int:facilitator_id>/<int:batch_id>/",
        views.expense_purchase_order_create,
    ),
    path(
        "purchase-order/expense/delete/<str:purchase_order_id>/",
        views.delete_expense_purchase_order,
        name="delete_expense_purchase_order",
    ),
    path(
        "get-all-sales-orders/",
        views.get_all_sales_orders,
        name="get_all_sales_orders",
    ),
    path(
        "get-sales-order-data-pdf/<int:salesorder_id>/",
        views.get_sales_order_data_pdf,
        name="get_sales_order_data",
    ),
    path(
        "get-sales-order-data/<int:salesorder_id>/",
        views.get_sales_order_data,
        name="get_sales_order_data",
    ),
    path(
        "customers-from-zoho/",
        views.get_customers_from_zoho,
        name="get_customers_from_zoho",
    ),
    path(
        "customer-details-from-zoho/<str:customer_id>/",
        views.get_customer_details_from_zoho,
        name="get_customer_details_from_zoho",
    ),
    path(
        "create-invoice/",
        views.create_invoice,
        name="create_invoice",
    ),
    path(
        "sales-order/create/",
        views.create_sales_order,
        name="create_sales_order",
    ),
    path(
        "get-all-client-invoices/",
        views.get_all_client_invoices,
        name="get_all_client_invoices",
    ),
    path(
        "get-client-invoice-data-pdf/<int:invoice_id>/",
        views.get_client_invoice_data_pdf,
        name="get_client_invoice_data",
    ),
    path(
        "get-client-invoice-data/<int:invoice_id>/",
        views.get_client_invoice_data,
        name="get_client_invoice_data",
    ),
    path(
        "project/caas/sales-orders/<int:project_id>/",
        views.get_project_sales_orders,
        name="get_project_sales_orders",
    ),
    path(
        "add-so-to-project/<int:project_id>/",
        views.add_so_to_project,
        name="add_so_to_project",
    ),
]
