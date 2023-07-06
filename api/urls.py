from django.urls import path, include
from . import views

urlpatterns = [
    path("pmos/", views.create_pmo),
    path("coaches/", views.coach_signup),
    path("coaches/all/", views.get_coaches),
    path("coaches/<int:coach_id>/approve/", views.approve_coach),
    path("pmo-login/", views.pmo_login, name="pmo-login"),
    path("coach-login/", views.coach_login, name="coach-login"),
    path(
        "password_reset/",
        include("django_rest_passwordreset.urls", namespace="password_reset"),
    ),
    # path('create-project/', views.create_project, name='create-project'),
    # path('learner/', views.create_learner, name='learner'),
    # path('get-coaches-by-project/', views.get_coaches_by_project, name='get-coaches-by-project'),
    # path('get-learners-by-project/', views.get_learners_by_project, name='get-learners-by-project'),
    # path('create_user_without_password/',views.create_user_without_password),
    # path('generate-otp/', views.otp_generation, name='generate_otp'),
    # path('validate-otp/', views.otp_validation, name='validate_otp'),
    # path('create-project/', views.create_project, name='create-project'),
    # path('learner/', views.create_learner, name='learner'),
    # path('projects/edit/<int:project_id>/',views.edit_project),
    # path('projects/all/',views.get_projects),
    path("projects/ongoing/", views.get_ongoing_projects),
    # path('projects/completed/',views.get_completed_projects),
    # path('project-details/<int:project_id>/', views.project_details, name='project-details'),
    path("projects/learner/<int:learner_id>/", views.get_projects_of_learner),
    # path('session-request/create/', views.create_session_request),
    # path('session-requests/<int:coach_id>/', views.session_requests_by_coach),
    # path('sessions/book/', views.book_session),
    # path('sessions/upcoming/coach/<int:coach_id>/',views.get_upcoming_session_coach),
    # path('sessions/past/coach/<int:coach_id>/',views.get_past_session_coach),
    # path('sessions/upcoming/learner/<int:learner_id>/',views.get_upcoming_session_learner),
    # path('sessions/past/learner/<int:learner_id>/',views.get_past_session_learner),
    # path('add-learner/<int:project_id>/', views.add_learner),
    # path('sessions/past/learner/<int:learner_id>/',views.get_past_session_learner),
    # path('sessions/upcoming/',views.get_upcoming_session),
    # path('sessions/past/',views.get_past_session),
    # path('session-requests/all/', views.get_session_requests),
    path("management-token/", views.get_management_token),
    # path('projects/complete/',views.complete_project),
    # path('sessions/coach/join/',views.mark_coach_joined_session),
    # path('sessions/learner/join/',views.mark_learner_joined_session),
    # path('session-requests/count/', views.get_session_request_count),
    # path('session-requests/pending/learner/<int:learner_id>/', views.get_pending_session_requests_by_learner),
    # path('session-requests/all/learner/<int:learner_id>/', views.get_all_session_requests_by_learner),
    # path('session-requests/delete/<int:session_request_id>/',views.delete_session_request),
    # path('dashboard/',views.get_dashboard_details),
    # path('coach-invites/all/',views.get_coach_invites),
    # path('coach-invites/create/',views.invite_coach),
    path(
        "project-and-sessions/coach/<int:coach_id>/",
        views.get_projects_and_sessions_by_coach,
    ),
    # path('session-requests/all/learner/<int:learner_id>/', views.get_all_session_requests_by_learner),
    # path('generate-otp-hr/', views.otp_generation_hr, name='generate_otp_hr'),
    # path('validate-otp-hr/', views.otp_validation_hr, name='validate_otp_hr'),
    path("projects/ongoing/hr/<int:hr_id>/", views.get_ongoing_projects_of_hr),
    # path('projects/completed/hr/<int:hr_id>/',views.get_completed_projects_of_hr),
    path("add-coach/", views.add_coach),
    path("hr/all/", views.get_hr),
    path("coaches/profile/<int:coach_id>/", views.update_coach_profile),
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
    path("notifications/unread-count/<int:user_id>/", views.unread_notification_count),
    path("mark_project_as_sold/", views.mark_project_as_sold),
    path(
        "session-requests-of-user-on-date/<str:user_type>/<int:user_id>/<str:date>/",
        views.get_session_requests_of_user_on_date,
    ),
    path("session/reschedule-request/<str:session_id>/", views.request_reschedule),
    path("session/reschedule/", views.reschedule_session),
    path("projects/engagement/all/<int:project_id>/", views.get_engagement_in_projects),
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
        "sessions/upcoming/<str:user_type>/<int:user_id>/",
        views.get_upcoming_sessions_of_user,
    ),
    path(
        "sessions/past/<str:user_type>/<int:user_id>/", views.get_past_sessions_of_user
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
    path("competency/", views.create_competency),
    path("competency/<int:engagement_id>/", views.get_engagement_competency),
    path(
        "competency/score/<int:competency_id>/",
        views.add_score_to_competency,
        name="create_score_competency",
    ),
    path("action-items/", views.create_action_item),
    path("action-items/<int:engagement_id>/", views.get_engagement_action_items),
    path(
        "action-items/edit/<int:action_item_id>/",
        views.edit_action_item,
        name="edit_action_item",
    ),
    path(
        "session/complete/<int:session_id>/",
        views.mark_session_as_complete,
    ),
    path(
        "engagement/complete/<int:engagement_id>/",
        views.complete_engagement,
    ),
]
