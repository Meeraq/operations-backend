# Generated by Django 4.1.7 on 2024-05-31 06:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0069_curriculum'),
        ('assessmentApi', '0019_alter_assessment_questionnaire_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParticipantTempResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('temp_participant_response', models.JSONField(blank=True, default=dict)),
                ('active_question', models.IntegerField(blank=True, default=0, null=True)),
                ('current_competency', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assessment', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='assessmentApi.assessment')),
                ('participant', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
            ],
        ),
        migrations.CreateModel(
            name='ObserverTempResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('temp_observer_response', models.JSONField(blank=True, default=dict)),
                ('active_question', models.IntegerField(blank=True, default=0, null=True)),
                ('current_competency', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assessment', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='assessmentApi.assessment')),
                ('observer', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='assessmentApi.observer')),
                ('participant', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
            ],
        ),
    ]