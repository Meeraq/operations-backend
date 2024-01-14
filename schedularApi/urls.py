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
    path(
        "add_learner_to_batch/<int:project_id>/",
        views.add_batch,
        name="add_learner_to_batch",
    ),
    path("coaches/", views.get_coaches),
    path("batch/<int:batch_id>/", views.update_batch),
    path(
        "create-coach-availibilty/",
        views.create_coach_schedular_availibilty,
    ),
    path(
        "schedular-availabilities/",
        views.get_all_schedular_availabilities,
    ),
    path("coach-availability/", views.get_coach_availabilities_booking_link),
    path("schedule-session/", views.schedule_session_fixed),
    path(
        "give_availibilty/",
        views.create_coach_availabilities,
    ),
    path(
        "get-availibilty/",
        views.get_coach_availabilities,
    ),
    path("sessions/", views.get_sessions),
    path("sessions/<str:sessions_type>/", views.get_sessions_by_type),
    path("sessions/status/update/<int:session_id>/", views.edit_session_status),
    path("sessions/time/update/<int:session_id>/", views.update_session_date_time),
    path(
        "current-session/<str:user_type>/<str:room_id>/<int:user_id>/",
        views.get_current_session,
    ),
    path(
        "learner-current-session/<str:room_id>/", views.get_current_session_of_learner
    ),
    path(
        "requests/<int:coach_id>/",
        views.get_requests_of_coach,
    ),
    path(
        "request/<int:request_id>/slots/",
        views.get_slots_of_request,
    ),
    path(
        "slots/upcoming/<int:coach_id>/",
        views.get_upcoming_slots_of_coach,
    ),
    path("slots/delete/", views.delete_slots),
    path(
        "existing_slots_of_coach/<int:request_id>/<int:coach_id>/",
        views.get_existing_slots_of_coach_on_request_dates,
    ),
    path("send_coaching_session_mail/", views.send_unbooked_coaching_session_mail),
    path("download_report/", views.export_available_slot),
    path(
        "create-schedular-participant/<int:batch_id>/", views.add_participant_to_batch
    ),
    path(
        "finalize-project-structure/<int:project_id>/",
        views.finalize_project_structure,
        name="finalize_project_structure",
    ),
    path("send_live_session_link/", views.send_live_session_link),
    path(
        "update-session-status/<int:session_id>/",
        views.update_session_status,
        name="update_session_status",
    ),
    path(
        "project-report-download/<int:project_id>/",
        views.project_report_download,
        name="project_report_download",
    ),
    path(
        "add-facilitator/",
        views.addFacilitator,
    ),
    path(
        "facilitators/",
        views.get_facilitators,
    ),
    path(
        "add-multiple-facilitator/",
        views.add_multiple_facilitator,
    ),
    path("facilitator/profile/<int:id>/", views.update_facilitator_profile),
    path("facilitator/delete/", views.delete_facilitator),
    path("facilitator-field-values/", views.get_facilitator_field_values),
    path(
        "delete-learner_from_course/",
        views.delete_learner_from_course,
    ),
    path("edit-project-schedular/<int:project_id>/", views.edit_schedular_project),
    path(
        "schedular-projects/<int:project_id>/updates/create/",
        views.add_schedular_project_update,
    ),
    path(
        "schedular-projects/<int:project_id>/updates/",
        views.get_schedular_project_updates,
    ),
]
