# Generated by Django 4.1.7 on 2024-02-01 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessmentApi', '0011_assessment_initial_reminder'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='questions_type',
            field=models.CharField(choices=[('single_correct', ' Single Correct'), ('rating_type', 'Rating Type')], default='single_correct', max_length=255),
        ),
    ]
