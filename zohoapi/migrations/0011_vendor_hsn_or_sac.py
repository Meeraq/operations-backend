# Generated by Django 4.1.7 on 2024-03-13 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0010_invoicedata_approver_email_invoicedata_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='hsn_or_sac',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
