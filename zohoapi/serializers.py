from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import InvoiceData, Vendor

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
        ]


class VendorDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
        depth = 1
