from django.urls import path, include
from . import views

urlpatterns =[
	  	path('pmos/',views.create_pmo),
		path('coaches/',views.coach_signup),
		path('coaches/all/',views.get_coaches),
		path('coaches/<int:coach_id>/approve/',views.approve_coach),
    	path('pmo-login/', views.pmo_login, name='pmo-login'),
	  	path('coach-login/', views.coach_login, name='coach-login'),
    	path('pmo-login/', views.pmo_login, name='pmo-login'),
        path('create-project/', views.create_project, name='create-project'),
        path('learner/', views.create_learner, name='learner'),
        path('get-coaches-by-project/', views.get_coaches_by_project, name='get-coaches-by-project'),
        path('get-learners-by-project/', views.get_learners_by_project, name='get-learners-by-project')
]