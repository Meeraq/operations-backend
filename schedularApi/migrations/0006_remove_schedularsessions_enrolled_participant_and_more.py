# Generated by Django 4.1.7 on 2023-12-16 11:54

from django.db import migrations, models
import django.db.models.deletion

from courses.views import create_or_get_learner


def changeEnrollParticipantToLearner(apps, schema_editor):
    SchedularSessions = apps.get_model("schedularApi", "SchedularSessions")
    Learner = apps.get_model("api", "Learner")

    # Iterate through existing SchedularSessions instances
    for session in SchedularSessions.objects.all():
        try:
            # Assuming enrolled_participant is the old field and learner is the new one
            learner = create_or_get_learner(
                {
                    "name": session.enrolled_participant.name,
                    "email": session.enrolled_participant.email,
                    "phone": session.enrolled_participant.phone,
                }
            )
            if learner:
                print(learner)
                session.learner = Learner.objects.get(id=learner.id)
                session.save()
        except Exception as e:
            # Handle specific exceptions or log the error
            print(f"Error updating session: {str(e)}")


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0035_trim_emails"),
        ("schedularApi", "0005_remove_schedularbatch_participants_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedularsessions",
            name="learner",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="api.learner"
            ),
        ),
        migrations.RunPython(changeEnrollParticipantToLearner),
        migrations.RemoveField(
            model_name="schedularsessions",
            name="enrolled_participant",
        ),
        migrations.DeleteModel(
            name="SchedularParticipants",
        ),
    ]
