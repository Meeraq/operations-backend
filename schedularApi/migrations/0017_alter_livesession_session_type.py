# Generated by Django 4.1.7 on 2024-02-05 09:58

from django.db import migrations, models

from schedularApi.models import LiveSession, SchedularProject
from courses.models import LiveSessionLesson, Course, FeedbackLesson
from django.db import transaction


def get_feedback_lesson_name(lesson_name):
    # Trim leading and trailing whitespaces
    trimmed_string = lesson_name.strip()
    # Convert to lowercase
    lowercased_string = trimmed_string.lower()
    # Replace spaces between words with underscores
    underscored_string = "_".join(lowercased_string.split())
    return underscored_string


def populate_virtual_session(apps, schema_editor):

    try:
        with transaction.atomic():
            live_sessions = LiveSession.objects.filter(session_type="live_session")

            for live_session in live_sessions:
                live_session.session_type = "virtual_session"
                live_session.save()

                live_session_lesson = LiveSessionLesson.objects.filter(
                    live_session=live_session
                ).first()
                if live_session_lesson:
                    if live_session_lesson.lesson.name.lower().find("live") != -1:
                        live_session_lesson.lesson.name = (
                            live_session_lesson.lesson.name.lower().replace(
                                "live", "virtual"
                            )
                        )

                        live_session_lesson.lesson.name = (
                            live_session_lesson.lesson.name.title()
                        )

                    live_session_lesson.lesson.save()

                course = Course.objects.filter(batch=live_session.batch).first()
                if course:
                    feedback_lesson_name_should_be = f"feedback_for_live_session_{live_session.live_session_number}"
                    feedback_lessons = FeedbackLesson.objects.filter(
                        lesson__course=course
                    )
                    for feedback_lesson in feedback_lessons:
                        current_lesson_name = feedback_lesson.lesson.name
                        formatted_lesson_name = get_feedback_lesson_name(
                            current_lesson_name
                        )
                        if formatted_lesson_name == feedback_lesson_name_should_be:
                            if (
                                feedback_lesson.lesson.name.lower().find("live")
                                != -1
                            ):
                                feedback_lesson.lesson.name = (
                                    feedback_lesson.lesson.name.lower().replace(
                                        "live", "virtual"
                                    )
                                )
                                feedback_lesson.lesson.name = (
                                    feedback_lesson.lesson.name.title()
                                )
                        feedback_lesson.lesson.save()

            projects = SchedularProject.objects.all()

            for project in projects:
                project_structure = project.project_structure

                for session in project_structure:
                    if session.get("session_type") == "live_session":
                        session["session_type"] = "virtual_session"

                project.project_structure = project_structure
                project.save()

    except Exception as e:
        print(str(e))


class Migration(migrations.Migration):

    dependencies = [
        ("schedularApi", "0016_remove_schedularproject_automated_reminder_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="livesession",
            name="session_type",
            field=models.CharField(
                choices=[
                    ("live_session", "Live Session"),
                    ("check_in_session", "Check In Session"),
                    ("in_person_session", "In Person Session"),
                    ("kickoff_session", "Kickoff Session"),
                    ("virtual_session", "Virtual Session"),
                ],
                default="live_session",
                max_length=50,
            ),
        ),
        migrations.RunPython(populate_virtual_session),
    ]
