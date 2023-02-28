from django.urls import path, include
from . import views

urlpatterns =[
	  path('pmos/',views.create_pmo),
		path('coaches/',views.coach_signup),
		path('coaches/all/',views.get_coaches),
		path('coaches/<int:coach_id>/approve/',views.approve_coach),
    path('pmo-login/', views.pmo_login, name='pmo-login'),
	  path('coach-login/', views.coach_login, name='coach-login'),
    path('create-project/', views.create_project, name='create-project'),
    path('learner/', views.create_learner, name='learner'),
		path('get-coaches-by-project/', views.get_coaches_by_project, name='get-coaches-by-project'),
    path('get-learners-by-project/', views.get_learners_by_project, name='get-learners-by-project'),
		path('create_user_without_password/',views.create_user_without_password),
		path('generate-otp/', views.otp_generation, name='generate_otp'),
    path('validate-otp/', views.otp_validation, name='validate_otp'),
   	path('create-project/', views.create_project, name='create-project'),
    path('learner/', views.create_learner, name='learner'),
    path('projects/all/',views.get_projects),
    path('project-details/<int:project_id>/', views.project_details, name='project-details'),
    path('projects/learner/<int:learner_id>/',views.get_projects_of_learner),
    path('session-request/create/', views.create_session_request),
    path('session-requests/<int:coach_id>/', views.session_requests_by_coach),
    path('sessions/book/', views.book_session)
]    
