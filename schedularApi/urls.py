from django.urls import path, include
from . import views
from .views import GetAllBatchesCoachDetails, GetAllBatchesParticipantDetails

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
    path("reschedule-session/<int:session_id>/", views.reschedule_session),
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
    path("send-live-session-link-whatsapp/", views.send_live_session_link_whatsapp),
    path(
        "update-session-status/<int:session_id>/",
        views.update_session_status,
        name="update_session_status",
    ),
    path(
        "project-batch-wise-report-download/<int:project_id>/<str:session_to_download>/",
        views.project_batch_wise_report_download,
        name="project_batch_wise_report_download",
    ),
    path(
        "project-report-download-live-session-wise/<int:project_id>/<str:batch_id>/",
        views.project_report_download_live_session_wise,
        name="project_report_download_session_wise",
    ),
    path(
        "project-report-download-coaching-session-wise/<int:project_id>/<str:batch_id>/",
        views.project_report_download_coaching_session_wise,
        name="project_report_download_session_wise",
    ),
    path(
        "add-facilitator/",
        views.add_facilitator,
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
    path("live-sessions/", views.get_live_sessions_by_status),
    path(
        "live-session/<int:pk>/",
        views.live_session_detail_view,
    ),
    path(
        "facilitators/<int:facilitator_id>/batches_and_projects/",
        views.facilitator_projects,
        name="facilitator_batches_projects",
    ),
    path(
        "facilitators/<int:facilitator_id>/sessions/",
        views.get_facilitator_sessions,
    ),
    path(
        "update-certificate-status/",
        views.update_certificate_status,
    ),
    path(
        "add-new-session-in-project-structure/",
        views.add_new_session_in_project_structure,
    ),
    path(
        "delete-session-from-project-structure/",
        views.delete_session_from_project_structure,
    ),
    path(
        "get-completed-sessions-for-project/<int:project_id>/",
        views.get_completed_sessions_for_project,
    ),
    path(
        "update-certificate-status-for-multiple-participants/",
        views.update_certificate_status_for_multiple_participants,
    ),
    path(
        "batches-coach-details/<int:project_id>/", GetAllBatchesCoachDetails.as_view()
    ),
    path(
        "batches-learner-details/<int:project_id>/",
        GetAllBatchesParticipantDetails.as_view(),
    ),
    path(
        "coach-inside-skill-training-or-not/<str:batch_id>/",
        views.coach_inside_skill_training_or_not,
    ),
    path(
        "facilitator-inside-that-batch/<str:batch_id>/",
        views.facilitator_inside_that_batch,
    ),
    path(
        "delete-coach-from-that-batch/",
        views.delete_coach_from_that_batch,
    ),
    path(
        "delete-facilitator-from-that-batch/",
        views.delete_facilitator_from_that_batch,
    ),
    path(
        "update-project-status/",
        views.update_project_status,
    ),
    path(
        "get-skill-dashboard-card-data/<str:project_id>/",
        views.get_skill_dashboard_card_data,
    ),
    path(
        "get-past-live-session-dashboard-data/<str:project_id>/",
        views.get_past_live_session_dashboard_data,
    ),
    path(
        "get-upcoming-live-session-dashboard-data/<str:project_id>/",
        views.get_upcoming_live_session_dashboard_data,
    ),
    path(
        "get-upcoming-coaching-session-dashboard-data/<str:project_id>/",
        views.get_upcoming_coaching_session_dashboard_data,
    ),
    path(
        "get-past-coaching-session-dashboard-data/<str:project_id>/",
        views.get_past_coaching_session_dashboard_data,
    ),
    path(
        "pre-post-assessment-or-nudge-update-in-project/",
        views.pre_post_assessment_or_nudge_update_in_project,
    ),
    path(
        "get-all-coach-of-project-or-batch/<str:project_id>/<str:batch_id>/",
        views.get_all_coach_of_project_or_batch,
    ),
    path(
        "get-slots-based-on-project-batch-coach/<str:project_id>/<str:batch_id>/<str:coach_id>/",
        views.get_slots_based_on_project_batch_coach,
    ),
    path("batch/add-facilitator/<int:batch_id>/", views.add_facilitator_to_batch),
    path(
        "get-sessions-pricing-for-a-coach/<int:coach_id>/<int:project_id>/",
        views.get_sessions_pricing_for_a_coach,
    ),
    path(
        "get-sessions-pricing-for-a-facilitator/<int:facilitator_id>/<int:project_id>/",
        views.get_sessions_pricing_for_a_facilitator,
    ),
    path(
        "update-facilitator-price/<int:facilitator_price_id>/",
        views.update_facilitator_price,
    ),
    path(
        "update-coach-price/<int:coach_price_id>/",
        views.update_coach_price,
    ),
    path(
        "update-price-in-project-structure/",
        views.update_price_in_project_structure,
    ),
    path("batches/facilitators/<str:batch_id>/", views.show_facilitator_inside_courses),
]
