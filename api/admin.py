from django.contrib import admin
from .models import Pmo,Coach,Organisation, Project, Learner, Availibility, SessionRequest,Session
# Register your models here.

admin.site.register(Pmo)
admin.site.register(Coach)
admin.site.register(Organisation)
admin.site.register(Project)
admin.site.register(Learner)
admin.site.register(Availibility)
admin.site.register(SessionRequest)
admin.site.register(Session)
