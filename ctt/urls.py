from django.urls import path, include
from . import views

urlpatterns = [
    path(
        "batches/",
        views.get_batches,
    ),
]
