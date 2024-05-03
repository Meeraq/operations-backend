from celery import shared_task
from .views import create_task
from zohoapi.models import Vendor, PurchaseOrder
from zohoapi.tasks import (
    fetch_purchase_orders,
    organization_id,
    filter_purchase_order_data,
)
from zohoapi.serializers import PurchaseOrderSerializer
from .models import Engagement, SessionRequestCaas
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import uuid


def get_start_and_end_of_current_month():
    current_date = timezone.now()
    start_of_month = current_date.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    if start_of_month.month == 12:
        next_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
    else:
        next_month = start_of_month.replace(month=start_of_month.month + 1)
    end_of_month = next_month - timezone.timedelta(microseconds=1)
    start_timestamp = int(start_of_month.timestamp()) * 1000
    end_timestamp = int(end_of_month.timestamp()) * 1000
    return start_timestamp, end_timestamp


@shared_task
def generate_invoice_task_for_pmo_on_25th_of_month():
    vendors = Vendor.objects.all()
    all_purchase_orders = filter_purchase_order_data(
        PurchaseOrderSerializer(PurchaseOrder.objects.all(), many=True).data
    )
    # fetch_purchase_orders(organization_id)
    for vendor in vendors:
        open_purchase_order_count = 0
        purchase_orders = [
            purchase_order
            for purchase_order in all_purchase_orders
            if purchase_order["vendor_id"] == vendor.vendor_id
        ]
        for purchase_order in purchase_orders:
            if purchase_order["status"] in ["partially_billed", "open"]:
                open_purchase_order_count += 1
        if open_purchase_order_count > 0:
            create_task(
                {
                    "task": "generate_invoice",
                    "priority": "low",
                    "status": "pending",
                    "vendor_user": vendor.user.user.id,
                    "remarks": [],
                },
                0,
            )


@shared_task
def creake_book_session_remind_coach_task_for_pmo_on_7th_of_month():
    engagements = Engagement.objects.filter(status="active")
    for engagement in engagements:
        if engagement.coach:
            start_timestamp, end_timestamp = get_start_and_end_of_current_month()
            session_requests = SessionRequestCaas.objects.filter(
                Q(is_booked=True),
                Q(confirmed_availability__start_time__gte=start_timestamp),
                Q(confirmed_availability__start_time__lte=end_timestamp),
            )
            if not session_requests.exists():
                create_task(
                    {
                        "task": "book_session",
                        "priority": "medium",
                        "status": "pending",
                        "engagement": engagement.id,
                        "remarks": [],
                    },
                    7,
                )
    return None


@shared_task
def archive_request_if_expired(session_id):
    try:
        current_time = timezone.now()
        session = SessionRequestCaas.objects.get(id=session_id)
        if (
            session.requested_at is not None
            and session.project.request_expiry_time is not None
        ):

            expiry_time_minutes = round(session.project.request_expiry_time)

            expiry_datetime = session.requested_at + timedelta(
                minutes=expiry_time_minutes
            )

            if expiry_datetime.date() == current_time.date():
                session.is_archive = True
                session.save()

    except Exception as e:
        print(str(e))


@shared_task
def schedule_request_expiry_for_session():
    try:

        current_time = timezone.now()

        sessions = SessionRequestCaas.objects.filter(
            project__project_type="COD",
            project__is_project_structure=False,
            status="requested",
        )

        for session in sessions:

            if (
                session.requested_at is not None
                and session.project.request_expiry_time is not None
            ):

                expiry_time_minutes = round(session.project.request_expiry_time)

                expiry_datetime = session.requested_at + timedelta(
                    minutes=expiry_time_minutes
                )

                if expiry_datetime.date() == current_time.date():

                    clocked_schedule = ClockedSchedule.objects.create(
                        clocked_time=expiry_datetime
                    )
                    periodic_task = PeriodicTask.objects.create(
                        name=uuid.uuid1(),
                        task="api.tasks.archive_request_if_expired",
                        args=[session.id],
                        clocked=clocked_schedule,
                        one_off=True,
                    )
                    print(session)

    except Exception as e:
        print(str(e))
