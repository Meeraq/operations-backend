# Generated by Django 4.1.7 on 2024-04-16 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0053_sales_sales_person_id_alter_goal_engagement_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='business',
            field=models.CharField(blank=True, default='meeraq', max_length=255),
        ),
    ]
