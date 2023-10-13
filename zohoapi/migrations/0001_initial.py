# Generated by Django 4.1.7 on 2023-10-13 06:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('refresh_token', models.CharField(max_length=255, null=True, unique=True)),
                ('access_token', models.CharField(max_length=255)),
                ('expires_in', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vendor_id', models.CharField(default=None, max_length=200)),
                ('vendor_name', models.CharField(default=None, max_length=200)),
                ('vendor_email', models.CharField(default=None, max_length=200)),
                ('vendor_billing_address', models.CharField(default=None, max_length=200)),
                ('vendor_gst', models.CharField(blank=True, default=None, max_length=200)),
                ('vendor_phone', models.CharField(blank=True, default=None, max_length=200)),
                ('purchase_order_id', models.CharField(default=None, max_length=200)),
                ('purchase_order_no', models.CharField(default=None, max_length=200)),
                ('invoice_number', models.CharField(default=None, max_length=200)),
                ('line_items', models.JSONField(default=list)),
                ('customer_name', models.CharField(default=None, max_length=200)),
                ('customer_notes', models.TextField(blank=True, default=None)),
                ('customer_gst', models.CharField(blank=True, default=None, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('is_oversea_account', models.BooleanField(default=False)),
                ('tin_number', models.CharField(blank=True, default='', max_length=255)),
                ('type_of_code', models.CharField(default='', max_length=50)),
                ('iban', models.CharField(blank=True, default='', max_length=255)),
                ('swift_code', models.CharField(blank=True, default='', max_length=255)),
                ('invoice_date', models.DateField(blank=True, default=None)),
                ('beneficiary_name', models.CharField(default='', max_length=255)),
                ('bank_name', models.CharField(default='', max_length=255)),
                ('account_number', models.CharField(default='', max_length=255)),
                ('ifsc_code', models.CharField(default='', max_length=11)),
                ('signature', models.ImageField(default='', upload_to='vendors-signature')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
