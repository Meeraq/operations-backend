# Generated by Django 4.1.7 on 2024-03-09 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0045_sessionrequestcaas_is_extra'),
    ]

    operations = [
        migrations.AddField(
            model_name='facilitator',
            name='is_approved',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
