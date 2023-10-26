import string
from celery import shared_task
from .models import SentEmail
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from django.conf import settings

# from api.views import refresh_microsoft_access_token
import environ

# from datetime import datetime, timedelta
from time import sleep


env = environ.Env()
environ.Env.read_env()


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


# @shared_task
# def refresh_user_tokens():
#     users = UserToken.objects.filter(account_type="microsoft")
#     for user in users:
#         refresh_microsoft_access_token(user)
#         print(f"token refresh for {user.user_mail}")


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
