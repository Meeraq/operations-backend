from django.urls import path, include
from .views import AddAffiliate, lead_create_view, leads_by_affiliate, lead_update, all_leads
from . import views



urlpatterns = [
   path(
        "add_affiliate/",
        AddAffiliate.as_view(),
    ),
    path("otp/generate/", views.generate_otp),
    path("otp/validate/", views.validate_otp),
    path('leads/create/', lead_create_view, name='lead-create'),
    path('leads/by-affiliate/<int:affiliate_id>/', leads_by_affiliate,),
    path('leads/update/<int:pk>/', lead_update,),
    path('leads/all_leads/', all_leads,),

]
