from django.urls import path, include
from . import views

urlpatterns =[
	  path('pmos/',views.create_pmo),
		path('coaches/',views.coach_signup),
		path('coaches/all/',views.get_coaches),
		path('coaches/<int:coach_id>/approve/',views.approve_coach),
    path('pmo-login/', views.pmo_login, name='pmo-login'),
	  path('coach-login/', views.coach_login, name='coach-login'),
		path('create_user_without_password/',views.create_user_without_password),
		path('generate-otp/', views.otp_generation, name='generate_otp'),
    path('validate-otp/', views.otp_validation, name='validate_otp'),
    path('create-project/', views.create_project, name='create-project'),
    path('learner/', views.create_learner, name='learner') 
]