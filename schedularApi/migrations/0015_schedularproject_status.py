# Generated by Django 4.1.7 on 2024-02-01 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0014_facilitator_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedularproject',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('ongoing', 'Ongoing'), ('completed', 'Completed')], default='draft', max_length=255),
        ),
    ]
