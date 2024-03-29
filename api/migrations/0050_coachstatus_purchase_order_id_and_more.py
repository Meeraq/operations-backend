# Generated by Django 4.1.7 on 2024-03-23 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0049_learner_job_roles_learner_profile_pic_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachstatus',
            name='purchase_order_id',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='coachstatus',
            name='purchase_order_no',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='facilitator',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='hr',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='learner',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pmo',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='project',
            name='finance',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='superadmin',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='coach',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
    ]
