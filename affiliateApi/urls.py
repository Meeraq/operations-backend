from django.urls import path, include
from .views import AddAffiliate, GetAffiliates ,ApproveRejectAffiliate
from . import views


urlpatterns = [
    path(
        "add_affiliate/",
        AddAffiliate.as_view(),
    ),
    path("otp/generate/", views.generate_otp),
    path("otp/validate/", views.validate_otp),
    path(
        "get-affiliates/",
        GetAffiliates.as_view(),
    ),
    path(
        "approve-reject-affiliates/",
        ApproveRejectAffiliate.as_view(),
    ),
]
