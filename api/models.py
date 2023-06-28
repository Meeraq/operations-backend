from django.db import models

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


import environ

env = environ.Env()


@receiver(reset_password_token_created)
def password_reset_token_created(
    sender, instance, reset_password_token, *args, **kwargs
):
    print(reset_password_token.key)
    email_plaintext_message = "{}?token={}".format(
        reverse("password_reset:reset-password-request"), reset_password_token.key
    )
    subject = "Meeraq - Forgot Password"
    name = "User"
    message = f'Dear {name},\n\nYour reset password link is {env("APP_URL")}/reset-password/{reset_password_token.key}'
    send_mail(
        subject, message, settings.DEFAULT_FROM_EMAIL, [reset_password_token.user.email]
    )


class Profile(models.Model):
    user_types = [
        ("pmo", "pmo"),
        ("coach", "coach"),
        ("learner", "learner"),
        ("hr", "hr"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=user_types)

    def __str__(self):
        return self.user.username


class Pmo(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)

    def __str__(self):
        return self.name


class Coach(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    coach_id = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    age = models.CharField(max_length=10, default="", blank=True)
    gender = models.CharField(max_length=50, blank=True)
    domain = models.CharField(max_length=50, blank=True)
    room_id = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=25)
    level = models.CharField(max_length=50)
    rating = models.CharField(max_length=20)
    area_of_expertise = models.JSONField(default=list, blank=True)
    completed_sessions = models.IntegerField(blank=True, default=0)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    education = models.CharField(max_length=200, blank=True)
    corporate_experience = models.TextField(blank=True)
    coaching_experience = models.TextField(blank=True)
    years_of_corporate_experience = models.CharField(max_length=20, blank=True)
    years_of_coaching_experience = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(blank=True, default=False)
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
    active_inactive = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return self.first_name


class Learner(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    area_of_expertise = models.CharField(max_length=100, blank=True)
    years_of_experience = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return self.name


class Organisation(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.ImageField(upload_to="post_images", blank=True)


class HR(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.first_name


# class CoachInvites(models.Model):
#     name= models.CharField(max_length=100)
#     email = models.EmailField()
#     created_at = models.DateTimeField(auto_now_add=True)


class CoachStatus(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    status = models.JSONField(default=dict, blank=True)
    learner_id = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    consent_expiry_date = models.DateField(blank=True, null=True)


class Project(models.Model):
    project_type_choice = [("COD", "COD"), ("4+2", "4+2"), ("CAAS", "CAAS")]
    name = models.CharField(max_length=100)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    project_type = models.CharField(
        max_length=50, choices=project_type_choice, default="cod"
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
    currency = models.CharField(max_length=30, default="Rupees")
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
    location = models.CharField(max_length=100, blank=True, default=None)


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


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


class SessionRequestCaas(models.Model):
    hr = models.ForeignKey(
        HR, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    learner = models.ForeignKey(
        Learner, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    coach = models.ForeignKey(
        Coach, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
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
    reschedule_request = models.JSONField(default=list,blank=True)
    status = models.CharField(max_length=30,default="",blank=True)
    session_number = models.IntegerField(blank=True,default=None,null=True)
    session_duration = models.IntegerField(blank=True,default=None,null=True)
    order=models.IntegerField(blank=True,default=None,null=True) # used for engagement structure


# class SessionCaas(models.Model):
#     coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
#     confirmed_availability = models.ForeignKey(Availibility, on_delete=models.CASCADE)
#     session_request = models.ForeignKey(SessionRequestCaas, on_delete=models.CASCADE)
#     status = models.CharField(max_length=20,default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)
#     coach_joined = models.BooleanField(blank=True,default=False)
#     learner_joined = models.BooleanField(blank=True,default=False)
#     hr_joined = models.BooleanField(blank=True,default=False)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    path = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True)
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


class Engagement(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
    )
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, null=True, blank=True)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    project_structure = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Goal(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("archive", "Archive"),
        ("complete", "Complete"),
    )
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES) 
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE)
    
class Competency(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    scoring = models.JSONField(default=list, blank=True)
    created_at = models.DateField(auto_now_add=True)