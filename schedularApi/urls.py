from django.urls import path, include
from . import views


urlpatterns = [
    path(
        "schedular-projects/",
        views.get_all_Schedular_Projects,
        name="get-all-schedular-projects",
    ),
    path(
        "create_project_structure/<int:project_id>/",
        views.create_project_structure,
        name="create_project_structure",
    ),
    path("create-project-schedular/", views.create_project_schedular),
    path(
        "create-schedular-participant/",
        views.create_schedular_participant,
        name="create-schedular-participant",
    ),
    path(
        "schedular-batches/",
        views.get_schedular_batches,
        name="schedular-batch-list",
    ),
    path(
        "schedular-project/<int:project_id>/",
        views.get_schedular_project,
        name="schedular-batch-list",
    ),
    path("batch-calendar/<str:batch_id>/", views.get_batch_calendar),
]
