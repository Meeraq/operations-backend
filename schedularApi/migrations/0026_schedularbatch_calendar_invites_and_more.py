# Generated by Django 4.1.7 on 2024-04-12 04:50

from django.db import migrations, models


def populate_reminder(apps, schema_editor):
    try:

        SchedularProject = apps.get_model("schedularApi", "SchedularProject")
        SchedularBatch = apps.get_model("schedularApi", "SchedularBatch")

        for project in SchedularProject.objects.all():
            batches = SchedularBatch.objects.filter(project=project)
            for batch in batches:
                batch.email_reminder = project.email_reminder
                batch.whatsapp_reminder = project.whatsapp_reminder
                batch.calendar_invites = project.calendar_invites
                batch.save()
                
    except Exception as e:
        print(e)

class Migration(migrations.Migration):

    dependencies = [
        (
            "schedularApi",
            "0025_remove_handoverdetails_billing_process_details_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="schedularbatch",
            name="calendar_invites",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name="schedularbatch",
            name="email_reminder",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name="schedularbatch",
            name="whatsapp_reminder",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.RunPython(populate_reminder),
    ]
