from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import InvoiceData, Vendor, InvoiceStatusUpdate, OrdersAndProjectMapping

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
        fields = fields = "__all__"
