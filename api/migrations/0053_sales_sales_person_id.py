# Generated by Django 4.1.7 on 2024-04-08 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0052_sales'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='sales_person_id',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
