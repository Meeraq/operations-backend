# Generated by Django 4.1.7 on 2024-01-15 09:26

from django.db import migrations, models
import django.db.models.deletion
from schedularApi.models import LiveSession
from datetime import timedelta
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import uuid
from django.utils import timezone


def populate_pt_30_min_before(apps, schema_editor):
    try:
        current_time = timezone.now()
        live_sessions = LiveSession.objects.filter(
            date_time__isnull=False, date_time__gt=current_time
        )
        for live_session in live_sessions:
            if live_session.date_time:
                scheduled_for = live_session.date_time - timedelta(minutes=30)
                clocked = ClockedSchedule.objects.create(
                    clocked_time=scheduled_for
                )  # time is utc one here
                periodic_task = PeriodicTask.objects.create(
                    name=uuid.uuid1(),
                    task="schedularApi.tasks.send_whatsapp_reminder_30_min_before_live_session",
                    args=[live_session.id],
                    clocked=clocked,
                    one_off=True,
                )
                periodic_task.save()
                live_session.pt_30_min_before = periodic_task
                live_session.save()
    except Exception as e:
        print(str(e))


class Migration(migrations.Migration):
    dependencies = [
        ("django_celery_beat", "0018_improve_crontab_helptext"),
        ("schedularApi", "0008_schedularupdate"),
    ]

    operations = [
        migrations.AddField(
            model_name="livesession",
            name="pt_30_min_before",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="django_celery_beat.periodictask",
            ),
        ),
        migrations.RunPython(populate_pt_30_min_before),
    ]
