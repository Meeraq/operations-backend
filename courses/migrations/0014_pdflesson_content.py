# Generated by Django 4.1.7 on 2024-01-31 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0013_videolesson_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdflesson',
            name='content',
            field=models.TextField(blank=True, default=''),
        ),
    ]
