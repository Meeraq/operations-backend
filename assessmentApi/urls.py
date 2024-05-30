from django.urls import path, include
from . import views


from .views import (
    CompetencyView,
    QuestionView,
    QuestionnaireView,
    AssessmentView,
    ParticipantObserverTypeList,
    QuestionnaireIdsInOngoingAndCompletedAssessments,
    QuestionIdsInOngoingAndCompletedAssessments,
    CompetencyIdsInOngoingAndCompletedAssessments,
    AddObserverToParticipant,
    DeleteObserverFromAssessment,
    DeleteParticipantFromAssessment,
    GetObserverResponseFormAssessment,
    GetObserverResponseForObserver,
    CreateObserverResponseView,
    QuestionsForAssessment,
    QuestionsForObserverAssessment,
    GetParticipantResponseFormAssessment,
    GetParticipantResponseForParticipant,
    CreateParticipantResponseView,
    AssessmentStatusChange,
    AssessmentEndDataChange,
    ObserverView,
    ObserverAssessment,
    AssessmentsOfParticipant,
    AddParticipantObserverToAssessment,
    ParticipantAddsObserverToAssessment,
    StartAssessmentDataForObserver,
    GetObserversUniqueIds,
    GetParticipantObserversUniqueIds,
    StartAssessmentDisabled,
    ReleaseResults,
    AssessmentsOfHr,
    GetParticipantResponseForAllAssessment,
    GetObserverResponseForAllAssessment,
    ReminderMailForObserverByPmoAndParticipant,
    GetObserverResponseForAllAssessments,
    GetParticipantResponseForAllAssessments,
    AddMultipleQuestions,
    AddMultipleParticipants,
    CreateObserverType,
    GetObserverTypes,
    DownloadParticipantResultReport,
    GetAssessmentNotification,
    MarkAllNotificationAsRead,
    MarkNotificationAsRead,
    GetUnreadNotificationCount,
    DownloadWordReport,
    GetLearnersUniqueId,
    StartAssessmentDataForParticipant,
    StartAssessmentParticipantDisabled,
    PrePostReportDownloadForParticipant,
    PrePostReportDownloadForAllParticipant,
    MoveParticipant,
    GetAllLearnersUniqueId,
    DownloadParticipantResponseStatusData,
    GetParticipantReleasedResults,
    GetAllAssessments,
    GetOneAssessment,
    GetAssessmentsOfHr,
    GetAssessmentsDataForMoveParticipant,
    CreateAssessmentAndAddMultipleParticipantsFromBatch,
    AssessmentInAssessmentLesson,
    AllAssessmentInAssessmentLesson,
    PostReportDownloadForAllParticipant,
    PostReportDownloadForParticipant,
    GetProjectWiseReport,
    GetAllAssessmentsOfSchedularProjects,
    AssessmentsResponseStatusDownload,
    GetAssessmentBatchAndProject,
    DownloadQuestionWiseExcelForProject,
    ResponseDownloadForAllParticipants,
    CreateCoachingAssessmentAndAddMultipleParticipants,
    GetAssessmentOfCoachingProject,
)


urlpatterns = [
    path("create-competency/", CompetencyView.as_view()),
    path("get-competencies/", CompetencyView.as_view()),
    path("delete-competency/", CompetencyView.as_view()),
    path("edit-competency/", CompetencyView.as_view()),
    path("create-question/", QuestionView.as_view()),
    path("get-questions/", QuestionView.as_view()),
    path("delete-question/", QuestionView.as_view()),
    path("edit-question/", QuestionView.as_view()),
    path("create-questionnaire/", QuestionnaireView.as_view()),
    path("get-questionnaires/", QuestionnaireView.as_view()),
    path("delete-questionnaire/", QuestionnaireView.as_view()),
    path("edit-questionnaire/", QuestionnaireView.as_view()),
    path("create-assessment/", AssessmentView.as_view()),
    path("get-assessments/", AssessmentView.as_view()),
    path("delete-assessment/", AssessmentView.as_view()),
    path("edit-assessment/", AssessmentView.as_view()),
    path("assessment-status-change/", AssessmentStatusChange.as_view()),
    path("assessment-end-data-change/", AssessmentEndDataChange.as_view()),
    path(
        "add-participant-observer-to-assessment/",
        AddParticipantObserverToAssessment.as_view(),
    ),
    path(
        "assessments-of-participant/<str:participant_email>/",
        AssessmentsOfParticipant.as_view(),
    ),
    path(
        "questions-for-assessment/<int:assessment_id>/",
        QuestionsForAssessment.as_view(),
    ),
    path(
        "questions-for-observer-assessment/<int:assessment_id>/",
        QuestionsForObserverAssessment.as_view(),
    ),
    path("observer-view/", ObserverView.as_view()),
    path("observer-assessment/<str:email>/", ObserverAssessment.as_view()),
    path("create-response/", CreateParticipantResponseView.as_view()),
    path("create-observer-response/", CreateObserverResponseView.as_view()),
    path(
        "get-response-result/<str:participant_email>/",
        GetParticipantResponseForParticipant.as_view(),
    ),
    path(
        "get-participants-response-result/<int:assessment_id>/",
        GetParticipantResponseFormAssessment.as_view(),
    ),
    path(
        "get-observer-response-result/<str:observer_email>/",
        GetObserverResponseForObserver.as_view(),
    ),
    path(
        "get-observer-assessment-response-result/<int:assessment_id>/",
        GetObserverResponseFormAssessment.as_view(),
    ),
    path("participant-observer-types/", ParticipantObserverTypeList.as_view()),
    path(
        "delete-participant-from-assessment/", DeleteParticipantFromAssessment.as_view()
    ),
    path("delete-observer-from-assessment/", DeleteObserverFromAssessment.as_view()),
    path("add-observer-to-participant/", AddObserverToParticipant.as_view()),
    path(
        "competency-ids-in-ongoing-and-completed-assessments/",
        CompetencyIdsInOngoingAndCompletedAssessments.as_view(),
    ),
    path(
        "question-ids-in-ongoing-and-completed-assessments/",
        QuestionIdsInOngoingAndCompletedAssessments.as_view(),
    ),
    path(
        "questionnaire-ids-in-ongoing-and-completed-assessments/",
        QuestionnaireIdsInOngoingAndCompletedAssessments.as_view(),
    ),
    path(
        "participant-adds-observer-to-assessment/",
        ParticipantAddsObserverToAssessment.as_view(),
    ),
    path(
        "get-start-assessment-data-for-observer/<str:unique_id>/",
        StartAssessmentDataForObserver.as_view(),
    ),
    path(
        "get-observers-unique-id/<int:assessment_id>/",
        GetObserversUniqueIds.as_view(),
    ),
    path(
        "get-participant-observers-unique-id/<str:participant_email>/",
        GetParticipantObserversUniqueIds.as_view(),
    ),
    path(
        "start-assessment-disabled/<str:unique_id>/",
        StartAssessmentDisabled.as_view(),
    ),
    path(
        "start-participant-assessment-disabled/<str:unique_id>/",
        StartAssessmentParticipantDisabled.as_view(),
    ),
    path(
        "release-assessment-result/<int:assessment_id>/",
        ReleaseResults.as_view(),
    ),
    path(
        "assessments-of-hr/<str:hr_email>/",
        AssessmentsOfHr.as_view(),
    ),
    path(
        "get-participants-response-result-for-all-assessment/<str:hr_email>/",
        GetParticipantResponseForAllAssessment.as_view(),
    ),
    path(
        "get-observer-assessment-response-result-for-all-assessment/<str:hr_email>/",
        GetObserverResponseForAllAssessment.as_view(),
    ),
    path(
        "reminder-mail-for-observer-by-pmo-and-participant/",
        ReminderMailForObserverByPmoAndParticipant.as_view(),
    ),
    path(
        "get-participants-response-result-for-all-assessments/",
        GetParticipantResponseForAllAssessments.as_view(),
    ),
    path(
        "get-observer-assessment-response-result-for-all-assessments/",
        GetObserverResponseForAllAssessments.as_view(),
    ),
    path(
        "add-multiple-questions/",
        AddMultipleQuestions.as_view(),
    ),
    path(
        "add-multiple-participants/",
        AddMultipleParticipants.as_view(),
    ),
    path(
        "create-observer-types/",
        CreateObserverType.as_view(),
    ),
    path(
        "get-observer-types/",
        GetObserverTypes.as_view(),
    ),
    path(
        "download-participant-result-report/",
        DownloadParticipantResultReport.as_view(),
    ),
    path(
        "download-participant-result-report/<int:assessment_id>/<int:participant_id>/",
        DownloadParticipantResultReport.as_view(),
    ),
    path("notifications/all/<int:user_id>/", GetAssessmentNotification.as_view()),
    path("notifications/mark-as-read/", MarkNotificationAsRead.as_view()),
    path("notifications/mark-all-as-read/", MarkAllNotificationAsRead.as_view()),
    path(
        "notifications/unread-count/<int:user_id>/",
        GetUnreadNotificationCount.as_view(),
    ),
    path(
        "download-word-report/<int:assessment_id>/<int:participant_id>/",
        DownloadWordReport.as_view(),
    ),
    path(
        "get/uniqueId/participant/<int:assessment_id>",
        GetLearnersUniqueId.as_view(),
    ),
    path(
        "get/all/uniqueId/participant/",
        GetAllLearnersUniqueId.as_view(),
    ),
    path(
        "get-start-assessment-data-for-participant/<str:unique_id>/",
        StartAssessmentDataForParticipant.as_view(),
    ),
    path(
        "pre-report-download-for-participant/<int:assessment_id>/<int:participant_id>/",
        PrePostReportDownloadForParticipant.as_view(),
    ),
    path(
        "pre-report-download-for-all-participant/<int:assessment_id>/",
        PrePostReportDownloadForAllParticipant.as_view(),
    ),
    path(
        "move-participant/",
        MoveParticipant.as_view(),
    ),
    path(
        "get-download-respose-status/<int:assessment_id>/",
        DownloadParticipantResponseStatusData.as_view(),
    ),
    path(
        "get-participant-released-results/<int:assessment_id>/",
        GetParticipantReleasedResults.as_view(),
    ),
    path(
        "get-all-assessments/",
        GetAllAssessments.as_view(),
    ),
    path("assessment/<int:assessment_id>/", GetOneAssessment.as_view()),
    path("assessments/hr/<int:hr_id>/", GetAssessmentsOfHr.as_view()),
    path(
        "get-assessments-for-move-participant/",
        GetAssessmentsDataForMoveParticipant.as_view(),
    ),
    path(
        "create-assessment-and-add-multiple-participants-from-batch/",
        CreateAssessmentAndAddMultipleParticipantsFromBatch.as_view(),
    ),
    path(
        "assessment-in-assessment-lesson/<int:assessment_id>/",
        AssessmentInAssessmentLesson.as_view(),
    ),
    path(
        "all-assessment-in-assessment-lesson/",
        AllAssessmentInAssessmentLesson.as_view(),
    ),
    path(
        "send-mail-to-non-responded-participant/<str:assessment_id>/",
        views.send_mail_to_not_responded_participant,
    ),
    path(
        "post-report-download-for-all-participants/<int:assessment_id>/",
        PostReportDownloadForAllParticipant.as_view(),
    ),
    path(
        "post-report-download-for-participant/<int:assessment_id>/<int:participant_id>/",
        PostReportDownloadForParticipant.as_view(),
    ),
    path(
        "get-project-wise-report/<int:project_id>/<str:report_to_download>/",
        GetProjectWiseReport.as_view(),
    ),
    path(
        "get-all-assessments-of-schedular-project/<str:project_id>/",
        GetAllAssessmentsOfSchedularProjects.as_view(),
    ),
    path(
        "assessments-download-respose-status/",
        AssessmentsResponseStatusDownload.as_view(),
    ),
    path(
        "assessment/<int:assessment_id>/batch-and-project/",
        GetAssessmentBatchAndProject.as_view(),
    ),
    path(
        "download-question-wise-excel/<int:project_id>/",
        DownloadQuestionWiseExcelForProject.as_view(),
    ),
    path(
        "response-download-for-all-participants/<int:assessment_id>/",
        ResponseDownloadForAllParticipants.as_view(),
    ),
    path(
        "learner-assessment-result-image/<int:learner_id>/",
        views.get_learner_assessment_result_image,
    ),
    path(
        "add-user-as-a-participant-of-assessment/",
        views.add_user_as_a_participant_of_assessment,
    ),
    path(
        "add-competency-to-batch/<int:batch_id>/",
        views.add_competency_to_batch,
        name="add_competency_to_batch",
    ),
    path(
        "edit-competency-assignment/<int:batch_id>/<int:assignment_id>/",
        views.edit_competency_assignment,
        name="edit_competency_assignment",
    ),
    path(
        "get-batch-competency-assignments/<int:batch_id>/",
        views.get_batch_competency_assignments,
        name="get_batch_competency_assignments",
    ),
    path(
        "delete-batch-competency/<int:course_competency_id>/",
        views.delete_batch_competency,
        name="delete_batch_competency",
    ),
    path(
        "create-coaching-assessment-and-add-multiple-participants/",
        CreateCoachingAssessmentAndAddMultipleParticipants.as_view(),
    ),
    path(
        "get-assessment-of-coaching-project/<int:project_id>/",
        GetAssessmentOfCoachingProject.as_view(),
    ),
    path(
        "assessment/<int:assessment_id>/send-whatsapp-reminder/",
        views.send_whatsapp_reminder,
    ),
    path(
        "assessment/<int:assessment_id>/send-email-reminder/",
        views.send_email_reminder,
    ),
]
