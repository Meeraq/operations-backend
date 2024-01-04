from django.db import models
from api.models import Profile

class Affiliate(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    first_name = models.CharField(max_length=255,blank=True)
    last_name = models.CharField(max_length=255,blank=True)
    email = models.CharField(max_length=255,blank=True)
    phone = models.CharField(max_length=25,blank=True)
    is_approved = models.BooleanField(blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



class Lead(models.Model):
    LEAD_STATUS_CHOICES = (
        ("not_contacted", "Not Contacted"),
        ("engaged", "Engaged"),
        ("converted", "Converted"),
        ("lost", "Lost")
    )
    lead_name = models.CharField(max_length=255, blank=True, null=True)
    lead_program = models.CharField(max_length=255, blank=True, null=True)
    lead_email = models.CharField(max_length=255,blank=True, null=True)
    lead_country = models.CharField(max_length=255, blank=True, null=True)
    lead_city = models.CharField(max_length=255, blank=True, null=True)
    lead_phone_country_code = models.CharField(max_length=255, blank=True, null=True)
    lead_phone = models.CharField(max_length=255, blank=True, null=True)
    lead_gender = models.CharField(max_length=255, blank=True, null=True)
    lead_status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default="not_contacted", blank=True, null=True)
    conversation_summary = models.TextField(blank=True, null=True)
    affiliate = models.ForeignKey(Affiliate, on_delete=models.SET_NULL, blank=True, null=True)


    def __str__(self):
        return f"{self.lead_name} with {self.lead_program}"




