from django.urls import path, include
from . import views
from .views import GetAllBatchesCoachDetails, GetAllBatchesParticipantDetails

urlpatterns = [
    path(
        "schedular-projects/",
        views.get_all_Schedular_Projects,
        name="get-all-schedular-projects",
    ),
    path("create-benchmark/", views.create_benchmark, name="create_benchmark"),
    # path("edit-benchmark/", views.edit_benchmark, name="edit_benchmark"),
    path('update-benchmark/', views.update_benchmark, name='update_benchmark'),
    path("get-benchmark/", views.get_all_benchmarks),
    path("create-gmsheet/", views.create_gmsheet, name="create_gmsheet"),
    path("update-status/", views.update_status, name="update-status"),
    path("update-gmsheet/<int:id>/", views.update_gmsheet),
    path(
        "accept-gmsheet/<int:pk>/",
        views.update_is_accepted_status,
        name="update_is_accepted_status",
    ),
    path("delete-gmsheet/", views.delete_gmsheet, name="delete_gmsheet"),
    path("all-gmsheet/", views.get_all_gmsheet),
    path(
        "offerings/<int:gmsheet_id>/",
        views.get_offerings_by_gmsheet_id,
        name="offerings-list",
    ),
    path("gmsheet/maxNumber/", views.max_gmsheet_number, name="max_gmsheet_number"),
    path("asset/maxNumber/", views.max_asset_number, name="max_asset_number"),
    path("gmsheet-by-sales/<int:sales_person_id>", views.get_gmsheet_by_sales),
    path('create-employee/', views.create_employee, name='employee-create'),
    path('employees/', views.get_employees, name='get_employees'),
    path('update-employee/', views.update_employee, name='update_employee'),
    path('delete-employee/', views.delete_employee, name='delete_employee'),

    path(
        "current-or-next-year/",
        views.get_current_or_next_year,
        name="current_or_next_year",
    ),
    path(
        "create_project_structure/<int:project_id>/",
        views.create_project_structure,
        name="create_project_structure",
    ),
    path("create-project-schedular/", views.create_project_schedular),
    path("handover/<str:project_type>/<int:project_id>/", views.get_project_handover),
    path("handover/create/", views.create_handover),
    path("handover/update/", views.update_handover),
    path("handover/<int:handover_id>/salesorders/", views.get_handover_salesorders),
    path("create-assets/", views.create_asset),
    path("assets/", views.get_all_assets),
    path("delete-asset/", views.delete_asset, name="delete_asset"),
    path("update-asset/", views.update_asset, name="update_asset"),
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
    path(
        "get-learner-by-project/<str:project_type>/<int:project_id>/",
        views.get_learner_by_project,
    ),
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
    path("batches/get/<int:batch_id>/", views.get_batch),
    path(
        "create-coach-availibilty/",
        views.create_coach_schedular_availibilty,
    ),
    path(
        "edit-slot-request/<int:request_id>/",
        views.edit_slot_request,
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
    # path("facilitator/delete/", views.delete_facilitator),
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
        "coach-inside-skill-training-or-not/<int:project_id>/<str:batch_id>/",
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
        "get-skill-dashboard-card-data-for-facilitator/<str:project_id>/<int:facilitator_id>/",
        views.get_skill_dashboard_card_data_for_facilitator,
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
    path(
        "get-project-wise-progress-data/<int:project_id>/",
        views.get_project_wise_progress_data,
    ),
    path(
        "requests/delete/<int:request_id>/",
        views.delete_request_with_availabilities,
        name="delete_request_with_availabilities",
    ),
    path(
        "get-session-progress-data-for-dashboard/<int:project_id>/",
        views.get_session_progress_data_for_dashboard,
    ),
    path(
        "get-coach-session-progress-data-for-skill-training-project/<int:batch_id>/",
        views.get_coach_session_progress_data_for_skill_training_project,
    ),
    path(
        "projects/facilitators-and-pricing/<str:project_id>/",
        views.get_facilitators_and_pricing_for_project,
    ),
    path(
        "projects/coaches-and-pricing/<str:project_id>/",
        views.get_coaches_and_pricing_for_project,
    ),
    path(
        "facilitator_pricing/",
        views.add_facilitator_pricing,
        name="add_facilitator_pricing",
    ),
    path(
        "facilitator_pricing/<int:facilitator_pricing_id>/",
        views.edit_facilitator_pricing,
        name="edit_facilitator_pricing",
    ),
    path("create-expense/", views.create_expense),
    path("edit-expense/", views.edit_expense),
    path(
        "expenses/<int:batch_or_project_id>/<str:usertype>/<int:user_id>/",
        views.get_expense_for_facilitator,
    ),
    path(
        "edit-status-expense/",
        views.edit_status_expense,
    ),
    path(
        "edit-amount-expense/",
        views.edit_expense_amount,
    ),
    path(
        "edit-amount-expense/",
        views.edit_expense_amount,
    ),
    path(
        "get-all-courses-for-all-batches/<int:project_id>/",
        views.get_all_courses_for_all_batches,
        name="get_all_courses_for_all_batches",
    ),
    path(
        "get-card-data-for-coach-in-skill-project/<int:project_id>/<int:coach_id>",
        views.get_card_data_for_coach_in_skill_project,
    ),
    path(
        "projects/<int:project_id>/check-project-structure-edit-allowed/",
        views.check_if_project_structure_edit_allowed,
    ),
    path(
        "get-upcoming-coaching-and-live-session-data-for-learner/<int:user_id>/",
        views.get_upcoming_coaching_and_live_session_data_for_learner,
    ),
    path(
        "get-upcoming-assessment-data/<int:user_id>/",
        views.get_upcoming_assessment_data,
    ),
    path(
        "get-just-upcoming-session-data/<int:user_id>/",
        views.get_just_upcoming_session_data,
    ),
    path(
        "get-all-project-purchase-orders-for-finance/<int:project_id>/<str:project_type>/",
        views.get_all_project_purchase_orders_for_finance,
    ),
    path(
        "get-project-and-handover/",
        views.get_project_and_handover,
        name="get_project_and_handover",
    ),
    path("handovers/<int:sales_id>/", views.get_handovers, name="get_handovers"),
    path(
        "send-mail-to-coaches/", views.send_mail_to_coaches, name="send_mail_to_coaches"
    ),
    path("handovers/pmo/", views.get_pmo_handovers, name="get_handovers"),
    path(
        "update-reminder-in-batch/<int:batch_id>/",
        views.update_reminder_in_batch,
        name="update_reminder_in_batch",
    ),
    path("action-items/add/", views.add_action_item, name="add_action_item"),
    path(
        "action-items/edit/<int:pk>/", views.edit_action_item, name="edit_action_item"
    ),
    path(
        "action-items/update-status/<int:pk>/",
        views.update_action_item_status,
        name="update_action_item_status",
    ),
    path(
        "action-items/delete/<int:pk>/",
        views.delete_action_item,
        name="delete_action_item",
    ),
    path("batches/learner/<int:pk>/", views.learner_batches, name="learner_batches"),
    path(
        "batch/action-items/<int:batch_id>/<int:learner_id>/<int:competency_id>/<int:behavior_id>/",
        views.learner_action_items_in_batch_of_competency_and_behavior,
        name="learner_action_items_in_batch",
    ),
    path(
        "batch/action-items/<int:batch_id>/<int:learner_id>/",
        views.learner_action_items_in_batch,
        name="learner_action_items_in_batch",
    ),
    path(
        "action-items/session/<int:session_id>/",
        views.learner_action_items_in_session,
        name="learner_action_items_in_session",
    ),
    path(
        "batch/action-items/<int:batch_id>/",
        views.action_items_in_batch,
        name="action_items_in_batch",
    ),
    path(
        "batch/competencies-and-behaviours/<int:batch_id>/",
        views.batch_competencies_and_behaviours,
        name="batch_competencies_and_behaviours",
    ),
    path(
        "batch/<int:batch_id>/competency/<int:competency_id>/behavior/<int:behavior_id>/movement/",
        views.batch_competency_behavior_movement,
    ),
    path(
        "batch/<int:batch_id>/competency/<int:competency_id>/movement/",
        views.batch_competency_movement,
    ),
    path(
        "all-actions/",
        views.get_all_action_items,
    ),
    path(
        "actions/<int:hr_id>/",
        views.get_all_action_items_hr,
    ),
    path(
        "get-batch-wise-assessment-data/<str:type>/<int:pk>/",
        views.get_all_assessments_of_batch,
        name="get_all_assessments_of_batch",
    ),
    path(
        "get-upcoming-past-live-session-facilitator/<int:user_id>/",
        views.get_upcoming_past_live_session_facilitator,
    ),
    path('get-upcoming-conflicting-sessions/', views.get_upcoming_conflicting_sessions, name='get_upcoming_conflicting_sessions'),
]
