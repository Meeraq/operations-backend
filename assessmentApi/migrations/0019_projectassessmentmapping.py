# Generated by Django 4.1.7 on 2024-05-27 06:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0064_project_nudges_project_post_assessment_and_more'),
        ('assessmentApi', '0018_batchcompetencyassignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectAssessmentMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assessments', models.ManyToManyField(blank=True, to='assessmentApi.assessment')),
                ('project', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.project')),
            ],
        ),
    ]
