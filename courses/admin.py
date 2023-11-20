from django.contrib import admin
from .models import Course, Lesson, TextLesson, QuizLesson, Question

# Register your models here.
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(TextLesson)
admin.site.register(QuizLesson)
admin.site.register(Question)
