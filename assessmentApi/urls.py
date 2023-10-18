from django.urls import path, include
from . import views
from .views import CompetencyView, QuestionView, QuestionnaireView,AssessmentView,AssessmentStatusOrTypeOrEndDataChange

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
    path("assessment-status-type-end-data-change/", AssessmentStatusOrTypeOrEndDataChange.as_view()), 
]
