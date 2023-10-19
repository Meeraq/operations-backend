from django.contrib import admin
from .models import (
    Competency,
    Question,
    Questionnaire,
    Assessment,
    ParticipantObserverMapping,
    Observer,
)

# Register your models here.


admin.site.register(Competency)
admin.site.register(Question)
admin.site.register(Questionnaire)
admin.site.register(Assessment)
admin.site.register(Observer)
admin.site.register(ParticipantObserverMapping)
