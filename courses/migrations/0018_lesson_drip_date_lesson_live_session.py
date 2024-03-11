# Generated by Django 4.1.7 on 2024-03-11 08:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0021_schedularproject_junior_pmo_and_more'),
        ('courses', '0017_feedback_coachingsessionsfeedbackresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='drip_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='live_session',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.livesession'),
        ),
    ]
