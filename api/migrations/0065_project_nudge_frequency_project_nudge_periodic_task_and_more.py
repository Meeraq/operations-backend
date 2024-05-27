# Generated by Django 4.1.7 on 2024-05-27 07:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0018_improve_crontab_helptext'),
        ('api', '0064_project_nudges_project_post_assessment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='nudge_frequency',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='nudge_periodic_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_celery_beat.periodictask'),
        ),
        migrations.AddField(
            model_name='project',
            name='nudge_start_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]