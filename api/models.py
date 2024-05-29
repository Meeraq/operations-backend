from django.db import models
import os
from django.core.exceptions import ValidationError

# Create your models here.
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from django.db import models
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django_rest_passwordreset.signals import reset_password_token_created
from django.urls import reverse
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.core.mail import EmailMessage, BadHeaderError
from django_celery_beat.models import PeriodicTask

import environ

env = environ.Env()


def send_mail_templates(file_name, user_email, email_subject, content, bcc_emails):
    try:
        email_message = render_to_string(file_name, content)
        email = EmailMessage(
            f"{env('EMAIL_SUBJECT_INITIAL',default='')} {email_subject}",
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            user_email,
            bcc_emails,
        )
        email.content_subtype = "html"

        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")


def get_user_name(user):
    try:
        roles = user.profile.roles.all()
        if not roles.exists():
            return "User"
        role = roles.first().name
        if role == "pmo":
            return user.profile.pmo.name
        elif role == "coach":
            return user.profile.coach.first_name + " " + user.profile.coach.last_name
        elif role == "vendor":
            return user.profile.vendor.name
        elif role == "hr":
            return user.profile.hr.first_name + " " + user.profile.hr.last_name
        elif role == "learner":
            return user.profile.learner.name
        elif role == "superadmin":
            return user.profile.superadmin.name
        elif role == "facilitator":
            return (
                user.profile.facilitator.first_name
                + " "
                + user.profile.facilitator.last_name
            )
        elif role == "finance":
            return user.profile.finance.name
        elif role == "sales":
            return user.profile.sales.name
        elif role == "ctt_pmo":
            return user.profile.cttpmo.name
        else:
            return "User"
    except Exception as e:
        print(str(e))
        return "User"


@receiver(reset_password_token_created)
def password_reset_token_created(
    sender, instance, reset_password_token, *args, **kwargs
):
    app_name = instance.request.data.get("app_name", "")
    user = reset_password_token.user
    email_plaintext_message = "{}?token={}".format(
        reverse("password_reset:reset-password-request"), reset_password_token.key
    )
    subject = "Meeraq - Forgot Password"
    if (
        user.profile.roles.all().count() == 1
        and user.profile.roles.all().first().name == "coach"
        and user.profile.coach.is_approved == False
    ):
        # link = f'{env("APP_URL")}/create-password/{reset_password_token.key}'
        if app_name == "assessment":
            link = f"{env('ASSESSMENT_APP_URL')}/create-password/{reset_password_token.key}"
        else:
            link = f"{env('APP_URL')}/create-password/{reset_password_token.key}"
        name = user.profile.coach.first_name
        send_mail_templates(
            "coach_templates/create_new_password.html",
            [reset_password_token.user.email],
            "Meeraq Platform | Create New Password",
            {"name": name, "createPassword": link},
            [],  # no bcc
        )
        return None
    else:
        learner_roles = user.profile.roles.all().filter(name="learner")
        hr_roles = user.profile.roles.all().filter(name="hr")
        if learner_roles.exists():
            engagements = Engagement.objects.filter(
                learner=user.profile.learner,
                project__enable_emails_to_hr_and_coachee=False,
            )
            if engagements.exists():
                return None
        if hr_roles.exists():
            projects = Project.objects.filter(
                hr=user.profile.hr, enable_emails_to_hr_and_coachee=False
            )
            if projects.exists():
                return None
        name = get_user_name(user)
        if app_name == "assessment":
            link = f"{env('ASSESSMENT_APP_URL')}/create-password/{reset_password_token.key}"
        elif app_name == "zoho":
            link = f"{env('ZOHO_APP_URL')}/reset-password/{reset_password_token.key}"
            # not sending when requested from vendor portal but user is not vendor in our system
            if not user.profile.roles.all().filter(name="vendor").exists():
                return None
        else:
            link = f"{env('APP_URL')}/create-password/{reset_password_token.key}"
        send_mail_templates(
            "hr_emails/forgot_password.html",
            [reset_password_token.user.email],
            "Meeraq Platform | Password Reset",
            {"name": name, "resetPassword": link},
            [],  # no bcc
        )


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user_types = [
        ("pmo", "pmo"),
        ("coach", "coach"),
        ("learner", "learner"),
        ("hr", "hr"),
        ("superadmin", "superadmin"),
        ("facilitator", "facilitator"),
        ("finance", "finance"),
        ("sales", "sales"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roles = models.ManyToManyField(Role)

    def __str__(self):
        return self.user.username


class SuperAdmin(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Finance(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    active_inactive = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Sales(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    active_inactive = models.BooleanField(default=True)
    sales_person_id = models.CharField(max_length=255, blank=True, default="")
    business = models.CharField(max_length=255, blank=True, default="meeraq")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Leader(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    active_inactive = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Pmo(models.Model):
    SUB_ROLE_CHOICES = [
        ("manager", "Manager"),
        ("junior_pmo", "Junior PMO"),
    ]

    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    sub_role = models.CharField(
        max_length=50, choices=SUB_ROLE_CHOICES, blank=True, default="manager"
    )
    room_id = models.CharField(max_length=50, blank=True)
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CTTPmo(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.name


def validate_pdf_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if not ext == ".pdf":
        raise ValidationError("Only PDF files are allowed.")


class Coach(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    vendor_id = models.CharField(max_length=255, blank=True, default="")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    age = models.CharField(max_length=10, default="", blank=True)
    gender = models.CharField(max_length=50, blank=True)
    domain = models.JSONField(default=list, blank=True)
    room_id = models.CharField(max_length=50, blank=True)
    phone_country_code = models.CharField(max_length=20, default="", blank=True)
    phone = models.CharField(max_length=25)
    level = models.CharField(max_length=50, blank=True)
    rating = models.CharField(max_length=20, blank=True)
    area_of_expertise = models.JSONField(default=list, blank=True)
    completed_sessions = models.IntegerField(blank=True, default=0)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    education = models.JSONField(default=list, blank=True)
    corporate_experience = models.TextField(blank=True)
    coaching_experience = models.TextField(blank=True)
    years_of_corporate_experience = models.CharField(max_length=20, blank=True)
    years_of_coaching_experience = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(blank=True, default=False)
    is_rejected = models.BooleanField(blank=True, default=False)
    location = models.JSONField(default=list, blank=True)
    ctt_nctt = models.BooleanField(blank=True, default=False)
    language = models.JSONField(default=list, blank=True)
    min_fees = models.CharField(max_length=120, blank=True)
    fee_remark = models.TextField(blank=True)
    job_roles = models.JSONField(default=list, blank=True)
    coaching_hours = models.CharField(max_length=50, blank=True)
    created_at = models.DateField(auto_now_add=True)
    edited_at = models.DateField(auto_now=True)
    linkedin_profile_link = models.CharField(max_length=500, blank=True)
    companies_worked_in = models.JSONField(default=list, blank=True)
    other_certification = models.JSONField(default=list, blank=True)
    active_inactive = models.BooleanField(default=True)
    currency = models.CharField(max_length=100, blank=True, default="")
    internal_coach = models.BooleanField(blank=True, default=False)
    organization_of_coach = models.CharField(max_length=100, blank=True)
    reason_for_inactive = models.JSONField(default=list, blank=True)
    client_companies = models.JSONField(default=list, blank=True)
    education_pic = models.ImageField(upload_to="post_images", blank=True)
    educational_qualification = models.JSONField(default=list, blank=True)
    education_upload_file = models.FileField(
        upload_to="pdf_files",
        blank=True,
        null=True,
        validators=[validate_pdf_extension],
    )
    remark = models.TextField(blank=True)
    is_coach = models.BooleanField(blank=True, default=False)
    is_mentor = models.BooleanField(blank=True, default=False)
    is_consultant = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return self.first_name + " " + self.last_name


class Facilitator(models.Model):
    user = models.OneToOneField(
        Profile, on_delete=models.CASCADE, blank=True, default=""
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    age = models.CharField(max_length=10, default="", blank=True)
    gender = models.CharField(max_length=50, blank=True)
    domain = models.JSONField(default=list, blank=True)
    phone_country_code = models.CharField(max_length=20, default="", blank=True)
    phone = models.CharField(max_length=25)
    level = models.JSONField(default=list, blank=True)
    rating = models.CharField(max_length=20, blank=True)
    area_of_expertise = models.JSONField(default=list, blank=True)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    education = models.JSONField(default=list, blank=True)
    corporate_experience = models.TextField(blank=True)
    coaching_experience = models.TextField(blank=True)
    years_of_corporate_experience = models.CharField(max_length=20, blank=True)
    city = models.JSONField(default=list, blank=True)
    language = models.JSONField(default=list, blank=True)
    job_roles = models.JSONField(default=list, blank=True)
    country = models.JSONField(default=list, blank=True)
    created_at = models.DateField(auto_now_add=True)
    edited_at = models.DateField(auto_now=True)
    linkedin_profile_link = models.CharField(max_length=500, blank=True)
    companies_worked_in = models.JSONField(default=list, blank=True)
    other_certification = models.JSONField(default=list, blank=True)
    currency = models.CharField(max_length=100, blank=True, default="")
    client_companies = models.JSONField(default=list, blank=True)
    education_pic = models.ImageField(upload_to="post_images", blank=True)
    # education_upload_file = models.ImageField(upload_to="post_images", blank=True)
    education_upload_file = models.FileField(
        upload_to="pdf_files", blank=True, validators=[validate_pdf_extension]
    )
    educational_qualification = models.JSONField(default=list, blank=True)
    fees_per_hour = models.CharField(max_length=20, blank=True)
    fees_per_day = models.CharField(max_length=20, blank=True)
    topic = models.JSONField(default=list, blank=True)
    is_approved = models.BooleanField(blank=True, default=False)
    is_rejected = models.BooleanField(blank=True, default=False)
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.first_name + " " + self.last_name


class Learner(models.Model):
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=25, blank=True)
    area_of_expertise = models.JSONField(default=list, blank=True)
    years_of_experience = models.IntegerField(default=0, blank=True)
    job_roles = models.JSONField(default=list, blank=True)
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Organisation(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.ImageField(upload_to="post_images", blank=True)

    def __str__(self):
        return self.name


class HR(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    active_inactive = models.BooleanField(default=True)

    def __str__(self):
        return self.first_name + " " + self.last_name


# class CoachInvites(models.Model):
#     name= models.CharField(max_length=100)
#     email = models.EmailField()
#     created_at = models.DateTimeField(auto_now_add=True)


class CoachStatus(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    status = models.JSONField(default=dict, blank=True)
    project_structure = models.JSONField(default=list, blank=True)
    learner_id = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    consent_expiry_date = models.DateField(blank=True, null=True)
    is_consent_asked = models.BooleanField(default=True)
    purchase_order_id = models.CharField(max_length=200, default="", blank=True)
    purchase_order_no = models.CharField(max_length=200, default="", blank=True)

    def __str__(self):
        return f"{self.id} {self.coach.first_name} {self.coach.last_name}"


class Project(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("completed", "Completed"),
        ("presales", "Presales"),
    )
    project_type_choice = [("COD", "COD"), ("4+2", "4+2"), ("CAAS", "CAAS")]
    name = models.CharField(max_length=100, unique=True)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    project_type = models.CharField(
        max_length=50, choices=project_type_choice, default="CAAS"
    )
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    session_duration = models.CharField(max_length=20)
    hr = models.ManyToManyField(HR, blank=True)
    coaches = models.ManyToManyField(Coach, blank=True)
    coaches_status = models.ManyToManyField(CoachStatus, blank=True)
    learner = models.ManyToManyField(Learner, blank=True)
    total_sessions = models.IntegerField(default=0, blank=True)
    cost_per_session = models.IntegerField(default=0, blank=True)
    sessions_per_employee = models.IntegerField(default=0, blank=True)
    steps = models.JSONField(default=dict)
    project_structure = models.JSONField(default=list, blank=True)
    specific_coach = models.BooleanField(blank=True, default=False)
    empanelment = models.BooleanField(blank=True, default=False)
    interview_allowed = models.BooleanField(blank=True, default=False)
    chemistry_allowed = models.BooleanField(blank=True, default=False)
    tentative_start_date = models.DateField(blank=True, default=None)
    sold = models.BooleanField(default=False)
    updated_to_sold = models.BooleanField(default=False)
    mode = models.CharField(max_length=100)
    location = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=30, default="Rupees")
    price_per_hour = models.IntegerField(default=0, blank=True)
    coach_fees_per_hour = models.IntegerField(default=0, blank=True)
    approx_coachee = models.TextField(blank=True)
    frequency_of_session = models.TextField(blank=True)
    project_description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, blank=True, null=True
    )
    coach_consent_mandatory = models.BooleanField(default=True)
    enable_emails_to_hr_and_coachee = models.BooleanField(default=True)
    masked_coach_profile = models.BooleanField(default=False)
    email_reminder = models.BooleanField(blank=True, default=False)
    whatsapp_reminder = models.BooleanField(blank=True, default=False)
    calendar_invites = models.BooleanField(blank=True, default=False)
    junior_pmo = models.ForeignKey(
        Pmo,
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
    )
    is_archive = models.BooleanField(default=False)
    finance = models.BooleanField(blank=True, default=False)
    is_project_structure = models.BooleanField(blank=True, default=True)
    total_credits = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    duration_of_each_session = models.IntegerField(blank=True, default=None, null=True)
    request_expiry_time = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    credit_history = models.JSONField(default=list, blank=True)
    is_session_expiry = models.BooleanField(blank=True, default=False)
    nudges = models.BooleanField(blank=True, default=True)
    pre_assessment = models.BooleanField(blank=True, default=True)
    post_assessment = models.BooleanField(blank=True, default=True)
    nudge_start_date = models.DateField(default=None, blank=True, null=True)
    nudge_frequency = models.CharField(max_length=50, default="", blank=True, null=True)
    nudge_periodic_task = models.ForeignKey(
        PeriodicTask, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Update(models.Model):
    pmo = models.ForeignKey(Pmo, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True
    )
    coach = models.ForeignKey(Coach, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} update by {self.pmo.name}"


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# class OTP_HR(models.Model):
#     hr = models.ForeignKey(HR, on_delete=models.CASCADE)
#     otp = models.CharField(max_length=6)
#     created_at = models.DateTimeField(auto_now_add=True)


class Availibility(models.Model):
    start_time = models.CharField(max_length=30)
    end_time = models.CharField(max_length=30)


# class SessionRequest(models.Model):
#     learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
#     project = models.ForeignKey(Project, on_delete=models.CASCADE)
#     availibility=models.ManyToManyField(Availibility)
#     is_booked = models.BooleanField(blank=True,default=False)
#     created_at = models.DateTimeField(auto_now_add=True)


# class Session(models.Model):
#     coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
#     confirmed_availability = models.ForeignKey(Availibility, on_delete=models.CASCADE)
#     session_request = models.ForeignKey(SessionRequest, on_delete=models.CASCADE)
#     status = models.CharField(max_length=20,default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)
#     coach_joined = models.BooleanField(blank=True,default=False)
#     learner_joined = models.BooleanField(blank=True,default=False)


class Engagement(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    )
    TYPE_CHOICES = (
        ("cod", "COD"),
        ("caas", "CAAS"),
    )
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, null=True, blank=True)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    project_structure = models.JSONField(default=list, blank=True)
    type = models.CharField(max_length=225, null=True, blank=True, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Project: {self.project.name} - Learner: {self.learner.name}"


class SessionRequestCaas(models.Model):
    hr = models.ForeignKey(
        HR, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    pmo = models.ForeignKey(
        Pmo, on_delete=models.CASCADE, blank=True, null=True, default=None
    )

    learner = models.ForeignKey(
        Learner, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    coach = models.ForeignKey(
        Coach, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    invitees = models.JSONField(default=list, blank=True)
    availibility = models.ManyToManyField(
        Availibility, related_name="requested_availability"
    )
    confirmed_availability = models.ForeignKey(
        Availibility,
        related_name="confirmed_availability",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
    )
    is_booked = models.BooleanField(blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    session_type = models.CharField(max_length=50, default="")
    is_archive = models.BooleanField(default=False)
    reschedule_request = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=30, default="", blank=True)
    session_number = models.IntegerField(blank=True, default=None, null=True)
    session_duration = models.IntegerField(blank=True, default=None, null=True)
    status_updated_at = models.DateTimeField(blank=True, null=True, default=None)
    billable_session_number = models.IntegerField(blank=True, default=None, null=True)
    is_extra = models.BooleanField(blank=True, default=False)
    auto_generated_status = models.CharField(
        max_length=50, default="pending", blank=True
    )
    order = models.IntegerField(
        blank=True, default=None, null=True
    )  # used for engagement structure
    requested_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        if self.session_type == "interview":
            return (
                f"interview = HR:{self.hr.first_name} - Coach:{self.coach.first_name}"
            )
        else:
            return f"{self.session_type} = Learner: {self.learner.name}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    path = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True)
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Goal(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("archive", "Archive"),
        ("complete", "Complete"),
    )
    name = models.TextField()
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, blank=True, null=True
    )
    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)


class Competency(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    name = models.TextField()
    scoring = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ActionItem(models.Model):
    STATUS_CHOICES = (
        ("done", "Done"),
        ("partially_done", "Partially done"),
        ("not_done", "Not done"),
    )
    name = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_done")
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProfileEditActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"Profile Edit for {self.user.username}"


class UserLoginActivity(models.Model):
    PLATFORM_CHOICES = (
        ("caas", "CAAS"),
        ("seeq", "SEEQ"),
        ("vendor", "VENDOR"),
        ("assessment", "ASSESSMENT"),
        ("unknown", "UNKNOWN"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    platform = models.CharField(blank=True, choices=PLATFORM_CHOICES, max_length=225)

    def __str__(self):
        return f"User Login Activity for {self.user.username}"


class SentEmailActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_subject = models.CharField(max_length=500)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"Sent Email - {self.user.username}"


class AddCoachActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"Coach Added - {self.user.username}"


class AddGoalActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user} added a goal."


class CoachProfileShare(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    emails = models.JSONField(default=list, blank=True)
    masked_coach_profile = models.BooleanField(default=False)
    unique_id = models.CharField(max_length=225, unique=True, blank=True)
    coaches = models.ManyToManyField(Coach, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CoachProfileTemplate(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    templates = models.JSONField(default=dict, blank=True)
    coach_profile_share = models.ForeignKey(
        CoachProfileShare, on_delete=models.CASCADE, blank=True, null=True, default=None
    )

    def __str__(self):
        return f"{self.coach} template."


class StandardizedField(models.Model):
    FIELD_CHOICES = (
        ("location", "Work Location"),
        ("other_certification", "Assessment Certification"),
        ("area_of_expertise", "Industry"),
        ("job_roles", "Job roles"),
        ("companies_worked_in", "Companies worked in"),
        ("language", "Language Proficiency"),
        ("education", "Education Institutions"),
        ("domain", "Functional Domain"),
        ("client_companies", "Client companies"),
        ("educational_qualification", "Educational Qualification"),
        ("city", "City"),
        ("country", "Country"),
        ("topic", "Topic"),
        ("product_type","Product Type"),
        ("category","Category"),
        ("asset_location","Location"),
        ("project_type","Project Type"),
    )

    field = models.CharField(max_length=50, choices=FIELD_CHOICES, blank=True)
    values = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.field}"


class StandardizedFieldRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, blank=True, null=True)
    facilitator = models.ForeignKey(
        Facilitator, on_delete=models.CASCADE, blank=True, null=True
    )
    learner = models.ForeignKey(
        Learner, on_delete=models.CASCADE, blank=True, null=True
    )
    standardized_field_name = models.ForeignKey(
        StandardizedField, on_delete=models.CASCADE, blank=True
    )
    value = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" {self.standardized_field_name} - {self.status}"


class SessionRequestedActivity(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    time_of_request = models.DateTimeField()
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    coachee = models.ForeignKey(Learner, on_delete=models.CASCADE)
    session_name = models.CharField(max_length=225, blank=True, null=True)


class DeleteCoachProfileActivity(models.Model):
    user_who_got_deleted = models.CharField(max_length=225, blank=True, null=True)
    user_who_deleted = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user_who_deleted} deleted coach profile."


class RemoveCoachActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    time_of_removal = models.DateTimeField()
    removed_coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    removed_from_project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} removed coach profile."


class PastSessionActivity(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user_who_added = models.ForeignKey(User, on_delete=models.CASCADE)
    coach = models.ForeignKey(Coach, on_delete=models.SET_NULL, null=True)
    coachee = models.ForeignKey(Learner, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    session_name = models.CharField(max_length=225, blank=True, null=True)

    def __str__(self):
        return f"{self.user_who_added} added past session."


class Template(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class UserToken(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ("google", "Google"),
        ("microsoft", "Microsoft"),
    ]

    user_profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    access_token_expiry = models.TextField(blank=True)
    authorization_code = models.TextField(blank=True)
    account_type = models.CharField(
        max_length=50, choices=ACCOUNT_TYPE_CHOICES, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_profile.user.username


class CalendarEvent(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ("google", "Google"),
        ("microsoft", "Microsoft"),
    ]

    event_id = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    start_datetime = models.CharField(max_length=255, blank=True, null=True)
    end_datetime = models.CharField(max_length=255, blank=True, null=True)
    attendee = models.CharField(max_length=255, blank=True, null=True)
    creator = models.CharField(max_length=255, blank=True, null=True)
    session = models.ForeignKey(
        SessionRequestCaas, on_delete=models.CASCADE, blank=True, null=True
    )
    account_type = models.CharField(
        max_length=50, choices=ACCOUNT_TYPE_CHOICES, blank=True
    )


class ShareCoachProfileActivity(models.Model):
    user_who_shared = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    coaches = models.ManyToManyField(Coach, blank=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user_who_shared.username} shared coach profiles."


class CreateProjectActivity(models.Model):
    user_who_created = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user_who_created.username} created project."


class FinalizeCoachActivity(models.Model):
    user_who_finalized = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    coach_who_got_finalized = models.ForeignKey(
        Coach, on_delete=models.CASCADE, blank=True
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user_who_finalized.username} finalized the coach."


class APILog(models.Model):
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.path}"


class TableHiddenColumn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    table_name = models.CharField(max_length=225, blank=True)
    hidden_columns = models.JSONField(default=list, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserFeedback(models.Model):
    user_types = [
        ("pmo", "pmo"),
        ("coach", "coach"),
        ("learner", "learner"),
        ("hr", "hr"),
        ("facilitator", "facilitator"),
    ]
    feedback_type_choices = [
        ("bulk_upload_of_coach", "Bulk Upload of Coach"),
        ("bulk_upload_of_facilitator", "Bulk Upload of Facilitator"),
        ("bulk_upload_of_batch", "Bulk Upload of Batch"),
        ("bulk_upload_of_questions", "Bulk Upload of Questions"),
        ("bulk_upload_of_participant", "Bulk Upload of Participant"),
        ("assigning_certificate", "Assigning Certificate"),
        ("assign_the_course", "Assign the Course"),
        ("requesting_availability_of_coach", "Requesting Availability of Coach"),
        ("adding_facilitator", "Adding Facilitator"),
        ("adding_coach", "Adding Coach"),
        ("editing_coach", "Editing Coach"),
        ("editing_facilitator", "Editing Facilitator"),
        ("editing_coachee", "Editing Coachee"),
        ("video_upload_inside_lesson", "Video Upload inside Lesson"),
        ("video_upload_inside_video_library", "Video Upload Inside Video Library"),
        ("pdf_upload_inside_lesson", "PDF Upload inside Lesson"),
        ("pdf_upload_inside_pdf_library", "PDF Upload Inside PDF Library"),
        ("coach_editing_the_profile", "Coach Editing the Profile"),
        ("coach_giving_his_availability", "Coach Giving his Availability"),
        ("learner_requesting_a_session", "Learner Requesting a Session"),
        ("learner_editing_the_profile", "Learner Editing the Profile"),
        ("learner_course_engagement", "Learner Course Engagement"),
        ("facilitator_editing_profile", "Facilitator Editing Profile"),
        ("hr_downloading_report", "HR Downloading Report"),
    ]
    hr = models.ForeignKey(
        HR, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    pmo = models.ForeignKey(
        Pmo, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    learner = models.ForeignKey(
        Learner, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    coach = models.ForeignKey(
        Coach, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    facilitator = models.ForeignKey(
        Facilitator, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    feedback_type = models.CharField(max_length=100, choices=feedback_type_choices)
    response = models.BooleanField(blank=True)
    comments = models.TextField(blank=True, default="")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
