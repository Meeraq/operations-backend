# Generated by Django 4.1.7 on 2023-07-17 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_sessionrequestcaas_invitees'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='coach_fees_per_hour',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='project',
            name='price_per_hour',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
