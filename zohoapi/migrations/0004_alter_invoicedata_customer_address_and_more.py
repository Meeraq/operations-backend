# Generated by Django 4.1.7 on 2023-10-26 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0003_invoicedata_customer_address_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoicedata',
            name='customer_address',
            field=models.TextField(blank=True, default=None),
        ),
        migrations.AlterField(
            model_name='invoicedata',
            name='vendor_billing_address',
            field=models.TextField(blank=True, default=None),
        ),
    ]
