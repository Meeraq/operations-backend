# Generated by Django 4.1.7 on 2024-06-14 05:45

from django.db import migrations, models

data = {}


def get_old_facilitator(apps, schema_editor):
    LiveSession = apps.get_model("schedularApi", "LiveSession")
    live_sessions = LiveSession.objects.all()
    for live_session in live_sessions:
        data[live_session.id] = (
            live_session.facilitator.id if live_session.facilitator else None
        )


def populate_facilitator(apps, schema_editor):
    LiveSession = apps.get_model("schedularApi", "LiveSession")
    Facilitator = apps.get_model("api", "Facilitator")
    for key, value in data.items():
        if value is not None:  # Check if facilitator id exists
            live_session = LiveSession.objects.get(id=key)
            facilitator = Facilitator.objects.get(id=value)
            live_session.facilitator.add(
                facilitator
            )  # Use add() instead of set() for ManyToManyField


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0071_coach_coaching_type_coach_competency_and_more"),
        ("schedularApi", "0045_schedularproject_is_ngo_project"),
    ]

    operations = [
        migrations.RunPython(get_old_facilitator),
        migrations.RemoveField(
            model_name="livesession",
            name="facilitator",
        ),
        migrations.AddField(
            model_name="livesession",
            name="facilitator",
            field=models.ManyToManyField(blank=True, to="api.facilitator"),
        ),
        migrations.RunPython(populate_facilitator),
    ]
