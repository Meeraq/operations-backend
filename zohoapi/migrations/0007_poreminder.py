# Generated by Django 4.1.7 on 2024-02-08 05:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zohoapi', '0006_invoicedata_currency_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PoReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_order_id', models.CharField(default=None, max_length=200)),
                ('purchase_order_no', models.CharField(default=None, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='zohoapi.vendor')),
            ],
        ),
    ]