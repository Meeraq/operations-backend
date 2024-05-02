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

    class Meta:
        model = SalesOrder
        fields = "__all__"

    def get_cf_invoicing_type(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_invoicing_type", "")

    def get_cf_ctt_batch(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_ctt_batch", "")


class SalesOrderLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderLineItem
        fields = "__all__"


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"


class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderLineItem
        fields = "__all__"


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = "__all__"


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
        fields = "__all__"

    def get_cf_ctt_batch(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_ctt_batch", "")


class ClientInvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoiceLineItem
        fields = "__all__"
