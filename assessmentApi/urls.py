from django.urls import path, include

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
    AssessmentStatusOrEndDataChange,
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
    path(
        "assessment-status-end-data-change/", AssessmentStatusOrEndDataChange.as_view()
    ),
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
        "start-assessment-disabled/<str:unique_id>/",StartAssessmentDisabled.as_view(),
    ),
    path(
        "release-assessment-result/<int:assessment_id>/",ReleaseResults.as_view(),
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
]
