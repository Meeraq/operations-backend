from django.db import models
from django.utils import timezone
from api.models import Profile, validate_pdf_extension, Project
from django.contrib.auth.models import User
from schedularApi.models import SchedularProject

# Create your models here.


class Vendor(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
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


class ZohoCustomer(models.Model):
    contact_id = models.CharField(max_length=50, blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_bcy_only_contact = models.BooleanField(default=False)
    is_credit_limit_migration_completed = models.BooleanField(default=False)
    language_code = models.CharField(max_length=10, blank=True, null=True)
    language_code_formatted = models.CharField(max_length=255, blank=True, null=True)
    contact_salutation = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    invited_by = models.CharField(max_length=255, blank=True, null=True)
    portal_status = models.CharField(max_length=20, blank=True, null=True)
    portal_status_formatted = models.CharField(max_length=255, blank=True, null=True)
    is_client_review_asked = models.BooleanField(default=False)
    has_transaction = models.BooleanField(default=False)
    contact_type = models.CharField(max_length=50, blank=True, null=True)
    customer_sub_type = models.CharField(max_length=50, blank=True, null=True)
    customer_sub_type_formatted = models.CharField(
        max_length=255, blank=True, null=True
    )
    owner_id = models.CharField(max_length=50, blank=True, null=True)
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    source_formatted = models.CharField(max_length=255, blank=True, null=True)
    documents = models.JSONField(blank=True, null=True)
    twitter = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    zoho_customer = models.BooleanField(default=False)
    is_linked_with_zohocrm = models.BooleanField(default=False)
    primary_contact_id = models.CharField(max_length=50, blank=True, null=True)
    zcrm_account_id = models.CharField(max_length=50, blank=True, null=True)
    zcrm_contact_id = models.CharField(max_length=50, blank=True, null=True)
    crm_owner_id = models.CharField(max_length=50, blank=True, null=True)
    payment_terms = models.IntegerField(default=0)
    payment_terms_label = models.CharField(max_length=255, blank=True, null=True)
    credit_limit_exceeded_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    currency_id = models.CharField(max_length=50, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)
    price_precision = models.IntegerField(default=2, blank=True, null=True)
    exchange_rate = models.CharField(max_length=50, blank=True, null=True)
    can_show_customer_ob = models.BooleanField(default=False)
    can_show_customer_ob_formatted = models.BooleanField(default=False)
    can_show_vendor_ob = models.BooleanField(default=False)
    can_show_vendor_ob_formatted = models.BooleanField(default=False)
    branch_id = models.CharField(max_length=50, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    opening_balance_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    opening_balance_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    opening_balance_amount_bcy = models.CharField(max_length=50, blank=True, null=True)
    opening_balance_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_ob_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_ob_receivable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_ob_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_ob_payable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_receivable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_receivable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_payable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_payable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_receivable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_payable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_payable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_retainer_payments = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_retainer_payments_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    status = models.CharField(max_length=20, blank=True, null=True)
    status_formatted = models.CharField(max_length=255, blank=True, null=True)
    payment_reminder_enabled = models.BooleanField(default=True)
    is_sms_enabled = models.BooleanField(default=True)
    is_portal_enabled = models.BooleanField(default=False)
    is_consent_agreed = models.BooleanField(default=False)
    consent_date = models.DateField(blank=True, null=True)
    is_client_review_settings_enabled = models.BooleanField(default=False)
    custom_fields = models.JSONField(blank=True, null=True)
    cf_meeraq_ctt = models.CharField(max_length=255, blank=True, null=True)
    cf_meeraq_ctt_unformatted = models.CharField(max_length=255, blank=True, null=True)
    custom_field_hash = models.JSONField(blank=True, null=True)
    is_taxable = models.BooleanField(default=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    tds_tax_id = models.CharField(max_length=50, blank=True, null=True)
    tax_name = models.CharField(max_length=255, blank=True, null=True)
    tax_name_formatted = models.CharField(max_length=255, blank=True, null=True)
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    country_code = models.CharField(max_length=10, blank=True, null=True)
    country_code_formatted = models.CharField(max_length=10, blank=True, null=True)
    place_of_contact = models.CharField(max_length=50, blank=True, null=True)
    place_of_contact_formatted = models.CharField(max_length=255, blank=True, null=True)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    pan_no = models.CharField(max_length=50, blank=True, null=True)
    trader_name = models.CharField(max_length=255, blank=True, null=True)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    vat_reg_no = models.CharField(max_length=50, blank=True, null=True)
    udyam_reg_no = models.CharField(max_length=50, blank=True, null=True)
    msme_type = models.CharField(max_length=50, blank=True, null=True)
    msme_type_formatted = models.CharField(max_length=255, blank=True, null=True)
    tax_treatment = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment_formatted = models.CharField(max_length=255, blank=True, null=True)
    tax_reg_no = models.CharField(max_length=50, blank=True, null=True)
    contact_category = models.CharField(max_length=50, blank=True, null=True)
    contact_category_formatted = models.CharField(max_length=255, blank=True, null=True)
    gst_treatment = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment_formatted = models.CharField(max_length=255, blank=True, null=True)
    is_linked_with_contact = models.BooleanField(default=False)
    sales_channel = models.CharField(max_length=50, blank=True, null=True)
    ach_supported = models.BooleanField(default=False)
    portal_receipt_count = models.IntegerField(default=0, blank=True, null=True)
    opening_balances = models.JSONField(blank=True, null=True)
    allow_parent_for_payment_and_view = models.BooleanField(default=False)
    tax_info_list = models.JSONField(blank=True, null=True)
    entity_address_id = models.CharField(max_length=50, blank=True, null=True)
    billing_address = models.JSONField(blank=True, null=True)
    shipping_address = models.JSONField(blank=True, null=True)
    contact_persons = models.JSONField(blank=True, null=True)
    addresses = models.JSONField(blank=True, null=True)
    pricebook_id = models.CharField(max_length=50, blank=True, null=True)
    pricebook_name = models.CharField(max_length=255, blank=True, null=True)
    associated_with_square = models.BooleanField(default=False)
    can_add_card = models.BooleanField(default=False)
    can_add_bank_account = models.BooleanField(default=False)
    cards = models.JSONField(blank=True, null=True)
    checks = models.JSONField(blank=True, null=True)
    bank_accounts = models.JSONField(blank=True, null=True)
    vpa_list = models.JSONField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    created_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    created_by_name = models.CharField(max_length=255, blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    zohopeople_client_id = models.CharField(max_length=50, blank=True, null=True)
    customer_currency_summaries = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.contact_name


class ZohoVendor(models.Model):
    contact_id = models.CharField(max_length=100, blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_bcy_only_contact = models.BooleanField(default=False)
    is_credit_limit_migration_completed = models.BooleanField(default=False)
    language_code = models.CharField(max_length=10, blank=True, null=True)
    language_code_formatted = models.CharField(max_length=50, blank=True, null=True)
    contact_salutation = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    invited_by = models.CharField(max_length=255, blank=True, null=True)
    portal_status = models.CharField(max_length=20, blank=True, null=True)
    portal_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    is_client_review_asked = models.BooleanField(default=False)
    has_transaction = models.BooleanField(default=False)
    contact_type = models.CharField(max_length=20, blank=True, null=True)
    customer_sub_type = models.CharField(max_length=20, blank=True, null=True)
    customer_sub_type_formatted = models.CharField(max_length=20, blank=True, null=True)
    owner_id = models.CharField(max_length=100, blank=True, null=True)
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    source_formatted = models.CharField(max_length=50, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True, null=True)
    twitter = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    zoho_customer = models.BooleanField(default=False)
    is_linked_with_zohocrm = models.BooleanField(default=False)
    zoho_customer = models.BooleanField(default=False)
    primary_contact_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_vendor_id = models.CharField(max_length=100, blank=True, null=True)
    crm_owner_id = models.CharField(max_length=100, blank=True, null=True)
    payment_terms = models.IntegerField(default=0, blank=True, null=True)
    payment_terms_label = models.CharField(max_length=50, blank=True, null=True)
    credit_limit_exceeded_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    credit_limit_exceeded_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    currency_id = models.CharField(max_length=100, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)
    price_precision = models.IntegerField(blank=True, null=True)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, blank=True, null=True
    )
    can_show_customer_ob = models.BooleanField(default=False)
    can_show_customer_ob_formatted = models.BooleanField(default=False)
    can_show_vendor_ob = models.BooleanField(default=False)
    can_show_vendor_ob_formatted = models.BooleanField(default=False)
    branch_id = models.CharField(max_length=100, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    opening_balance_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    opening_balance_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    opening_balance_amount_bcy = models.CharField(max_length=20, blank=True, null=True)
    opening_balance_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_ob_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_ob_receivable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_ob_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_ob_payable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_receivable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_receivable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_payable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_payable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_receivable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_payable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_payable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_retainer_payments = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_retainer_payments_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    status = models.CharField(max_length=20, blank=True, null=True)
    status_formatted = models.CharField(max_length=20, blank=True, null=True)
    payment_reminder_enabled = models.BooleanField(default=False)
    is_sms_enabled = models.BooleanField(default=False)
    is_portal_enabled = models.BooleanField(default=False)
    is_consent_agreed = models.BooleanField(default=False)
    consent_date = models.DateField(blank=True, null=True)
    is_client_review_settings_enabled = models.BooleanField(default=False)
    custom_fields = models.JSONField(default=dict, blank=True, null=True)
    custom_field_hash = models.JSONField(default=dict, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    tds_tax_id = models.CharField(max_length=100, blank=True, null=True)
    tax_name = models.CharField(max_length=100, blank=True, null=True)
    tax_name_formatted = models.CharField(max_length=100, blank=True, null=True)
    tax_percentage = models.DecimalField(
        max_digits=10, decimal_places=6, blank=True, null=True
    )
    country_code = models.CharField(max_length=10, blank=True, null=True)
    country_code_formatted = models.CharField(max_length=10, blank=True, null=True)
    place_of_contact = models.CharField(max_length=100, blank=True, null=True)
    place_of_contact_formatted = models.CharField(max_length=100, blank=True, null=True)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    pan_no = models.CharField(max_length=50, blank=True, null=True)
    trader_name = models.CharField(max_length=255, blank=True, null=True)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    vat_reg_no = models.CharField(max_length=50, blank=True, null=True)
    udyam_reg_no = models.CharField(max_length=50, blank=True, null=True)
    msme_type = models.CharField(max_length=50, blank=True, null=True)
    msme_type_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_reg_no = models.CharField(max_length=50, blank=True, null=True)
    contact_category = models.CharField(max_length=50, blank=True, null=True)
    contact_category_formatted = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    is_linked_with_contact = models.BooleanField(default=False)
    sales_channel = models.CharField(max_length=50, blank=True, null=True)
    ach_supported = models.BooleanField(default=False)
    portal_receipt_count = models.IntegerField(default=0, blank=True, null=True)
    opening_balances = models.JSONField(default=list, blank=True, null=True)
    allow_parent_for_payment_and_view = models.BooleanField(default=False)
    tax_info_list = models.JSONField(default=list, blank=True, null=True)
    entity_address_id = models.CharField(max_length=100, blank=True, null=True)
    billing_address = models.JSONField(default=dict, blank=True, null=True)
    shipping_address = models.JSONField(default=dict, blank=True, null=True)
    contact_persons = models.JSONField(default=list, blank=True, null=True)
    addresses = models.JSONField(default=list, blank=True, null=True)
    pricebook_id = models.CharField(max_length=100, blank=True, null=True)
    pricebook_name = models.CharField(max_length=255, blank=True, null=True)
    default_templates = models.JSONField(default=dict, blank=True, null=True)
    associated_with_square = models.BooleanField(default=False)
    can_add_card = models.BooleanField(default=False)
    can_add_bank_account = models.BooleanField(default=True)
    cards = models.JSONField(default=list, blank=True, null=True)
    checks = models.JSONField(default=list, blank=True, null=True)
    bank_accounts = models.JSONField(default=list, blank=True, null=True)
    vpa_list = models.JSONField(default=list, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    created_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    created_by_name = models.CharField(max_length=255, blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True, null=True)
    zohopeople_client_id = models.CharField(max_length=100, blank=True, null=True)
    vendor_currency_summaries = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return self.contact_name


class SalesOrderLineItem(models.Model):
    line_item_id = models.CharField(max_length=100)
    variant_id = models.CharField(max_length=100, blank=True)
    item_id = models.CharField(max_length=100, blank=True)
    product_id = models.CharField(max_length=100, blank=True)
    attribute_name1 = models.CharField(max_length=255, blank=True)
    attribute_name2 = models.CharField(max_length=255, blank=True)
    attribute_name3 = models.CharField(max_length=255, blank=True)
    attribute_option_name1 = models.CharField(max_length=255, blank=True)
    attribute_option_name2 = models.CharField(max_length=255, blank=True)
    attribute_option_name3 = models.CharField(max_length=255, blank=True)
    attribute_option_data1 = models.CharField(max_length=255, blank=True)
    attribute_option_data2 = models.CharField(max_length=255, blank=True)
    attribute_option_data3 = models.CharField(max_length=255, blank=True)
    is_combo_product = models.BooleanField(default=False)
    sku = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=255, blank=True)
    group_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    item_order = models.IntegerField(default=1)
    bcy_rate = models.DecimalField(max_digits=15, decimal_places=2)
    bcy_rate_formatted = models.CharField(max_length=20)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    rate_formatted = models.CharField(max_length=20)
    sales_rate = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sales_rate_formatted = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit = models.CharField(max_length=50, blank=True)
    pricebook_id = models.CharField(max_length=100, blank=True)
    header_id = models.CharField(max_length=100, blank=True)
    header_name = models.CharField(max_length=255, blank=True)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    discount_amount_formatted = models.CharField(max_length=20)
    discount = models.DecimalField(max_digits=10, decimal_places=6, default=0.00)
    discounts = models.JSONField(default=list)
    gst_treatment_code = models.CharField(max_length=50, blank=True)
    tax_id = models.CharField(max_length=100)
    tax_name = models.CharField(max_length=100)
    tax_type = models.CharField(max_length=50)
    tax_percentage = models.DecimalField(max_digits=10, decimal_places=6)
    line_item_taxes = models.JSONField(default=list)
    item_total = models.DecimalField(max_digits=15, decimal_places=2)
    item_total_formatted = models.CharField(max_length=20)
    item_sub_total = models.DecimalField(max_digits=15, decimal_places=2)
    item_sub_total_formatted = models.CharField(max_length=20)
    item_total_inclusive_of_tax = models.DecimalField(max_digits=15, decimal_places=2)
    item_total_inclusive_of_tax_formatted = models.CharField(max_length=20)
    product_type = models.CharField(max_length=50)
    line_item_type = models.CharField(max_length=50)
    item_type = models.CharField(max_length=50, blank=True)
    item_type_formatted = models.CharField(max_length=50, blank=True)
    hsn_or_sac = models.CharField(max_length=20)
    is_invoiced = models.BooleanField(default=False)
    tags = models.JSONField(default=list)
    image_name = models.CharField(max_length=255, blank=True)
    image_type = models.CharField(max_length=50, blank=True)
    image_document_id = models.CharField(max_length=100, blank=True)
    document_id = models.CharField(max_length=100, blank=True)
    item_custom_fields = models.JSONField(default=list)
    custom_field_hash = models.JSONField(default=dict)
    quantity_invoiced = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00
    )
    quantity_backordered = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00
    )
    quantity_cancelled = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00
    )
    is_fulfillable = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    project_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Line Item {self.line_item_id}"


class SalesOrder(models.Model):
    zoho_customer = models.ForeignKey(
        ZohoCustomer, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    so_line_items = models.ManyToManyField(SalesOrderLineItem, blank=True)
    salesorder_id = models.CharField(max_length=100, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True, null=True)
    crm_owner_id = models.CharField(max_length=100, blank=True, null=True)
    crm_custom_reference_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_potential_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_potential_name = models.CharField(max_length=255, blank=True, null=True)
    salesorder_number = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    date_formatted = models.CharField(max_length=20, blank=True, null=True)
    offline_created_date_with_time = models.CharField(
        max_length=100, blank=True, null=True
    )
    offline_created_date_with_time_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    tracking_url = models.URLField(blank=True, null=True)
    has_discount = models.BooleanField(default=False)
    is_pre_gst = models.BooleanField(default=False)
    invoice_conversion_type = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    status_formatted = models.CharField(max_length=20, blank=True, null=True)
    color_code = models.CharField(max_length=20, blank=True, null=True)
    current_sub_status_id = models.CharField(max_length=100, blank=True, null=True)
    current_sub_status = models.CharField(max_length=20, blank=True, null=True)
    current_sub_status_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    sub_statuses = models.JSONField(default=list, blank=True, null=True)
    shipment_date = models.DateField(blank=True, null=True)
    shipment_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    reference_number = models.CharField(max_length=255, blank=True, null=True)
    customer_id = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    currency_formatter = models.JSONField(default=dict, blank=True, null=True)
    contact_persons = models.JSONField(default=list, blank=True, null=True)
    contact_persons_associated = models.JSONField(default=list, blank=True, null=True)
    contact_person_details = models.JSONField(default=list, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    contact_category = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    place_of_supply = models.CharField(max_length=50, blank=True, null=True)
    place_of_supply_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_specification = models.CharField(max_length=50, blank=True, null=True)
    is_taxable = models.BooleanField(default=False)
    has_shipping_address = models.BooleanField(default=True)
    currency_id = models.CharField(max_length=100, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, blank=True, null=True
    )
    is_fba_shipment_created = models.BooleanField(default=False)
    is_discount_before_tax = models.BooleanField(default=True)
    discount_type = models.CharField(max_length=20, blank=True, null=True)
    estimate_id = models.CharField(max_length=100, blank=True, null=True)
    delivery_method = models.CharField(max_length=100, blank=True, null=True)
    delivery_method_id = models.CharField(max_length=100, blank=True, null=True)
    is_inclusive_tax = models.BooleanField(default=False)
    tax_rounding = models.CharField(max_length=50, blank=True, null=True)
    tds_override_preference = models.CharField(max_length=50, blank=True, null=True)
    order_status = models.CharField(max_length=20, blank=True, null=True)
    order_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    invoiced_status = models.CharField(max_length=20, blank=True, null=True)
    invoiced_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    paid_status = models.CharField(max_length=20, blank=True, null=True)
    paid_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    account_identifier = models.CharField(max_length=100, blank=True, null=True)
    integration_id = models.CharField(max_length=100, blank=True, null=True)
    has_qty_cancelled = models.BooleanField(default=False)
    is_reverse_charge_applied = models.BooleanField(default=False)
    shipping_details = models.JSONField(default=dict, blank=True, null=True)
    created_by_email = models.EmailField(blank=True, null=True)
    created_by_name = models.CharField(max_length=255, blank=True, null=True)
    branch_id = models.CharField(max_length=100, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    total_quantity = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    total_quantity_formatted = models.CharField(max_length=20, blank=True, null=True)
    is_portal_enabled = models.BooleanField(default=False)
    is_data_redacted = models.BooleanField(default=False)
    can_fetch_redacted_data = models.BooleanField(default=False)
    can_edit_marketplace_tax = models.BooleanField(default=False)
    entity_tags = models.CharField(max_length=255, blank=True, null=True)
    submitter_id = models.CharField(max_length=100, blank=True, null=True)
    approver_id = models.CharField(max_length=100, blank=True, null=True)
    submitted_date = models.CharField(max_length=100, blank=True, null=True)
    submitted_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    submitted_by = models.CharField(max_length=100, blank=True, null=True)
    submitted_by_name = models.CharField(max_length=255, blank=True, null=True)
    submitted_by_email = models.EmailField(blank=True, null=True)
    submitted_by_photo_url = models.URLField(blank=True, null=True)
    price_precision = models.IntegerField(blank=True, null=True)
    is_emailed = models.BooleanField(default=False)
    purchaseorders = models.JSONField(default=list, blank=True, null=True)
    billing_address_id = models.CharField(max_length=100, blank=True, null=True)
    billing_address = models.JSONField(default=dict, blank=True, null=True)
    shipping_address_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_address = models.JSONField(default=dict, blank=True, null=True)
    is_test_order = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    payment_terms = models.IntegerField(default=0, blank=True, null=True)
    payment_terms_label = models.CharField(max_length=100, blank=True, null=True)
    custom_fields = models.JSONField(default=list, blank=True, null=True)
    custom_field_hash = models.JSONField(default=dict, blank=True, null=True)
    template_id = models.CharField(max_length=100, blank=True, null=True)
    template_name = models.CharField(max_length=255, blank=True, null=True)
    page_width = models.CharField(max_length=20, blank=True, null=True)
    page_height = models.CharField(max_length=20, blank=True, null=True)
    orientation = models.CharField(max_length=20, blank=True, null=True)
    template_type = models.CharField(max_length=20, blank=True, null=True)
    template_type_formatted = models.CharField(max_length=20, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    created_time_formatted = models.CharField(max_length=20, blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    last_modified_time_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    created_by_id = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    created_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    last_modified_by_id = models.CharField(max_length=100, blank=True, null=True)
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    can_send_in_mail = models.BooleanField(default=False)
    salesperson_id = models.CharField(max_length=100, blank=True, null=True)
    salesperson_name = models.CharField(max_length=255, blank=True, null=True)
    merchant_id = models.CharField(max_length=100, blank=True, null=True)
    merchant_name = models.CharField(max_length=255, blank=True, null=True)
    merchant_gst_no = models.CharField(max_length=50, blank=True, null=True)
    pickup_location_id = models.CharField(max_length=100, blank=True, null=True)
    discount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    discount_applied_on_amount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    is_adv_tracking_in_package = models.BooleanField(default=False)
    shipping_charge_tax_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_charge_tax_name = models.CharField(max_length=255, blank=True, null=True)
    shipping_charge_tax_type = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_tax_percentage = models.CharField(
        max_length=10, blank=True, null=True
    )
    shipping_charge_tax_exemption_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    shipping_charge_tax_exemption_code = models.CharField(
        max_length=50, blank=True, null=True
    )
    shipping_charge_sac_code = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_tax = models.CharField(max_length=50, blank=True, null=True)
    bcy_shipping_charge_tax = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_exclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    shipping_charge_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    shipping_charge_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    shipping_charge_exclusive_of_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    shipping_charge_inclusive_of_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    shipping_charge = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    shipping_charge_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_shipping_charge = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    adjustment = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    adjustment_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_adjustment = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    adjustment_description = models.CharField(max_length=255, blank=True, null=True)
    roundoff_value = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    roundoff_value_formatted = models.CharField(max_length=20, blank=True, null=True)
    transaction_rounding_type = models.CharField(max_length=20, blank=True, null=True)
    sub_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_sub_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_inclusive_of_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    sub_total_exclusive_of_discount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_exclusive_of_discount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    discount_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    discount_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_discount_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    discount_percent = models.DecimalField(
        max_digits=10, decimal_places=6, blank=True, null=True
    )
    tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    tax_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_formatted = models.CharField(max_length=20, blank=True, null=True)
    computation_type = models.CharField(max_length=20, blank=True, null=True)
    bcy_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    reverse_charge_tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    reverse_charge_tax_total_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    taxes = models.JSONField(default=list, blank=True, null=True)
    tds_summary = models.JSONField(default=list, blank=True, null=True)
    invoices = models.JSONField(default=list, blank=True, null=True)
    contact = models.JSONField(default=dict, blank=True, null=True)
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    balance_formatted = models.CharField(max_length=20, blank=True, null=True)
    approvers_list = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"Sales Order {self.salesorder_id}"


class ClientInvoiceLineItem(models.Model):
    line_item_id = models.CharField(max_length=255)
    item_id = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    item_order = models.IntegerField()
    product_type = models.CharField(max_length=255)
    has_product_type_mismatch = models.BooleanField(default=False)
    has_invalid_hsn = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    internal_name = models.CharField(max_length=255)
    description = models.TextField()
    unit = models.CharField(max_length=255)
    quantity = models.IntegerField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount_formatted = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discounts = models.JSONField(default=list)
    bcy_rate = models.DecimalField(max_digits=10, decimal_places=2)
    bcy_rate_formatted = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_formatted = models.CharField(max_length=255)
    account_id = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    header_id = models.CharField(max_length=255)
    header_name = models.CharField(max_length=255)
    pricebook_id = models.CharField(max_length=255)
    item_total_inclusive_of_tax = models.DecimalField(max_digits=10, decimal_places=2)
    item_total_inclusive_of_tax_formatted = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=255)
    tax_name = models.CharField(max_length=255)
    tax_type = models.CharField(max_length=255)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    gst_treatment_code = models.CharField(max_length=255)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
    item_total_formatted = models.CharField(max_length=255)
    item_custom_fields = models.JSONField(default=dict)
    pricing_scheme = models.CharField(max_length=255)
    tags = models.JSONField(default=list)
    documents = models.JSONField(default=list)
    hsn_or_sac = models.CharField(max_length=255)
    image_document_id = models.CharField(max_length=255)
    reverse_charge_tax_id = models.CharField(max_length=255)
    line_item_taxes = models.JSONField(default=list)
    bill_id = models.CharField(max_length=255)
    bill_item_id = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255)
    time_entry_ids = models.JSONField(default=list)
    expense_id = models.CharField(max_length=255)
    item_type = models.CharField(max_length=255)
    item_type_formatted = models.CharField(max_length=255)
    expense_receipt_name = models.CharField(max_length=255)
    sales_rate = models.CharField(max_length=255)
    sales_rate_formatted = models.CharField(max_length=255)
    salesorder_item_id = models.CharField(max_length=255)
    can_show_in_task_table = models.BooleanField(default=False)
    cost_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cost_amount_formatted = models.CharField(max_length=255)
    markup_percent = models.DecimalField(max_digits=5, decimal_places=2)
    markup_percent_formatted = models.CharField(max_length=255)

    class Meta:
        db_table = "line_items"


class ClientInvoice(models.Model):
    zoho_customer = models.ForeignKey(
        ZohoCustomer, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    client_invoice_line_items = models.ManyToManyField(ClientInvoiceLineItem)
    invoice_id = models.CharField(max_length=100)
    invoice_number = models.CharField(max_length=100)
    date = models.DateField()
    date_formatted = models.CharField(max_length=20)
    due_date = models.DateField()
    due_date_formatted = models.CharField(max_length=20)
    offline_created_date_with_time = models.CharField(max_length=100, blank=True)
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)
    cf_meeraq_ctt = models.CharField(max_length=100)
    cf_meeraq_ctt_unformatted = models.CharField(max_length=100)
    email = models.EmailField()
    currency_id = models.CharField(max_length=100)
    invoice_source = models.CharField(max_length=100)
    invoice_source_formatted = models.CharField(max_length=100)
    currency_code = models.CharField(max_length=10)
    currency_symbol = models.CharField(max_length=10)
    currency_name_formatted = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    status_formatted = models.CharField(max_length=20)
    custom_fields = models.JSONField(default=list)
    custom_field_hash = models.JSONField(default=dict)
    recurring_invoice_id = models.CharField(max_length=100, blank=True)
    place_of_supply = models.CharField(max_length=50)
    place_of_supply_formatted = models.CharField(max_length=50)
    payment_terms = models.IntegerField()
    payment_terms_label = models.CharField(max_length=100)
    payment_reminder_enabled = models.BooleanField(default=False)
    payment_made = models.DecimalField(max_digits=15, decimal_places=2)
    payment_made_formatted = models.CharField(max_length=20)
    crm_owner_id = models.CharField(max_length=100, blank=True)
    crm_custom_reference_id = models.CharField(max_length=100, blank=True)
    zcrm_potential_id = models.CharField(max_length=100, blank=True)
    zcrm_potential_name = models.CharField(max_length=255, blank=True)
    next_retry_date = models.CharField(max_length=100, blank=True)
    next_retry_date_formatted = models.CharField(max_length=20, blank=True)
    next_retry_number = models.IntegerField(default=0)
    reference_number = models.CharField(max_length=255)
    is_inventory_valuation_pending = models.BooleanField(default=False)
    due_days = models.CharField(max_length=100, blank=True)
    lock_details = models.JSONField(default=dict)
    credits = models.JSONField(default=list)
    journal_credits = models.JSONField(default=list)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6)
    is_autobill_enabled = models.BooleanField(default=False)
    inprocess_transaction_present = models.BooleanField(default=False)
    allow_partial_payments = models.BooleanField(default=False)
    price_precision = models.IntegerField()
    sub_total = models.DecimalField(max_digits=15, decimal_places=2)
    sub_total_formatted = models.CharField(max_length=20)
    tax_total = models.DecimalField(max_digits=15, decimal_places=2)
    tax_total_formatted = models.CharField(max_length=20)
    discount_total = models.DecimalField(max_digits=15, decimal_places=2)
    discount_total_formatted = models.CharField(max_length=20)
    discount_percent = models.DecimalField(max_digits=10, decimal_places=6)
    discount = models.DecimalField(max_digits=15, decimal_places=2)
    discount_applied_on_amount = models.DecimalField(max_digits=15, decimal_places=2)
    discount_type = models.CharField(max_length=20)
    tds_override_preference = models.CharField(max_length=50)
    is_discount_before_tax = models.BooleanField(default=True)
    adjustment = models.DecimalField(max_digits=15, decimal_places=2)
    adjustment_formatted = models.CharField(max_length=20)
    adjustment_description = models.CharField(max_length=255)
    shipping_charge_tax_id = models.CharField(max_length=100, blank=True)
    shipping_charge_tax_name = models.CharField(max_length=255, blank=True)
    shipping_charge_tax_type = models.CharField(max_length=50, blank=True)
    shipping_charge_tax_percentage = models.CharField(max_length=10, blank=True)
    shipping_charge_tax_exemption_id = models.CharField(max_length=100, blank=True)
    shipping_charge_tax_exemption_code = models.CharField(max_length=50, blank=True)
    shipping_charge_sac_code = models.CharField(max_length=50, blank=True)
    shipping_charge_tax = models.CharField(max_length=50, blank=True)
    bcy_shipping_charge_tax = models.CharField(max_length=50, blank=True)
    shipping_charge_exclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2
    )
    shipping_charge_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2
    )
    shipping_charge_tax_formatted = models.CharField(max_length=20, blank=True)
    shipping_charge_exclusive_of_tax_formatted = models.CharField(max_length=20)
    shipping_charge_inclusive_of_tax_formatted = models.CharField(max_length=20)
    shipping_charge = models.DecimalField(max_digits=15, decimal_places=2)
    shipping_charge_formatted = models.CharField(max_length=20)
    bcy_shipping_charge = models.DecimalField(max_digits=15, decimal_places=2)
    bcy_adjustment = models.DecimalField(max_digits=15, decimal_places=2)
    bcy_sub_total = models.DecimalField(max_digits=15, decimal_places=2)
    bcy_discount_total = models.DecimalField(max_digits=15, decimal_places=2)
    bcy_tax_total = models.DecimalField(max_digits=15, decimal_places=2)
    bcy_total = models.DecimalField(max_digits=15, decimal_places=2)
    is_reverse_charge_applied = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    total_formatted = models.CharField(max_length=20)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    balance_formatted = models.CharField(max_length=20)
    write_off_amount = models.DecimalField(max_digits=15, decimal_places=2)
    write_off_amount_formatted = models.CharField(max_length=20)
    roundoff_value = models.DecimalField(max_digits=15, decimal_places=2)
    roundoff_value_formatted = models.CharField(max_length=20)
    transaction_rounding_type = models.CharField(max_length=20)
    reference_invoice_type = models.CharField(max_length=100)
    is_inclusive_tax = models.BooleanField(default=False)
    sub_total_inclusive_of_tax = models.DecimalField(max_digits=15, decimal_places=2)
    sub_total_inclusive_of_tax_formatted = models.CharField(max_length=20)
    tax_specification = models.CharField(max_length=50)
    gst_no = models.CharField(max_length=50)
    gst_treatment = models.CharField(max_length=50)
    gst_treatment_formatted = models.CharField(max_length=50)
    tax_reg_no = models.CharField(max_length=50)
    contact_category = models.CharField(max_length=50)
    tax_treatment = models.CharField(max_length=50)
    tax_treatment_formatted = models.CharField(max_length=50)
    tax_rounding = models.CharField(max_length=50)
    taxes = models.JSONField(default=list)
    filed_in_vat_return_id = models.CharField(max_length=100)
    filed_in_vat_return_name = models.CharField(max_length=100)
    filed_in_vat_return_type = models.CharField(max_length=100)
    gst_return_details = models.JSONField(default=dict)
    reverse_charge_tax_total = models.DecimalField(max_digits=15, decimal_places=2)
    reverse_charge_tax_total_formatted = models.CharField(max_length=20)
    tds_calculation_type = models.CharField(max_length=50)
    can_send_invoice_sms = models.BooleanField(default=False)
    payment_expected_date = models.CharField(max_length=100)
    payment_expected_date_formatted = models.CharField(max_length=20)
    payment_discount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_discount_formatted = models.CharField(max_length=20)
    stop_reminder_until_payment_expected_date = models.BooleanField(default=False)
    last_payment_date = models.CharField(max_length=100)
    last_payment_date_formatted = models.CharField(max_length=20)
    autobill_status = models.CharField(max_length=50)
    autobill_status_formatted = models.CharField(max_length=50)
    ach_supported = models.BooleanField(default=False)
    ach_payment_initiated = models.BooleanField(default=False)
    payment_options = models.JSONField(default=dict)
    payments = models.JSONField(default=list)
    reader_offline_payment_initiated = models.BooleanField(default=False)
    is_square_transaction = models.BooleanField(default=False)
    contact_persons = models.JSONField(default=list)
    contact_persons_associated = models.JSONField(default=list)
    attachment_name = models.CharField(max_length=255)
    documents = models.JSONField(default=list)
    computation_type = models.CharField(max_length=20)
    tds_summary = models.JSONField(default=list)
    debit_notes = models.JSONField(default=list)
    deliverychallans = models.JSONField(default=list)
    bills = models.JSONField(default=list)
    ewaybills = models.JSONField(default=list)
    dispatch_from_address = models.JSONField(default=dict)
    is_eway_bill_required = models.BooleanField(default=False)
    can_generate_ewaybill_using_irn = models.BooleanField(default=True)
    branch_id = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=255)
    merchant_id = models.CharField(max_length=100)
    merchant_name = models.CharField(max_length=255)
    merchant_gst_no = models.CharField(max_length=50)
    ecomm_operator_id = models.CharField(max_length=100)
    ecomm_operator_name = models.CharField(max_length=255)
    ecomm_operator_gst_no = models.CharField(max_length=50)
    salesorder_id = models.CharField(max_length=100)
    salesorder_number = models.CharField(max_length=255)
    salesorders = models.JSONField(default=list)
    shipping_bills = models.JSONField(default=list)
    unbilled_expenses_count = models.IntegerField(default=0)
    unbilled_bill_items_count = models.IntegerField(default=0)
    has_timesheet_entries = models.BooleanField(default=False)
    is_associated_with_project = models.BooleanField(default=False)
    warn_convert_to_open = models.BooleanField(default=True)
    warn_create_creditnotes = models.BooleanField(default=False)
    contact_persons_details = models.JSONField(default=list)
    contact = models.JSONField(default=dict)
    salesperson_id = models.CharField(max_length=100)
    salesperson_name = models.CharField(max_length=255)
    is_emailed = models.BooleanField(default=False)
    reminders_sent = models.IntegerField(default=0)
    last_reminder_sent_date = models.CharField(max_length=100)
    last_reminder_sent_date_formatted = models.CharField(max_length=20)
    next_reminder_date_formatted = models.CharField(max_length=20)
    is_portal_enabled = models.BooleanField(default=False)
    is_viewed_by_client = models.BooleanField(default=False)
    client_viewed_time = models.CharField(max_length=100)
    client_viewed_time_formatted = models.CharField(max_length=20)
    submitter_id = models.CharField(max_length=100)
    approver_id = models.CharField(max_length=100)
    submitted_date = models.CharField(max_length=100)
    submitted_date_formatted = models.CharField(max_length=20)
    submitted_by = models.CharField(max_length=100)
    submitted_by_name = models.CharField(max_length=255)
    submitted_by_email = models.EmailField()
    submitted_by_photo_url = models.URLField()
    template_id = models.CharField(max_length=100)
    template_name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=20)
    template_type_formatted = models.CharField(max_length=20)
    notes = models.TextField()
    terms = models.TextField()
    billing_address = models.JSONField(default=dict)
    shipping_address = models.JSONField(default=dict)
    invoice_url = models.URLField()
    subject_content = models.TextField()
    can_send_in_mail = models.BooleanField(default=False)
    created_time = models.DateTimeField()
    last_modified_time = models.DateTimeField()
    created_date = models.DateField()
    created_date_formatted = models.CharField(max_length=20)
    created_by_id = models.CharField(max_length=100)
    created_by_name = models.CharField(max_length=255)
    last_modified_by_id = models.CharField(max_length=100)
    page_width = models.CharField(max_length=20)
    page_height = models.CharField(max_length=20)
    orientation = models.CharField(max_length=20)
    is_backorder = models.BooleanField(default=False)
    sales_channel = models.CharField(max_length=50)
    sales_channel_formatted = models.CharField(max_length=50)
    is_pre_gst = models.BooleanField(default=False)
    type_formatted = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    color_code = models.CharField(max_length=20)
    current_sub_status_id = models.CharField(max_length=100)
    current_sub_status = models.CharField(max_length=50)
    current_sub_status_formatted = models.CharField(max_length=50)
    sub_statuses = models.JSONField(default=list)
    reason_for_debit_note = models.CharField(max_length=50)
    reason_for_debit_note_formatted = models.CharField(max_length=50)
    estimate_id = models.CharField(max_length=100)
    is_client_review_settings_enabled = models.BooleanField(default=False)
    is_taxable = models.BooleanField(default=True)
    unused_credits_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2
    )
    unused_credits_receivable_amount_formatted = models.CharField(max_length=20)
    unused_retainer_payments = models.DecimalField(max_digits=15, decimal_places=2)
    unused_retainer_payments_formatted = models.CharField(max_length=20)
    credits_applied = models.DecimalField(max_digits=15, decimal_places=2)
    credits_applied_formatted = models.CharField(max_length=20)
    tax_amount_withheld = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount_withheld_formatted = models.CharField(max_length=20)
    is_cloneable = models.BooleanField(default=True)
    can_send_in_mail_state = models.BooleanField(default=False)
    schedule_time = models.CharField(max_length=100)
    schedule_time_formatted = models.CharField(max_length=20)
    no_of_copies = models.IntegerField(default=1)
    show_no_of_copies = models.BooleanField(default=True)
    auto_reminders_configured = models.BooleanField(default=False)
    customer_default_billing_address = models.JSONField(default=dict)
    can_send_comment_notification = models.BooleanField(default=False)
    reference_invoice = models.JSONField(default=dict)
    includes_package_tracking_info = models.BooleanField(default=False)
    approvers_list = models.JSONField(default=list)
    qr_code = models.JSONField(default=dict)

    def __str__(self):
        return f"Invoice {self.invoice_number}"


class PurchaseOrderLineItem(models.Model):
    item_id = models.CharField(max_length=100)
    line_item_id = models.CharField(max_length=100)
    salesorder_item_id = models.CharField(max_length=100)
    image_document_id = models.CharField(max_length=100)
    sku = models.CharField(max_length=100)
    account_id = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    item_order = models.IntegerField()
    bcy_rate = models.DecimalField(max_digits=10, decimal_places=2)
    bcy_rate_formatted = models.CharField(max_length=20)
    pricebook_id = models.CharField(max_length=100)
    header_id = models.CharField(max_length=100)
    header_name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_formatted = models.CharField(max_length=20)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discounts = models.JSONField(default=list)  # New field for discounts
    quantity_cancelled = models.IntegerField()
    quantity_billed = models.IntegerField()
    unit = models.CharField(max_length=50)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
    item_total_formatted = models.CharField(max_length=20)
    item_total_inclusive_of_tax = models.DecimalField(max_digits=10, decimal_places=2)
    item_total_inclusive_of_tax_formatted = models.CharField(max_length=20)
    tax_exemption_id = models.CharField(max_length=100)
    tax_exemption_code = models.CharField(max_length=100)
    gst_treatment_code = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=100)
    tax_name = models.CharField(max_length=100)
    tax_type = models.CharField(max_length=50)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    product_type = models.CharField(max_length=50)
    item_type = models.CharField(max_length=50)
    item_type_formatted = models.CharField(max_length=50)
    line_item_taxes = models.JSONField(default=list)
    hsn_or_sac = models.CharField(max_length=50)
    reverse_charge_tax_id = models.CharField(max_length=100)
    tags = models.JSONField(default=list)
    item_custom_fields = models.JSONField(default=list)
    project_id = models.CharField(max_length=100)
    image_name = models.CharField(max_length=100)
    image_type = models.CharField(max_length=100)
    purchase_request_items = models.JSONField(default=list)

    def __str__(self):
        return self.item_id  # or any other field you prefer


class PurchaseOrder(models.Model):
    zoho_vendor = models.ForeignKey(
        ZohoVendor, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    po_line_items = models.ManyToManyField(PurchaseOrderLineItem)
    purchaseorder_id = models.CharField(max_length=100)
    branch_id = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100)
    documents = models.JSONField(default=list)
    crm_owner_id = models.CharField(max_length=100)
    crm_custom_reference_id = models.CharField(max_length=100)
    tax_treatment = models.CharField(max_length=100)
    tax_treatment_formatted = models.CharField(max_length=100)
    gst_no = models.CharField(max_length=100)
    contact_category = models.CharField(max_length=100)
    gst_treatment = models.CharField(max_length=100)
    gst_treatment_formatted = models.CharField(max_length=100)
    purchaseorder_number = models.CharField(max_length=100)
    date = models.DateField()
    date_formatted = models.CharField(max_length=20)
    currency_formatter = models.JSONField()
    client_viewed_time = models.CharField(max_length=100)
    client_viewed_time_formatted = models.CharField(max_length=100)
    is_viewed_by_client = models.BooleanField(default=False)
    is_pre_gst = models.BooleanField(default=False)
    expected_delivery_date = models.CharField(max_length=100)
    expected_delivery_date_formatted = models.CharField(max_length=100)
    reference_number = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    status_formatted = models.CharField(max_length=100)
    order_status = models.CharField(max_length=100)
    order_status_formatted = models.CharField(max_length=100)
    billed_status = models.CharField(max_length=100)
    billed_status_formatted = models.CharField(max_length=100)
    color_code = models.CharField(max_length=100)
    current_sub_status_id = models.CharField(max_length=100)
    current_sub_status = models.CharField(max_length=100)
    current_sub_status_formatted = models.CharField(max_length=100)
    sub_statuses = models.JSONField(default=list)
    source_of_supply = models.CharField(max_length=100)
    source_of_supply_formatted = models.CharField(max_length=100)
    destination_of_supply = models.CharField(max_length=100)
    destination_of_supply_formatted = models.CharField(max_length=100)
    vendor_id = models.CharField(max_length=100)
    vendor_name = models.CharField(max_length=100)
    is_portal_enabled = models.BooleanField(default=False)
    contact_persons = models.JSONField(default=list)
    currency_id = models.CharField(max_length=100)
    currency_code = models.CharField(max_length=10)
    currency_symbol = models.CharField(max_length=10)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_date = models.CharField(max_length=100)
    delivery_date_formatted = models.CharField(max_length=100)
    is_emailed = models.BooleanField(default=False)
    show_convert_to_bill = models.BooleanField(default=True)
    is_inclusive_tax = models.BooleanField(default=False)
    tax_rounding = models.CharField(max_length=100)
    is_reverse_charge_applied = models.BooleanField(default=False)
    is_adv_tracking_in_receive = models.BooleanField(default=False)
    salesorder_id = models.CharField(max_length=100)
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_quantity_formatted = models.CharField(max_length=20)
    tds_calculation_type = models.CharField(max_length=100)
    has_qty_cancelled = models.BooleanField(default=False)
    adjustment = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment_formatted = models.CharField(max_length=20)
    adjustment_description = models.CharField(max_length=100)
    discount_amount_formatted = models.CharField(max_length=20)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied_on_amount_formatted = models.CharField(max_length=20)
    discount_applied_on_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_discount_before_tax = models.BooleanField(default=True)
    discount_account_id = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=100)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total_formatted = models.CharField(max_length=20)
    sub_total_inclusive_of_tax = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total_inclusive_of_tax_formatted = models.CharField(max_length=20)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax_total_formatted = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    total_formatted = models.CharField(max_length=20)
    taxes = models.JSONField(default=list)
    tax_override = models.BooleanField(default=False)
    tds_override_preference = models.CharField(max_length=100)
    tds_summary = models.JSONField(default=list)
    price_precision = models.IntegerField()
    submitted_date = models.CharField(max_length=100)
    submitted_date_formatted = models.CharField(max_length=100)
    submitted_by = models.CharField(max_length=100)
    submitted_by_name = models.CharField(max_length=100)
    submitted_by_email = models.CharField(max_length=100)
    submitted_by_photo_url = models.CharField(max_length=100)
    submitter_id = models.CharField(max_length=100)
    approver_id = models.CharField(max_length=100)
    approvers_list = models.JSONField(default=list)
    billing_address_id = models.CharField(max_length=100)
    billing_address = models.JSONField()
    notes = models.TextField()
    terms = models.TextField()
    payment_terms = models.IntegerField()
    payment_terms_label = models.CharField(max_length=100)
    ship_via = models.CharField(max_length=100)
    ship_via_id = models.CharField(max_length=100)
    attention = models.CharField(max_length=100)
    delivery_org_address_id = models.CharField(max_length=100)
    delivery_customer_id = models.CharField(max_length=100)
    delivery_customer_address_id = models.CharField(max_length=100)
    delivery_address = models.JSONField()
    custom_fields = models.JSONField(default=list)
    custom_field_hash = models.JSONField()
    attachment_name = models.CharField(max_length=100)
    can_send_in_mail = models.BooleanField(default=False)
    template_id = models.CharField(max_length=100)
    template_name = models.CharField(max_length=100)
    page_width = models.CharField(max_length=100)
    page_height = models.CharField(max_length=100)
    orientation = models.CharField(max_length=100)
    template_type = models.CharField(max_length=100)
    template_type_formatted = models.CharField(max_length=100)
    created_time = models.DateTimeField()
    created_by_id = models.CharField(max_length=100)
    last_modified_time = models.DateTimeField()
    can_mark_as_bill = models.BooleanField(default=False)
    can_mark_as_unbill = models.BooleanField(default=False)
    salesorders = models.JSONField(default=list)
    bills = models.JSONField(default=list)

    def __str__(self):
        return self.purchaseorder_number


class BillLineItem(models.Model):
    purchaseorder_item_id = models.CharField(max_length=100)
    line_item_id = models.CharField(max_length=100)
    item_id = models.CharField(max_length=100)
    itc_eligibility = models.CharField(max_length=100)
    gst_treatment_code = models.CharField(max_length=100)
    image_document_id = models.CharField(max_length=100)
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    account_id = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    description = models.TextField()
    bcy_rate = models.DecimalField(max_digits=10, decimal_places=2)
    bcy_rate_formatted = models.CharField(max_length=20)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_formatted = models.CharField(max_length=20)
    pricebook_id = models.CharField(max_length=100)
    header_id = models.CharField(max_length=100)
    header_name = models.CharField(max_length=100)
    tags = models.JSONField(default=list)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discounts = models.JSONField(default=list)
    markup_percent = models.DecimalField(max_digits=10, decimal_places=2)
    markup_percent_formatted = models.CharField(max_length=20)
    tax_id = models.CharField(max_length=100)
    tax_exemption_id = models.CharField(max_length=100)
    tax_exemption_code = models.CharField(max_length=100)
    tax_name = models.CharField(max_length=100)
    tax_type = models.CharField(max_length=50)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    line_item_taxes = models.JSONField(default=list)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
    item_total_formatted = models.CharField(max_length=20)
    item_total_inclusive_of_tax = models.DecimalField(max_digits=10, decimal_places=2)
    item_total_inclusive_of_tax_formatted = models.CharField(max_length=20)
    item_order = models.IntegerField()
    unit = models.CharField(max_length=50)
    product_type = models.CharField(max_length=50)
    item_type = models.CharField(max_length=50)
    item_type_formatted = models.CharField(max_length=50)
    has_product_type_mismatch = models.BooleanField(default=False)
    hsn_or_sac = models.CharField(max_length=50)
    reverse_charge_tax_id = models.CharField(max_length=100)
    image_name = models.CharField(max_length=100)
    image_type = models.CharField(max_length=100)
    is_billable = models.BooleanField(default=False)
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    project_id = models.CharField(max_length=100)
    project_name = models.CharField(max_length=100)
    invoice_id = models.CharField(max_length=100)
    invoice_number = models.CharField(max_length=100)
    item_custom_fields = models.JSONField(default=list)
    purchase_request_items = models.JSONField(default=list)

    def __str__(self):
        return self.line_item_id


class Bill(models.Model):
    zoho_vendor = models.ForeignKey(
        ZohoVendor, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    bill_line_items = models.ManyToManyField(BillLineItem)
    bill_id = models.CharField(max_length=100)
    branch_id = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100)
    purchaseorder_ids = models.JSONField(default=list)
    vendor_id = models.CharField(max_length=100)
    vendor_name = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    source_of_supply = models.CharField(max_length=100)
    source_of_supply_formatted = models.CharField(max_length=100)
    destination_of_supply = models.CharField(max_length=100)
    destination_of_supply_formatted = models.CharField(max_length=100)
    can_amend_transaction = models.BooleanField(default=False)
    gst_no = models.CharField(max_length=100)
    reference_invoice_type = models.CharField(max_length=100)
    contact_category = models.CharField(max_length=100)
    gst_treatment = models.CharField(max_length=100)
    gst_treatment_formatted = models.CharField(max_length=100)
    tax_treatment = models.CharField(max_length=100)
    tax_treatment_formatted = models.CharField(max_length=100)
    gst_return_details = models.JSONField(default=dict)
    invoice_conversion_type = models.CharField(max_length=100)
    unused_credits_payable_amount = models.DecimalField(max_digits=10, decimal_places=2)
    unused_credits_payable_amount_formatted = models.CharField(max_length=20)
    status = models.CharField(max_length=100)
    status_formatted = models.CharField(max_length=100)
    color_code = models.CharField(max_length=100)
    current_sub_status_id = models.CharField(max_length=100)
    current_sub_status = models.CharField(max_length=100)
    current_sub_status_formatted = models.CharField(max_length=100)
    sub_statuses = models.JSONField(default=list)
    bill_number = models.CharField(max_length=100)
    date = models.DateField()
    date_formatted = models.CharField(max_length=100)
    is_pre_gst = models.BooleanField(default=False)
    due_date = models.DateField()
    due_date_formatted = models.CharField(max_length=100)
    discount_setting = models.CharField(max_length=100)
    tds_calculation_type = models.CharField(max_length=100)
    is_tds_amount_in_percent = models.BooleanField(default=True)
    tds_percent_formatted = models.CharField(max_length=100)
    tds_percent = models.DecimalField(max_digits=5, decimal_places=2)
    tds_amount_formatted = models.CharField(max_length=20)
    tds_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_account_id = models.CharField(max_length=100)
    tds_tax_id = models.CharField(max_length=100)
    tds_tax_name = models.CharField(max_length=100)
    tds_section_formatted = models.CharField(max_length=100)
    tds_section = models.CharField(max_length=100)
    payment_terms = models.IntegerField()
    payment_terms_label = models.CharField(max_length=100)
    payment_expected_date = models.DateField()
    payment_expected_date_formatted = models.CharField(max_length=100)
    reference_number = models.CharField(max_length=100)
    recurring_bill_id = models.CharField(max_length=100)
    due_by_days = models.IntegerField()
    due_in_days = models.CharField(max_length=100)
    due_days = models.CharField(max_length=100)
    currency_id = models.CharField(max_length=100)
    currency_code = models.CharField(max_length=100)
    currency_symbol = models.CharField(max_length=100)
    currency_name_formatted = models.CharField(max_length=100)
    documents = models.JSONField(default=list)
    subject_content = models.CharField(max_length=100)
    price_precision = models.IntegerField()
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2)
    custom_fields = models.JSONField(default=list)
    custom_field_hash = models.JSONField(default=dict)
    is_viewed_by_client = models.BooleanField(default=False)
    client_viewed_time = models.CharField(max_length=100)
    client_viewed_time_formatted = models.CharField(max_length=100)
    is_item_level_tax_calc = models.BooleanField(default=False)
    is_inclusive_tax = models.BooleanField(default=False)
    tax_rounding = models.CharField(max_length=100)
    filed_in_vat_return_id = models.CharField(max_length=100)
    filed_in_vat_return_name = models.CharField(max_length=100)
    filed_in_vat_return_type = models.CharField(max_length=100)
    is_reverse_charge_applied = models.BooleanField(default=False)
    is_uber_bill = models.BooleanField(default=False)
    is_tally_bill = models.BooleanField(default=False)
    track_discount_in_account = models.BooleanField(default=True)
    is_bill_reconciliation_violated = models.BooleanField(default=False)
    submitted_date = models.CharField(max_length=100)
    submitted_date_formatted = models.CharField(max_length=100)
    submitted_by = models.CharField(max_length=100)
    submitted_by_name = models.CharField(max_length=100)
    submitted_by_email = models.CharField(max_length=100)
    submitted_by_photo_url = models.CharField(max_length=100)
    submitter_id = models.CharField(max_length=100)
    approver_id = models.CharField(max_length=100)
    adjustment = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment_formatted = models.CharField(max_length=100)
    adjustment_description = models.CharField(max_length=100)
    discount_amount_formatted = models.CharField(max_length=100)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied_on_amount_formatted = models.CharField(max_length=100)
    discount_applied_on_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_discount_before_tax = models.BooleanField(default=True)
    discount_account_id = models.CharField(max_length=100)
    discount_account_name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=100)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total_formatted = models.CharField(max_length=100)
    sub_total_inclusive_of_tax = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total_inclusive_of_tax_formatted = models.CharField(max_length=100)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax_total_formatted = models.CharField(max_length=100)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    total_formatted = models.CharField(max_length=100)
    payment_made = models.DecimalField(max_digits=10, decimal_places=2)
    payment_made_formatted = models.CharField(max_length=100)
    vendor_credits_applied = models.DecimalField(max_digits=10, decimal_places=2)
    vendor_credits_applied_formatted = models.CharField(max_length=100)
    is_line_item_invoiced = models.BooleanField(default=False)
    purchaseorders = models.JSONField(default=list)
    taxes = models.JSONField(default=list)
    tax_override = models.BooleanField(default=False)
    tds_override_preference = models.CharField(max_length=100)
    tds_summary = models.JSONField(default=list)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    balance_formatted = models.CharField(max_length=100)
    unprocessed_payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    unprocessed_payment_amount_formatted = models.CharField(max_length=100)
    billing_address = models.JSONField(default=dict)
    is_portal_enabled = models.BooleanField(default=False)
    payments = models.JSONField(default=list)
    vendor_credits = models.JSONField(default=list)
    journal_credits = models.JSONField(default=list)
    created_time = models.DateTimeField()
    created_by_id = models.CharField(max_length=100)
    last_modified_id = models.CharField(max_length=100)
    last_modified_time = models.DateTimeField()
    warn_create_vendor_credits = models.BooleanField(default=True)
    reference_id = models.CharField(max_length=100)
    notes = models.CharField(max_length=100)
    terms = models.CharField(max_length=100)
    attachment_name = models.CharField(max_length=100)
    open_purchaseorders_count = models.IntegerField()
    un_billed_items = models.JSONField(default=dict)
    template_id = models.CharField(max_length=100)
    template_name = models.CharField(max_length=100)
    page_width = models.CharField(max_length=100)
    page_height = models.CharField(max_length=100)
    orientation = models.CharField(max_length=100)
    template_type = models.CharField(max_length=100)
    template_type_formatted = models.CharField(max_length=100)
    invoices = models.JSONField(default=list)
    is_approval_required = models.BooleanField(default=False)
    can_create_bill_of_entry = models.BooleanField(default=False)
    allocated_landed_costs = models.JSONField(default=list)
    unallocated_landed_costs = models.JSONField(default=list)
    entity_type = models.CharField(max_length=100)
    credit_notes = models.JSONField(default=list)
    reference_bill_id = models.CharField(max_length=100)
    can_send_in_mail = models.BooleanField(default=False)
    approvers_list = models.JSONField(default=list)

    def __str__(self):
        return self.bill_id
