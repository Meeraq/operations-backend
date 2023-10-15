from django.db import models
from django.utils import timezone


# Create your models here.



class InvoiceData(models.Model):
    type_of_code_choices = [("IBAN", "iban"), ("SWIFT_CODE", "swift_code")]
    vendor_id = models.CharField(max_length=200, default=None)
    vendor_name = models.CharField(max_length=200, default=None)
    vendor_email = models.CharField(max_length=200, default=None)
    vendor_billing_address = models.CharField(max_length=200, default=None)
    vendor_gst = models.CharField(max_length=200, default=None, blank=True)
    vendor_phone = models.CharField(max_length=200, default=None, blank=True)
    purchase_order_id = models.CharField(max_length=200, default=None)
    purchase_order_no = models.CharField(max_length=200, default=None)
    invoice_number = models.CharField(max_length=200, default=None)
    line_items = models.JSONField(default=list)
    customer_name = models.CharField(max_length=200, default=None)
    customer_notes = models.TextField(blank=True, default=None)
    customer_gst = models.CharField(max_length=200, default=None, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    is_oversea_account = models.BooleanField(default=False)
    tin_number = models.CharField(max_length=255, default="", blank=True)
    type_of_code = models.CharField(max_length=50, default="")
    iban = models.CharField(max_length=255, default="", blank=True)
    swift_code = models.CharField(max_length=255, default="", blank=True)
    invoice_date = models.DateField(blank=True, default=None)
    beneficiary_name = models.CharField(max_length=255, default="")
    bank_name = models.CharField(max_length=255, default="")
    account_number = models.CharField(max_length=255, default="")
    ifsc_code = models.CharField(max_length=11, default="")
    signature = models.ImageField(upload_to="vendors-signature", default="",blank=True)

    def __str__(self):
        return f"{self.invoice_number}"

    class Meta:
        ordering = ["-created_at"]



class AccessToken(models.Model):
    refresh_token = models.CharField(max_length=255, unique=True, null=True)
    access_token = models.CharField(max_length=255)
    expires_in = models.IntegerField()  # Store the expiration time in seconds
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() >= self.created_at + timezone.timedelta(
            seconds=self.expires_in
        )

    def __str__(self):
        return self.access_token
