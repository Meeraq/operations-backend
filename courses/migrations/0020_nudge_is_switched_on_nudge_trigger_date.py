# Generated by Django 4.1.7 on 2024-03-26 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0019_remove_course_nudge_frequency_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='nudge',
            name='is_switched_on',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nudge',
            name='trigger_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
