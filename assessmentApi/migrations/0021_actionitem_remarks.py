# Generated by Django 4.1.7 on 2024-06-01 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessmentApi', '0020_participanttempresponse_observertempresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionitem',
            name='remarks',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
