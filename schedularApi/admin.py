from django.contrib import admin

from .models import (
    SchedularProject,
    SchedularBatch,
    CoachSchedularAvailibilty,
    CoachingSession,
    SchedularSessions,
    LiveSession,
    EmailTemplate,
    SentEmail,
    RequestAvailibilty,
    Facilitator,
)

# Register your models here.


admin.site.register(SchedularProject)
admin.site.register(SchedularBatch)
admin.site.register(CoachSchedularAvailibilty)
admin.site.register(CoachingSession)
admin.site.register(SchedularSessions)
admin.site.register(LiveSession)
admin.site.register(EmailTemplate)
admin.site.register(SentEmail)
admin.site.register(RequestAvailibilty)
admin.site.register(Facilitator)
