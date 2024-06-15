# Generated by Django 4.1.7 on 2024-06-14 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0029_cttsessionattendance'),
    ]

    operations = [
        migrations.AddField(
            model_name='cttfeedback',
            name='program',
            field=models.CharField(choices=[('level-1', 'Level-1'), ('level-2', 'Level-2'), ('level-3', 'Level-3'), ('actc', 'ACTC')], default='', max_length=255),
        ),
    ]
