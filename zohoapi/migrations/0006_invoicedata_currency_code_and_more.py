# Generated by Django 4.1.7 on 2024-02-07 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0005_vendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoicedata',
            name='currency_code',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='invoicedata',
            name='currency_symbol',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
