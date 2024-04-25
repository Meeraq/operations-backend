from django.db import models
from django.utils import timezone
from api.models import Profile, validate_pdf_extension, Project
from django.contrib.auth.models import User
from schedularApi.models import SchedularProject

# Create your models here.


class Vendor(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    name = models.CharField(max_length=155)
    phone = models.CharField(max_length=25)
    email = models.EmailField()
    vendor_id = models.CharField(max_length=255, blank=True, default="")
    hsn_or_sac = models.IntegerField(blank=True, default=0, null=True)
    is_upload_invoice_allowed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class InvoiceData(models.Model):
    INVOICE_STATUS_CHOICES = (
        ("in_review", "In Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    type_of_code_choices = [("IBAN", "iban"), ("SWIFT_CODE", "swift_code")]
    vendor_id = models.CharField(max_length=200, default=None)
    vendor_name = models.CharField(max_length=200, default=None, blank=True)
    vendor_email = models.CharField(max_length=200, default=None, blank=True)
    vendor_billing_address = models.TextField(default=None, blank=True)
    vendor_gst = models.CharField(max_length=200, default=None, blank=True)
    vendor_pan = models.CharField(max_length=255, default="", blank=True)
    vendor_phone = models.CharField(max_length=200, default=None, blank=True)
    purchase_order_id = models.CharField(max_length=200, default=None)
    purchase_order_no = models.CharField(max_length=200, default=None)
    currency_code = models.CharField(max_length=255, default="", blank=True)
    currency_symbol = models.CharField(max_length=255, default="", blank=True)
    invoice_number = models.CharField(max_length=200, default=None)
    line_items = models.JSONField(default=list)
    customer_name = models.CharField(max_length=200, default=None, blank=True)
    customer_notes = models.TextField(blank=True, default=None)
    customer_gst = models.CharField(max_length=200, default=None, blank=True)
    customer_address = models.TextField(default=None, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    is_oversea_account = models.BooleanField(default=False)
    tin_number = models.CharField(max_length=255, default="", blank=True)
    type_of_code = models.CharField(max_length=50, default="", blank=True)
    iban = models.CharField(max_length=255, default="", blank=True)
    swift_code = models.CharField(max_length=255, default="", blank=True)
    invoice_date = models.DateField(blank=True, default=None)
    beneficiary_name = models.CharField(max_length=255, default="")
    bank_name = models.CharField(max_length=255, default="")
    account_number = models.CharField(max_length=255, default="")
    ifsc_code = models.CharField(max_length=11, default="")
    signature = models.ImageField(upload_to="vendors-signature", default="", blank=True)
    attatched_invoice = models.FileField(
        upload_to="pdf_files",
        blank=True,
        default="",
        validators=[validate_pdf_extension],
    )
    status = models.CharField(
        max_length=50, choices=INVOICE_STATUS_CHOICES, default="in_review"
    )
    approver_email = models.EmailField(default="", blank=True)
    tax_names = models.JSONField(default=list, blank=True)


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


class PoReminder(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    purchase_order_id = models.CharField(max_length=200, default=None)
    purchase_order_no = models.CharField(max_length=200, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor.name} for {self.purchase_order_no}"


class InvoiceStatusUpdate(models.Model):
    invoice = models.ForeignKey(
        InvoiceData, related_name="approvals", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=50, choices=InvoiceData.INVOICE_STATUS_CHOICES, default="in_review"
    )
    comment = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.status} by {self.user.username}"


class OrdersAndProjectMapping(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    schedular_project = models.ForeignKey(
        SchedularProject, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )

    purchase_order_ids = models.JSONField(default=list, blank=True)
    sales_order_ids = models.JSONField(default=list, blank=True)


class LineItems(models.Model):
    sales_order_id = models.CharField(max_length=200, default=None)
    sales_order_number = models.CharField(max_length=200, default=None)
    line_item_id = models.CharField(max_length=200, default=None)
    client_name = models.CharField(max_length=200, default=None, blank=True)
    line_item_description = models.TextField(default=None, blank=True)
    due_date = models.DateField(blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    