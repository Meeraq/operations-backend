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
    SchedularProject,
    SchedularParticipants,
    SchedularBatch,
    CoachSchedularAvailibilty,
    CoachingSession,
    SchedularSessions,
    LiveSession,
    EmailTemplate,
    SentEmail,
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
admin.site.register(SchedularProject)
admin.site.register(SchedularParticipants)
admin.site.register(SchedularBatch)
admin.site.register(CoachSchedularAvailibilty)
admin.site.register(CoachingSession)
admin.site.register(SchedularSessions)
admin.site.register(LiveSession)
admin.site.register(EmailTemplate)
admin.site.register(SentEmail)
