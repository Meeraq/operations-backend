# Generated by Django 4.1.7 on 2024-01-19 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_assessment_assessment_modal'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='type',
            field=models.CharField(choices=[('pre', 'Pre-Assessment'), ('post', 'Post-Assessment'), ('none', 'None')], default='none', max_length=255),
        ),
    ]
