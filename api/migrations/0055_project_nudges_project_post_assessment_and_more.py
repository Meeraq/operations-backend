# Generated by Django 4.1.7 on 2024-04-24 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0054_sales_business'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='nudges',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='project',
            name='post_assessment',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='project',
            name='pre_assessment',
            field=models.BooleanField(blank=True, default=True),
        ),
    ]
