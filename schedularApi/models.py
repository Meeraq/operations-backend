from django.db import models
from api.models import Organisation, HR, Coach


# Create your models here.
class SchedularProject(models.Model):
    name = models.CharField(max_length=100, unique=True, default=None)
    project_structure = models.JSONField(default=list, blank=True)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    hr = models.ManyToManyField(HR, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SchedularParticipants(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)


class SchedularBatch(models.Model):
    name = models.CharField(max_length=100, blank=True)
    project = models.ForeignKey(SchedularProject, on_delete=models.CASCADE)
    coaches = models.ManyToManyField(Coach, blank=True)
    participants = models.ManyToManyField(SchedularParticipants, blank=True)
    facilitator = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)


class CoachSchedularAvailibilty(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    start_time = models.CharField(max_length=30)
    end_time = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)


class CoachingSession(models.Model):
    booking_link = models.CharField(max_length=500)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    batch = models.ForeignKey(SchedularBatch, on_delete=models.CASCADE)
    coaching_session_number = models.IntegerField(blank=True, default=None, null=True)
    coaching_session_order = models.IntegerField(blank=True, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)
    duration = models.CharField(max_length=50, default=None)


class SchedularSessions(models.Model):
    enrolled_participant = models.ForeignKey(
        SchedularParticipants, on_delete=models.CASCADE
    )
    availibility = models.ForeignKey(
        CoachSchedularAvailibilty, on_delete=models.CASCADE
    )
    coaching_session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)


class LiveSession(models.Model):
    date_time = models.DateTimeField(auto_now_add=True)
    zoom_id = models.CharField(max_length=500)
    batch = models.ForeignKey(SchedularBatch, on_delete=models.CASCADE)
    live_session_number = models.IntegerField(blank=True, default=None, null=True)
    live_session_order = models.IntegerField(blank=True, default=None, null=True)
    attendees = models.CharField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, default=None)
    duration = models.CharField(max_length=50, default=None)
