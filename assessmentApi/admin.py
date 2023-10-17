from django.contrib import admin
from .models import Competency, Question, Questionnaire,Assessment

# Register your models here.


admin.site.register(Competency)
admin.site.register(Question)
admin.site.register(Questionnaire)
admin.site.register(Assessment)
