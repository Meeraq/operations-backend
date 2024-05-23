from django.db import models
from django_celery_beat.models import PeriodicTask
from api.models import (
    Organisation,
    HR,
    Coach,
    Learner,
    Pmo,
    SessionRequestCaas,
    Profile,
    Facilitator,
    Project,
    Engagement,
    Goal,
    Sales,
)
from django.utils import timezone
from django.contrib.auth.models import User


# Create your models here.
class SchedularProject(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
    ]

    name = models.CharField(max_length=100, unique=True, default=None)
    project_structure = models.JSONField(default=list, blank=True)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    hr = models.ManyToManyField(HR, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    is_project_structure_finalized = models.BooleanField(default=False)
    nudges = models.BooleanField(blank=True, default=True)
    pre_post_assessment = models.BooleanField(blank=True, default=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="draft")
    email_reminder = models.BooleanField(blank=True, default=True)
    whatsapp_reminder = models.BooleanField(blank=True, default=True)
    calendar_invites = models.BooleanField(blank=True, default=True)
    is_finance_enabled = models.BooleanField(blank=True, default=False)
    junior_pmo = models.ForeignKey(
        Pmo,
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
    )
    is_archive = models.BooleanField(default=False)
    teams_enabled = models.BooleanField(blank=True, default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SchedularBatch(models.Model):
    name = models.CharField(max_length=100, blank=True)
    project = models.ForeignKey(SchedularProject, on_delete=models.CASCADE)
    coaches = models.ManyToManyField(Coach, blank=True)
    learners = models.ManyToManyField(Learner, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    nudge_start_date = models.DateField(default=None, blank=True, null=True)
    nudge_frequency = models.CharField(max_length=50, default="", blank=True, null=True)
    nudge_periodic_task = models.ForeignKey(
        PeriodicTask, blank=True, null=True, on_delete=models.SET_NULL
    )
    email_reminder = models.BooleanField(blank=True, default=True)
    whatsapp_reminder = models.BooleanField(blank=True, default=True)
    calendar_invites = models.BooleanField(blank=True, default=True)


class RequestAvailibilty(models.Model):
    request_name = models.CharField(max_length=100, blank=True)
    coach = models.ManyToManyField(Coach, blank=True)
    provided_by = models.JSONField(
        default=list
    )  # used to store coach ids who already provided the slots
    expiry_date = models.DateField(blank=True, null=True)
    slot_duration = models.PositiveIntegerField(null=True, blank=True)
    availability = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)


class CoachSchedularAvailibilty(models.Model):
    request = models.ForeignKey(
        RequestAvailibilty,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None,
    )
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    start_time = models.CharField(max_length=30)
    end_time = models.CharField(max_length=30)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, auto_now=True)

    def __str__(self):
        return self.coach.first_name


class CoachingSession(models.Model):
    SESSION_CHOICES = [
        ("laser_coaching_session", "Laser Coaching Session"),
        ("mentoring_session", "Mentoring Session"),
    ]
    booking_link = models.CharField(max_length=500, blank=True, default="")
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    batch = models.ForeignKey(SchedularBatch, on_delete=models.CASCADE)
    coaching_session_number = models.IntegerField(blank=True, default=None, null=True)
    order = models.IntegerField(blank=True, default=None, null=True)
    duration = models.CharField(max_length=50, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    session_type = models.CharField(
        max_length=50, choices=SESSION_CHOICES, default="laser_coaching_session"
    )


class SchedularSessions(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, null=True)
    availibility = models.ForeignKey(
        CoachSchedularAvailibilty, on_delete=models.CASCADE
    )
    coaching_session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="pending", blank=True)
    auto_generated_status = models.CharField(
        max_length=50, default="pending", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)


class LiveSession(models.Model):
    SESSION_CHOICES = [
        ("live_session", "Live Session"),
        ("check_in_session", "Check In Session"),
        ("in_person_session", "In Person Session"),
        ("kickoff_session", "Kickoff Session"),
        ("virtual_session", "Virtual Session"),
    ]

    batch = models.ForeignKey(SchedularBatch, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(
        Facilitator, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    live_session_number = models.IntegerField(blank=True, default=None, null=True)
    order = models.IntegerField(blank=True, default=None, null=True)
    date_time = models.DateTimeField(blank=True, null=True)
    attendees = models.JSONField(blank=True, default=list)
    description = models.TextField(default="", blank=True)
    status = models.CharField(blank=True, default="pending", max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration = models.CharField(max_length=50, default=None)
    pt_30_min_before = models.ForeignKey(
        PeriodicTask, blank=True, null=True, on_delete=models.SET_NULL
    )
    session_type = models.CharField(
        max_length=50, choices=SESSION_CHOICES, default="virtual_session"
    )
    meeting_link = models.TextField(default="", blank=True)
    teams_meeting_id = models.TextField(default="", blank=True)


class EmailTemplate(models.Model):
    title = models.CharField(max_length=100, default="", blank=True)  # Add title field
    template_data = models.TextField(max_length=200, default="")


class SentEmail(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    recipients = models.JSONField()  # Use a JSONField to store JSON data.
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    template = models.ForeignKey(EmailTemplate, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    periodic_task = models.ForeignKey(
        PeriodicTask, null=True, on_delete=models.SET_NULL
    )
    subject = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.id} Subject: {self.subject}"


class CalendarInvites(models.Model):
    event_id = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    start_datetime = models.CharField(max_length=255, blank=True, null=True)
    end_datetime = models.CharField(max_length=255, blank=True, null=True)
    attendees = models.JSONField(blank=True, null=True)
    creator = models.CharField(max_length=255, blank=True, null=True)
    caas_session = models.ForeignKey(
        SessionRequestCaas, on_delete=models.CASCADE, blank=True, null=True
    )
    schedular_session = models.ForeignKey(
        SchedularSessions, on_delete=models.CASCADE, blank=True, null=True
    )
    live_session = models.ForeignKey(
        LiveSession, on_delete=models.CASCADE, blank=True, null=True
    )


class SchedularUpdate(models.Model):
    pmo = models.ForeignKey(Pmo, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(SchedularProject, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} update by {self.pmo.name}"


class CoachPricing(models.Model):
    SESSION_CHOICES = [
        ("laser_coaching_session", "Laser Coaching Session"),
        ("mentoring_session", "Mentoring Session"),
    ]

    project = models.ForeignKey(SchedularProject, on_delete=models.CASCADE)
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    session_type = models.CharField(
        max_length=50, choices=SESSION_CHOICES, default="laser_coaching_session"
    )
    coaching_session_number = models.IntegerField(blank=True, default=None, null=True)
    order = models.IntegerField(blank=True, default=None, null=True)
    purchase_order_id = models.CharField(max_length=200, default="", blank=True)
    purchase_order_no = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_type} {self.coaching_session_number}  in {self.project.name} for {self.coach.first_name} {self.coach.last_name}"


class FacilitatorPricing(models.Model):
    project = models.ForeignKey(SchedularProject, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(Facilitator, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    purchase_order_id = models.CharField(max_length=200, default="", blank=True)
    purchase_order_no = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.facilitator.first_name} {self.facilitator.last_name} pricing for {self.project.name} "


class Expense(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("created", "Created"),
        ("invoiced", "Invoiced"),
    ]

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    facilitator = models.ForeignKey(
        Facilitator, on_delete=models.SET_NULL, null=True, blank=True
    )
    coach = models.ForeignKey(Coach, on_delete=models.SET_NULL, null=True)
    session = models.ForeignKey(
        SessionRequestCaas, on_delete=models.SET_NULL, null=True
    )
    date_of_expense = models.DateField(blank=True, null=True)
    batch = models.ForeignKey(
        SchedularBatch, on_delete=models.SET_NULL, null=True, blank=True
    )
    live_session = models.ForeignKey(
        LiveSession, on_delete=models.SET_NULL, blank=True, null=True
    )
    file = models.FileField(upload_to="expenses/", blank=True, null=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="pending")

    amount = models.DecimalField(max_digits=65, decimal_places=2, blank=True, null=True)
    purchase_order_id = models.CharField(max_length=200, default="", blank=True)
    purchase_order_no = models.CharField(max_length=200, default="", blank=True)
    update_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

class Assets(models.Model):
    STATUS_CHOICES = [
        ("idle", "Idle"),
        ("assigned", "Assigned"),
        ("lost", "Lost"),
        ("damaged", "Damaged"),
    ]
    name = models.CharField(max_length=255, default="",blank=True)
    category = models.CharField(max_length=255, default="",blank=True)
    assigned_to = models.CharField(max_length=255, default="",blank=True)
    update_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="idle")
    updates = models.JSONField(default=list, blank=True)


class Benchmark(models.Model):
    year = models.CharField(max_length=9, blank=True, null=True)
    caas_benchmark = models.CharField(max_length=3, blank=True, null=True)
    seeq_benchmark = models.CharField(max_length=3, blank=True, null=True)
    both_benchmark = models.CharField(max_length=3, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class GmSheet(models.Model):
    PROJECT_TYPE_CHOICES = [
        ("CAAS", "CAAS"),
        ("SEEQ", "Skill Training"),
        ("Coaching + Traning", "Coaching+Training"),
    ]
    DEAL_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("won", "Won"),
        ("lost", "Lost"),
        ("deferred", "Deferred"),
    ]
    client_name = models.TextField(blank=True, null=True)
    project_type = models.CharField(
        max_length=255,  blank=True, null=True
    )
    product_type= models.CharField(
        max_length=255, blank=True, null=True
    )
    currency = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    gmsheet_number = models.CharField(max_length=6, blank=True, null=True)
    other_details = models.TextField(blank=True, null=True)
    sales = models.ForeignKey(Sales, null=True, on_delete=models.SET_NULL)
    is_accepted = models.BooleanField(default=False)
    deal_status = models.CharField(
        max_length=255, choices=DEAL_STATUS_CHOICES, default="pending"
    )
    benchmark = models.ForeignKey(Benchmark, null=True, on_delete=models.SET_NULL)
    participant_level = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(null=True, blank=True) 

    def _str_(self):
        return f"{self.client_name} for {self.product_type}"

class StandardizedFieldGmSheet(models.Model):
    FIELD_CHOICES = (
        ("project_type", "Project Type"),
    )
    field = models.CharField(max_length=50, choices=FIELD_CHOICES, blank=True)
    values = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"{self.field}"
    
class Offering(models.Model):
    MODE_CHOICES = [
        ("in_person", "In Person"),
        ("virtual", "Virtual"),
        ("hybrid", "Hybrid"),
    ]
    gm_sheet = models.ForeignKey(GmSheet, on_delete=models.CASCADE)
    mode = models.CharField(max_length=100, choices=MODE_CHOICES,blank=True,null=True,default="")
    revenue_structure = models.JSONField(default=list, blank=True, null=True)
    cost_structure = models.JSONField(default=list, blank=True, null=True)
    gross_margin = models.CharField(max_length=100,blank=True,null=True)

class StandardizedFieldGmSheet(models.Model):
    FIELD_CHOICES = (
        ("project_type", "Project Type"),
    )
    field = models.CharField(max_length=50, choices=FIELD_CHOICES, blank=True)
    values = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"{self.field}"
    
class HandoverDetails(models.Model):
    PROJECT_TYPE_CHOICES = [
        ("caas", "CAAS"),
        ("skill_training", "Skill Training"),
        ("COD", "COD"),
    ]
    DELIVERY_MODE_CHOICES = [
        ("online", "Online"),
        ("hybrid", "Hybrid"),
        ("offline", "Offline"),
    ]
    PROGRAM_TYPE_CHOICES = [
        ("soft_skill_training", "Soft skill training"),
        ("coaching", "Coaching"),
        ("coach_training", "Coach Training"),
        ("coaching_and_coach_training", "Coaching + Coach Training"),
    ]

    LOGISTICE_MANAGER_CHOICES = [
        ("client", "Client"),
        ("meeraq", "Meeraq"),
        ("faculty", "Faculty"),
    ]

    schedular_project = models.OneToOneField(
        SchedularProject,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="handover_details",
    )
    caas_project = models.OneToOneField(
        Project, on_delete=models.SET_NULL, blank=True, null=True
    )
    sales = models.ForeignKey(Sales, on_delete=models.SET_NULL, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    hr = models.ManyToManyField(HR, blank=True)
    project_type = models.CharField(
        max_length=255, choices=PROJECT_TYPE_CHOICES, blank=True, null=True
    )  # caas or skill_training
    delivery_mode = models.CharField(
        max_length=255, choices=DELIVERY_MODE_CHOICES, blank=True, null=True
    )
    # program_type = models.CharField(max_length=255, blank=True, null=True)
    program_type = models.CharField(
        max_length=255, choices=PROGRAM_TYPE_CHOICES, blank=True, null=True
    )
    logistics_manager = models.CharField(
        max_length=255, choices=LOGISTICE_MANAGER_CHOICES, blank=True, null=True
    )
    project_duration = models.CharField(max_length=255, blank=True, null=True)
    po_number = models.CharField(max_length=255, blank=True, null=True)
    participant_count = models.IntegerField(default=0, blank=True, null=True)
    coach_fee = models.CharField(max_length=255, blank=True, null=True)
    invoice_status = models.BooleanField(default=False, blank=True)
    reporting_requirements = models.TextField(blank=True, null=True)
    coach_names = models.TextField(blank=True, null=True)
    poc_contact_details = models.TextField(blank=True, null=True)
    audience_level = models.JSONField(max_length=255, blank=True, null=True)
    project_structure = models.JSONField(default=list, blank=True, null=True)
    sales_order_ids = models.JSONField(default=list, blank=True, null=True)
    # sales_order_nos = models.JSONField(default=list, blank=True, null=True)
    total_coaching_hours = models.IntegerField(default=0, blank=True, null=True)
    tentative_start_date = models.DateField(blank=True, null=True)
    pre_post_assessment = models.BooleanField(blank=True, default=True)
    nudges = models.BooleanField(blank=True, default=True)
    end_of_program_certification = models.BooleanField(default=False, blank=True)
    out_of_pocket_expenses = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    is_accepted = models.BooleanField(default=False, blank=True)
    gm_sheet = models.FileField(upload_to="gm_sheets/", blank=True, null=True)
    proposals = models.FileField(upload_to="proposals/", blank=True, null=True)

    class Meta:
        verbose_name = "Handover Detail"
        verbose_name_plural = "Handover Details"

    # def __str__(self):
    #     return f"Handover Details for"


class Task(models.Model):
    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )
    TASK_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    )
    PROJECT_TYPE_CHOICES = [("caas", "CAAS"), ("skill_training", "Skill Training")]
    task = models.CharField(max_length=100)
    project_type = models.CharField(
        max_length=255, choices=PROJECT_TYPE_CHOICES, blank=True, null=True
    )  # caas or skill_training
    caas_project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
    )
    schedular_project = models.ForeignKey(
        SchedularProject,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
    )
    schedular_batch = models.ForeignKey(
        SchedularBatch,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
    )
    session_caas = models.ForeignKey(
        SessionRequestCaas,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
    )
    coach = models.ForeignKey(
        Coach, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, blank=True, null=True, default=None
    )

    goal = models.ForeignKey(
        Goal, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    facilitator = models.ForeignKey(
        Facilitator, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    live_session = models.ForeignKey(
        LiveSession, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    coaching_session = models.ForeignKey(
        CoachingSession, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    schedular_session = models.ForeignKey(
        SchedularSessions, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    vendor_user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(
        max_length=20, choices=TASK_STATUS_CHOICES, default="pending"
    )

    remarks = models.JSONField(default=list, blank=True)
    trigger_date = models.DateTimeField(default=timezone.now, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_remark(self, remark_message):
        current_datetime = timezone.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        new_remark = {
            "message": remark_message,
            "datetime": formatted_datetime,
        }
        self.remarks.append(new_remark)
        self.save()

    def is_visible(self):
        return timezone.now() >= self.trigger_date

    def __str__(self):
        return self.task


#  }


# initialValues
#  form.setFieldsValue({ "name" : "", })

# useState
# setLineITems([])
# set costLineItems()
