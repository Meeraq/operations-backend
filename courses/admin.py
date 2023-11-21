from django.contrib import admin
from .models import Course, Lesson, LiveSession, TextLesson, LaserCoachingSession

# Register your models here.
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(LiveSession)
admin.site.register(TextLesson)
admin.site.register(LaserCoachingSession)
