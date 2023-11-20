from django.urls import path, include
from . import views
from .views import (
    CourseListView,
    CourseDetailView,
    TextLessonCreateView,
    TextLessonEditView,
    LessonListView,
    LessonDetailView,
)
import environ

env = environ.Env()

urlpatterns = [
    path(
        "courses/<int:pk>/",
        CourseDetailView.as_view(),
        name="course-detail",
    ),
    path(
        "courses/",
        CourseListView.as_view(),
        name="course-list-create-update-destroy",
    ),
    path("text-lessons/", TextLessonCreateView.as_view(), name="text-lesson-create"),
    path(
        "text-lessons/<int:pk>/", TextLessonEditView.as_view(), name="text-lesson-edit"
    ),
    path(
        "courses/<int:course_id>/lessons/", LessonListView.as_view(), name="lesson-list"
    ),
    path(
        "lessons/<str:lesson_type>/<int:lesson_id>/",
        LessonDetailView.as_view(),
        name="lesson-list",
    ),
    path("quiz-lessons/", views.create_quiz_lesson, name="text-lesson-create"),
]
