from django.contrib import admin
from .models import (
    Pmo,
    Coach,
    Profile,
    Project,
    CoachStatus,
    Availibility,
    SessionRequestCaas,
    Notification,
    Organisation,
    Learner,
    HR,
    Engagement,
    Goal,
    Competency,
    ActionItem,
    UserToken,
)

# Register your models here.

admin.site.register(Pmo)
admin.site.register(Coach)
admin.site.register(Organisation)
admin.site.register(Project)
admin.site.register(Learner)
admin.site.register(Availibility)
# admin.site.register(SessionRequest)
# admin.site.register(Session)
admin.site.register(HR)
admin.site.register(Profile)
admin.site.register(Engagement)
admin.site.register(CoachStatus)
admin.site.register(SessionRequestCaas)
admin.site.register(Notification)
admin.site.register(Goal)
admin.site.register(Competency)
admin.site.register(ActionItem)
admin.site.register(UserToken)
