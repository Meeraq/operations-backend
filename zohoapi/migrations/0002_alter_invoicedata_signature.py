# Generated by Django 4.1.7 on 2023-10-15 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoicedata',
            name='signature',
            field=models.ImageField(blank=True, default='', upload_to='vendors-signature'),
        ),
    ]
