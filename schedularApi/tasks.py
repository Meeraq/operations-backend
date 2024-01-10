import string
from celery import shared_task
from .models import SentEmail, SchedularSessions
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from django.conf import settings
from api.models import Coach, User, UserToken
from django.utils import timezone
from datetime import datetime
from api.views import send_mail_templates, refresh_microsoft_access_token
# /from assessmentApi.views import send_whatsapp_message
from django.core.exceptions import ObjectDoesNotExist
from assessmentApi.models import Assessment, ParticipantResponse, ParticipantUniqueId
from django.db.models import Q
import environ
from time import sleep

env = environ.Env()
environ.Env.read_env()


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
            "broadcast_name": "Testing 19th postman",
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
    except Exception as e:
        return {"error": str(e)}, 500

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
        coach_id = session.availibility.coach.id
        if coach_id not in coach_sessions:
            coach_sessions[coach_id] = []
        coach_sessions[coach_id].append(session)
    # Create time slots for each coach
    coach_time_slots = {}
    for coach_id, sessions in coach_sessions.items():
        slots = []
        for session in sessions:
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
        name = session.learner.name
        meeting_link = (
            f"{env('CAAS_APP_URL')}/coaching/join/{session.availibility.coach.room_id}"
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
        name = session.learner.name
        meeting_link = (
            f"{env('CAAS_APP_URL')}/coaching/join/{session.availibility.coach.room_id}"
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

        if (
            start_date <= today <= end_date
            and not day_of_week == "Saturday"
            and not day_of_week == "Sunday"
        ):
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
        if (
            start_date <= today <= end_date
            and not day_of_week == "Saturday"
            and not day_of_week == "Sunday"
        ):
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
        if (
            start_date <= today <= end_date
            and not day_of_week == "Saturday"
            and not day_of_week == "Sunday"
        ):
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
        except Exception as  e:
            print(str(e))
            pass
        sleep(5)
        
