# Generated by Django 4.1.7 on 2023-10-18 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_coachingsession_coachschedularavailibilty_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedularbatch',
            name='name',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
