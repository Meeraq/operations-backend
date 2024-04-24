from celery import shared_task
from .views import create_task
from zohoapi.models import Vendor
from zohoapi.tasks import fetch_purchase_orders, organization_id
from .models import Engagement, SessionRequestCaas, Coach, CoachStatus
from django.utils import timezone
from django.db.models import Q, F, ExpressionWrapper, DurationField
from schedularApi.models import RequestAvailibilty, CoachSchedularAvailibilty
from datetime import datetime, timedelta


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
    all_purchase_orders = fetch_purchase_orders(organization_id)
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
def check_coach_availability_for_this_month():
    try:
        coaches = Coach.objects.all()
        for coach in coaches:
            engagements = Engagement.objects.filter(coach=coach)
            durations = {}
            for engagement in engagements:

                session_requests = SessionRequestCaas.objects.filter(
                    Q(is_booked=False),
                    Q(learner=engagement.learner),
                    Q(project=engagement.project),
                    Q(is_archive=False),
                    Q(status="pending"),
                )
                for session in session_requests:
                    if session.session_duration not in durations:
                        durations[session.session_duration] = 1
                    else:
                        durations[session.session_duration] += 1

            request_for_durations = []
            for duration, count in durations.items():
                current_time = timezone.now()
                start_timestamp_milliseconds = str(int(current_time.timestamp() * 1000))
                end_timestamp_milliseconds = str(
                    int((current_time + timedelta(days=30)).timestamp() * 1000)
                )

                coach_availability = CoachSchedularAvailibilty.objects.filter(
                    coach=coach,
                    is_confirmed=False,
                    request__slot_duration=duration,
                    start_time__gte=start_timestamp_milliseconds,
                    end_time__lte=end_timestamp_milliseconds,
                )
                if len(coach_availability) < count * 3:
                    request_for_durations.append(duration)
            if len(request_for_durations)> 0:
                create_task(
                    {
                        "task": "availability_shortage",
                        "priority": "high",
                        "coach": coach.id,
                        "status": "pending",
                        "remarks": [],
                        "extra_info": f"durations {', '.join(str(duration) for duration in request_for_durations)} (minutes)",
                    },
                    0,
                )

    except Exception as e:
        print(str(e))
