# Generated by Django 4.1.7 on 2024-02-26 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0008_invoicedata_vendor_pan'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='hsn_or_sac',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
