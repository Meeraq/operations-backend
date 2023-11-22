from django.contrib import admin
from .models import (
    Course,
    Lesson,
    QuizLesson,
    Question,
    LiveSession,
    TextLesson,
    LaserCoachingSession,
    FeedbackLesson,
    Assessment,
    Video,
    VideoLesson,
)

# Register your models here.
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(LiveSession)
admin.site.register(TextLesson)
admin.site.register(QuizLesson)
admin.site.register(FeedbackLesson)
admin.site.register(Question)
admin.site.register(LaserCoachingSession)
admin.site.register(Assessment)
admin.site.register(Video)
admin.site.register(VideoLesson)
