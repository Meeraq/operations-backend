# Generated by Django 4.1.7 on 2024-05-28 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessmentApi', '0021_remove_observerresponse_temp_observer_response_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='observertempresponse',
            name='active_question',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='observertempresponse',
            name='current_competency',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='participanttempresponse',
            name='active_question',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='participanttempresponse',
            name='current_competency',
            field=models.TextField(blank=True, null=True),
        ),
    ]
