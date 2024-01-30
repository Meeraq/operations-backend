import string
from celery import shared_task
from .models import SentEmail, SchedularSessions, LiveSession
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from django.conf import settings
from api.models import Coach, User, UserToken, SessionRequestCaas, Learner
from schedularApi.models import CoachingSession, SchedularSessions, RequestAvailibilty,CoachSchedularAvailibilty
from django.utils import timezone
from api.views import (
    send_mail_templates,
    refresh_microsoft_access_token,
)
from schedularApi.serializers import AvailabilitySerializer
from datetime import timedelta, time, datetime
import pytz

# /from assessmentApi.views import send_whatsapp_message
from django.core.exceptions import ObjectDoesNotExist
from assessmentApi.models import Assessment, ParticipantResponse, ParticipantUniqueId
from courses.models import Course, Lesson, FeedbackLesson, FeedbackLessonResponse, Nudge
from courses.views import get_file_extension
from django.db.models import Q
from assessmentApi.models import Assessment, ParticipantResponse
import environ
from time import sleep
import requests

env = environ.Env()
environ.Env.read_env()

def timestamp_to_datetime(timestamp):
    return datetime.utcfromtimestamp(int(timestamp) / 1000.0)


def generate_slots(start, end, duration):
    slots = []
    current_time = timestamp_to_datetime(start)

    while current_time + timedelta(minutes=duration) <= timestamp_to_datetime(end):
        new_end_time = current_time + timedelta(minutes=duration)
        slots.append(
            {
                "start_time": int(current_time.timestamp() * 1000),
                "end_time": int(new_end_time.timestamp() * 1000),
            }
        )
        current_time += timedelta(minutes=15)
    return slots


def get_upcoming_availabilities_of_coaching_session(coaching_session_id):
    coaching_session = CoachingSession.objects.get(id=coaching_session_id)
    if (
        not coaching_session.start_date
        or not coaching_session.end_date
        or not coaching_session.end_date
    ):
        return None
    coaches_in_batch = coaching_session.batch.coaches.all()
    start_date = datetime.combine(coaching_session.start_date, datetime.min.time())
    end_date = (
        datetime.combine(coaching_session.end_date, datetime.min.time())
        + timedelta(days=1)
        - timedelta(milliseconds=1)
    )
    start_timestamp = str(int(start_date.timestamp() * 1000))
    end_timestamp = str(int(end_date.timestamp() * 1000))
    coach_availabilities = CoachSchedularAvailibilty.objects.filter(
        coach__in=coaches_in_batch,
        start_time__gte=start_timestamp,
        end_time__lte=end_timestamp,
        is_confirmed=False,
    )
    current_time = timezone.now()
    timestamp_milliseconds = str(int(current_time.timestamp() * 1000))
    upcoming_availabilities = coach_availabilities.filter(
        start_time__gt=timestamp_milliseconds
    )
    serializer = AvailabilitySerializer(upcoming_availabilities, many=True)
    return serializer.data

def merge_time_slots(slots, slots_by_coach):
    res = []
    for key in slots_by_coach:
        sorted_slots = sorted(slots_by_coach[key], key=lambda x: x["start_time"])
        merged_slots = []
        for i in range(len(sorted_slots)):
            if (
                len(merged_slots) == 0
                or sorted_slots[i]["start_time"] > merged_slots[-1]["end_time"]
            ):
                merged_slots.append(sorted_slots[i])
            else:
                merged_slots[-1]["end_time"] = max(
                    merged_slots[-1]["end_time"], sorted_slots[i]["end_time"]
                )
        res.extend(merged_slots)

    return res


def available_slots_count_for_participant(id):
    try:
        coaching_session = CoachingSession.objects.filter(id=id)
        session_duration = coaching_session[0].duration
        availabilities = get_upcoming_availabilities_of_coaching_session(
            coaching_session[0].id
        )
        result = []

        if availabilities is not None and len(availabilities):
            slots = []
            slots_by_coach = {}
            for availability in availabilities:
                slots_by_coach[availability["coach"]] = (
                    [*slots_by_coach[availability["coach"]], availability]
                    if availability["coach"] in slots_by_coach
                    else [availability]
                )
                slots.append(availability)

            final_merge_slots = merge_time_slots(slots, slots_by_coach)
            for slot in final_merge_slots:
                startT = slot["start_time"]
                endT = slot["end_time"]
                small_session_duration = int(session_duration)
                result += generate_slots(startT, endT, small_session_duration)
        return result 

    except Exception as inner_exception:
        print(f"Inner Exception: {str(inner_exception)}")
        return 0 



def get_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000) + timedelta(
        hours=5, minutes=30
    )  # Convert milliseconds to seconds
    return dt.strftime("%I:%M %p")


def send_whatsapp_message(user_type, participant, assessment, unique_id):
    try:
        assessment_name = assessment.participant_view_name
        participant_phone = participant.phone
        participant_name = participant.name
        if not participant_phone:
            return {"error": "Participant phone not available"}, 500
        wati_api_endpoint = env("WATI_API_ENDPOINT")
        wati_authorization = env("WATI_AUTHORIZATION")
        wati_api_url = f"{wati_api_endpoint}/api/v1/sendTemplateMessage?whatsappNumber={participant_phone}"
        headers = {
            "content-type": "text/json",
            "Authorization": wati_authorization,
        }
        participant_id = unique_id
        payload = {
            "broadcast_name": "send_whatsapp_message",
            "parameters": [
                {
                    "name": "participant_name",
                    "value": participant_name,
                },
                {
                    "name": "assessment_name",
                    "value": assessment_name,
                },
                {
                    "name": "participant_id",
                    "value": participant_id,
                },
            ],
            "template_name": "assessment_reminders_message",
        }

        response = requests.post(wati_api_url, headers=headers, json=payload)
        response.raise_for_status()

        return response.json(), response.status_code

    except requests.exceptions.HTTPError as errh:
        return {"error": f"HTTP Error: {errh}"}, 500
    except requests.exceptions.RequestException as err:
        return {"error": f"Request Error: {err}"}, 500
    except:
        pass


def send_whatsapp_message_template(phone, payload):
    try:
        if not phone:
            return {"error": "Phone not available"}, 500
        wati_api_endpoint = env("WATI_API_ENDPOINT")
        wati_authorization = env("WATI_AUTHORIZATION")
        wati_api_url = (
            f"{wati_api_endpoint}/api/v1/sendTemplateMessage?whatsappNumber={phone}"
        )
        headers = {
            "content-type": "text/json",
            "Authorization": wati_authorization,
        }
        response = requests.post(wati_api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json(), response.status_code
    except Exception as e:
        print(str(e))


def get_current_date_timestamps():
    now = timezone.now()
    current_date = now.date()
    start_timestamp = str(
        int(datetime.combine(current_date, datetime.min.time()).timestamp() * 1000)
    )
    end_timestamp = str(
        int(datetime.combine(current_date, datetime.max.time()).timestamp() * 1000)
    )
    return start_timestamp, end_timestamp

@shared_task
def send_email_to_recipients(id):
    try:
        sent_email = SentEmail.objects.get(id=id)
        if sent_email.status == "pending":
            sent_email.status = "completed"
            sent_email.save()
            for recipient in sent_email.recipients:
                recipient_name = recipient["name"]
                recipient_email = recipient["email"]
                email_content = sent_email.template.template_data.replace(
                    "{{learnerName}}", recipient_name
                )
                email_message_learner = render_to_string(
                    "default.html",
                    {
                        "email_content": mark_safe(email_content),
                        "email_title": "hello",
                        "subject": sent_email.subject,
                    },
                )
                email = EmailMessage(
                    sent_email.subject,
                    email_message_learner,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],
                )
                email.content_subtype = "html"
                email.send()
                print(
                    "Email sent to:", recipient_email, "for recipient:", recipient_name
                )
                sleep(6)
            return "success"
        return "error: sent email is not pending"
    except:
        print("error")
        return "error: sent email not found "


# @shared_task
# def send_event_link_to_learners(id):
#     print("success")
#     event = Events.objects.get(id=id)
#     batch = event.batch
#     learners = Learner.objects.filter(batch=batch)
#     learners_with_no_sessions = []
#     for learner in learners:
#         sessions = LeanerConfirmedSlots.objects.filter(email=learner.email, event=event)
#         if len(sessions) == 0:
#             learners_with_no_sessions.append(learner.email)
#     # print(learner_emails, type(learner_emails))
#     # learner_emails_array = json.loads(learner_emails)
#     for learner_mail in learners_with_no_sessions:
#         try:
#             email_message = render_to_string(
#                 "seteventlink.html",
#                 {"event_link": event.link},
#             )
#             send_mail(
#                 "Event link to join sessions on  {title}".format(title="Meeraq"),
#                 email_message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [learner_mail],
#                 html_message=email_message,
#             )
#         except Exception as e:
#             print("Failed to send to ", learner_mail)
#             pass
#         sleep(6)


@shared_task
def refresh_user_tokens():
    users = UserToken.objects.filter(account_type="microsoft")
    for user in users:
        refresh_microsoft_access_token(user)
        print(f"token refresh for {user.user_mail}")


# @shared_task
# def send_authorization_mail_to_learners(learners_json):
#     for learner_json in json.loads(learners_json):
#         try:
#             learner_obj = json.loads(learner_json)
#             email = learner_obj["email"]
#             backend_domain = env("BACKEND_DOMAIN")
#             url = f"{backend_domain}/microsoft/oauth/{email}"
#             email_message = render_to_string(
#                 "authorizationLearner.html",
#                 {
#                     "coachee_name": learner_obj["name"],
#                     "email": learner_obj["email"],
#                     "microsoft_authentication_url": url,
#                 },
#             )
#             send_mail(
#                 "Meeraq | Welcome!",
#                 email_message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [learner_obj["email"]],
#                 html_message=email_message,
#             )
#             print(f"send authorization mail to {email}")
#         except Exception as e:
#             print(f"failed to send_authorization_mail_to_learners: {str(e)}")
#         sleep(6)


# @shared_task
# def send_session_reminder_one_day_prior():
#     tomorrow_date = datetime.now() + timedelta(days=1)
#     tomorrow_date_str = tomorrow_date.strftime("%Y-%m-%d")
#     slots_for_tomorrow = LeanerConfirmedSlots.objects.filter(
#         slot__date=tomorrow_date_str
#     )
#     for learner_slot in slots_for_tomorrow:
#         try:
#             coach_slot = learner_slot.slot
#             coach_data = Coach.objects.get(id=learner_slot.slot.coach_id)
#             start_time_for_mail = datetime.fromtimestamp(
#                 (int(coach_slot.start_time) / 1000) + 19800
#             ).strftime("%I:%M %p")
#             date = datetime.fromtimestamp(
#                 (int(coach_slot.start_time) / 1000) + 19800
#             ).strftime("%d %B %Y")
#             duration = "30 Min"
#             meet_link = coach_data.meet_link
#             email_message_learner = render_to_string(
#                 "learnerSessionReminder.html",
#                 {
#                     "learner_name": learner_slot.name,
#                     "time": start_time_for_mail,
#                     "duration": duration,
#                     "date": date,
#                     "link": meet_link,
#                 },
#             )
#             email = EmailMessage(
#                 "Meeraq | Coaching Session",
#                 email_message_learner,
#                 settings.DEFAULT_FROM_EMAIL,  # from email address
#                 [learner_slot.email],  # to email address
#             )
#             email.content_subtype = "html"
#             email.send()
#         except Exception as e:
#             print(f"Failed to send reminder for session {str(e)}", learner_slot.id)
#         sleep(6)


@shared_task
def send_coach_morning_reminder_email():
    start_timestamp, end_timestamp = get_current_date_timestamps()
    today_sessions = SchedularSessions.objects.filter(
        availibility__start_time__lte=end_timestamp,
        availibility__end_time__gte=start_timestamp,
    )
    # Format sessions coach-wise
    coach_sessions = {}
    for session in today_sessions:
        if True:
            coach_id = session.availibility.coach.id
            if coach_id not in coach_sessions:
                coach_sessions[coach_id] = []
            coach_sessions[coach_id].append(session)
    # Create time slots for each coach
    coach_time_slots = {}
    for coach_id, sessions in coach_sessions.items():
        slots = []
        for session in sessions:
            if True:
                start_time_for_mail = datetime.fromtimestamp(
                    (int(session.availibility.start_time) / 1000) + 19800
                ).strftime("%I:%M %p")
                # start_time = int(session.availibility.start_time)
                # end_time = int(session.availibility.end_time)
                slots.append(f"{start_time_for_mail}")
        coach_time_slots[coach_id] = slots

    # Send email to each coach
    for coach_id, slots in coach_time_slots.items():
        coach = Coach.objects.get(id=coach_id)
        coach_name = (
            coach.first_name + " " + coach.last_name
        )  # Replace with actual field name
        content = {"name": coach_name, "session_count": len(slots), "slots": slots}
        send_mail_templates(
            "coach_templates/session_reminder.html",
            [coach.email],
            "Meeraq - Coaching Session Reminder",
            content,
            [],  # bcc
        )
        sleep(5)


@shared_task
def send_participant_morning_reminder_email():
    start_timestamp, end_timestamp = get_current_date_timestamps()
    today_sessions = SchedularSessions.objects.filter(
        availibility__start_time__lte=end_timestamp,
        availibility__end_time__gte=start_timestamp,
    )
    for session in today_sessions:
        if session.coaching_session.batch.project.automated_reminder:
            name = session.learner.name
            meeting_link = (
                f"{env('CAAS_APP_URL')}/call/{session.availibility.coach.room_id}"
            )
            time = datetime.fromtimestamp(
                (int(session.availibility.start_time) / 1000) + 19800
            ).strftime("%I:%M %p")
            content = {"time": time, "meeting_link": meeting_link, "name": name}
            send_mail_templates(
                "coachee_emails/session_reminder.html",
                [session.learner.email],
                "Meeraq - Coaching Session Reminder",
                content,
                [],  # bcc
            )
            sleep(5)


@shared_task
def send_upcoming_session_pmo_at_10am():
    start_timestamp, end_timestamp = get_current_date_timestamps()
    today_sessions = SchedularSessions.objects.filter(
        availibility__start_time__lte=end_timestamp,
        availibility__end_time__gte=start_timestamp,
    )
    if today_sessions:
        # Compose the email message with session information
        subject = "Daily Sessions"
        message = "List of sessions scheduled for today:\n"

        sessions_list = []
        for session in today_sessions:
            if True:
                start_time = datetime.fromtimestamp(
                    (int(session.availibility.start_time) / 1000) + 19800
                ).strftime("%I:%M %p")
                end_time = datetime.fromtimestamp(
                    (int(session.availibility.start_time) / 1000) + 19800
                ).strftime("%I:%M %p")
                session_details = {
                    # "Session ID":,
                    "coach": session.availibility.coach.first_name
                    + " "
                    + session.availibility.coach.last_name,
                    "participant": session.learner.name,
                    "batch_name": session.coaching_session.batch.name,
                    "status": session.status,
                    # "session_date": start_time.strftime("%d %B %Y"),
                    "session_time": start_time + " - " + end_time,
                }
                sessions_list.append(session_details)
                pmo_user = User.objects.filter(profile__roles__name="pmo").first()
        if sessions_list:
            send_mail_templates(
                "pmo_emails/daily_session.html",
                [pmo_user.email],
                subject,
                {"sessions": sessions_list},
                [],
            )


@shared_task
def send_participant_morning_reminder_one_day_before_email():
    start_timestamp, end_timestamp = get_current_date_timestamps()
    one_day_in_miliseconds = 86400000
    start_timestamp_one_day_ahead = str(int(start_timestamp) + one_day_in_miliseconds)
    end_timestamp_one_day_ahead = str(int(end_timestamp) + one_day_in_miliseconds)
    tomorrow_sessions = SchedularSessions.objects.filter(
        availibility__start_time__lte=end_timestamp_one_day_ahead,
        availibility__end_time__gte=start_timestamp_one_day_ahead,
    )
    for session in tomorrow_sessions:
        if session.coaching_session.batch.project.automated_reminder:
            name = session.learner.name
            meeting_link = (
                f"{env('CAAS_APP_URL')}/call/{session.availibility.coach.room_id}"
            )
            time = datetime.fromtimestamp(
                (int(session.availibility.start_time) / 1000) + 19800
            ).strftime("%I:%M %p")
            content = {"time": time, "meeting_link": meeting_link, "name": name}
            send_mail_templates(
                "coachee_emails/one_day_before_remailder.html",
                [session.learner.email],
                "Meeraq - Coaching Session Reminder",
                content,
                [],  # bcc
            )
            sleep(5)


@shared_task
def send_reminder_email_to_participants_for_assessment_at_2PM():
    ongoing_assessments = Assessment.objects.filter(
        status="ongoing", automated_reminder=True
    )

    for assessment in ongoing_assessments:
        # Convert assessment_start_date and assessment_end_date to datetime objects
        start_date = datetime.strptime(
            assessment.assessment_start_date, "%Y-%m-%d"
        ).date()
        end_date = datetime.strptime(assessment.assessment_end_date, "%Y-%m-%d").date()
        # Check if today's date is within the assessment date range
        today = datetime.now().date()
        day_of_week = today.strftime("%A")

        if start_date <= today <= end_date and not day_of_week == "Sunday":
            participants_observers = assessment.participants_observers.all()

            for participant_observer_mapping in participants_observers:
                participant = participant_observer_mapping.participant

                try:
                    participant_response = ParticipantResponse.objects.filter(
                        participant=participant, assessment=assessment
                    )

                    if not participant_response:
                        participant_unique_id = ParticipantUniqueId.objects.get(
                            participant=participant, assessment=assessment
                        )
                        unique_id = participant_unique_id.unique_id

                        assessment_link = f"{env('ASSESSMENT_URL')}/participant/meeraq/assessment/{unique_id}"

                        # Send email only if today's date is within the assessment date range
                        send_mail_templates(
                            "assessment/assessment_reminder_mail_to_participant.html",
                            [participant.email],
                            "Meeraq - Assessment Reminder !",
                            {
                                "assessment_name": assessment.participant_view_name,
                                "participant_name": participant.name.capitalize(),
                                "link": assessment_link,
                            },
                            [],
                        )

                except ObjectDoesNotExist:
                    print(f"No unique ID found for participant {participant.name}")
                sleep(5)


@shared_task
def send_whatsapp_message_to_participants_for_assessment_at_9AM():
    ongoing_assessments = Assessment.objects.filter(
        status="ongoing", automated_reminder=True
    )
    for assessment in ongoing_assessments:
        start_date = datetime.strptime(
            assessment.assessment_start_date, "%Y-%m-%d"
        ).date()
        end_date = datetime.strptime(assessment.assessment_end_date, "%Y-%m-%d").date()

        # Check if today's date is within the assessment date range
        today = datetime.now().date()
        day_of_week = today.strftime("%A")
        if start_date <= today <= end_date and not day_of_week == "Sunday":
            participants_observers = assessment.participants_observers.all()

            for participant_observer_mapping in participants_observers:
                participant = participant_observer_mapping.participant
                try:
                    participant_response = ParticipantResponse.objects.filter(
                        participant=participant, assessment=assessment
                    )
                    if not participant_response:
                        participant_unique_id = ParticipantUniqueId.objects.get(
                            participant=participant, assessment=assessment
                        )
                        unique_id = participant_unique_id.unique_id
                        print("Participant Unique ID:", unique_id)
                        send_whatsapp_message(
                            "learner", participant, assessment, unique_id
                        )
                except ObjectDoesNotExist:
                    print(f"No unique ID found for participant {participant.name}")
                sleep(2)


@shared_task
def send_whatsapp_message_to_participants_for_assessment_at_7PM():
    ongoing_assessments = Assessment.objects.filter(
        status="ongoing", automated_reminder=True
    )
    for assessment in ongoing_assessments:
        start_date = datetime.strptime(
            assessment.assessment_start_date, "%Y-%m-%d"
        ).date()
        end_date = datetime.strptime(assessment.assessment_end_date, "%Y-%m-%d").date()

        # Check if today's date is within the assessment date range
        today = datetime.now().date()
        day_of_week = today.strftime("%A")
        if start_date <= today <= end_date and not day_of_week == "Sunday":
            participants_observers = assessment.participants_observers.all()
            for participant_observer_mapping in participants_observers:
                participant = participant_observer_mapping.participant
                try:
                    participant_response = ParticipantResponse.objects.filter(
                        participant=participant, assessment=assessment
                    )
                    if not participant_response:
                        participant_unique_id = ParticipantUniqueId.objects.get(
                            participant=participant, assessment=assessment
                        )
                        unique_id = participant_unique_id.unique_id
                        print("Participant Unique ID:", unique_id)
                        send_whatsapp_message(
                            "learner", participant, assessment, unique_id
                        )
                except ObjectDoesNotExist:
                    print(f"No unique ID found for participant {participant.name}")
                sleep(2)


@shared_task
def update_assessment_status():
    assessments = Assessment.objects.filter(
        Q(automated_reminder=True), ~Q(assessment_timing="none")
    )
    for assessment in assessments:
        # Parse start and end dates to datetime objects
        start_date = datetime.strptime(
            assessment.assessment_start_date, "%Y-%m-%d"
        ).date()
        end_date = datetime.strptime(assessment.assessment_end_date, "%Y-%m-%d").date()
        # Get the current date in UTC
        current_date = timezone.now().date()
        # Update assessment status based on conditions
        if current_date == start_date:
            assessment.status = "ongoing"
        elif current_date > end_date:
            assessment.status = "completed"
        # Save the updated assessment
        assessment.save()


@shared_task
def send_assessment_invitation_mail(assessment_id):
    print("called")
    assessment = Assessment.objects.get(id=assessment_id)
    for participant_observers in assessment.participants_observers.all():
        try:
            participant = participant_observers.participant
            participant_response = ParticipantResponse.objects.filter(
                participant=participant, assessment=assessment
            ).first()
            if not participant_response:
                participant_unique_id = ParticipantUniqueId.objects.filter(
                    participant=participant, assessment=assessment
                ).first()
                if participant_unique_id:
                    assessment_link = f"{env('ASSESSMENT_URL')}/participant/meeraq/assessment/{participant_unique_id.unique_id}"
                    send_mail_templates(
                        "assessment/assessment_initial_reminder.html",
                        [participant.email],
                        "Meeraq - Welcome to Assessment Platform !",
                        {
                            "assessment_name": assessment.participant_view_name,
                            "participant_name": participant.name.title(),
                            "link": assessment_link,
                        },
                        [],
                    )
        except Exception as e:
            print(str(e))
            pass
        sleep(5)


@shared_task
def send_whatsapp_reminder_1_day_before_live_session():
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        live_sessions = LiveSession.objects.filter(date_time__date=tomorrow)

        for session in live_sessions:
            if session.batch.project.automated_reminder:
                learners = session.batch.learners.all()
                session_datetime_str = session.date_time.astimezone(
                    pytz.timezone("Asia/Kolkata")
                ).strftime("%I:%M %p")
                for learner in learners:
                    send_whatsapp_message_template(
                        learner.phone,
                        {
                            "broadcast_name": "1 day before live session starts!",
                            "parameters": [
                                {
                                    "name": "name",
                                    "value": learner.name,
                                },
                                {
                                    "name": "live_session_name",
                                    "value": f"Live Session {session.live_session_number}",
                                },
                                {
                                    "name": "project_name",
                                    "value": session.batch.project.name,
                                },
                                {
                                    "name": "time",
                                    "value": f"{session_datetime_str} IST",
                                },
                            ],
                            "template_name": "reminder_coachee_live_session_one_day_before",
                        },
                    )
                    sleep(5)
    except Exception as e:
        print(str(e))
        pass


@shared_task
def send_whatsapp_reminder_same_day_morning():
    try:
        today_morning = timezone.now().replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        live_sessions = LiveSession.objects.filter(date_time__date=today_morning.date())

        for session in live_sessions:
            if session.batch.project.automated_reminder:
                learners = session.batch.learners.all()
                session_datetime_str = session.date_time.astimezone(
                    pytz.timezone("Asia/Kolkata")
                ).strftime("%I:%M %p")
                for learner in learners:
                    send_whatsapp_message_template(
                        learner.phone,
                        {
                            "broadcast_name": "Same day morning reminder",
                            "parameters": [
                                {
                                    "name": "name",
                                    "value": learner.name,
                                },
                                {
                                    "name": "live_session_name",
                                    "value": f"Live Session {session.live_session_number}",
                                },
                                {
                                    "name": "description",
                                    "value": session.description,
                                },
                                {
                                    "name": "time",
                                    "value": f"{session_datetime_str} IST",
                                },
                            ],
                            "template_name": "reminder_coachee_live_session_same_day",
                        },
                    )
                    sleep(5)
    except Exception as e:
        print(str(e))
        pass


@shared_task
def send_whatsapp_reminder_30_min_before_live_session(id):
    try:
        live_session = LiveSession.objects.get(id=id)
        if live_session.batch.project.automated_reminder:
            learners = live_session.batch.learners.all()
            for learner in learners:
                send_whatsapp_message_template(
                    learner.phone,
                    {
                        "broadcast_name": "30 min before live session reminder",
                        "parameters": [
                            {
                                "name": "project_name",
                                "value": live_session.batch.project.name,
                            },
                            {
                                "name": "live_session_name",
                                "value": f"Live Session {live_session.live_session_number}",
                            },
                            {
                                "name": "description",
                                "value": live_session.description,
                            },
                        ],
                        "template_name": "reminder_coachee_live_session_30min_before",
                    },
                )
                sleep(5)

    except Exception as e:
        print(str(e))


def get_feedback_lesson_name(lesson_name):
    # Trim leading and trailing whitespaces
    trimmed_string = lesson_name.strip()
    # Convert to lowercase
    lowercased_string = trimmed_string.lower()
    # Replace spaces between words with underscores
    underscored_string = "_".join(lowercased_string.split())
    return underscored_string


@shared_task
def send_feedback_lesson_reminders():
    today = timezone.now().date()
    today_live_sessions = LiveSession.objects.filter(date_time__date=today)
    for live_session in today_live_sessions:
        if live_session.batch.project.automated_reminder:
            try:
                # Get the associated SchedularBatch for each LiveSession
                schedular_batch = live_session.batch
                if schedular_batch:
                    # Now, you can access the associated Course through the SchedularBatch
                    course = Course.objects.filter(batch=schedular_batch).first()
                    if course:
                        feedback_lesson_name_should_be = f"feedback_for_{live_session.session_type}_{live_session.live_session_number}"
                        feedback_lessons = FeedbackLesson.objects.filter(
                            lesson__course=course
                        )
                        for feedback_lesson in feedback_lessons:
                            try:
                                current_lesson_name = feedback_lesson.lesson.name
                                formatted_lesson_name = get_feedback_lesson_name(
                                    current_lesson_name
                                )
                                if (
                                    formatted_lesson_name
                                    == feedback_lesson_name_should_be
                                ):
                                    for (
                                        learner
                                    ) in (
                                        feedback_lesson.lesson.course.batch.learners.all()
                                    ):
                                        try:
                                            feedback_lesson_response_exists = (
                                                FeedbackLessonResponse.objects.filter(
                                                    feedback_lesson=feedback_lesson,
                                                    learner=learner,
                                                ).exists()
                                            )
                                            if not feedback_lesson_response_exists:
                                                send_whatsapp_message_template(
                                                    learner.phone,
                                                    {
                                                        "broadcast_name": "Feedback Reminder",
                                                        "parameters": [
                                                            {
                                                                "name": "name",
                                                                "value": learner.name,
                                                            },
                                                            {
                                                                "name": "live_session_name",
                                                                "value": f"Live Session {live_session.live_session_number}",
                                                            },
                                                            {
                                                                "name": "feedback_lesson_id",
                                                                "value": feedback_lesson.unique_id,
                                                            },
                                                        ],
                                                        "template_name": "one_time_reminder_feedback_form_live_session",
                                                    },
                                                )
                                        except Exception as e:
                                            print(
                                                f"error sending whatsapp message to {learner}: {str(e)}"
                                            )
                                    # send whatsapp message to all participants
                            except Exception as e_inner:
                                print(
                                    f"Error processing feedback lesson: {str(e_inner)}"
                                )
                    else:
                        print(
                            f"Live Session {live_session.id} is associated with a batch but not with any Course"
                        )
                else:
                    print(
                        f"Live Session {live_session.id} is not associated with any SchedularBatch"
                    )
            except Exception as e_outer:
                print(f"Error processing live session: {str(e_outer)}")


@shared_task
def send_coach_morning_reminder_whatsapp_message_at_8AM_seeq():
    try:
        start_timestamp, end_timestamp = get_current_date_timestamps()
        # schedular sessions scheduled today
        today_sessions = SchedularSessions.objects.filter(
            availibility__start_time__lte=end_timestamp,
            availibility__end_time__gte=start_timestamp,
        )
        # Format sessions coach-wise
        coach_sessions = {}
        for session in today_sessions:
            if True:
                coach_id = session.availibility.coach.id
                if coach_id not in coach_sessions:
                    coach_sessions[coach_id] = []
                coach_sessions[coach_id].append(session)
        # Create time slots for each coach
        for coach_id, sessions in coach_sessions.items():
            slots = []
            for session in sessions:
                if True:
                    # start_time_for_mail = datetime.fromtimestamp(
                    #     (int(session.availibility.start_time) / 1000) + 19800
                    # ).strftime("%I:%M %p")
                    start_time_for_mail = get_time(int(session.availibility.start_time))
                    phone = (
                        session.availibility.coach.phone_country_code
                        + session.availibility.coach.phone
                    )
                    coach_name = (
                        session.availibility.coach.first_name
                        + " "
                        + session.availibility.coach.last_name
                    )
                    booking_id = session.availibility.coach.room_id
                    send_whatsapp_message_template(
                        phone,
                        {
                            "broadcast_name": "send_coach_morning_reminder_whatsapp_message_at_8AM_seeq",
                            "parameters": [
                                {
                                    "name": "name",
                                    "value": coach_name,
                                },
                                {
                                    "name": "time",
                                    "value": f"{start_time_for_mail} IST",
                                },
                                {
                                    "name": "booking_id",
                                    "value": booking_id,
                                },
                            ],
                            "template_name": "training_reminders_final",
                        },
                    )
    except Exception as e:
        print(str(e))


@shared_task
def send_coach_morning_reminder_whatsapp_message_at_8AM_caas():
    try:
        start_timestamp, end_timestamp = get_current_date_timestamps()
        # caas_Sessions scheduled today
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__gte=start_timestamp),
            Q(confirmed_availability__start_time__lte=end_timestamp),
            ~Q(status="completed"),
        )
        for caas_session in session_requests:
            if True:
                if caas_session.coach:
                    coach = caas_session.coach
                    coach_name = coach.first_name + " " + coach.last_name
                    phone = coach.phone_country_code + coach.phone
                    time = caas_session.confirmed_availability.start_time
                    # final_time = datetime.fromtimestamp(
                    #     (int(time) / 1000) + 19800
                    # ).strftime("%I:%M %p")
                    final_time = get_time(int(time))
                    booking_id = caas_session.coach.room_id
                    print(booking_id)
                    send_whatsapp_message_template(
                        phone,
                        {
                            "broadcast_name": "send_coach_morning_reminder_whatsapp_message_at_8AM_caas",
                            "parameters": [
                                {
                                    "name": "name",
                                    "value": coach_name,
                                },
                                {
                                    "name": "time",
                                    "value": f"{final_time} IST",
                                },
                                {
                                    "name": "booking_id",
                                    "value": booking_id,
                                },
                            ],
                            "template_name": "training_reminders_final",
                        },
                    )
    except Exception as e:
        print(str(e))


@shared_task
def send_participant_morning_reminder_whatsapp_message_at_8AM_seeq():
    try:
        start_timestamp, end_timestamp = get_current_date_timestamps()
        # schedular sessions scheduled today
        today_sessions = SchedularSessions.objects.filter(
            availibility__start_time__lte=end_timestamp,
            availibility__end_time__gte=start_timestamp,
        )
        for session in today_sessions:
            if session.coaching_session.batch.project.automated_reminder:
                name = session.learner.name
                phone = session.learner.phone
                booking_id = session.availibility.coach.room_id
                # time = datetime.fromtimestamp(
                #     (int(session.availibility.start_time) / 1000) + 19800
                # ).strftime("%I:%M %p")
                time = get_time(int(session.availibility.start_time))
                send_whatsapp_message_template(
                    phone,
                    {
                        "broadcast_name": "send_participant_morning_reminder_whatsapp_message_at_8AM_seeq",
                        "parameters": [
                            {
                                "name": "name",
                                "value": name,
                            },
                            {
                                "name": "time",
                                "value": f"{time} IST",
                            },
                            {
                                "name": "booking_id",
                                "value": booking_id,
                            },
                        ],
                        "template_name": "training_reminders_final",
                    },
                )
    except Exception as e:
        print(str(e))


@shared_task
def send_participant_morning_reminder_whatsapp_message_at_8AM_caas():
    try:
        start_timestamp, end_timestamp = get_current_date_timestamps()
        # caas_Sessions scheduled today
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__gte=start_timestamp),
            Q(confirmed_availability__start_time__lte=end_timestamp),
            ~Q(status="completed"),
        )
        for caas_session in session_requests:
            if caas_session.project.automated_reminder:
                learner = caas_session.learner
                learner_name = learner.name
                phone = learner.phone
                time = caas_session.confirmed_availability.start_time
                # final_time = datetime.fromtimestamp(
                #     (int(time) / 1000) + 19800
                # ).strftime("%I:%M %p")
                final_time = get_time(int(time))
                booking_id = caas_session.coach.room_id
                send_whatsapp_message_template(
                    phone,
                    {
                        "broadcast_name": "send_participant_morning_reminder_whatsapp_message_at_8AM_caas",
                        "parameters": [
                            {
                                "name": "name",
                                "value": learner_name,
                            },
                            {
                                "name": "time",
                                "value": f"{final_time} IST",
                            },
                            {
                                "name": "booking_id",
                                "value": booking_id,
                            },
                        ],
                        "template_name": "training_reminders_final",
                    },
                )
    except Exception as e:
        print(str(e))


@shared_task
def send_whatsapp_reminder_to_users_before_5mins_in_caas(session_id):
    try:
        # for caas sessions
        caas_session = SessionRequestCaas.objects.get(id=session_id)
        if True:
            if caas_session.coach:
                coach = caas_session.coach
                caas_coach_name = coach.first_name + " " + coach.last_name
                caas_coach_phone = coach.phone_country_code + coach.phone
                time = caas_session.confirmed_availability.start_time
                # caas_coach_final_time = datetime.fromtimestamp(
                #     (int(time) / 1000) + 19800
                # ).strftime("%I:%M %p")
                caas_coach_final_time = get_time(int(time))
                booking_id = caas_session.coach.room_id
                send_whatsapp_message_template(
                    caas_coach_phone,
                    {
                        "broadcast_name": "send_whatsapp_reminder_to_users_before_5mins_in_caas_to_coach",
                        "parameters": [
                            {
                                "name": "name",
                                "value": caas_coach_name,
                            },
                            {
                                "name": "time",
                                "value": f"{caas_coach_final_time} IST",
                            },
                            {
                                "name": "booking_id",
                                "value": booking_id,
                            },
                        ],
                        "template_name": "session_reminder_5_mins_before_final",
                    },
                )
            learner = caas_session.learner
            caas_learner_name = learner.name
            caas_learner_phone = learner.phone
            time = caas_session.confirmed_availability.start_time
            # caas_learner_final_time = datetime.fromtimestamp(
            #     (int(time) / 1000) + 19800
            # ).strftime("%I:%M %p")
            caas_learner_final_time = get_time(int(time))
            send_whatsapp_message_template(
                caas_learner_phone,
                {
                    "broadcast_name": "send_whatsapp_reminder_to_users_before_5mins_in_caas_to_learner",
                    "parameters": [
                        {
                            "name": "name",
                            "value": caas_learner_name,
                        },
                        {
                            "name": "time",
                            "value": f"{caas_learner_final_time} IST",
                        },
                        {
                            "name": "booking_id",
                            "value": booking_id,
                        },
                    ],
                    "template_name": "session_reminder_5_mins_before_final",
                },
            )
    except Exception as e:
        print(str(e))


@shared_task
def send_whatsapp_reminder_to_users_before_5mins_in_seeq(session_id):
    try:
        # for seeq sessions
        session = SchedularSessions.objects.get(id=session_id)
        if True:
            # seeq_coach_start_time_for_mail = datetime.fromtimestamp(
            #     (int(session.availibility.start_time) / 1000) + 19800
            # ).strftime("%I:%M %p")
            seeq_coach_start_time_for_mail = get_time(
                int(session.availibility.start_time)
            )
            seeq_coach_phone = (
                session.availibility.coach.phone_country_code
                + session.availibility.coach.phone
            )
            coach_name = (
                session.availibility.coach.first_name
                + " "
                + session.availibility.coach.last_name
            )
            booking_id = session.availibility.coach.room_id
            send_whatsapp_message_template(
                seeq_coach_phone,
                {
                    "broadcast_name": "send_whatsapp_message_reminder_before_5mins_to_joinees_in_seeq_to_Coach",
                    "parameters": [
                        {
                            "name": "name",
                            "value": coach_name,
                        },
                        {
                            "name": "time",
                            "value": f"{seeq_coach_start_time_for_mail} IST",
                        },
                        {
                            "name": "booking_id",
                            "value": booking_id,
                        },
                    ],
                    "template_name": "session_reminder_5_mins_before_final",
                },
            )
            seeq_participant_name = session.learner.name
            seeq_participant_phone = session.learner.phone
            # seeq_participant_time = datetime.fromtimestamp(
            #     (int(session.availibility.start_time) / 1000) + 19800
            # ).strftime("%I:%M %p")
            seeq_participant_time = get_time(int(session.availibility.start_time))
            send_whatsapp_message_template(
                seeq_participant_phone,
                {
                    "broadcast_name": "send_whatsapp_message_reminder_before_5mins_to_joinees_in_seeq_to_participant",
                    "parameters": [
                        {
                            "name": "name",
                            "value": seeq_participant_name,
                        },
                        {
                            "name": "time",
                            "value": f"{seeq_participant_time} IST",
                        },
                        {
                            "name": "booking_id",
                            "value": booking_id,
                        },
                    ],
                    "template_name": "session_reminder_5_mins_before_final",
                },
            )
    except Exception as e:
        print(str(e))


@shared_task
def send_whatsapp_reminder_to_users_after_3mins_in_seeq(session_id):
    try:
        # for seeq sessions
        session = SchedularSessions.objects.get(id=session_id)
        if True:
            # seeq_coach_start_time_for_mail = datetime.fromtimestamp(
            #     (int(session.availibility.start_time) / 1000) + 19800
            # ).strftime("%I:%M %p")
            seeq_coach_start_time_for_mail = get_time(
                int(session.availibility.start_time)
            )
            seeq_coach_phone = (
                session.availibility.coach.phone_country_code
                + session.availibility.coach.phone
            )
            coach_name = (
                session.availibility.coach.first_name
                + " "
                + session.availibility.coach.last_name
            )
            send_whatsapp_message_template(
                seeq_coach_phone,
                {
                    "broadcast_name": "send_whatsapp_reminder_to_users_after_3mins_in_seeq",
                    "parameters": [
                        {
                            "name": "name",
                            "value": coach_name,
                        },
                        {
                            "name": "time",
                            "value": f"{seeq_coach_start_time_for_mail} IST",
                        },
                    ],
                    "template_name": "did_you_start_session_msg_to_coach",
                },
            )
    except Exception as e:
        print(str(e))


@shared_task
def send_whatsapp_reminder_to_users_after_3mins_in_caas(session_id):
    try:
        # for caas sessions
        caas_session = SessionRequestCaas.objects.get(id=session_id)
        if True:
            if caas_session.coach:
                coach = caas_session.coach
                caas_coach_name = coach.first_name + " " + coach.last_name
                caas_coach_phone = coach.phone_country_code + coach.phone
                time = caas_session.confirmed_availability.start_time
                # caas_coach_final_time = datetime.fromtimestamp(
                #     (int(time) / 1000) + 19800
                # ).strftime("%I:%M %p")
                caas_coach_final_time = get_time(int(time))
                send_whatsapp_message_template(
                    caas_coach_phone,
                    {
                        "broadcast_name": "whatsapp reminder after 3 mins",
                        "parameters": [
                            {
                                "name": "name",
                                "value": caas_coach_name,
                            },
                            {
                                "name": "time",
                                "value": f"{caas_coach_final_time} IST",
                            },
                        ],
                        "template_name": "did_you_start_session_msg_to_coach",
                    },
                )
    except Exception as e:
        print(str(e))


@shared_task
def coachee_booking_reminder_whatsapp_at_8am():
    try:
        current_date = timezone.now().date()
        coaching_sessions_exist = CoachingSession.objects.filter(
            expiry_date__isnull=False, expiry_date__gt=current_date
        )
        for coaching_session in coaching_sessions_exist:
            result = available_slots_count_for_participant(coaching_session.id)
            if coaching_session.batch.project.automated_reminder:
                learners_in_coaching_session = coaching_session.batch.learners.all()
                for learner in learners_in_coaching_session:
                    try:
                        SchedularSessions.objects.get(
                            learner=learner, coaching_session=coaching_session
                        )
                        print(f"Don't send WhatsApp message to {learner.name}")
                    except ObjectDoesNotExist:
                        name = learner.name
                        phone = learner.phone
                        if len(result) != 0:
                            session_name = (
                                coaching_session.session_type.replace("_", " ").capitalize()
                                if not coaching_session.session_type
                                == "laser_coaching_session"
                                else "Coaching Session"
                                + " "
                                + str(coaching_session.coaching_session_number)
                            )
                            project_name = coaching_session.batch.project.name
                            path_parts = coaching_session.booking_link.split("/")
                            booking_id = path_parts[-1]
                            send_whatsapp_message_template(
                                phone,
                                {
                                    "broadcast_name": "coachee_booking_reminder_whatsapp_at_8am",
                                    "parameters": [
                                        {
                                            "name": "name",
                                            "value": name,
                                        },
                                        {
                                            "name": "session_name",
                                            "value": session_name,
                                        },
                                        {
                                            "name": "project_name",
                                            "value": project_name,
                                        },
                                        {
                                            "name": "1",
                                            "value": booking_id,
                                        },
                                    ],
                                    "template_name": "reminder_coachee_book_slot_daily",
                                },
                            )
                    except Exception as e:
                        print(str(e))
    except Exception as e:
        print(str(e))


@shared_task
def coach_has_to_give_slots_availability_reminder():
    try:
        current_date = timezone.now().date()
        for request_availability in RequestAvailibilty.objects.all():
            coaches = request_availability.coach.all()
            coaches_not_gave_availibility = coaches.exclude(
                Q(id__in=request_availability.provided_by)
                | Q(requestavailibilty__expiry_date__lte=current_date)
            )
            for coach in coaches_not_gave_availibility:
                name = coach.first_name + " " + coach.last_name
                expiry_date = request_availability.expiry_date
                phone = coach.phone_country_code + coach.phone
                expiry_date_string = expiry_date.strftime("%d-%m-%Y")
                send_whatsapp_message_template(
                    phone,
                    {
                        "broadcast_name": "reminder_for_coach_to_give_availability",
                        "parameters": [
                            {
                                "name": "name",
                                "value": name,
                            },
                            {
                                "name": "date",
                                "value": expiry_date_string,
                            },
                        ],
                        "template_name": "reminder_for_coach_availability",
                    },
                )
    except Exception as e:
        print(str(e))


@shared_task
def schedule_nudges(course_id):
    course = Course.objects.get(id=course_id)
    nudges = Nudge.objects.filter(course__id=course_id).order_by("order")

    desired_time = time(8, 30)
    nudge_scheduled_for = datetime.combine(course.nudge_start_date, desired_time)
    for nudge in nudges:
        if (
            nudge.course.batch.project.automated_reminder
            and nudge.course.batch.project.nudges
        ):
            clocked = ClockedSchedule.objects.create(clocked_time=nudge_scheduled_for)
            periodic_task = PeriodicTask.objects.create(
                name=uuid.uuid1(),
                task="schedularApi.tasks.send_nudge",
                args=[nudge.id],
                clocked=clocked,
                one_off=True,
            )
            nudge_scheduled_for = nudge_scheduled_for + timedelta(
                int(course.nudge_frequency)
            )


def get_file_content(file_url):
    response = requests.get(file_url)
    return response.content


@shared_task
def send_nudge(nudge_id):
    nudge = Nudge.objects.get(id=nudge_id)
    if (
        nudge.course.batch.project.automated_reminder
        and nudge.course.batch.project.nudges
    ):
        subject = f"New Nudge: {nudge.name}"
        if nudge.is_sent:
            return
        message = nudge.content
        if nudge.file:
            attachment_path = nudge.file.url
            file_content = get_file_content(nudge.file.url)

        for learner in nudge.course.batch.learners.all():
            email = EmailMessage(
                subject, message, settings.DEFAULT_FROM_EMAIL, [learner.email]
            )
            if nudge.file:
                extension = get_file_extension(nudge.file.url)
                file_name = f"Attatchment.{extension}"
                email.attach(file_name, file_content, f"application/{extension}")
            email.content_subtype = "html"
            email.send()
            sleep(5)
        nudge.is_sent = True
        nudge.save()
