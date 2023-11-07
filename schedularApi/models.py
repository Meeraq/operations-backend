from django.db import models
from django_celery_beat.models import PeriodicTask
from api.models import Organisation, HR, Coach


# Create your models here.
class SchedularProject(models.Model):
    name = models.CharField(max_length=100, unique=True, default=None)
    project_structure = models.JSONField(default=list, blank=True)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    hr = models.ManyToManyField(HR, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    is_project_structure_finalized = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SchedularParticipants(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=25)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)


class SchedularBatch(models.Model):
    name = models.CharField(max_length=100, blank=True)
    project = models.ForeignKey(SchedularProject, on_delete=models.CASCADE)
    coaches = models.ManyToManyField(Coach, blank=True)
    participants = models.ManyToManyField(SchedularParticipants, blank=True)
    facilitator = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)


class RequestAvailibilty(models.Model):
    request_name = models.CharField(max_length=100, blank=True)
    coach = models.ManyToManyField(Coach, blank=True)
    provided_by = models.JSONField(
        default=list
    )  # used to store coach ids who already provided the slots
    expiry_date = models.DateField(blank=True, null=True)
    availability = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)


class CoachSchedularAvailibilty(models.Model):
    request = models.ForeignKey(
        RequestAvailibilty, on_delete=models.CASCADE, default=""
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


class SchedularSessions(models.Model):
    enrolled_participant = models.ForeignKey(
        SchedularParticipants, on_delete=models.CASCADE
    )
    availibility = models.ForeignKey(
        CoachSchedularAvailibilty, on_delete=models.CASCADE
    )
    coaching_session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="pending", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)


class LiveSession(models.Model):
    batch = models.ForeignKey(SchedularBatch, on_delete=models.CASCADE)
    live_session_number = models.IntegerField(blank=True, default=None, null=True)
    order = models.IntegerField(blank=True, default=None, null=True)
    date_time = models.DateTimeField(blank=True, null=True)
    attendees = models.JSONField(blank=True, default=list)
    description = models.TextField(default="", blank=True)
    status = models.CharField(blank=True, default="pending", max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration = models.CharField(max_length=50, default=None)


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


class Facilitator(models.Model):
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
    years_of_corporate_experience = models.CharField(max_length=20, blank=True)
    city = models.JSONField(default=list, blank=True)
    language = models.JSONField(default=list, blank=True)
    job_roles = models.JSONField(default=list, blank=True)
    city = models.JSONField(default=list, blank=True)
    country = models.JSONField(default=list, blank=True)
    created_at = models.DateField(auto_now_add=True)
    edited_at = models.DateField(auto_now=True)
    linkedin_profile_link = models.CharField(max_length=500, blank=True)
    companies_worked_in = models.JSONField(default=list, blank=True)
    other_certification = models.JSONField(default=list, blank=True)
    currency = models.CharField(max_length=100, blank=True, default="")
    client_companies = models.JSONField(default=list, blank=True)
    educational_qualification = models.JSONField(default=list, blank=True)
    fees_per_hour = models.JSONField(default=list, blank=True)
    fees_per_day = models.JSONField(default=list, blank=True)
    topic = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.first_name + " " + self.last_name
