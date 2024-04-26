from django.urls import path, include
from . import views

urlpatterns = [
    path(
        "batches/",
        views.get_batches,
    ),
    path("batch-details/", views.batch_details, name="batch-details"),
    path("participant-details/", views.participant_details, name="participant-details"),
    path(
        "participant-so-in-batch/<str:email>/",
        views.participant_so_in_batch,
        name="participant-so-in-batch",
    ),
    path(
        "participant-so-and-invoices-in-batch/<str:email>/",
        views.participant_so_and_invoices_in_batch,
        name="participant-so-and-invoices-in-batch",
    ),
    path(
        "sales-persons/finances/",
        views.sales_persons_finances,
        name="sales-persons-finances",
    ),
    path(
        "participant-finances/",
        views.participant_finances,
        name="participant-finances",
    ),
    path("faculties/", views.get_faculties),
     path(
        "get-all-faculties/",
        views.get_all_faculties,
        name="get_all_faculties",
    ),
]
