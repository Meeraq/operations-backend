from django.contrib import admin
from .models import (
    Competency,
    Question,
    Questionnaire,
    Assessment,
    ParticipantObserverMapping,
    Observer,
    ParticipantResponse,
    ObserverResponse,
    ParticipantObserverType,
    ObserverUniqueId,
    Behavior,
    AssessmentNotification,
    ParticipantUniqueId,
    ParticipantReleasedResults,
    ActionItem
)

# Register your models here.


admin.site.register(Competency)
admin.site.register(Question)
admin.site.register(Questionnaire)
admin.site.register(Assessment)
admin.site.register(Observer)
admin.site.register(ParticipantObserverMapping)
admin.site.register(ParticipantResponse)
admin.site.register(ObserverResponse)
admin.site.register(ParticipantObserverType)
admin.site.register(ObserverUniqueId)
admin.site.register(Behavior)
admin.site.register(AssessmentNotification)
admin.site.register(ParticipantUniqueId)
admin.site.register(ParticipantReleasedResults)
admin.site.register(ActionItem)
