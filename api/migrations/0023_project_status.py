# Generated by Django 4.1.7 on 2023-11-07 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_alter_coachprofiletemplate_templates'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='status',
            field=models.CharField(blank=True, choices=[('active', 'Active'), ('completed', 'Completed')], max_length=20, null=True),
        ),
    ]
