# Generated by Django 4.1.7 on 2024-03-05 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0043_facilitator_coaching_experience_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sessionrequestcaas',
            name='is_extra',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
