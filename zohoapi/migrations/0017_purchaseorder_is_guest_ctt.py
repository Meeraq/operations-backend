# Generated by Django 4.1.7 on 2024-05-22 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0016_purchaseorder_caas_project_purchaseorder_coach_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='is_guest_ctt',
            field=models.BooleanField(default=False),
        ),
    ]
