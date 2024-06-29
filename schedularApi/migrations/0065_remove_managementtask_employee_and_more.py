# Generated by Django 4.1.7 on 2024-06-28 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0064_rename_efficiency_managementtask_actual_effort_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='managementtask',
            name='employee',
        ),
        migrations.AlterField(
            model_name='managementtask',
            name='status',
            field=models.CharField(choices=[('not_started', 'Not Started'), ('ongoing', 'Ongoing'), ('completed', 'Completed')], default='not_started', max_length=20),
        ),
        migrations.AddField(
            model_name='managementtask',
            name='employee',
            field=models.ManyToManyField(blank=True, null=True, to='schedularApi.employee'),
        ),
    ]
