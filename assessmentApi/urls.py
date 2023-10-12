from django.urls import path, include
from . import views
from .views import (
    CompetencyView,
)

urlpatterns = [

    path('create-competency/', CompetencyView.as_view()),
    path('get-competencies/', CompetencyView.as_view()),
    path('delete-competency/', CompetencyView.as_view()),
    path('edit-competency/', CompetencyView.as_view()),
]