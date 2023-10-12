from django.urls import path, include
from . import views
from .views import CompetencyView, QuestionView, QuestionnaireView

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
]
