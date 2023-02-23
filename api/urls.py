from django.urls import path, include
from . import views

urlpatterns =[
	  path('pmos/',views.create_pmo),
		path('add-coaches/',views.coach_signup),
		path('coaches/',views.get_coaches),
		path('coaches/<int:coach_id>/approve/',views.approve_coach),
    	path('pmo-login/', views.pmo_login, name='pmo-login'),
        path('create-project/', views.create_project, name='create-project'),
        path('learner/', views.create_learner, name='learner') 
]