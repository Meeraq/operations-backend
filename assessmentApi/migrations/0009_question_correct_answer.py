# Generated by Django 4.1.7 on 2024-01-06 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessmentApi', '0008_assessment_assessment_start_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='correct_answer',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
