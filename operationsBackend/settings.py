"""
Django settings for operationsBackend project.

Generated by 'django-admin startproject' using Django 3.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import environ
import os
import json
from celery.schedules import crontab
from datetime import timedelta


env = environ.Env()
environ.Env.read_env()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-@4lj39m8fw$6-h66bk=!!8qws9jo!7vg-i@m+r&3c+z&iiabk@"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

ALLOWED_HOSTS = [env("ALLOWED_HOSTS")]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "api",
    "zohoapi",
    "schedularApi",
    "assessmentApi",
    "courses",
    "rest_framework.authtoken",
    "django_rest_passwordreset",
    "corsheaders",
    "django_celery_beat",
    "django_celery_results",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "api.middlewares.APILoggingMiddleware",
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True

ROOT_URLCONF = "operationsBackend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "operationsBackend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASS"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
        "OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# PROD ONLY
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CORS_ALLOWED_ORIGINS = json.loads(env("CORS_ALLOWED_ORIGINS"))
CSRF_TRUSTED_ORIGINS = json.loads(env("CSRF_TRUSTED_ORIGINS"))

CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]
CORS_ALLOW_CREDENTIALS = True

# Configure Django Storage Backend for Amazon S3
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
# AWS_DEFAULT_ACL = (
#     "public-read"  # Set the default access control list for the uploaded files
# )
# Set the region where your S3 bucket is located
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")  # Change this to the appropriate region

#  Set the S3 endpoint URL (optional, but useful if using a non-AWS S3-compatible service)
#  AWS_S3_ENDPOINT_URL = "https://your-s3-endpoint-url.com"

#  Use Amazon S3 for static and media files storage
DEFAULT_FILE_STORAGE = env("DEFAULT_FILE_STORAGE")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True

SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN")

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

CELERY_BEAT_SCHEDULE = {
    "coach_laser_coaching_session_reminder": {
        "task": "schedularApi.tasks.send_coach_morning_reminder_email",
        "schedule": crontab(hour=3, minute=30, day_of_week="*"),
    },
    "participant_laser_coaching_session_reminder": {
        "task": "schedularApi.tasks.send_participant_morning_reminder_email",
        "schedule": crontab(hour=3, minute=15, day_of_week="*"),
    },
    "send_upcoming_session_pmo_at_10am": {
        "task": "schedularApi.tasks.send_upcoming_session_pmo_at_10am",
        "schedule": crontab(hour=4, minute=30, day_of_week="*"),
    },
    "send_participant_morning_reminder_one_day_before_email": {
        "task": "schedularApi.tasks.send_participant_morning_reminder_one_day_before_email",
        "schedule": crontab(hour=3, minute=0, day_of_week="*"),
    },
    "send_coach_morning_reminder_whatsapp_message_at_8AM_seeq": {
        "task": "schedularApi.tasks.send_coach_morning_reminder_whatsapp_message_at_8AM_seeq",
        "schedule": crontab(hour=2, minute=30, day_of_week="*"),
    },
    "send_coach_morning_reminder_whatsapp_message_at_8AM_caas": {
        "task": "schedularApi.tasks.send_coach_morning_reminder_whatsapp_message_at_8AM_caas",
        "schedule": crontab(hour=2, minute=30, day_of_week="*"),
    },
    "send_participant_morning_reminder_whatsapp_message_at_8AM_seeq": {
        "task": "schedularApi.tasks.send_participant_morning_reminder_whatsapp_message_at_8AM_seeq",
        "schedule": crontab(hour=2, minute=30, day_of_week="*"),
    },
    "send_participant_morning_reminder_whatsapp_message_at_8AM_caas": {
        "task": "schedularApi.tasks.send_participant_morning_reminder_whatsapp_message_at_8AM_caas",
        "schedule": crontab(hour=2, minute=30, day_of_week="*"),
    },
    "send_reminder_email_to_participants_for_assessment_at_2PM": {
        "task": "schedularApi.tasks.send_reminder_email_to_participants_for_assessment_at_2PM",
        "schedule": crontab(hour=8, minute=30, day_of_week="*"),
    },
    "send_whatsapp_message_to_participants_for_assessment_at_9AM": {
        "task": "schedularApi.tasks.send_whatsapp_message_to_participants_for_assessment_at_9AM",
        "schedule": crontab(hour=3, minute=30, day_of_week="*"),
    },
    # "send_whatsapp_message_to_participants_for_assessment_at_7PM": {
    #     "task": "schedularApi.tasks.send_whatsapp_message_to_participants_for_assessment_at_7PM",
    #     "schedule": crontab(hour=13, minute=30, day_of_week="*"),
    # },
    "update_assessment_status": {
        "task": "schedularApi.tasks.update_assessment_status",
        "schedule": crontab(hour=1, minute=30, day_of_week="*"),  #  7 AM
    },
    "refreshing_user_tokens": {
        "task": "schedularApi.tasks.refresh_user_tokens",
        "schedule": timedelta(hours=12),  # every 12 hours
    },
    "send_whatsapp_reminder_1_day_before_live_session": {
        "task": "schedularApi.tasks.send_whatsapp_reminder_1_day_before_live_session",
        "schedule": crontab(hour=12, minute=30),  # 6 PM
    },
    "send_whatsapp_reminder_same_day_morning": {
        "task": "schedularApi.tasks.send_whatsapp_reminder_same_day_morning",
        "schedule": crontab(hour=2, minute=30),  # 8 AM
    },
    "send_feedback_lesson_reminders": {
        "task": "schedularApi.tasks.send_feedback_lesson_reminders",
        "schedule": crontab(hour=13, minute=0),  # 8 AM
    },
    "send_reminder_to_book_slots_to_coachee": {
        "task": "schedularApi.tasks.send_reminder_to_book_slots_to_coachee",
        "schedule": crontab(hour=2, minute=30, day_of_week="*"),
    },
    "coach_has_to_give_slots_availability_reminder": {
        "task": "schedularApi.tasks.coach_has_to_give_slots_availability_reminder",
        "schedule": crontab(hour=2, minute=30, day_of_week="*"),
    },
    "coachee_booking_reminder_whatsapp_at_8am": {
        "task": "schedularApi.tasks.coachee_booking_reminder_whatsapp_at_8am",
        "schedule": crontab(hour=2, minute=30, day_of_week="*"),
    },
    "update_schedular_session_status": {
        "task": "schedularApi.tasks.update_schedular_session_status",
        "schedule": crontab(hour=16, minute=30, day_of_week="*"),  # 10 PM Night
    },
    "generate_invoice_reminder_on_first_of_month": {
        "task": "schedularApi.tasks.generate_invoice_reminder_on_first_of_month",
        "schedule": crontab(hour=3, minute=30, day_of_month="25"),  # 10 AM IST
    },
    "generate_invoice_reminder_once_when_po_is_created": {
        "task": "schedularApi.tasks.generate_invoice_reminder_once_when_po_is_created",
        "schedule": crontab(hour=3, minute=30, day_of_month="2-31"),  # 10 AM IST
    },
    "reminder_to_pmo_bank_details_unavailable": {
        "task": "schedularApi.tasks.reminder_to_pmo_bank_details_unavailable",
        "schedule": crontab(hour=3, minute=30, day_of_week="mon"),  # 10 AM IST Monday
    },
    "weekly_invoice_approval_reminder": {
        "task": "schedularApi.tasks.weekly_invoice_approval_reminder",
        "schedule": crontab(hour=3, minute=30, day_of_week="mon"),  # 10 AM IST Monday
    },
}


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",  # Optional
        # Other authentication classes if needed
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
