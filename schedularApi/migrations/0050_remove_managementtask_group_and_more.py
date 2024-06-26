# Generated by Django 4.1.7 on 2024-06-25 13:57

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0049_group_managementtask'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='managementtask',
            name='group',
        ),
        migrations.AddField(
            model_name='managementtask',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='managementtask',
            name='deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='managementtask',
            name='groups',
            field=models.ManyToManyField(to='schedularApi.group'),
        ),
    ]
