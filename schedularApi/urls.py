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
    path("batch-details/<str:batch_id>/", views.get_batch_calendar),
    path(
        "live-sessions/<int:live_session_id>/update/",
        views.update_live_session,
        name="update_live_session",
    ),
    path(
        "coaching-sessions/<int:coaching_session_id>/update/",
        views.update_coaching_session,
        name="update_coaching_session",
    ),
]
