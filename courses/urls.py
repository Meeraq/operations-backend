from django.urls import path, include
from . import views
from .views import (
    CourseListView,
    CourseDetailView,
    TextLessonCreateView,
    TextLessonEditView,
    LessonListView,
    LessonDetailView,
    CertificateListAPIView,
    GetFilteredCoursesForCertificate,
    AssignCoursesToCertificate,
    DeleteCourseFromCertificate
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
    path(
        "create-laser-booking-lesson/",
        views.create_laser_booking_lesson,
    ),
    path(
        "courses/<int:course_id>/lessons/<int:lesson_id>/laser-coaching-sessions/",
        views.get_laser_coaching_sessions,
    ),
    path(
        "courses/<int:course_id>/lessons/<int:lesson_id>/laser-coaching-sessions/<int:session_id>/",
        views.update_laser_coaching_session,
    ),
    path("quiz-lessons/", views.create_quiz_lesson, name="quiz-lesson-create"),
    path(
        "quiz-lessons/<int:quiz_lesson_id>/",
        views.edit_quiz_lesson,
        name="quiz-lesson-edit",
    ),
    path(
        "create-assessment-lesson/",
        views.create_assessment_and_lesson,
    ),
    path(
        "courses/<int:course_id>/lessons/<int:lesson_id>/assessment-lesson/",
        views.get_assessment_lesson,
    ),
    path(
        "courses/<int:course_id>/lessons/<int:lesson_id>/assessment-lesson/<int:session_id>/",
        views.update_assessment_lesson,
    ),
    path(
        "feedback-lessons/", views.create_feedback_lesson, name="feedback-lesson-create"
    ),
    path(
        "feedback-lessons/<int:feedback_lesson_id>/",
        views.edit_feedback_lesson,
        name="feedback-lesson-edit",
    ),
    path(
        "courses/<int:course_id>/enroll-participants/<int:schedular_batch_id>/",
        views.enroll_participants_to_course,
        name="enroll-participants-to-course",
    ),
    path('certificates/', CertificateListAPIView.as_view()),

    path('get-courses-for-certificates/<int:certificate_id>', GetFilteredCoursesForCertificate.as_view()),

    path('assign-courses-to-certificate/', AssignCoursesToCertificate.as_view()),

    path('delete-courses-to-certificate/', DeleteCourseFromCertificate.as_view()),

]
