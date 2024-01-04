# Generated by Django 4.1.7 on 2024-01-04 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('affiliateApi', '0009_alter_lead_lead_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lead',
            name='lead_status',
            field=models.CharField(blank=True, choices=[('not_contacted', 'Not Contacted'), ('engaged', 'Engaged'), ('converted', 'Converted'), ('lost', 'Lost')], default='not_contacted', max_length=20, null=True),
        ),
    ]
