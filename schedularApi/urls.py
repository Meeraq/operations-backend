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
    path(
        "pending-scheduled-mails/<int:email_template_id>/",
        views.pending_scheduled_mails_exists,
    ),
    path("edit_email_template/<int:template_id>/", views.editEmailTemplate),
    path("save_template/", views.addEmailTemplate),
    path("send_test_mails/", views.send_test_mails),
    path("get-learner-by-batch/<str:batch_id>/", views.participants_list),
    path("saved_emailsTemplates/", views.getSavedTemplates),
    path("all_batches/", views.get_batches, name="batch-list"),
    path("send_mails/", views.send_mails),
    path("emails-data/", views.get_mail_data),
    path("cancel-schedule-email/<int:sent_mail_id>/", views.cancel_scheduled_mail),
    path("delete_email_template/<int:template_id>/", views.deleteEmailTemplate),
    path('add_learner_to_batch/<int:project_id>/', views.add_batch, name='add_learner_to_batch'),
    path("coaches/", views.get_coaches),
    path("batch/<int:batch_id>/",views.update_batch)
]
