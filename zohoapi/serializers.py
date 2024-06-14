from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import (
    InvoiceData,
    Vendor,
    InvoiceStatusUpdate,
    OrdersAndProjectMapping,
    ZohoCustomer,
    ZohoVendor,
    SalesOrder,
    SalesOrderLineItem,
    PurchaseOrder,
    PurchaseOrderLineItem,
    Bill,
    BillLineItem,
    ClientInvoice,
    ClientInvoiceLineItem,
)

# UserModel=get_user_model()


class InvoiceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceData
        fields = "__all__"


class InvoiceDataGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceData
        fields = [
            "id",
            "vendor_id",
            "vendor_name",
            "vendor_email",
            "purchase_order_id",
            "purchase_order_no",
            "currency_code",
            "currency_symbol",
            "invoice_number",
            "created_at",
            "total",
            "invoice_date",
            "approver_email",
            "status",
            "attatched_invoice",
        ]


class InvoiceDataEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceData
        fields = [
            "invoice_number",
            "line_items",
            "customer_notes",
            "total",
            "invoice_date",
            "signature",
            "tin_number",
            "type_of_code",
            "iban",
            "swift_code",
            "attatched_invoice",
        ]


class VendorDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
        depth = 1


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class InvoiceStatusUpdateGetSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = InvoiceStatusUpdate
        fields = ["id", "status", "comment", "username", "created_at"]


class VendorEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ["name", "phone", "is_upload_invoice_allowed"]


class OrdersAndProjectMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersAndProjectMapping
        fields = "__all__"


class ZohoCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZohoCustomer
        fields = "__all__"


class ZohoVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZohoVendor
        fields = "__all__"


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = "__all__"


class SalesOrderGetSerializer(serializers.ModelSerializer):
    cf_invoicing_type = serializers.SerializerMethodField()
    cf_ctt_batch = serializers.SerializerMethodField()
    gm_sheet_number = serializers.SerializerMethodField()

    class Meta:
        model = SalesOrder
        fields = [
            "id",
            "cf_invoicing_type",
            "cf_ctt_batch",
            "salesorder_id",
            "salesorder_number",
            "date",
            "status",
            "customer_name",
            "customer_id",
            "invoiced_status",
            "paid_status",
            "order_status",
            "total_quantity",
            "created_date",
            "total",
            "currency_code",
            "gm_sheet_number",
            "salesperson_name",
        ]

    def get_cf_invoicing_type(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_invoicing_type", "")

    def get_cf_ctt_batch(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_ctt_batch", "")

    def get_gm_sheet_number(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.gm_sheet.gmsheet_number if obj.gm_sheet else None


class SalesOrderLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderLineItem
        fields = "__all__"


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"


class PurchaseOrderGetSerializer(serializers.ModelSerializer):
    cf_invoice_approver_s_email = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "cf_invoice_approver_s_email",
            "purchaseorder_id",
            "purchaseorder_number",
            "date",
            "created_time",
            "reference_number",
            "status",
            "billed_status",
            "vendor_name",
            "vendor_id",
            "currency_id",
            "currency_code",
            "currency_symbol",
            "exchange_rate",
            "total_quantity",
            "salesorder_id",
            "total",
            "tax_total",
            "po_type",
        ]

    def get_cf_invoice_approver_s_email(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_invoice_approver_s_email", "")


class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderLineItem
        fields = "__all__"


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = "__all__"


class BillGetSerializer(serializers.ModelSerializer):
    cf_invoice = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = [
            "id",
            "cf_invoice",
            "bill_id",
            "bill_number",
            "vendor_name",
            "vendor_id",
            "status",
            "date",
            "reference_number",
            "currency_symbol",
            "currency_code",
        ]

    def get_cf_invoice(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_invoice", "")


class BillLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLineItem
        fields = "__all__"


class ClientInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoice
        fields = "__all__"


class ClientInvoiceGetSerializer(serializers.ModelSerializer):
    cf_ctt_batch = serializers.SerializerMethodField()

    class Meta:
        model = ClientInvoice
        fields = [
            "id",
            "invoice_id",
            "invoice_number",
            "date",
            "customer_name",
            "currency_symbol",
            "status",
            "total",
            "salesorder_number",
            "salesperson_name",
            "salesperson_id",
            "created_date",
            "cf_ctt_batch",
        ]

    def get_cf_ctt_batch(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_ctt_batch", "")


class ClientInvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoiceLineItem
        fields = "__all__"
