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
    path(
        "create-lesson-with-live-session/",
        views.create_lesson_with_live_session,
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
    path(
        "course/<int:course_id>/lesson/<int:lesson_id>/live-sessions/",
        views.get_live_sessions_for_lesson,
    ),
    path(
        "courses/<int:course_id>/lessons/<int:lesson_id>/update-live-session/",
        views.update_live_session,
        name="update-live-session",
    ),
]
