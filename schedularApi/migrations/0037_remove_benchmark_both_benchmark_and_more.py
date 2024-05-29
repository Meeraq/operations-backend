# Generated by Django 4.1.7 on 2024-05-28 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0036_offering_is_won'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='benchmark',
            name='both_benchmark',
        ),
        migrations.RemoveField(
            model_name='benchmark',
            name='caas_benchmark',
        ),
        migrations.RemoveField(
            model_name='benchmark',
            name='seeq_benchmark',
        ),
        migrations.AddField(
            model_name='benchmark',
            name='project_type',
            field=models.JSONField(blank=True, default=list),
        ),
    ]