# Generated by Django 4.1.7 on 2024-06-14 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0019_vendor_is_msme'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='po_type',
            field=models.CharField(blank=True, max_length=225, null=True),
        ),
    ]
