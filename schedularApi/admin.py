from django.contrib import admin

from .models import (
    SchedularProject,
    SchedularParticipants,
    SchedularBatch,
    CoachSchedularAvailibilty,
    CoachingSession,
    SchedularSessions,
    LiveSession,
    EmailTemplate,
    SentEmail,
    RequestAvailibilty,
    
)

# Register your models here.


admin.site.register(SchedularProject)
admin.site.register(SchedularParticipants)
admin.site.register(SchedularBatch)
admin.site.register(CoachSchedularAvailibilty)
admin.site.register(CoachingSession)
admin.site.register(SchedularSessions)
admin.site.register(LiveSession)
admin.site.register(EmailTemplate)
admin.site.register(SentEmail)
admin.site.register(RequestAvailibilty)
