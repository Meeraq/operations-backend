# Generated by Django 4.1.7 on 2024-06-06 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0069_curriculum'),
    ]

    operations = [
        migrations.AddField(
            model_name='facilitator',
            name='remarks',
            field=models.TextField(blank=True),
        ),
    ]
