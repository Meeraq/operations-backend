from django.urls import path, include
from .views import AddAffiliate
from . import views



urlpatterns = [
   path(
        "add_affiliate/",
        AddAffiliate.as_view(),
    ),
    path("otp/generate/", views.generate_otp),
    path("otp/validate/", views.validate_otp),
]
