# Generated by Django 4.1.7 on 2024-02-06 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0016_remove_schedularproject_automated_reminder_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedularsessions',
            name='auto_generated_status',
            field=models.CharField(blank=True, default='pending', max_length=50),
        ),
    ]
