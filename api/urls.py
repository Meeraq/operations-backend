from django.urls import path, include
from . import views
from .views import (
    UpdateInviteesView,
    SessionCountsForAllLearners,
    SessionsProgressOfAllCoacheeForAnHr,
    AddRegisteredCoach,
    ActivitySummary,
    StandardizedFieldAPI,
    StandardizedFieldRequestAPI,
    StandardFieldAddValue,
    StandardFieldEditValue,
    StandardFieldDeleteValue,
    StandardizedFieldRequestAcceptReject,
    ProjectContractAPIView,
    CoachContractList,
    CoachContractDetail,
    AssignCoachContractAndProjectContract,
    ProjectContractDetailView,
    UpdateCoachContract,
    ApprovedCoachContract,
    SendContractReminder,
    CoachWithApprovedContractsInProject,
    UserTokenAvaliableCheck,
)

urlpatterns = [
    path("pmos/", views.create_pmo),
    path("coaches/", views.coach_signup),
    path("coaches/all/", views.get_coaches),
    path("coaches/approve/", views.approve_coach),
    path("pmo-login/", views.pmo_login, name="pmo-login"),
    path("coach-login/", views.coach_login, name="coach-login"),
    path(
        "password_reset/",
        include("django_rest_passwordreset.urls", namespace="password_reset"),
    ),
    path("projects/ongoing/", views.get_ongoing_projects),
    path("projects/<int:project_id>/updates/", views.get_project_updates),
    path("projects/<int:project_id>/updates/create/", views.add_project_update),
    path("projects/learner/<int:learner_id>/", views.get_projects_of_learner),
    path("management-token/", views.get_management_token),
    path(
        "project-and-sessions/coach/<int:coach_id>/",
        views.get_projects_and_sessions_by_coach,
    ),
    path("projects/ongoing/hr/<int:hr_id>/", views.get_ongoing_projects_of_hr),
    # path('projects/completed/hr/<int:hr_id>/',views.get_completed_projects_of_hr),
    path("add-coach/", views.add_coach),
    path("hr/all/", views.get_hr),
    path("coaches/profile/<int:id>/", views.update_coach_profile),
    path("csrf/", views.get_csrf, name="api-csrf"),
    path("login/", views.login_view, name="api-login"),
    path("logout/", views.logout_view, name="api-logout"),
    path("session/", views.session_view, name="api-session"),
    path("otp/generate/", views.generate_otp),
    path("otp/validate/", views.validate_otp),
    path("add_hr/", views.add_hr),
    path("add_organisation/", views.add_organisation),
    path("get_organisation/", views.get_organisation),
    path("create-project-cass/", views.create_project_cass),
    path("add_project_structure/", views.add_project_struture),
    path("send_consent/", views.send_consent),
    # path('select_coaches/',views.select_coaches),
    path("project/caas/<int:project_id>/", views.get_project_details),
    # path('filter_coach/',views.filter_coach),
    path("receive_coach_consent/", views.receive_coach_consent),
    path(
        "coach/update_project_structure_consent/",
        views.update_project_structure_consent_by_coach,
    ),
    path("complete_coach_consent/", views.complete_coach_consent),
    path("get-interview-data/<int:project_id>/", views.get_interview_data),
    path("sessions/book/caas", views.book_session_caas),
    path("session-request-caas/create/", views.create_session_request_caas),
    path("complete_coach_list_to_hr/", views.complete_coach_list_to_hr),
    path("complete-interview-step/", views.complete_interviews_step),
    path("send_list_to_hr/", views.send_list_to_hr),
    path("session-requests-caas/all/hr/<int:hr_id>/", views.get_session_requests_of_hr),
    path(
        "session-requests-caas/all/coach/<int:coach_id>/",
        views.get_session_requests_of_coach,
    ),
    path("accept-coach-caas/hr", views.accept_coach_caas_hr),
    path("accept-coach-caas/learner", views.accept_coach_caas_learner),
    path("complete_empanelment/", views.complete_empanelment),
    # path('complete-interview/',views.complete_interview),
    path("complete-project-structure/", views.complete_project_structure),
    # path('complete-coach-approval/',views.complete_coach_approval),
    # path('complete-chemistry-sessions/',views.complete_chemistry_sessions),
    path("complete-caas-step/", views.complete_cass_step),
    path(
        "session-requests-caas/all/learner/<int:learner_id>/",
        views.get_session_requests_of_learner,
    ),
    path("projects/learners/add/", views.add_learner_to_project),
    # path('send_contract/',views.send_contract),
    # path('approve-contract/',views.approve_contract),
    path(
        "get-chemistry-session-data/<int:project_id>/", views.get_chemistry_session_data
    ),
    path("mark_as_incomplete/", views.mark_as_incomplete),
    path("send_project_strure_to_hr/", views.send_project_strure_to_hr),
    path("send_reject_reason/", views.send_reject_reason),
    path("project_structure_agree_by_hr/", views.project_structure_agree_by_hr),
    path("request_more_profiles_by_hr/", views.request_more_profiles_by_hr),
    path("edit_learner/", views.edit_learner),
    path("mark-finalized-list-complete/", views.mark_finalized_list_complete),
    path(
        "finalized-coach-from-coach-consent/", views.finalized_coach_from_coach_consent
    ),
    path(
        "upcoming-booked-session/coach/<int:coach_id>/",
        views.get_upcoming_booked_session_of_coach,
    ),
    path("coach-field-values/", views.get_coach_field_values),
    path("add-multiple-coaches/", views.add_mulitple_coaches),
    path("coach/delete/", views.delete_coach),
    path("notifications/all/<int:user_id>/", views.get_notifications),
    path("notifications/mark-as-read/", views.mark_notifications_as_read),
    path("notifications/mark-all-as-read/", views.mark_all_notifications_as_read),
    path("notifications/unread-count/<int:user_id>/", views.unread_notification_count),
    path("mark_project_as_sold/", views.mark_project_as_sold),
    path(
        "session-requests-of-user-on-date/<str:user_type>/<int:user_id>/<str:date>/",
        views.get_session_requests_of_user_on_date,
    ),
    path("session/reschedule-request/<str:session_id>/", views.request_reschedule),
    path("session/reschedule/", views.reschedule_session),
    path("projects/engagement/all/<int:project_id>/", views.get_engagement_in_projects),
    path("hr/engagement/all/<int:user_id>/", views.get_engagements_of_hr),
    path(
        "engagement/<int:project_id>/<int:learner_id>/",
        views.get_learner_engagement_of_project,
    ),
    path("engagement/learner/<int:learner_id>/", views.get_learners_engagement),
    path("sessions/create/<int:learner_id>/", views.create_session_request_by_learner),
    path(
        "sessions/requested/<str:user_type>/<int:user_id>/",
        views.get_session_requests_of_user,
    ),
    path(
        "sessions/pending/<str:user_type>/<int:user_id>/",
        views.get_session_pending_of_user,
    ),
    path(
        "sessions/all/<str:user_type>/<int:user_id>/",
        views.get_all_sessions_of_user,
    ),
    path(
        "sessions/upcoming/<str:user_type>/<int:user_id>/",
        views.get_upcoming_sessions_of_user,
    ),
    path(
        "new/sessions/upcoming/<str:user_type>/<int:user_id>/",
        views.new_get_upcoming_sessions_of_user,
    ),
    path(
        "sessions/past/<str:user_type>/<int:user_id>/", views.get_past_sessions_of_user
    ),
     path(
        "new/sessions/past/<str:user_type>/<int:user_id>/", views.new_get_past_sessions_of_user
    ),
    path("sessions/edit/<int:session_id>/", views.edit_session_availability),
    path("learners/<str:user_type>/<int:user_id>/", views.get_coachee_of_user),
    path("learner/<int:learner_id>/", views.get_learner_data),
    path(
        "session/request/chemistry/<int:project_id>/<int:learner_id>/",
        views.request_chemistry_session,
    ),
    path(
        "session/<int:project_id>/<int:learner_id>/",
        views.get_learner_sessions_in_project,
    ),
    path("session/request/<int:session_id>/<int:coach_id>/", views.request_session),
    path("session/reschedule/<int:session_id>/", views.reschedule_session_of_coachee),
    path("sessions/edit/<int:session_id>/", views.edit_session_availability),
    path("goals/", views.create_goal),
    path("goals/<int:engagement_id>/", views.get_engagement_goals),
    path("goals/edit/<int:goal_id>/", views.edit_goal, name="edit_goal"),
    path("goals/delete/<int:goal_id>/", views.delete_goal, name="delete_goal"),
    path("competency/", views.create_competency),
    path(
        "competency/edit/<int:competency_id>/",
        views.edit_competency,
        name="edit_competency",
    ),
    path(
        "competency/delete/<int:competency_id>/",
        views.delete_competency,
        name="delete_competency",
    ),
    path("competency/<int:engagement_id>/", views.get_engagement_competency),
    path(
        "competency/score/<int:competency_id>/",
        views.add_score_to_competency,
        name="create_score_competency",
    ),
    path("action-items/", views.create_action_item),
    path("action-items/<int:engagement_id>/", views.get_engagement_action_items),
    path(
        "action_items/edit/<int:action_item_id>/",
        views.edit_action_item,
        name="edit_action_item",
    ),
    path(
        "action-items/delete/<int:action_item_id>/",
        views.delete_action_item,
        name="delete_action_item",
    ),
    path(
        "session/complete/<int:session_id>/",
        views.mark_session_as_complete,
    ),
    path("sessions/status/update/<int:session_id>/", views.edit_session_status),
    path(
        "engagement/<str:status>/<int:engagement_id>/",
        views.update_engagement_status,
    ),
    path(
        "all/competency/",
        views.get_all_competencies,
    ),
    path(
        "current-session/<str:user_type>/<str:room_id>/<int:user_id>/",
        views.get_current_session,
    ),
    path(
        "current-session/stakeholder/<str:room_id>/",
        views.get_current_session_of_stakeholder,
    ),
    path("competency/goal/<int:goal_id>/", views.get_competency_by_goal),
    path(
        "action-items/competency/<int:competency_id>/",
        views.get_action_items_by_competency,
    ),
    path(
        "action_items/pending/competency/<int:learner_id>/",
        views.get_pending_action_items_by_competency,
    ),
    path("sessions/direct-schedule/<int:session_id>/", views.schedule_session_directly),
    path("learner/delete/<int:engagement_id>/", views.delete_learner_from_project),
    path("competency/averages/<int:hr_id>/", views.get_competency_averages),
    path("upcoming-sessions/count/<int:hr_id>/", views.get_upcoming_session_count),
    path("requests/count/<int:hr_id>/", views.get_requests_count),
    path("completed-sessions/count/<int:hr_id>/", views.get_completed_sessions_count),
    path("idle-coachee/<int:hr_id>/", views.get_learners_without_sessions),
    path("engagement/select-coach-for-coachee/", views.select_coach_for_coachee),
    path("add-past-session/<int:session_id>/", views.add_past_session),
    path("reset_consent/", views.reset_consent),
    path("update_organisation/<int:org_id>/", views.update_organisation),
    path("update_hr/<int:hr_id>/", views.update_hr),
    path("delete_hr/<int:hr_id>/", views.delete_hr),
    path(
        "learner_completed_sessions/count/<int:learner_id>/",
        views.get_completed_learner_sessions_count,
    ),
    path(
        "learner_total_goals/count/<int:learner_id>/", views.get_total_goals_for_learner
    ),
    path(
        "learner_total_competency/count/<int:learner_id>/",
        views.get_total_competencies_for_learner,
    ),
    path(
        "learner_competencies/<int:learner_id>/", views.get_learner_competency_averages
    ),
    path("update-invitee/<int:session_request_id>/", UpdateInviteesView.as_view()),
    path("hr/<int:hr_id>/competencies/", views.get_all_competencies_of_hr),
    path("coach/<int:coach_id>/sessions/", views.coach_session_list),
    path("projects/<int:project_id>/coaches/", views.remove_coach_from_project),
    path(
        "coachee-session-counts/<str:user_type>/<int:user_id>/",
        SessionCountsForAllLearners.as_view(),
    ),
    path(
        "sessions-progress-of-all-coachee-for-an-hr/<int:user_id>/",
        SessionsProgressOfAllCoacheeForAnHr.as_view(),
    ),
    path(
        "coaches-which-are-included-in-projects/",
        views.coaches_which_are_included_in_projects,
    ),
    path("add_registered_coach/", AddRegisteredCoach.as_view()),
    path("get-registered-coaches/", views.get_registered_coaches),
    path("edit-project-caas/<int:project_id>/", views.edit_project_caas),
    path(
        "pmo-dashboard/",
        views.get_all_engagements,
    ),
    path("activity-summary/", ActivitySummary.as_view()),
    path("send-reset-password-link/", views.send_reset_password_link),
    path("coach-profile-templates/", views.create_coach_profile_template),
    path("project/<int:project_id>/data/", views.get_coach_profile_template),
    path("project-status-changing/<int:project_id>/", views.project_status),
    path("completed-projects/<int:user_id>/", views.completed_projects),
    path("standard_field/<int:user_id>/", views.standard_field_request),
    path("standardized-fields/", StandardizedFieldAPI.as_view()),
    path("standardized-field-requests/", StandardizedFieldRequestAPI.as_view()),
    path("standard-field-add-value/", StandardFieldAddValue.as_view()),
    path("standard-field-edit-value/", StandardFieldEditValue.as_view()),
    path(
        "standardized-field-request-accept-reject/",
        StandardizedFieldRequestAcceptReject.as_view(),
    ),
    path("standard-field-delete-value/", StandardFieldDeleteValue.as_view()),

    path("projects/<int:project_id>/coaches/", views.remove_coach_from_project),
    path("templates/", views.template_list_create_view),
    path("templates/<int:pk>/", views.template_retrieve_update_destroy_view),
    path("create-project-contract/", views.create_project_contract),
    path("get-project-contracts/", ProjectContractAPIView.as_view()),
    path("coach-contracts/", CoachContractList.as_view()),
    path("coach-contracts/<int:pk>/", CoachContractDetail.as_view()),
    path("handle-assign/", AssignCoachContractAndProjectContract.as_view()),
    path("project-contracts/<int:project_id>/", ProjectContractDetailView.as_view()),
    path("update-contract/", UpdateCoachContract.as_view()),
    path("send-contract-reminder/", SendContractReminder.as_view()),
    path(
        "get-approved-coach-contract/<int:project_id>/<int:coach_id>/",
        ApprovedCoachContract.as_view(),
    ),
    path(
        "coaches-with-approved-contracts-in-project/<int:project_id>/",
        CoachWithApprovedContractsInProject.as_view(),
    ),
    path('google/oauth/<str:user_email>/', views.google_oauth, name='google_oauth'),
    path('google-auth-callback/', views.google_auth_callback, name='google_auth_callback'),
    path('microsoft/oauth/<str:user_mail_address>/', views.microsoft_auth),
    path('microsoft-auth-callback/', views.microsoft_callback),
    path(
        "user-token-avaliable-check/<str:user_mail>/",
        UserTokenAvaliableCheck.as_view(),
    ),


   
]
