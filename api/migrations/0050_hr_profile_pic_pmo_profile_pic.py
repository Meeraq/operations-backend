# Generated by Django 4.1.7 on 2024-03-20 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0049_learner_job_roles_learner_profile_pic_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='hr',
            name='profile_pic',
            field=models.ImageField(blank=True, upload_to='post_images'),
        ),
        migrations.AddField(
            model_name='pmo',
            name='profile_pic',
            field=models.ImageField(blank=True, upload_to='post_images'),
        ),
    ]
