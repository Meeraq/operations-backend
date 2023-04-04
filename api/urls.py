from django.urls import path,include
from . import views

urlpatterns =[
	  path('pmos/',views.create_pmo),
		path('coaches/',views.coach_signup),
		path('coaches/all/',views.get_coaches),
		path('coaches/<int:coach_id>/approve/',views.approve_coach),
    path('pmo-login/', views.pmo_login, name='pmo-login'),
	  path('coach-login/', views.coach_login, name='coach-login'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('create-project/', views.create_project, name='create-project'),
    path('learner/', views.create_learner, name='learner'),
		path('get-coaches-by-project/', views.get_coaches_by_project, name='get-coaches-by-project'),
    path('get-learners-by-project/', views.get_learners_by_project, name='get-learners-by-project'),
		path('create_user_without_password/',views.create_user_without_password),
		path('generate-otp/', views.otp_generation, name='generate_otp'),
    path('validate-otp/', views.otp_validation, name='validate_otp'),
   	path('create-project/', views.create_project, name='create-project'),
    path('learner/', views.create_learner, name='learner'),
    path('projects/edit/<int:project_id>/',views.edit_project),
    path('projects/all/',views.get_projects),
    path('projects/ongoing/',views.get_ongoing_projects),
    path('projects/completed/',views.get_completed_projects),
    path('project-details/<int:project_id>/', views.project_details, name='project-details'),
    path('projects/learner/<int:learner_id>/',views.get_projects_of_learner),
    path('session-request/create/', views.create_session_request),
    path('session-requests/<int:coach_id>/', views.session_requests_by_coach),
    path('sessions/book/', views.book_session),
    path('sessions/upcoming/coach/<int:coach_id>/',views.get_upcoming_session_coach),
    path('sessions/past/coach/<int:coach_id>/',views.get_past_session_coach),
    path('sessions/upcoming/learner/<int:learner_id>/',views.get_upcoming_session_learner),
    path('sessions/past/learner/<int:learner_id>/',views.get_past_session_learner),
    path('add-learner/<int:project_id>/', views.add_learner),
    path('sessions/past/learner/<int:learner_id>/',views.get_past_session_learner),
    path('sessions/upcoming/',views.get_upcoming_session),
    path('sessions/past/',views.get_past_session),
		path('session-requests/all/', views.get_session_requests),
    path('management-token/',views.get_management_token),
    path('projects/complete/',views.complete_project),
    path('sessions/coach/join/',views.mark_coach_joined_session),
    path('sessions/learner/join/',views.mark_learner_joined_session),
    path('session-requests/count/', views.get_session_request_count),
    path('session-requests/pending/learner/<int:learner_id>/', views.get_pending_session_requests_by_learner),
		path('session-requests/all/learner/<int:learner_id>/', views.get_all_session_requests_by_learner),
		path('session-requests/delete/<int:session_request_id>/',views.delete_session_request),
    path('dashboard/',views.get_dashboard_details),
    path('coach-invites/all/',views.get_coach_invites),
    path('coach-invites/create/',views.invite_coach),
		path('project-and-sessions/coach/<int:coach_id>/',views.get_projects_and_sessions_by_coach),
		path('session-requests/all/learner/<int:learner_id>/', views.get_all_session_requests_by_learner),
    path('generate-otp-hr/', views.otp_generation_hr, name='generate_otp_hr'),
    path('validate-otp-hr/', views.otp_validation_hr, name='validate_otp_hr'),
    path('projects/ongoing/hr/<int:hr_id>/',views.get_ongoing_projects_of_hr),
    path('projects/completed/hr/<int:hr_id>/',views.get_completed_projects_of_hr),
    path('add-coach/', views.add_coach),
    path('hr/all/',views.get_hr),
		path('coaches/profile/<int:coach_id>/',views.update_coach_profile),
		path('add_hr/',views.create_hr),
		path('add_organisation/',views.add_organisation),
		path('get_organisation/',views.get_organisation),
		# path('filter_coach/',views.filter_coach),
    path('add_project_structure/',views.add_project_struture),
    path('send_consent/',views.send_consent),
] 
