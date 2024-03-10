from django.urls import path, include
from . import views
from .views import (
    CourseListView,
    CourseTemplateListView,
    CourseDetailView,
    CourseTemplateDetailView,
    TextLessonCreateView,
    TextLessonEditView,
    LessonListView,
    CourseTemplateLessonListView,
    LessonDetailView,
    CertificateListAPIView,
    GetFilteredCoursesForCertificate,
    AssignCoursesToCertificate,
    DeleteCourseFromCertificate,
    LessonMarkAsCompleteAndNotComplete,
    DownloadLessonCertificate,
    GetCertificateForCourse,
    GetLaserCoachingTime,
    AssignCourseTemplateToBatch,
    FileListAPIView,
    FileUploadView,
    FileDownloadView,
    update_file,
    DownloadableLessonUpdateView,
    DownloadableLessonCreateView,
    FeedbackEmailValidation,
    GetFeedbackForm,
    EditAllowedFeedbackLesson,
    DuplicateLesson,
    LessonCompletedWebhook,
    GetUniqueIdParticipantFromCourse,
    GetAssessmentsOfBatch,
    GetAllNudgesOfSchedularProjects,
    CreateAssignmentLesson,
    UpdateAssignmentLesson,
    GetAllAssignmentsResponses,
    CreateAssignmentLessonResponse,
    GetAssignmentsResponses,
    UpdateAssignmentLessonFile,
    FacilitatorWiseFeedback,
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
        "course-templates/<int:pk>/",
        CourseTemplateDetailView.as_view(),
        name="course-detail",
    ),
    path(
        "courses/",
        CourseListView.as_view(),
        name="course-list-create-update-destroy",
    ),
    path(
        "course-templates/",
        CourseTemplateListView.as_view(),
    ),
    path(
        "courses/<int:course_id>/duplicate/",
        views.DuplicateCourseAPIView.as_view(),
        name="course-detail",
    ),
    path(
        "create-lesson-with-live-session/",
        views.create_lesson_with_live_session,
    ),
    path(
        "lessons/update_lesson_order/",
        views.UpdateLessonOrder.as_view(),
        name="update_lesson_order",
    ),
    path(
        "nudges/update_nudges_order/",
        views.UpdateNudgesOrder.as_view(),
        name="update_lesson_order",
    ),
    path("text-lessons/", TextLessonCreateView.as_view(), name="text-lesson-create"),
    path(
        "text-lessons/<int:pk>/", TextLessonEditView.as_view(), name="text-lesson-edit"
    ),
    path(
        "courses/<int:course_id>/lessons/", LessonListView.as_view(), name="lesson-list"
    ),
    path(
        "courses/<int:course_id>/nudges/",
        views.get_nudges_and_course,
        name="lesson-list",
    ),
    path("nudges/create", views.create_new_nudge),
    path("nudges/<int:nudge_id>/update/", views.update_nudge),
    path("nudges/<int:nudge_id>/file/download/", views.download_nudge_file),
    path(
        "courses/<int:course_id>/update-nudge-date-frequency/",
        views.add_nudges_date_frequency_to_course,
    ),
    path(
        "course-templates/<int:course_template_id>/lessons/",
        CourseTemplateLessonListView.as_view(),
        name="course-template-lesson-list",
    ),
    path(
        "lessons/<str:lesson_type>/<int:lesson_id>/",
        LessonDetailView.as_view(),
        name="lesson-list",
    ),
    path(
        "lessons/<int:lesson_id>/",
        views.DeleteLessonAPIView.as_view(),
        name="delete_lesson",
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
        "lessons/<int:lesson_id>/assessment-lesson/",
        views.get_assessment_lesson,
    ),
    path(
        "lessons/<int:lesson_id>/assessment-lesson/<int:session_id>/",
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
        "course-enrollment/<int:course_id>/<int:learner_id>/",
        views.get_course_enrollment,
    ),
    path(
        "course-enrollment/pmo/<int:course_id>/",
        views.get_course_enrollment_for_pmo_preview,
    ),
    path(
        "course-template/preview/pmo/<int:course_template_id>/",
        views.get_course_enrollment_for_pmo_preview_for_course_template,
    ),
    path(
        "course-enrollments/<int:learner_id>/",
        views.get_course_enrollments_of_learner,
    ),
    path(
        "submit-quiz/<int:quiz_lesson_id>/<int:learner_id>/",
        views.submit_quiz_answers,
    ),
    path(
        "quiz-result/<int:quiz_lesson_id>/<int:learner_id>/",
        views.get_quiz_result,
    ),
    path(
        "submit-feedback/<int:feedback_lesson_id>/<int:learner_id>/",
        views.submit_feedback_answers,
    ),
    path("certificates/", CertificateListAPIView.as_view()),
    path(
        "get-courses-for-certificates/",
        GetFilteredCoursesForCertificate.as_view(),
    ),
    path("assign-courses-to-certificate/", AssignCoursesToCertificate.as_view()),
    path("delete-courses-to-certificate/", DeleteCourseFromCertificate.as_view()),
    path("lesson-mark-as-complete/", LessonMarkAsCompleteAndNotComplete.as_view()),
    path(
        "download-lesson-certificate/<int:lesson_id>/<int:learner_id>/",
        DownloadLessonCertificate.as_view(),
    ),
    path(
        "get-certificate-for-course/<int:course_id>/", GetCertificateForCourse.as_view()
    ),
    path("certificates/", CertificateListAPIView.as_view()),
    path(
        "get-courses-for-certificates/<int:certificate_id>",
        GetFilteredCoursesForCertificate.as_view(),
    ),
    path("assign-courses-to-certificate/", AssignCoursesToCertificate.as_view()),
    path("delete-courses-to-certificate/", DeleteCourseFromCertificate.as_view()),
    path(
        "create_video_with_lesson/",
        views.create_videos,
    ),
    path("videos/", views.get_all_videos, name="get-all-videos"),
    path("create_video_lesson/", views.create_video_lesson, name="create_video_lesson"),
    path("video_library/", views.get_all_videos, name="video-list"),
    path(
        "video-lesson/<int:lesson_id>/",
        views.update_video_lesson,
        name="update-video-lesson",
    ),
    path("videos/<int:pk>/update/", views.update_video, name="update_video"),
    path("courses/report/all/", views.get_all_courses_progress),
    path("courses/<int:course_id>/report/", views.get_course_progress),
    path("courses/<int:course_id>/report/download/", views.course_report_download),
    path("quizes/report/all/", views.get_all_quizes_report),
    path("quizes/<int:quiz_id>/report/", views.get_quiz_report),
    path("quizes/<int:quiz_id>/report/download/", views.quiz_report_download),
    path("feedbacks/report/all/", views.get_all_feedbacks_report),
    path("consolidated-feedback-report/", views.get_consolidated_feedback_report),
    path("feedbacks/<int:feedback_id>/report/", views.get_feedback_report),
    path(
        "get-consolidated-feedback-report-response/<int:lesson_id>/report/",
        views.get_consolidated_feedback_report_response,
    ),
    path(
        "get-laser-coaching-time/<int:laser_coaching_id>/<str:participant_email>/",
        GetLaserCoachingTime.as_view(),
    ),
    path(
        "assign-course-template-to-batch/<int:course_template_id>/<int:batch_id>/",
        AssignCourseTemplateToBatch.as_view(),
    ),
    path("resources/", views.get_resources),
    path(
        "create_resource/",
        views.create_resource,
    ),
    path(
        "create_pdf_lesson/",
        views.create_pdf_lesson,
    ),
    path(
        "update_pdf_lessons/<int:pk>/",
        views.update_pdf_lesson,
        name="update_pdf_lesson",
    ),
    path(
        "update_course_template_status/",
        views.update_course_template_status,
        name="update_course_template",
    ),
    path("update-course_status/", views.update_course_status),
    path("update-lesson-status/", views.lesson_update_status),
    path("files/", FileListAPIView.as_view(), name="file-list"),
    path("files/upload/", FileUploadView.as_view(), name="file-upload"),
    path(
        "files/<int:file_id>/download/",
        FileDownloadView.as_view(),
        name="file-download",
    ),
    path(
        "files/<int:file_id>/",
        update_file,
        name="update-file",
    ),
    path(
        "downloadable-lessons/create/",
        DownloadableLessonCreateView.as_view(),
        name="create-downloadable-lesson",
    ),
    path(
        "downloadable-lessons/update/<int:pk>/",
        DownloadableLessonUpdateView.as_view(),
        name="update-downloadable-lesson",
    ),
    path(
        "feedback-email-validation/",
        FeedbackEmailValidation.as_view(),
        name="update-downloadable-lesson",
    ),
    path(
        "get-feedback-form/<str:unique_id>/",
        GetFeedbackForm.as_view(),
    ),
    path(
        "feedback-lesson-edit-allowed/<str:feedback_lesson_id>/",
        EditAllowedFeedbackLesson.as_view(),
    ),
    path(
        "duplicate-lesson/",
        DuplicateLesson.as_view(),
    ),
    path(
        "lesson-completed-webhook/",
        LessonCompletedWebhook.as_view(),
    ),
    path(
        "get/uniqueId/participant-from-course/<int:user_id>/<int:assessment_id>/",
        GetUniqueIdParticipantFromCourse.as_view(),
    ),
    path(
        "get-assessments-of-batch/<str:project_or_batch>/<int:id>/",
        GetAssessmentsOfBatch.as_view(),
    ),
    path(
        "feedback-report-download/<str:feedback_id>/",
        views.get_all_feedbacks_download_report,
    ),
    path(
        "feedback/reports/project/consolidated/download/<int:project_id>/",
        views.download_consolidated_project_report,
    ),
    path(
        "feedback/reports/project/consolidated/",
        views.feedback_reports_project_wise_consolidated,
    ),
    path(
        "consolidated-feedback-download-report/<str:live_session_id>/",
        views.get_consolidated_feedback_download_report,
    ),
    path(
        "projects/<int:project_id>/nudges/",
        views.get_nudges_by_project_id,
        name="get_nudges_by_project_id",
    ),
    path("send-test-nudge/<int:nudge_id>/", views.send_nudge_to_email),
    path(
        "nudges/<int:nudge_id>/duplicate/<int:course_id>/",
        views.duplicate_nudge,
        name="duplicate_nudge",
    ),
    path(
        "get-nps-project-wise/",
        views.get_nps_project_wise,
    ),
    path(
        "get-all-nudges-of-schedular-project/<str:project_id>/",
        GetAllNudgesOfSchedularProjects.as_view(),
    ),
    path("create_assignment_lesson/", CreateAssignmentLesson.as_view()),
    path(
        "update_assignment_lessons/<int:assignment_id>/",
        UpdateAssignmentLesson.as_view(),
    ),
    path(
        "get_all_assignments_responses/<str:user_type>/<int:user_id>",
        GetAllAssignmentsResponses.as_view(),
    ),
    path(
        "create_assignment_lesson_response/", CreateAssignmentLessonResponse.as_view()
    ),
    path(
        "get_assignments_responses/<int:assignment_id>/<int:learner_id>/",
        GetAssignmentsResponses.as_view(),
    ),
    path(
        "update_assignments_responses/",
        UpdateAssignmentLessonFile.as_view(),
    ),
    path(
        "facilitator-wise-feedback/",
        FacilitatorWiseFeedback.as_view(),
    ),
    path(
        "get-feedback/<int:feedback_id>/",
        views.get_feedback,
    ),
    path(
        "submit-session-feedback/<int:feedback_id>/<int:learner_id>/",
        views.submit_feedback,
    ),
    path(
        "get-end-meeting-feedback-response-data/",
        views.get_end_meeting_feedback_response_data,
    ),
    path(
        "get-coach-session-feedback-response-data/<int:feedback_response_id>/",
        views.get_coach_session_feedback_response_data,
    ),
]
