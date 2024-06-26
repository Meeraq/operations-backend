# Generated by Django 4.1.7 on 2024-06-04 12:15

from django.db import migrations, models
import uuid


def populate_unique_ids(apps, schema_editor):
    SchedularProject = apps.get_model("schedularApi", "SchedularProject")
    for schedular_project in SchedularProject.objects.all():
        schedular_project.unique_id = uuid.uuid4()
        schedular_project.save()


class Migration(migrations.Migration):

    dependencies = [
        ("schedularApi", "0040_alter_coachingsession_session_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedularproject",
            name="unique_id",
            field=models.CharField(blank=True, default="", max_length=225, null=True),
        ),
        migrations.RunPython(populate_unique_ids),
    ]
