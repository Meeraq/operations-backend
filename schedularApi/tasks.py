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
from api.models import Coach, User, UserToken, SessionRequestCaas, Learner, Project
from schedularApi.models import (
    CoachingSession,
    SchedularSessions,
    RequestAvailibilty,
    CoachSchedularAvailibilty,
    SchedularProject,
    SchedularBatch,
    Task,
)
from django.db import transaction
from django.utils import timezone
from api.views import (
    send_mail_templates,
    refresh_microsoft_access_token,
    generateManagementToken,
    create_send_email,
    add_contact_in_wati,
    create_task,
    get_live_session_name,
)
from datetime import datetime, timedelta
from schedularApi.serializers import AvailabilitySerializer
from datetime import timedelta, time, datetime, date
import pytz
import json

# /from assessmentApi.views import send_whatsapp_message
from django.core.exceptions import ObjectDoesNotExist
from assessmentApi.models import (
    Assessment,
    ParticipantResponse,
    ParticipantUniqueId,
    ObserverUniqueId,
    ObserverResponse,
    ParticipantObserverType,
    Competency,
    ParticipantReleasedResults,
)
from courses.models import (
    Course,
    Lesson,
    FeedbackLesson,
    FeedbackLessonResponse,
    Nudge,
    Assessment as AssessmentLesson,
    CourseEnrollment,
)
from django.db.models import Q
from assessmentApi.models import Assessment, ParticipantResponse
import environ
from time import sleep
import requests
from zohoapi.models import (
    Vendor,
    PoReminder,
    SalesOrder,
    SalesOrderLineItem,
    OrdersAndProjectMapping,
)
from zohoapi.views import (
    filter_purchase_order_data,
)
from zohoapi.tasks import get_access_token, organization_id, base_url
from courses.serializers import NudgeSerializer
from api.models import Role, Profile
import matplotlib.pyplot as plt

env = environ.Env()
environ.Env.read_env()
import random
import io
from io import BytesIO
import base64
import numpy as np


def swap_positions(length):
    numbers = list(range(1, length + 1))

    midpoint = length // 2

    for i in range(midpoint):
        numbers[i], numbers[-(i + 1)] = numbers[-(i + 1)], numbers[i]

    swapped_dict = {
        orig: swapped for orig, swapped in zip(range(1, length + 1), numbers)
    }
    return swapped_dict


def generate_graph_for_pre_assessment(competency_percentage, total_for_each_comp):
    comp_labels = list(competency_percentage.keys())
    percentage_values = list(competency_percentage.values())
    colors1 = ["#eb0081", "#d1cdcd"]
    colors2 = ["#b91689", "#d1cdcd"]
    colors3 = ["#7a3191", "#d1cdcd"]
    colors4 = ["#374e9c", "#d1cdcd"]

    fig = plt.figure(figsize=(15, len(comp_labels) * 0.6 + 3))
    ax = fig.add_subplot(111)

    bottom = np.zeros(len(comp_labels))
    bar_positions = np.arange(len(comp_labels))
    for i in range(len(comp_labels)):
        color_index = i % 4  # Use modulo to repeat colors after every four bars

        if color_index == 0:
            color = colors1
        elif color_index == 1:
            color = colors2
        elif color_index == 2:
            color = colors3
        else:
            color = colors4

        ax.barh(comp_labels[i], percentage_values[i], color=color, left=bottom[i])

    for index, value in enumerate(percentage_values):
        # new_value = value / 100 * total_for_each_comp[comp_labels[index]]
        ax.text(
            value,
            bar_positions[index],
            f"{value}%",
            ha="left",
            va="center",
            color="black",
        )
    ax.set_yticks(bar_positions)
    ax.set_yticklabels(
        [f"{comp}\n" if len(comp) > 15 else comp for comp in comp_labels],
        fontweight="bold",
        fontsize=14,
    )
    plt.title("Your Awareness Level", fontweight="bold", fontsize=14)
    plt.xlim(0, 100)
    plt.xlabel("Percentage")
    plt.tight_layout()

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="png")
    plt.close()

    encoded_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return encoded_image


def generate_graph_for_pre_post_assessment(
    pre_competency_percentage, competency_percentage, total_for_each_comp
):
    comp_labels = list(competency_percentage.keys())
    pre_percentage_values = list(pre_competency_percentage.values())
    post_percentage_values = list(competency_percentage.values())

    fig = plt.figure(figsize=(15, len(comp_labels) * 0.6 + 5))
    ax = fig.add_subplot(111)

    width = 0.4  # Width of each bar
    bar_positions = np.arange(len(comp_labels))

    # Plot pre-assessment values
    pre_bars = ax.barh(
        bar_positions - width / 2,
        pre_percentage_values,
        height=width,
        label="Pre-Assessment",
        color="#eb0081",
    )

    # Plot post-assessment values
    post_bars = ax.barh(
        bar_positions + width / 2,
        post_percentage_values,
        height=width,
        label="Post-Assessment",
        color="#374e9c",
    )

    ax.set_yticks(bar_positions)
    ax.set_yticklabels(comp_labels)
    ax.legend()
    ax.set_yticklabels(
        [f"{comp}\n" if len(comp) > 15 else comp for comp in comp_labels],
        fontweight="bold",
    )
    plt.title("Your Awareness Level", fontweight="bold", fontsize=14)
    plt.xlabel("Percentage")
    plt.xlim(0, 100)
    plt.tight_layout()

    # Add numbers on top of the pre-assessment bars
    for index, value in enumerate(pre_percentage_values):
        # new_value = value / 100 * total_for_each_comp[comp_labels[index]]
        ax.text(
            value,
            bar_positions[index] - width / 2,
            f"{value}%",
            ha="left",
            va="center",
            color="black",
        )

    # Add numbers on top of the post-assessment bars
    for index, value in enumerate(post_percentage_values):
        # new_value = value / 100 * total_for_each_comp[comp_labels[index]]
        ax.text(
            value,
            bar_positions[index] + width / 2,
            f"{value}%",
            ha="left",
            va="center",
            color="black",
        )

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format="png")
    plt.close()

    encoded_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return encoded_image


def generate_graph_for_participant(
    participant, assessment_id, assessment, project_wise=False
):
    participant_response = ParticipantResponse.objects.filter(
        participant__id=participant.id, assessment__id=assessment_id
    ).first()

    if participant_response:
        total_for_each_comp = {}
        compentency_with_description = []

        for competency in assessment.questionnaire.questions.values(
            "competency"
        ).distinct():
            competency_id = competency["competency"]

            competency_name_for_object = Competency.objects.get(id=competency_id).name
            competency_description_for_object = Competency.objects.get(
                id=competency_id
            ).description
            competency_object = {
                "competency_name": competency_name_for_object,
                "competency_description": competency_description_for_object,
            }
            compentency_with_description.append(competency_object)

        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in total_for_each_comp:
                total_for_each_comp[question.competency.name] = 1
            else:
                total_for_each_comp[question.competency.name] += 1

        competency_object = {}
        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in competency_object:
                competency_object[question.competency.name] = 0

            participant_response_value = participant_response.participant_response.get(
                str(question.id)
            )

            if question.response_type == "correct_answer":
                correct_answer = (
                    assessment.questionnaire.questions.filter(id=question.id)
                    .first()
                    .correct_answer
                )

                if str(participant_response_value) in correct_answer:
                    competency_object[question.competency.name] = (
                        competency_object[question.competency.name] + 1
                    )

            elif question.response_type == "rating_type":
                if participant_response_value:
                    label_count = sum(
                        1 for key in question.label.keys() if question.label[key]
                    )
                    if not question.reverse_question:

                        swap_dict = swap_positions(label_count)

                        competency_object[question.competency.name] = competency_object[
                            question.competency.name
                        ] + (swap_dict[participant_response_value] / label_count)
                    else:

                        competency_object[question.competency.name] = competency_object[
                            question.competency.name
                        ] + (participant_response_value / label_count)

        competency_percentage = {}
        for comp in total_for_each_comp:
            competency_percentage[comp] = round(
                (competency_object[comp] / total_for_each_comp[comp]) * 100
            )

        if project_wise:
            return competency_percentage

        encoded_image = generate_graph_for_pre_assessment(
            competency_percentage, total_for_each_comp
        )

        return encoded_image, compentency_with_description

    if project_wise:
        return None

    return None, None


def generate_graph_for_participant_for_post_assessment(
    participant, assessment_id, assessment, project_wise=False
):
    participant_response = ParticipantResponse.objects.filter(
        participant__id=participant.id, assessment__id=assessment_id
    ).first()

    pre_assessment_participant_response = ParticipantResponse.objects.filter(
        participant__id=participant.id, assessment__id=assessment.pre_assessment.id
    ).first()

    if participant_response and pre_assessment_participant_response:
        total_for_each_comp = {}
        compentency_with_description = []

        for competency in assessment.questionnaire.questions.values(
            "competency"
        ).distinct():
            competency_id = competency["competency"]

            competency_name_for_object = Competency.objects.get(id=competency_id).name
            competency_description_for_object = Competency.objects.get(
                id=competency_id
            ).description
            competency_object = {
                "competency_name": competency_name_for_object,
                "competency_description": competency_description_for_object,
            }
            compentency_with_description.append(competency_object)

        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in total_for_each_comp:
                total_for_each_comp[question.competency.name] = 1
            else:
                total_for_each_comp[question.competency.name] += 1

        competency_object = {}
        pre_competency_object = {}
        for question in assessment.questionnaire.questions.all():
            if question.response_type == "descriptive":
                continue
            if question.competency.name not in competency_object:
                competency_object[question.competency.name] = 0
            if question.competency.name not in pre_competency_object:
                pre_competency_object[question.competency.name] = 0

            participant_response_value = participant_response.participant_response.get(
                str(question.id)
            )
            pre_assessment_participant_response_value = (
                pre_assessment_participant_response.participant_response.get(
                    str(question.id)
                )
            )

            if question.response_type == "correct_answer":

                correct_answer = (
                    assessment.questionnaire.questions.filter(id=question.id)
                    .first()
                    .correct_answer
                )

                if str(pre_assessment_participant_response_value) in correct_answer:

                    pre_competency_object[question.competency.name] = (
                        pre_competency_object[question.competency.name] + 1
                    )

                if str(participant_response_value) in correct_answer:
                    competency_object[question.competency.name] = (
                        competency_object[question.competency.name] + 1
                    )

            elif question.response_type == "rating_type":
                if participant_response_value:
                    label_count = sum(
                        1 for key in question.label.keys() if question.label[key]
                    )
                    swap_dict = swap_positions(label_count)
                    if pre_assessment_participant_response_value:
                        if not question.reverse_question:

                            pre_competency_object[
                                question.competency.name
                            ] = pre_competency_object[question.competency.name] + (
                                swap_dict[pre_assessment_participant_response_value]
                                / label_count
                            )
                        else:
                            pre_competency_object[
                                question.competency.name
                            ] = pre_competency_object[question.competency.name] + (
                                pre_assessment_participant_response_value / label_count
                            )

                    if participant_response_value:
                        if not question.reverse_question:
                            competency_object[question.competency.name] = (
                                competency_object[question.competency.name]
                                + (swap_dict[participant_response_value] / label_count)
                            )
                        else:
                            competency_object[question.competency.name] = (
                                competency_object[question.competency.name]
                                + (participant_response_value / label_count)
                            )

        competency_percentage = {}
        pre_competency_percentage = {}
        for comp in total_for_each_comp:
            competency_percentage[comp] = round(
                (competency_object[comp] / total_for_each_comp[comp]) * 100
            )
            pre_competency_percentage[comp] = round(
                (pre_competency_object[comp] / total_for_each_comp[comp]) * 100
            )

        if project_wise:
            return pre_competency_percentage, competency_percentage
        encoded_image = generate_graph_for_pre_post_assessment(
            pre_competency_percentage, competency_percentage, total_for_each_comp
        )

        return encoded_image, compentency_with_description

    return None, None


def create_learner(learner_name, learner_email, learner_phone=None):
    try:
        with transaction.atomic():
            learner_email = learner_email.strip().lower()
            temp_password = "".join(
                random.choices(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits,
                    k=8,
                )
            )
            user = User.objects.create_user(
                username=learner_email,
                password=temp_password,
                email=learner_email,
            )
            user.save()
            learner_role, created = Role.objects.get_or_create(name="learner")
            profile = Profile.objects.create(user=user)
            profile.roles.add(learner_role)
            profile.save()

            phone = learner_phone if learner_phone else None
            learner = None
            if phone:
                learner = Learner.objects.create(
                    user=profile,
                    name=learner_name.strip().title(),
                    email=learner_email,
                    phone=phone,
                )
            else:
                learner = Learner.objects.create(
                    user=profile,
                    name=learner_name.strip().title(),
                    email=learner_email,
                )

            return learner

    except Exception as e:
        return None


def create_or_get_learner(learner_data):
    try:
        # check if the same email user exists or not
        phone = learner_data.get("phone", None)
        user = User.objects.filter(username=learner_data["email"]).first()
        if user:
            if user.profile.roles.all().filter(name="learner").exists():
                learner = Learner.objects.get(user=user.profile)
                learner.name = learner_data["name"].strip()

                if learner_data["phone"]:
                    learner.phone = learner_data["phone"]

                learner.save()
                return learner
            else:
                learner_role, created = Role.objects.get_or_create(name="learner")
                learner_profile = user.profile
                learner_profile.roles.add(learner_role)
                learner_role.save()

                learner, created = Learner.objects.get_or_create(
                    user=learner_profile,
                    defaults={
                        "name": learner_data["name"],
                        "email": learner_data["email"],
                        "phone": phone,
                    },
                )
                return learner
        else:
            learner = create_learner(learner_data["name"], learner_data["email"], phone)
            return learner
    except Exception as e:
        # Handle specific exceptions or log the error
        print(f"Error processing participant: {str(e)}")


def timestamp_to_datetime(timestamp):
    return datetime.utcfromtimestamp(int(timestamp) / 1000.0)


def get_live_session_name(session_type):
    session_name = None
    if session_type == "live_session":
        session_name = "Live Session"
    elif session_type == "check_in_session":
        session_name = "Check In Session"
    elif session_type == "in_person_session":
        session_name = "In Person Session"
    elif session_type == "kickoff_session":
        session_name = "Kickoff Session"
    elif session_type == "virtual_session":
        session_name = "Virtual Session"
    elif session_type == "pre_study":
        session_name = "Pre Study"
    return session_name


def get_nudges_of_course(course):
    try:
        data = []
        nudges = Nudge.objects.filter(batch__id=course.batch.id).order_by("order")
        desired_time = time(8, 30)
        if course.batch.nudge_start_date:
            nudge_scheduled_for = datetime.combine(
                course.batch.nudge_start_date, desired_time
            )
            for nudge in nudges:
                temp = {
                    "is_sent": nudge.is_sent,
                    "name": nudge.name,
                    "learner_count": nudge.batch.learners.count(),
                    "batch_name": nudge.batch.name,
                    "nudge_scheduled_for": nudge_scheduled_for,
                }

                data.append(temp)
                nudge_scheduled_for = nudge_scheduled_for + timedelta(
                    int(course.batch.nudge_frequency)
                )
        return data
    except Exception as e:
        print(str(e))


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


def get_coaching_session_according_to_time(
    schedular_session, time_period, start_time=None, end_time=None
):
    current_time = timezone.now()

    if time_period == "upcoming":
        filter_criteria = {
            "availibility__end_time__gt": current_time.timestamp() * 1000
        }
    elif time_period == "past":
        filter_criteria = {
            "availibility__end_time__lt": current_time.timestamp() * 1000
        }
    elif time_period == "today":
        start_of_day = (
            current_time.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            * 1000
        )

        end_of_day = (
            current_time.replace(
                hour=23, minute=59, second=59, microsecond=999999
            ).timestamp()
            * 1000
        )
        filter_criteria = {"availibility__end_time__range": (start_of_day, end_of_day)}
    elif time_period == "tomorrow":
        tomorrow = current_time + timedelta(days=1)
        start_of_tomorrow = (
            tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            * 1000
        )
        end_of_tomorrow = (
            tomorrow.replace(
                hour=23, minute=59, second=59, microsecond=999999
            ).timestamp()
            * 1000
        )
        filter_criteria = {
            "availibility__end_time__range": (start_of_tomorrow, end_of_tomorrow)
        }
    elif time_period == "yesterday":
        yesterday = current_time - timedelta(days=1)
        start_of_yesterday = (
            yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
            * 1000
        )
        end_of_yesterday = (
            yesterday.replace(
                hour=23, minute=59, second=59, microsecond=999999
            ).timestamp()
            * 1000
        )
        filter_criteria = {
            "availibility__end_time__range": (start_of_yesterday, end_of_yesterday)
        }
    elif time_period == "duration":
        if start_time is None or end_time is None:
            raise ValueError(
                "Start time and end time must be provided for duration filter."
            )
        filter_criteria = {"availibility__end_time__range": (start_time, end_time)}
    else:
        raise ValueError("Invalid time period.")

    # Apply additional filter criteria if necessary
    if time_period != "duration":
        upcoming_schedular_sessions = schedular_session.filter(**filter_criteria)
    else:
        upcoming_schedular_sessions = schedular_session.filter(
            availibility__end_time__range=(start_time, end_time), **filter_criteria
        )

    return upcoming_schedular_sessions


def get_live_session_according_to_time(
    session, time_period, start_time=None, end_time=None
):
    current_time = timezone.now()

    if time_period == "upcoming":
        filter_criteria = {"date_time__gt": current_time}
    elif time_period == "past":
        filter_criteria = {"date_time__lt": current_time}
    elif time_period == "today":
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = current_time.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        filter_criteria = {"date_time__range": (start_of_day, end_of_day)}
    elif time_period == "tomorrow":
        tomorrow = current_time + timedelta(days=1)
        start_of_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_tomorrow = tomorrow.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        filter_criteria = {"date_time__range": (start_of_tomorrow, end_of_tomorrow)}
    elif time_period == "yesterday":
        yesterday = current_time - timedelta(days=1)
        start_of_yesterday = yesterday.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_yesterday = yesterday.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        filter_criteria = {"date_time__range": (start_of_yesterday, end_of_yesterday)}
    elif time_period == "duration":
        if start_time is None or end_time is None:
            raise ValueError(
                "Start time and end time must be provided for duration filter."
            )
        filter_criteria = {"date_time__range": (start_time, end_time)}
    else:
        raise ValueError("Invalid time period.")

    live_sessions = session.filter(**filter_criteria)

    return live_sessions


def get_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000) + timedelta(
        hours=5, minutes=30
    )  # Convert milliseconds to seconds
    return dt.strftime("%I:%M %p")


def get_date_time(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000) + timedelta(
        hours=5, minutes=30
    )  # Convert milliseconds to seconds
    return dt.strftime("%d-%m-%Y %H:%M")


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
        if (
            session.coaching_session.batch.email_reminder
            and session.coaching_session.batch.project.status == "ongoing"
        ):
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
                    (int(session.availibility.end_time) / 1000) + 19800
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
        if (
            session.coaching_session.batch.email_reminder
            and session.coaching_session.batch.project.status == "ongoing"
        ):
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
def update_assessment_status():
    assessments = Assessment.objects.filter(~Q(assessment_timing="none"))
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
            assessment_lesson = AssessmentLesson.objects.filter(
                assessment_modal=assessment
            ).first()
            if assessment_lesson:
                assessment_lesson.lesson.status = "public"

                assessment_lesson.lesson.save()
                assessment_lesson.save()

        elif current_date > end_date:
            assessment.status = "completed"
        # Save the updated assessment
        assessment.save()


@shared_task
def send_assessment_invitation_mail(assessment_id):
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
                        "Meeraq - Welcome to Meeraq Assessment!",
                        {
                            "assessment_name": assessment.participant_view_name,
                            "participant_name": participant.name.title(),
                            "link": assessment_link,
                        },
                        [],
                    )
                    sleep(3)
            if (
                assessment.assessment_type == "360"
                or assessment.assessment_type == "90"
                or assessment.assessment_type == "270"
                or assessment.assessment_type == "180"
            ):
                for observer in participant_observers.observers.all():
                    observer_response = ObserverResponse.objects.filter(
                        observer=observer, assessment=assessment
                    ).first()
                    if not observer_response:
                        observer_unique_id = ObserverUniqueId.objects.filter(
                            observer=observer, assessment=assessment
                        ).first()
                        observer_link = f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{observer_unique_id.unique_id}"
                        send_mail_templates(
                            "assessment/assessment_email_to_observer.html",
                            [observer.email],
                            "Welcome to Meeraq Assessment!",
                            {
                                "assessment_name": assessment.participant_view_name,
                                "participant_name": participant.name.title(),
                                "observer_name": observer.name.title(),
                                "link": observer_link,
                            },
                            [],
                        )
                        sleep(3)
        except Exception as e:
            print(str(e))
            pass


@shared_task
def send_whatsapp_reminder_1_day_before_live_session():
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        live_sessions = LiveSession.objects.filter(date_time__date=tomorrow.date())

        for session in live_sessions:
            if (
                session.batch.whatsapp_reminder
                and session.batch.project.status == "ongoing"
            ):
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
                                    "value": f"{get_live_session_name(session.session_type)} {session.live_session_number}",
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
            if (
                session.batch.whatsapp_reminder
                and session.batch.project.status == "ongoing"
            ):
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
                                    "value": (
                                        session.description
                                        if session.description
                                        else ""
                                    )
                                    + (
                                        f"Please join using this link: {session.meeting_link}"
                                        if session.meeting_link
                                        else ""
                                    ),
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
        if (
            live_session.batch.whatsapp_reminder
            and live_session.batch.project.status == "ongoing"
        ):
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
                                "value": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                            },
                            {
                                "name": "description",
                                "value": (
                                    live_session.description
                                    if live_session.description
                                    else ""
                                )
                                + (
                                    f"Please join using this link: {live_session.meeting_link}"
                                    if live_session.meeting_link
                                    else ""
                                ),
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
        if (
            live_session.batch.whatsapp_reminder
            and live_session.batch.project.status == "ongoing"
        ):
            try:
                # Get the associated SchedularBatch for each LiveSession
                schedular_batch = live_session.batch
                if schedular_batch:
                    # Now, you can access the associated Course through the SchedularBatch
                    course = Course.objects.filter(batch=schedular_batch).first()
                    if course:
                        feedback_lesson = FeedbackLesson.objects.filter(
                            lesson__course=course,
                            live_session__session_type=live_session.session_type,
                            live_session__live_session_number=live_session.live_session_number,
                        ).first()
                        try:
                            if feedback_lesson:
                                for (
                                    learner
                                ) in feedback_lesson.lesson.course.batch.learners.all():
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
                            print(f"Error processing feedback lesson: {str(e_inner)}")
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
            if (
                session.coaching_session.batch.whatsapp_reminder
                and session.coaching_session.batch.project.status == "ongoing"
            ):
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
            if caas_session.project.whatsapp_reminder:
                learner = caas_session.learner
                learner_name = learner.name
                phone = learner.phone
                time = caas_session.confirmed_availability.start_time
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
            if caas_session.project.whatsapp_reminder:
                learner = caas_session.learner
                caas_learner_name = learner.name
                caas_learner_phone = learner.phone
                time = caas_session.confirmed_availability.start_time
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
        caas_session = SessionRequestCaas.objects.get(id=session_id)
        if True:
            if caas_session.coach:
                coach = caas_session.coach
                caas_coach_name = coach.first_name + " " + coach.last_name
                caas_coach_phone = coach.phone_country_code + coach.phone
                time = caas_session.confirmed_availability.start_time
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
            if (
                coaching_session.batch.whatsapp_reminder
                and coaching_session.batch.project.status == "ongoing"
            ):
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
                                coaching_session.session_type.replace(
                                    "_", " "
                                ).capitalize()
                                if not coaching_session.session_type
                                == "laser_coaching_session"
                                else "Coaching Session"
                                + " "
                                + str(coaching_session.coaching_session_number)
                            )
                            project_name = coaching_session.batch.project.name
                            path_parts = coaching_session.booking_link.split("/")
                            booking_id = path_parts[-1]
                            expiry_date = coaching_session.expiry_date.strftime(
                                "%d-%m-%Y"
                            )
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
                                        {
                                            "name": "expiry_date",
                                            "value": expiry_date,
                                        },
                                    ],
                                    "template_name": "participant_slot_booking_reminder_for_skill_training_sessions",
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
def schedule_nudges(instance_id, instance_type=None):
    if instance_type == "project":
        project = Project.objects.get(id=instance_id)
        nudge_scheduled_for = project.nudge_start_date
        nudge_frequency = project.nudge_frequency
        nudges = Nudge.objects.filter(caas_project=project).order_by("order")
    elif instance_type == "batch" or not instance_type:
        batch = SchedularBatch.objects.get(id=instance_id)
        nudge_scheduled_for = batch.nudge_start_date
        nudge_frequency = batch.nudge_frequency
        nudges = Nudge.objects.filter(batch=batch).order_by("order")

    for nudge in nudges:
        nudge.trigger_date = nudge_scheduled_for
        nudge.save()
        nudge_scheduled_for = nudge_scheduled_for + timedelta(int(nudge_frequency))


def get_file_content(file_url):
    response = requests.get(file_url)
    return response.content


def get_file_extension(url):
    # Split the URL by '.' to get an array of parts
    url_parts = url.split(".")
    # Get the last part of the array, which should be the full file name with extension
    full_file_name = url_parts[-1]
    # Extract the file extension
    file_extension = full_file_name.split("?")[0]
    return file_extension


# runs every day at 8:30 AM
# @shared_task
# def send_nudges():
#     today_date = date.today()
#     nudges = Nudge.objects.filter(
#         trigger_date=today_date,
#         is_sent=False,
#         is_switched_on=True,
#         batch__project__nudges=True,
#         batch__project__status="ongoing",
#     )
#     for nudge in nudges:
#         subject = f"New Nudge: {nudge.name}"
#         message = nudge.content
#         email_message = render_to_string(
#             "nudge/nudge_wrapper.html", {"message": mark_safe(message)}
#         )
#         if nudge.file:
#             attachment_path = nudge.file.url
#             file_content = get_file_content(nudge.file.url)

#         for learner in nudge.batch.learners.all():
#             email = EmailMessage(
#                 subject,
#                 email_message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [learner.email],
#             )
#             if nudge.file:
#                 extension = get_file_extension(nudge.file.url)
#                 file_name = f"Attatchment.{extension}"
#                 email.attach(file_name, file_content, f"application/{extension}")
#             email.content_subtype = "html"
#             email.send()
#             sleep(5)
#         nudge.is_sent = True
#         nudge.save()


@shared_task
def celery_send_unbooked_coaching_session_mail(data):
    try:
        batch_name = data.get("batchName", "")
        project_name = data.get("project_name", "")
        participants = data.get("participants", [])
        booking_link = data.get("bookingLink", "")
        expiry_date = data.get("expiry_date", "")
        date_obj = datetime.strptime(expiry_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d %B %Y")
        session_type = data.get("session_type", "")
        for participant in participants:
            try:
                learner_name = Learner.objects.get(email=participant).name
            except:
                continue

            send_mail_templates(
                "seteventlink.html",
                [participant],
                # "Meeraq -Book Laser Coaching Session"
                # if session_type == "laser_coaching_session"
                # else "Meeraq - Book Mentoring Session",
                f"{project_name} | Book Individual 1:1 coaching sessions",
                {
                    "name": learner_name,
                    "project_name": project_name,
                    "event_link": booking_link,
                    "expiry_date": formatted_date,
                },
                [],
            )
            sleep(5)
    except Exception as e:
        print(f"Error occurred while sending unbooked coaching email : {e}")


@shared_task
def send_assessment_invitation_mail_on_click(data):
    try:
        participant_ids = data.get("req")
        assessment = Assessment.objects.get(id=data.get("assessment_id"))

        participants_observers = assessment.participants_observers.all().filter(
            participant__id__in=participant_ids
        )

        for participant_observer_mapping in participants_observers:
            participant = participant_observer_mapping.participant

            try:
                participant_response = ParticipantResponse.objects.get(
                    participant=participant, assessment=assessment
                )
            except ObjectDoesNotExist:
                participant_unique_id = ParticipantUniqueId.objects.get(
                    participant=participant, assessment=assessment
                )
                unique_id = participant_unique_id.unique_id

                assessment_link = (
                    f"{env('ASSESSMENT_URL')}/participant/meeraq/assessment/{unique_id}"
                )
                send_mail_templates(
                    "assessment/assessment_reminder_mail_to_participant.html",
                    [participant.email],
                    "Meeraq - Assessment Reminder !",
                    {
                        "assessment_name": assessment.participant_view_name,
                        "participant_name": participant.name.title(),
                        "link": assessment_link,
                    },
                    [],
                )
                sleep(5)
    except Exception as e:
        print(str(e))


@shared_task
def send_whatsapp_reminder_assessment_on_click(data):
    participant_observer_ids = data.get("participant_observers")
    assessment = Assessment.objects.get(id=data.get("assessment_id"))
    participants_observers = assessment.participants_observers.filter(
        id__in=participant_observer_ids
    )
    for participant_observer_mapping in participants_observers:
        participant = participant_observer_mapping.participant
        try:
            participant_response = ParticipantResponse.objects.filter(
                participant=participant, assessment=assessment
            )
            if not participant_response.exists():
                participant_unique_id = ParticipantUniqueId.objects.get(
                    participant=participant, assessment=assessment
                )
                unique_id = participant_unique_id.unique_id
                assessment_link = (
                    f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{unique_id}"
                )
                send_whatsapp_message("learner", participant, assessment, unique_id)
        except ObjectDoesNotExist:
            print(f"No unique ID found for participant {participant.name}")
        sleep(2)


@shared_task
def send_email_reminder_assessment_on_click(data):
    participant_observer_ids = data.get("participant_observers")
    assessment = Assessment.objects.get(id=data.get("assessment_id"))
    participants_observers = assessment.participants_observers.filter(
        id__in=participant_observer_ids
    )
    for participant_observer_mapping in participants_observers:
        participant = participant_observer_mapping.participant
        try:
            participant_response = ParticipantResponse.objects.filter(
                participant=participant, assessment=assessment
            )
            if not participant_response.exists():
                participant_unique_id = ParticipantUniqueId.objects.get(
                    participant=participant, assessment=assessment
                )
                unique_id = participant_unique_id.unique_id
                assessment_link = (
                    f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{unique_id}"
                )
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
        sleep(2)


# returns start and end time of today in format - YYYY-MM-DDTHH:mm:ss.sssZ
def get_current_date_start_and_end_time_in_string():
    now = timezone.now()
    current_date = now.date()

    start_datetime = datetime.combine(current_date, datetime.min.time())
    end_datetime = datetime.combine(current_date, datetime.max.time())

    start_time = start_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    end_time = end_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return start_time, end_time


def get_todays_100ms_sessions_of_room_id(management_token, room_id, start, end):
    try:
        headers = {"Authorization": f"Bearer {management_token}"}
        url = f"https://api.100ms.live/v2/sessions?room_id={room_id}&after={start}&before={end}&limit=100"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sessions = response.json()
            return sessions["data"]
        else:
            print(f"Failed to get sessions. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to get sessions. Exception: {str(e)}")
        return None


# convert YYYY-MM-DDTHH:mm:ss.sssZ to timestamp in milliseconds
def convert_timestr_to_timestamp(timestamp_str):
    try:
        timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        timestamp_unix = int(timestamp_datetime.timestamp() * 1000)
        return timestamp_unix
    except ValueError:
        # Handle invalid timestamp format
        return None


@shared_task
def update_schedular_session_status():
    start_timestamp, end_timestamp = get_current_date_timestamps()
    start_time, end_time = get_current_date_start_and_end_time_in_string()
    today_sessions = SchedularSessions.objects.filter(
        availibility__start_time__lte=end_timestamp,
        availibility__end_time__gte=start_timestamp,
    )
    memoized_100ms_sessions_today = {}  # <room_id> : [] sessions array
    for schedular_session in today_sessions:
        is_coach_joined = False
        is_coachee_joined = False
        is_both_joined_at_same_time = False
        schedular_session_start_timestamp = int(
            schedular_session.availibility.start_time
        )
        schedular_session_end_timestamp = int(schedular_session.availibility.end_time)
        coach_room_id = schedular_session.availibility.coach.room_id
        if coach_room_id in memoized_100ms_sessions_today:
            todays_sessions_in_100ms = memoized_100ms_sessions_today[coach_room_id]
        else:
            todays_sessions_in_100ms = []
            try:
                management_token = generateManagementToken()
                todays_sessions_in_100ms = get_todays_100ms_sessions_of_room_id(
                    management_token, coach_room_id, start_time, end_time
                )
            except Exception as e:
                print("failed to get coach room 100ms sessions")
        sessions_in_100ms_at_scheduled_time_of_schedular_session = []

        for session in todays_sessions_in_100ms:
            created_at_in_timestamp = convert_timestr_to_timestamp(
                session["created_at"]
            )
            five_minutes_prior_schedular_start_time = (
                schedular_session_start_timestamp - 5 * 60 * 1000
            )
            if (
                created_at_in_timestamp >= five_minutes_prior_schedular_start_time
                or created_at_in_timestamp < schedular_session_end_timestamp
            ):
                sessions_in_100ms_at_scheduled_time_of_schedular_session.append(session)

        for session in sessions_in_100ms_at_scheduled_time_of_schedular_session:
            if len(session["peers"].keys()) == 2:
                is_both_joined_at_same_time = True
                break
            for key, peer in session["peers"].items():
                if (
                    schedular_session.availibility.coach.first_name
                    + " "
                    + schedular_session.availibility.coach.last_name
                ).lower().strip() == peer["name"].lower().strip():
                    is_coach_joined = True
                if (
                    schedular_session.learner.name.lower().strip()
                    == peer["name"].lower().strip()
                ):
                    is_coachee_joined = True
        if is_both_joined_at_same_time:
            schedular_session.auto_generated_status = "completed"
        # pending because both joined at the same time
        elif is_coach_joined and is_coachee_joined:
            schedular_session.auto_generated_status = "pending"
        elif is_coachee_joined:
            schedular_session.auto_generated_status = "coach_no_show"
        elif is_coach_joined:
            schedular_session.auto_generated_status = "coachee_no_show"
        schedular_session.save()


# Notify vendor by email when the po is in open status, 1st of every month (pending PO)
@shared_task
def generate_invoice_reminder_on_first_of_month():
    return None
    vendors = Vendor.objects.all()
    access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    for vendor in vendors:
        if access_token_purchase_data:
            api_url = f"{base_url}/purchaseorders/?organization_id={organization_id}&vendor_id={vendor.vendor_id}"
            auth_header = {"Authorization": f"Bearer {access_token_purchase_data}"}
            response = requests.get(api_url, headers=auth_header)
            if response.status_code == 200:
                open_purchase_order_count = 0
                purchase_orders = response.json().get("purchaseorders", [])
                purchase_orders = filter_purchase_order_data(purchase_orders)
                for purchase_order in purchase_orders:
                    if purchase_order["status"] in ["partially_billed", "open"]:
                        open_purchase_order_count += 1
                if open_purchase_order_count > 0:
                    send_mail_templates(
                        "vendors/monthly_generate_invoice_reminder.html",
                        [
                            (
                                vendor.email
                                if env("ENVIRONMENT") == "PRODUCTION"
                                else "pankaj@meeraq.com"
                            )
                        ],
                        "Meeraq - Action pending: Raise your invoice",
                        {
                            "name": vendor.name,
                            "open_purchase_order_count": open_purchase_order_count,
                        },
                        [],
                    )
                    print(
                        "sending mail to",
                        vendor.name,
                        open_purchase_order_count,
                        "open po exist",
                    )
                    sleep(5)
            else:
                print({"error": "Failed to fetch purchase orders"})
        else:
            print(
                {
                    "error": "Access token not found. Please generate an access token first."
                }
            )


# Reminder to vendor for new PO, Checks every day if any po without reminder exist and then send the reminder
@shared_task
def generate_invoice_reminder_once_when_po_is_created():
    return None
    vendors = Vendor.objects.all()
    access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    for vendor in vendors:
        if access_token_purchase_data:
            api_url = f"{base_url}/purchaseorders/?organization_id={organization_id}&vendor_id={vendor.vendor_id}"
            auth_header = {"Authorization": f"Bearer {access_token_purchase_data}"}
            response = requests.get(api_url, headers=auth_header)
            if response.status_code == 200:
                purchase_orders = response.json().get("purchaseorders", [])
                purchase_orders = filter_purchase_order_data(purchase_orders)
                for purchase_order in purchase_orders:
                    if (
                        purchase_order["status"] in ["partially_billed", "open"]
                        and not PoReminder.objects.filter(
                            purchase_order_no=purchase_order["purchaseorder_number"]
                        ).exists()
                    ):
                        send_mail_templates(
                            "vendors/new_po_reminder.html",
                            [
                                (
                                    vendor.email
                                    if env("ENVIRONMENT") == "PRODUCTION"
                                    else "pankaj@meeraq.com"
                                )
                            ],
                            "Meeraq - New Purchase Order",
                            {"name": vendor.name},
                            [],
                        )
                        PoReminder.objects.create(
                            vendor=vendor,
                            purchase_order_no=purchase_order["purchaseorder_number"],
                            purchase_order_id=purchase_order["purchaseorder_id"],
                        )
                        sleep(5)
            else:
                print({"error": "Failed to fetch purchase orders"})
        else:
            print(
                {
                    "error": "Access token not found. Please generate an access token first."
                }
            )


# getting vendor details
def get_vendor(vendor_id):
    access_token = get_access_token(env("ZOHO_REFRESH_TOKEN"))
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/contacts/{vendor_id}?organization_id={env('ZOHO_ORGANIZATION_ID')}"
        vendor_response = requests.get(
            url,
            headers=headers,
        )
        if (
            vendor_response.json()["message"] == "success"
            and vendor_response.json()["contact"]
        ):
            return vendor_response.json()["contact"]
        return None
    else:
        return None


@shared_task
def reminder_to_pmo_bank_details_unavailable():
    vendors = Vendor.objects.all()
    vendors_with_no_bank_details = []
    for vendor in vendors:
        vendor_details = get_vendor(vendor.vendor_id)
        if vendor_details and len(vendor_details["bank_accounts"]) == 0:
            vendors_with_no_bank_details.append(vendor_details["contact_name"])
    if len(vendors_with_no_bank_details) > 0:
        send_mail_templates(
            "vendors/reminder_to_pmo_bank_details_unavailable.html",
            [env("FINANCE_EMAIL")],
            "Meeraq: Action Needed - Add bank details of vendors",
            {
                "count": len(vendors_with_no_bank_details),
                "vendors_with_no_bank_details": vendors_with_no_bank_details,
            },
            [env("BCC_EMAIL")],  # no bcc
        )


@shared_task
def send_tomorrow_action_items_data():
    try:
        current_date_time = timezone.now()
        current_date = date.today()
        schedular_projects = SchedularProject.objects.all()

        projects_data = {}
        for project in schedular_projects:
            projects_data[project.name] = {
                "laser_coaching_sessions": [],
                "mentoring_sessions": [],
                "live_sessions": [],
                "assessments": [],
                "nudges": [],
                "email_reminder": "ON" if project.email_reminder else "OFF",
                "whatsapp_reminder": "ON" if project.whatsapp_reminder else "OFF",
                "calendar_invites": "ON" if project.calendar_invites else "OFF",
            }

            schedular_sessions = get_coaching_session_according_to_time(
                SchedularSessions.objects.filter(
                    coaching_session__batch__project=project
                ),
                "tomorrow",
            )

            for schedular_session in schedular_sessions:
                temp = {
                    "date_time": get_date_time(
                        int(schedular_session.availibility.start_time)
                    ),
                    "coach": schedular_session.availibility.coach.first_name
                    + " "
                    + schedular_session.availibility.coach.last_name,
                    "coach_phone_number": schedular_session.availibility.coach.phone,
                    "batch_name": schedular_session.coaching_session.batch.name,
                    "learner": schedular_session.learner.name,
                    "learner_phone_number": schedular_session.learner.phone,
                }
                if (
                    schedular_session.coaching_session.session_type
                    == "laser_coaching_session"
                ):
                    projects_data[project.name]["laser_coaching_sessions"].append(temp)
                elif (
                    schedular_session.coaching_session.session_type
                    == "mentoring_session"
                ):
                    projects_data[project.name]["mentoring_sessions"].append(temp)

            live_sessions = get_live_session_according_to_time(
                LiveSession.objects.filter(batch__project=project), "tomorrow"
            )

            for live_session in live_sessions:
                temp = {
                    "date_time": (
                        live_session.date_time.strftime("%d-%m-%Y %H:%M")
                        if live_session.date_time
                        else None
                    ),
                    "session_name": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                    "batch_name": live_session.batch.name,
                    "duration": live_session.duration,
                    "description": live_session.description,
                }
                projects_data[project.name]["live_sessions"].append(temp)

            # Filter ongoing assessments
            assessments = Assessment.objects.filter(
                assessment_end_date__gt=current_date,
                status="ongoing",
                assessment_modal__lesson__course__batch__project=project,
            )

            for assessment in assessments:
                total_responses_count = ParticipantResponse.objects.filter(
                    assessment=assessment
                ).count()

                assessment_lesson = AssessmentLesson.objects.filter(
                    assessment_modal=assessment
                ).first()
                temp = {
                    "name": assessment.name,
                    "batch_name": (
                        assessment_lesson.lesson.course.batch.name
                        if assessment_lesson
                        else None
                    ),
                    "response_status": f"{total_responses_count} / {assessment.participants_observers.count()}",
                    "email_reminder": "On" if assessment.email_reminder else "Off",
                    "whatsapp_reminder": (
                        "On" if assessment.whatsapp_reminder else "Off"
                    ),
                }
                projects_data[project.name]["assessments"].append(temp)
            courses = Course.objects.filter(batch__project=project)

            for course in courses:
                today_date = date.today()
                tomorrow_date = today_date + timedelta(days=1)
                nudges = Nudge.objects.filter(
                    batch__id=course.batch.id,
                    trigger_date=tomorrow_date,
                    is_sent=False,
                    is_switched_on=True,
                    batch__project__nudges=True,
                    batch__project__status="ongoing",
                )
                nudges = NudgeSerializer(nudges, many=True).data
                for nudge in nudges:
                    nudge["nudge_scheduled_for"] = str(nudge["trigger_date"])
                    projects_data[project.name]["nudges"].append(nudge)

        assessments = Assessment.objects.filter(
            assessment_end_date__gt=current_date,
            status="ongoing",
            assessment_timing="none",
        )
        assessment_data = []
        for assessment in assessments:
            assessment_lesson = AssessmentLesson.objects.filter(
                assessment_modal=assessment
            ).first()
            assessment_lesson = AssessmentLesson.objects.filter(
                assessment_modal=assessment
            ).first()
            if not assessment_lesson:
                total_responses_count = ParticipantResponse.objects.filter(
                    assessment=assessment
                ).count()

                assessment_lesson = AssessmentLesson.objects.filter(
                    assessment_modal=assessment
                ).first()
                temp = {
                    "name": assessment.name,
                    "response_status": f"{total_responses_count} / {assessment.participants_observers.count()}",
                    "email_reminder": "On" if assessment.email_reminder else "Off",
                    "whatsapp_reminder": (
                        "On" if assessment.whatsapp_reminder else "Off"
                    ),
                    "type": assessment.assessment_type,
                }
                assessment_data.append(temp)

        send_mail_templates(
            "pmo_emails/tomorrow_action_items_mail.html",
            json.loads(env("ACTION_ITEMS_MAIL")),
            "Tomorrow's Project Updates for PMO Review",
            {"projects_data": projects_data, "Assessments": assessment_data},
            json.loads(env("ACTION_ITEMS_MAIL_CC_EMAILS")),
        )

    except Exception as e:
        print(str(e))


@shared_task
def send_whatsapp_reminder_assessment(assessment_id):
    assessment = Assessment.objects.get(id=assessment_id)
    # if assessment.assessment_type == "360":
    # participants_observers = assessment.participants_observers.all()
    # print(1,participants_observers)
    # for participant_observer_mapping in participants_observers:
    #     participant = participant_observer_mapping.participant
    #     print(2,participant)
    #     try:
    #         observers = participant_observer_mapping.observers.all()
    #         print(3,observers)
    #         for observer in observers:
    #             print(4, observer)
    #             observer_response_exists = ObserverResponse.objects.filter(
    #                 participant=participant,
    #                 observer=observer,
    #                 assessment=assessment,
    #             ).exists()
    #             if not observer_response_exists:
    #                 observer_unique_id = ObserverUniqueId.objects.get(
    #                     observer=observer, assessment=assessment
    #                 )
    #                 unique_id = observer_unique_id.unique_id
    #                 print(5,unique_id, observer.phone)
    #                 send_whatsapp_message_template(
    #                     observer.phone,
    #                     {
    #                         "broadcast_name": "Assessment Reminder",
    #                         "parameters": [
    #                             {
    #                                 "name": "observer_name",
    #                                 "value": observer.name,
    #                             },
    #                             {
    #                                 "name": "participant_name",
    #                                 "value": participant.name,
    #                             },
    #                             {
    #                                 "name": "assessment_name",
    #                                 "value": assessment.participant_view_name,
    #                             },
    #                             {
    #                                 "name": "observer_id",
    #                                 "value": unique_id,
    #                             },
    #                         ],
    #                         "template_name": "assessment_reminder_observer",
    #                     },
    #                 )
    #     except ObjectDoesNotExist:
    #         print(f"No unique ID found for participant {observer.name}")
    #     sleep(2)
    # else:
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
                assessment_link = (
                    f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{unique_id}"
                )
                print("Participant Unique ID:", unique_id)
                send_whatsapp_message("learner", participant, assessment, unique_id)
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
        sleep(2)


@shared_task
def send_email_reminder_assessment(assessment_id):
    assessment = Assessment.objects.get(id=assessment_id)
    # if assessment.assessment_type == "360":
    # participants_observers = assessment.participants_observers.all()
    # for participant_observer_mapping in participants_observers:
    #     participant = participant_observer_mapping.participant
    #     try:
    #         observers = participant_observer_mapping.observers.all()
    #         for observer in observers:
    #             observer_response_exists = ObserverResponse.objects.filter(
    #                 participant=participant,
    #                 observer=observer,
    #                 assessment=assessment,
    #             ).exists()
    #             if not observer_response_exists:
    #                 observer_unique_id = ObserverUniqueId.objects.get(
    #                     observer=observer, assessment=assessment
    #                 )
    #                 unique_id = observer_unique_id.unique_id
    #                 assessment_link = f"{env('ASSESSMENT_URL')}/observer/meeraq/assessment/{unique_id}"
    #                 send_mail_templates(
    #                     "assessment/assessment_reminder_mail_to_observer.html",
    #                     [observer.email],
    #                     "Meeraq - Assessment Reminder !",
    #                     {
    #                         "assessment_name": assessment.participant_view_name,
    #                         "observer_name": observer.name.capitalize(),
    #                         "link": assessment_link,
    #                     },
    #                     [],
    #                 )
    #     except ObjectDoesNotExist:
    #         print(f"No unique ID found for participant {observer.name}")
    #     sleep(5)
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
                assessment_link = (
                    f"{env('ASSESSMENT_URL')}/participant/meeraq/assessment/{unique_id}"
                )
                # Send email only if today's date is within the assessment date range
                send_whatsapp_message("learner", participant, assessment, unique_id)
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
def update_lesson_status_according_to_drip_dates():
    try:
        today = date.today()
        lessons = Lesson.objects.filter(
            Q(live_session__date_time__date=today) | Q(drip_date=today)
        )
        for lesson in lessons:
            change_status = False
            if (
                lesson.live_session
                and lesson.live_session.date_time
                and lesson.live_session.date_time.date() == today
            ):
                change_status = True
            elif lesson.drip_date == today:
                change_status = True

            if change_status:
                if lesson.lesson_type == "assessment":
                    assessment = Assessment.objects.filter(lesson=lesson).first()

                    assessment_modal = Assessment.objects.get(
                        id=assessment.assessment_modal.id
                    )
                    lesson.status == "public"
                    assessment_modal.status = "ongoing"
                    lesson.save()
                    assessment_modal.save()
                else:

                    lesson.status = "public"
                    lesson.save()
    except Exception as e:
        print(str(e))


def send_mail_templates_dynamic_smtp_config(
    file_name, user_email, email_subject, content, bcc_emails, smtp_config
):
    try:
        email_message = render_to_string(file_name, content)
        send_mail(
            subject=email_subject,
            message=email_message,
            from_email=smtp_config["EMAIL_HOST_USER"],
            recipient_list=[user_email],
            auth_user=smtp_config["EMAIL_HOST_USER"],
            auth_password=smtp_config["EMAIL_HOST_PASSWORD"],
            connection=None,
            html_message=email_message,
        )
        create_send_email(user_email, file_name)
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")


@shared_task
def send_emails_in_bulk(content_of_mails):
    smtp_configs = json.loads(env("SMTP_EMAILS"))  # List of SMTP configurations
    num_configs = len(smtp_configs)
    num_mails_per_config = len(content_of_mails) // num_configs
    start_idx = 0
    for i, smtp_config in enumerate(smtp_configs):
        end_idx = start_idx + num_mails_per_config
        if i < len(content_of_mails) % num_configs:
            end_idx += 1  # Distribute the remaining emails equally
        emails_to_send = content_of_mails[start_idx:end_idx]
        for email_data in emails_to_send:
            send_mail_templates_dynamic_smtp_config(
                email_data["file_name"],
                email_data["user_email"],
                email_data["email_subject"],
                email_data["content"],
                email_data["bcc_emails"],
                smtp_config,
            )
            sleep(3)
        start_idx = end_idx


@shared_task
def update_caas_session_status():
    try:
        with transaction.atomic():
            start_timestamp, end_timestamp = get_current_date_timestamps()
            start_time, end_time = get_current_date_start_and_end_time_in_string()
            today_sessions = SessionRequestCaas.objects.filter(
                confirmed_availability__start_time__lte=end_timestamp,
                confirmed_availability__end_time__gte=start_timestamp,
            )
            memoized_100ms_sessions_today = {}
            for caas_session in today_sessions:
                is_coach_joined = False
                is_coachee_joined = False
                is_both_joined_at_same_time = False
                caas_session_start_timestamp = int(
                    caas_session.confirmed_availability.start_time
                )
                caas_session_end_timestamp = int(
                    caas_session.confirmed_availability.end_time
                )
                coach_room_id = caas_session.coach.room_id
                if coach_room_id in memoized_100ms_sessions_today:
                    todays_sessions_in_100ms = memoized_100ms_sessions_today[
                        coach_room_id
                    ]
                else:
                    todays_sessions_in_100ms = []
                    try:
                        management_token = generateManagementToken()
                        todays_sessions_in_100ms = get_todays_100ms_sessions_of_room_id(
                            management_token, coach_room_id, start_time, end_time
                        )
                    except Exception as e:
                        print("failed to get coach room 100ms sessions")
                sessions_in_100ms_at_scheduled_time_of_caas_session = []

                for session in todays_sessions_in_100ms:
                    created_at_in_timestamp = convert_timestr_to_timestamp(
                        session["created_at"]
                    )
                    five_minutes_prior_schedular_start_time = (
                        caas_session_start_timestamp - 5 * 60 * 1000
                    )
                    if (
                        created_at_in_timestamp
                        >= five_minutes_prior_schedular_start_time
                        or created_at_in_timestamp < caas_session_end_timestamp
                    ):
                        sessions_in_100ms_at_scheduled_time_of_caas_session.append(
                            session
                        )

                for session in sessions_in_100ms_at_scheduled_time_of_caas_session:
                    is_coach_joined_in_current_100ms_session = False
                    is_learner_joined_in_current_100ms_session = False

                    for key, peer in session["peers"].items():
                        if (
                            caas_session.availibility.coach.first_name
                            + " "
                            + caas_session.availibility.coach.last_name
                        ).lower().strip() == peer["name"].lower().strip():
                            is_coach_joined = True
                            is_coach_joined_in_current_100ms_session = True
                        if (
                            caas_session.learner.name.lower().strip()
                            == peer["name"].lower().strip()
                        ):
                            is_coachee_joined = True
                            is_learner_joined_in_current_100ms_session = True
                        if (
                            is_coach_joined_in_current_100ms_session
                            and is_learner_joined_in_current_100ms_session
                        ):
                            is_both_joined_at_same_time = True
                            break

                if is_both_joined_at_same_time:
                    caas_session.auto_generated_status = "completed"

                elif is_coach_joined and is_coachee_joined:
                    caas_session.auto_generated_status = "pending"
                elif is_coachee_joined:
                    caas_session.auto_generated_status = "coach_no_show"
                elif is_coach_joined:
                    caas_session.auto_generated_status = "coachee_no_show"
                caas_session.save()

    except Exception as e:
        print(str(e))


@shared_task
def update_caas_session_status():
    try:
        with transaction.atomic():
            start_timestamp, end_timestamp = get_current_date_timestamps()
            start_time, end_time = get_current_date_start_and_end_time_in_string()
            today_sessions = SessionRequestCaas.objects.filter(
                confirmed_availability__start_time__lte=end_timestamp,
                confirmed_availability__end_time__gte=start_timestamp,
            )
            memoized_100ms_sessions_today = {}
            for caas_session in today_sessions:
                is_coach_joined = False
                is_coachee_joined = False
                is_both_joined_at_same_time = False
                caas_session_start_timestamp = int(
                    caas_session.confirmed_availability.start_time
                )
                caas_session_end_timestamp = int(
                    caas_session.confirmed_availability.end_time
                )
                coach_room_id = caas_session.coach.room_id
                if coach_room_id in memoized_100ms_sessions_today:
                    todays_sessions_in_100ms = memoized_100ms_sessions_today[
                        coach_room_id
                    ]
                else:
                    todays_sessions_in_100ms = []
                    try:
                        management_token = generateManagementToken()
                        todays_sessions_in_100ms = get_todays_100ms_sessions_of_room_id(
                            management_token, coach_room_id, start_time, end_time
                        )
                    except Exception as e:
                        print("failed to get coach room 100ms sessions")
                sessions_in_100ms_at_scheduled_time_of_caas_session = []

                for session in todays_sessions_in_100ms:
                    created_at_in_timestamp = convert_timestr_to_timestamp(
                        session["created_at"]
                    )
                    five_minutes_prior_schedular_start_time = (
                        caas_session_start_timestamp - 5 * 60 * 1000
                    )
                    if (
                        created_at_in_timestamp
                        >= five_minutes_prior_schedular_start_time
                        or created_at_in_timestamp < caas_session_end_timestamp
                    ):
                        sessions_in_100ms_at_scheduled_time_of_caas_session.append(
                            session
                        )

                for session in sessions_in_100ms_at_scheduled_time_of_caas_session:
                    is_coach_joined_in_current_100ms_session = False
                    is_learner_joined_in_current_100ms_session = False

                    for key, peer in session["peers"].items():
                        if (
                            caas_session.availibility.coach.first_name
                            + " "
                            + caas_session.availibility.coach.last_name
                        ).lower().strip() == peer["name"].lower().strip():
                            is_coach_joined = True
                            is_coach_joined_in_current_100ms_session = True
                        if (
                            caas_session.learner.name.lower().strip()
                            == peer["name"].lower().strip()
                        ):
                            is_coachee_joined = True
                            is_learner_joined_in_current_100ms_session = True
                        if (
                            is_coach_joined_in_current_100ms_session
                            and is_learner_joined_in_current_100ms_session
                        ):
                            is_both_joined_at_same_time = True
                            break

                if is_both_joined_at_same_time:
                    caas_session.auto_generated_status = "completed"

                elif is_coach_joined and is_coachee_joined:
                    caas_session.auto_generated_status = "pending"
                elif is_coachee_joined:
                    caas_session.auto_generated_status = "coach_no_show"
                elif is_coach_joined:
                    caas_session.auto_generated_status = "coachee_no_show"
                caas_session.save()

    except Exception as e:
        print(str(e))


@shared_task
def schedule_assessment_reminders():
    # Get the timezone for IST
    ist = pytz.timezone("Asia/Kolkata")
    # Get ongoing assessments with email or WhatsApp reminders enabled
    ongoing_assessments = Assessment.objects.filter(
        Q(status="ongoing"), Q(email_reminder=True) | Q(whatsapp_reminder=True)
    )
    # Loop through each ongoing assessment
    for assessment in ongoing_assessments:
        start_date = datetime.strptime(
            assessment.assessment_start_date, "%Y-%m-%d"
        ).date()
        end_date = datetime.strptime(assessment.assessment_end_date, "%Y-%m-%d").date()
        # Check if today's date is within the assessment date range
        today = datetime.now().date()
        day_of_week = today.strftime("%A")
        if start_date <= today <= end_date and not day_of_week == "Sunday":
            if assessment.whatsapp_reminder:
                for time in assessment.reminders["whatsapp"]["timings"]:
                    # Parse time in hh:mm A format to a datetime object
                    reminder_time = datetime.strptime(time, "%I:%M %p")
                    # Set the reminder time to today with the specified time in IST
                    reminder_datetime_ist = ist.localize(
                        datetime.combine(timezone.now().date(), reminder_time.time())
                    )
                    # Convert reminder time from IST to UTC
                    reminder_datetime_utc = reminder_datetime_ist.astimezone(pytz.utc)
                    # Create a clocked schedule for the reminder time
                    clocked_schedule = ClockedSchedule.objects.create(
                        clocked_time=reminder_datetime_utc
                    )
                    # Create a periodic task for sending the reminder
                    periodic_task = PeriodicTask.objects.create(
                        name=uuid.uuid1(),
                        task="schedularApi.tasks.send_whatsapp_reminder_assessment",
                        args=[assessment.id],
                        clocked=clocked_schedule,
                        one_off=True,
                    )

            # Check and schedule email reminders
            if assessment.email_reminder:
                for time in assessment.reminders["email"]["timings"]:
                    reminder_time = datetime.strptime(time, "%I:%M %p")
                    reminder_datetime_ist = ist.localize(
                        datetime.combine(timezone.now().date(), reminder_time.time())
                    )
                    reminder_datetime_utc = reminder_datetime_ist.astimezone(pytz.utc)
                    clocked_schedule = ClockedSchedule.objects.create(
                        clocked_time=reminder_datetime_utc
                    )
                    periodic_task = PeriodicTask.objects.create(
                        name=uuid.uuid1(),
                        task="schedularApi.tasks.send_email_reminder_assessment",
                        args=[assessment.id],
                        clocked=clocked_schedule,
                        one_off=True,
                    )


@shared_task
def invoice_due_email_reminder():
    try:
        current_date = datetime.now().date()
        line_items = SalesOrderLineItem.objects.filter(
            custom_field_hash__cf_due_date__isnull=False, is_invoiced=False
        )
        line_item_data = []
        for item in line_items:
            due_date = datetime.strptime(
                item.custom_field_hash["cf_due_date"], "%d/%m/%Y"
            ).date()
            if due_date <= current_date:
                sales_order = SalesOrder.objects.filter(
                    so_line_items__line_item_id=item.line_item_id
                ).first()
                if sales_order:
                    line_item = {
                        "sales_order_id": sales_order.salesorder_id,
                        "sales_order_number": sales_order.salesorder_number,
                        "line_item_id": item.line_item_id,
                        "client_name": sales_order.customer_name,
                        "line_item_description": item.description,
                        "due_date": item.custom_field_hash["cf_due_date"],
                    }
                    line_item_data.append(line_item)
        if len(line_item_data) > 0:
            send_mail_templates(
                "due_invoice_email_reminder.html",
                (
                    [
                        "finance@meeraq.com",
                        "kumar@coachtotransformation.com",
                        "raju@coachtotransformation.com",
                    ]
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else ["tech@meeraq.com"]
                ),
                "Invoices due today",
                {"line_item_data": line_item_data},
                (
                    ["rajat@meeraq.com", "sujata@meeraq.com"]
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else ["naveen@meeraq.com"]
                ),
            )
    except Exception as e:
        print(str(e))


@shared_task
def send_live_session_link_whatsapp_to_facilitators_30_min_before(id):
    try:
        live_session = LiveSession.objects.get(id=id)
        if (
            live_session.batch.whatsapp_reminder
            and live_session.batch.project.status == "ongoing"
        ):
            facilitator = live_session.facilitator
            if not facilitator:
                return None
            send_whatsapp_message_template(
                facilitator.phone,
                {
                    "broadcast_name": "30 min before live session reminder",
                    "parameters": [
                        {
                            "name": "name",
                            "value": facilitator.first_name
                            + " "
                            + facilitator.last_name,
                        },
                        {
                            "name": "live_session_name",
                            "value": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                        },
                        {
                            "name": "live_session_meeting_link",
                            "value": live_session.meeting_link,
                        },
                    ],
                    "template_name": "send_whatsapp_reminder_to_facilitator_same_day_30_min_before",
                },
            )
    except Exception as e:
        print(str(e))


@shared_task
def send_live_session_link_whatsapp_to_facilitators_one_day_before():
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        live_sessions = LiveSession.objects.filter(date_time__date=tomorrow.date())
        for live_session in live_sessions:
            if (
                live_session.batch.whatsapp_reminder
                and live_session.batch.project.status == "ongoing"
            ):
                facilitator = live_session.facilitator
                if not facilitator:
                    continue
                session_datetime_str = live_session.date_time.astimezone(
                    pytz.timezone("Asia/Kolkata")
                ).strftime("%I:%M %p")
                send_whatsapp_message_template(
                    facilitator.phone,
                    {
                        "broadcast_name": "one day before live session reminder",
                        "parameters": [
                            {
                                "name": "name",
                                "value": facilitator.first_name
                                + " "
                                + facilitator.last_name,
                            },
                            {
                                "name": "live_session_name",
                                "value": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                            },
                            {
                                "name": "time",
                                "value": f"{session_datetime_str} IST",
                            },
                            {
                                "name": "live_session_meeting_link",
                                "value": live_session.meeting_link,
                            },
                        ],
                        "template_name": "send_whatsapp_reminder_to_facilitator_one_day_before",
                    },
                )
                sleep(5)
    except Exception as e:
        print(str(e))


@shared_task
def send_live_session_reminder_to_facilitator_one_day_before():
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        live_sessions = LiveSession.objects.filter(date_time__date=tomorrow.date())
        for live_session in live_sessions:
            if (
                live_session.batch.whatsapp_reminder
                and live_session.batch.project.status == "ongoing"
            ):
                facilitator = live_session.facilitator
                if not facilitator:
                    continue
                session_datetime_str = live_session.date_time.astimezone(
                    pytz.timezone("Asia/Kolkata")
                ).strftime("%I:%M %p")
                send_mail_templates(
                    "facilitator_templates/send_live_session_reminder_to_facilitator_one_day_before.html",
                    [facilitator.email],
                    "Meeraq - Live Session",
                    {
                        "participant_name": facilitator.first_name
                        + " "
                        + facilitator.last_name,
                        "live_session_name": f"{get_live_session_name(live_session.session_type)} {live_session.live_session_number}",
                        "project_name": live_session.batch.project.name,
                        "description": (
                            live_session.description if live_session.description else ""
                        ),
                        "meeting_link": live_session.meeting_link,
                    },
                    [],
                )
                sleep(5)
    except Exception as e:
        print(str(e))


@shared_task
def send_live_session_whatsapp_reminder_same_day_morning_for_facilitator():
    try:
        today_morning = timezone.now().replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        live_sessions = LiveSession.objects.filter(date_time__date=today_morning.date())

        for session in live_sessions:
            if (
                session.batch.whatsapp_reminder
                and session.batch.project.status == "ongoing"
            ):
                facilitator = session.batch.facilitator
                if not facilitator:
                    return None
                session_datetime_str = session.date_time.astimezone(
                    pytz.timezone("Asia/Kolkata")
                ).strftime("%I:%M %p")
                send_mail_templates(
                    "facilitator_templates/send_live_session_reminder_to_facilitator_on_same_day_morning.html",
                    [facilitator.email],
                    "Meeraq - Live Session",
                    {
                        "participant_name": facilitator.first_name
                        + " "
                        + facilitator.last_name,
                        "live_session_name": f"{get_live_session_name(session.session_type)} {session.live_session_number}",
                        "project_name": session.batch.project.name,
                        "description": (
                            session.description if session.description else ""
                        ),
                        "meeting_link": session.meeting_link,
                    },
                    [],
                )
    except Exception as e:
        print(str(e))
        pass


def create_batch_calendar(batch):
    for session_data in batch.project.project_structure:
        order = session_data.get("order")
        duration = session_data.get("duration")
        session_type = session_data.get("session_type")

        if session_type in [
            "live_session",
            "check_in_session",
            "in_person_session",
            "pre_study",
            "kickoff_session",
            "virtual_session",
        ]:
            session_number = (
                LiveSession.objects.filter(
                    batch=batch, session_type=session_type
                ).count()
                + 1
            )
            live_session = LiveSession.objects.create(
                batch=batch,
                live_session_number=session_number,
                order=order,
                duration=duration,
                session_type=session_type,
            )
            create_task(
                {
                    "task": "add_session_details",
                    "schedular_project": batch.project.id,
                    "project_type": "skill_training",
                    "live_session": live_session.id,
                    "priority": "medium",
                    "status": "pending",
                    "remarks": [],
                },
                3,
            )
        elif session_type in [
            "laser_coaching_session",
            "mentoring_session",
            "action_coaching_session",
        ]:
            coaching_session_number = (
                CoachingSession.objects.filter(
                    batch=batch, session_type=session_type
                ).count()
                + 1
            )
            booking_link = f"{env('CAAS_APP_URL')}/coaching/book/{str(uuid.uuid4())}"  # Generate a unique UUID for the booking link
            coaching_session = CoachingSession.objects.create(
                batch=batch,
                coaching_session_number=coaching_session_number,
                order=order,
                duration=duration,
                booking_link=booking_link,
                session_type=session_type,
            )
            create_task(
                {
                    "task": "add_dates",
                    "schedular_project": batch.project.id,
                    "project_type": "skill_training",
                    "coaching_session": coaching_session.id,
                    "priority": "medium",
                    "status": "pending",
                    "remarks": [],
                },
                7,
            )


@shared_task
def add_batch_to_project(data):
    try:
        participants_data = data.get("participants", [])
        project_id = data.get("project_id")
        with transaction.atomic():
            project = SchedularProject.objects.get(id=project_id)
            learners_in_excel_sheet = len(participants_data)
            learners_in_excel_which_already_exists = 0
            for participant_data in participants_data:
                email = participant_data.get("email", "").strip().lower()
                if Learner.objects.filter(email=email).exists():
                    learners_in_excel_which_already_exists += 1
            for participant_data in participants_data:
                name = participant_data.get("name")
                email = participant_data.get("email", "").strip().lower()
                phone = participant_data.get("phone", None)
                batch_name = participant_data.get("batch").strip().upper()
                # Assuming 'project_id' is in your request data

                # Check if batch with the same name exists
                batch = SchedularBatch.objects.filter(
                    name=batch_name, project=project
                ).first()

                if not batch:
                    # If batch does not exist, create a new batch
                    batch = SchedularBatch.objects.create(
                        name=batch_name, project=project
                    )
                    batch.email_reminder = project.email_reminder
                    batch.whatsapp_reminder = project.whatsapp_reminder
                    batch.calendar_invites = project.calendar_invites
                    batch.save()
                    create_batch_calendar(batch)
                    try:
                        tasks = Task.objects.filter(
                            task="add_batches",
                            status="pending",
                            schedular_project=project,
                        )
                        tasks.update(status="completed")
                    except Exception as e:
                        print(str(e))
                        pass
                    try:
                        create_task(
                            {
                                "task": "add_coach",
                                "schedular_project": batch.project.id,
                                "schedular_batch": batch.id,
                                "project_type": "skill_training",
                                "priority": "high",
                                "status": "pending",
                                "remarks": [],
                            },
                            1,
                        )
                        create_task(
                            {
                                "task": "add_facilitator",
                                "schedular_project": batch.project.id,
                                "schedular_batch": batch.id,
                                "project_type": "skill_training",
                                "priority": "high",
                                "status": "pending",
                                "remarks": [],
                            },
                            1,
                        )
                        create_task(
                            {
                                "task": "request_availability",
                                "schedular_project": batch.project.id,
                                "schedular_batch": batch.id,
                                "project_type": "skill_training",
                                "priority": "medium",
                                "status": "pending",
                                "remarks": [],
                            },
                            7,
                        )
                        if batch.project.nudges:
                            create_task(
                                {
                                    "task": "add_nudges",
                                    "schedular_project": batch.project.id,
                                    "schedular_batch": batch.id,
                                    "project_type": "skill_training",
                                    "priority": "medium",
                                    "status": "pending",
                                    "remarks": [],
                                },
                                1,
                            )
                            create_task(
                                {
                                    "task": "add_nudge_date_and_frequency",
                                    "schedular_project": batch.project.id,
                                    "schedular_batch": batch.id,
                                    "project_type": "skill_training",
                                    "priority": "medium",
                                    "status": "pending",
                                    "remarks": [],
                                },
                                1,
                            )
                    except Exception as e:
                        print(str(e))
                        pass

                    # Create Live Sessions and Coaching Sessions based on project structure

                # Check if participant with the same email exists
                learner = create_or_get_learner(
                    {"name": name, "email": email, "phone": phone}
                )
                if learner:
                    name = learner.name
                    if learner.phone:
                        add_contact_in_wati("learner", name, learner.phone)

                # Add participant to the batch if not already added
                if learner and learner not in batch.learners.all():
                    batch.learners.add(learner)
                    try:
                        course = Course.objects.get(batch=batch)
                        course_enrollments = CourseEnrollment.objects.filter(
                            learner=learner, course=course
                        )
                        if not course_enrollments.exists():
                            datetime = timezone.now()
                            CourseEnrollment.objects.create(
                                learner=learner,
                                course=course,
                                enrollment_date=datetime,
                            )
                    except Exception:
                        pass
            learner_message = (
                f"{learners_in_excel_sheet-learners_in_excel_which_already_exists} learner"
                if (learners_in_excel_sheet - learners_in_excel_which_already_exists)
                == 1
                else f"{learners_in_excel_sheet-learners_in_excel_which_already_exists} learners"
            )
            learner_msg = (
                f"{learners_in_excel_which_already_exists} learner"
                if (learners_in_excel_which_already_exists) == 1
                else f"{learners_in_excel_which_already_exists} learners"
            )

            send_mail_templates(
                "pmo_emails/participant_uploaded.html",
                [data.get("user_email")],
                "Meeraq | Participants Uploaded Sucessfully!",
                {
                    "learner_message": learner_message,
                    "learner_msg": learner_msg,
                    "name": "Pmo",
                },
                [],  # bcc
            )

    except Exception as e:
        print(str(e))


@shared_task
def send_nudge_reminder_on_trigger_date_at_6pm():
    today = datetime.now().date()
    nudges = Nudge.objects.filter(
        Q(trigger_date=today),
        Q(is_sent=False),
        Q(is_switched_on=True),
        Q(batch__project__nudges=True, batch__project__status="ongoing")
        | Q(caas_project__nudges=True),
    )
    for nudge in nudges:
        learners = (
            nudge.batch.learners.all()
            if nudge.batch
            else (
                Learner.objects.filter(
                    engagement__project=nudge.caas_project
                ).distinct()
                if nudge.caas_project
                else []
            )
        )
        for learner in learners:
            if learner.id not in nudge.learner_ids:
                nudge_id = nudge.unique_id
                send_whatsapp_message_template(
                    learner.phone,
                    {
                        "broadcast_name": "send_nudge_reminder_on_trigger_date_at_6pm",
                        "parameters": [
                            {
                                "name": "learner_name",
                                "value": learner.name,
                            },
                            {
                                "name": "nudge_name",
                                "value": nudge.name,
                            },
                            {
                                "name": "nudge_id",
                                "value": nudge_id,
                            },
                        ],
                        "template_name": "nudge_reminder_at6",
                    },
                )
                link = f"{env('CAAS_APP_URL')}/view-nudge/{nudge_id}"
                send_mail_templates(
                    "coachee_emails/nudge_reminder.html",
                    [learner.email],
                    f"Meeraq: Your Monthly Nudge: {nudge.name} ",
                    {
                        "learner_name": learner.name.title(),
                        "nudge_name": nudge.name.title(),
                        "link": link,
                    },
                    [],
                )
                nudge.is_sent = True
                nudge.save()
                sleep(5)


@shared_task
def result_sending(assessment):
    try:
        if assessment.assessment_type == "self":
            (
                participant_released_results,
                created,
            ) = ParticipantReleasedResults.objects.get_or_create(assessment=assessment)
            participant_with_released_results = []
            if not created:
                participant_with_released_results = (
                    participant_released_results.participants.all()
                )

            participant_with_not_released_results = []
            for participant_observer in assessment.participants_observers.all():
                participant_response_present = ParticipantResponse.objects.filter(
                    assessment=assessment,
                    participant=participant_observer.participant,
                ).exists()
                if participant_response_present:
                    if (
                        participant_observer.participant
                        not in participant_with_released_results
                    ):
                        participant_with_not_released_results.append(
                            participant_observer.participant
                        )
                        participant_released_results.participants.add(
                            participant_observer.participant
                        )

            participant_released_results.save()

            if len(assessment.participants_observers.all()) == (
                len(participant_with_released_results)
                + len(participant_with_not_released_results)
            ):
                assessment.result_released = True
                assessment.save()

            for participant in participant_with_not_released_results:

                encoded_image = None
                compentency_with_description = None
                if (
                    assessment.assessment_timing == "pre"
                    or assessment.assessment_timing == "none"
                ):
                    (
                        encoded_image,
                        compentency_with_description,
                    ) = generate_graph_for_participant(
                        participant, assessment.id, assessment
                    )
                elif assessment.assessment_timing == "post":
                    (
                        encoded_image,
                        compentency_with_description,
                    ) = generate_graph_for_participant_for_post_assessment(
                        participant, assessment.id, assessment
                    )
                send_mail_templates(
                    "assessment/air_india_report_mail.html",
                    [participant.email],
                    "Meeraq Assessment Report",
                    {
                        "name": participant.name.title(),
                        "image_base64": encoded_image,
                        "compentency_with_description": compentency_with_description,
                        "assessment_timing": assessment.assessment_timing,
                        "assessment_name": assessment.participant_view_name,
                    },
                    [],
                )
                sleep(5)

        else:
            assessment.result_released = True
            assessment.save()

    except Exception as e:
        print(str(e))
