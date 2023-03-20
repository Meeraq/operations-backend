from django.contrib import admin
from .models import Pmo,Coach,Organisation,OTP_HR, Project, Learner, Availibility, SessionRequest,Session,HR,Profile
# Register your models here.

admin.site.register(Pmo)
admin.site.register(Coach)
admin.site.register(Organisation)
admin.site.register(Project)
admin.site.register(Learner)
admin.site.register(Availibility)
admin.site.register(SessionRequest)
admin.site.register(Session)
admin.site.register(HR)
admin.site.register(Profile)
admin.site.register(OTP_HR)
