from django.contrib import admin
from .models import (
    Course,
    Lesson,
    QuizLesson,
    Question,
    LiveSessionLesson,
    TextLesson,
    LaserCoachingSession,
    FeedbackLesson,
    Assessment,
    CourseEnrollment,
    Answer,
    Certificate,
    QuizLessonResponse,
    FeedbackLessonResponse,
    Video,
    VideoLesson,
    CourseTemplate,
    Resources,
    PdfLesson,
    ThinkificLessonCompleted,
    Nudge,
    AssignmentLesson,
    AssignmentLessonResponse,
    Feedback, 
    CoachingSessionsFeedbackResponse,
    CttFeedback,
    CttFeedbackResponse,
    CttParticipantPerformanceEvaluation,
)

# Register your models here.
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(LiveSessionLesson)
admin.site.register(TextLesson)
admin.site.register(QuizLesson)
admin.site.register(FeedbackLesson)
admin.site.register(Question)
admin.site.register(LaserCoachingSession)
admin.site.register(Assessment)
admin.site.register(CourseEnrollment)
admin.site.register(Answer)
admin.site.register(Certificate)
admin.site.register(QuizLessonResponse)
admin.site.register(FeedbackLessonResponse)
admin.site.register(Video)
admin.site.register(VideoLesson)
admin.site.register(CourseTemplate)
admin.site.register(Resources)
admin.site.register(PdfLesson)
admin.site.register(ThinkificLessonCompleted)
admin.site.register(Nudge)
admin.site.register(AssignmentLesson)
admin.site.register(AssignmentLessonResponse)
admin.site.register(Feedback)
admin.site.register(CoachingSessionsFeedbackResponse)
admin.site.register(CttFeedback)
admin.site.register(CttFeedbackResponse)
admin.site.register(CttParticipantPerformanceEvaluation)