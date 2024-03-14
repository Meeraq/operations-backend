# Generated by Django 4.1.7 on 2024-03-14 05:54

from django.db import migrations, models
import django.db.models.deletion


def update_nudges_from_course_to_batch(apps, schema_editor):
    CourseModel = apps.get_model("courses", "Course")
    BatchModel = apps.get_model("schedularApi", "SchedularBatch")
    NudgeModel = apps.get_model("courses", "Nudge")
    for nudge in NudgeModel.objects.all():
        try:
            if nudge.course.batch:
                nudge.batch = nudge.course.batch
                nudge.save()
        except Exception as e:
            print(str(e))
            pass

    for course in CourseModel.objects.all():
        try:
            if course.batch_id:
                batch = BatchModel.objects.get(pk=course.batch_id)
                batch.nudge_start_date = course.nudge_start_date
                batch.nudge_frequency = course.nudge_frequency
                batch.nudge_periodic_task = course.nudge_periodic_task
                batch.save()
        except Exception as e:
            print(str(e))


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0022_schedularbatch_nudge_frequency_and_more'),
        ('courses', '0018_lesson_drip_date_lesson_live_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='nudge',
            name='batch',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.schedularbatch'),
        ),
        migrations.RunPython(update_nudges_from_course_to_batch),
        migrations.RemoveField(
            model_name='course',
            name='nudge_frequency',
        ),
        migrations.RemoveField(
            model_name='course',
            name='nudge_periodic_task',
        ),
        migrations.RemoveField(
            model_name='course',
            name='nudge_start_date',
        ),
        migrations.RemoveField(
            model_name='nudge',
            name='course',
        ),
       
    ]