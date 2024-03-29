# Generated by Django 4.1.7 on 2024-03-23 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0050_coachstatus_purchase_order_id_and_more'),
        ('schedularApi', '0023_expense_amount_expense_purchase_order_id_and_more'),
        ('zohoapi', '0011_vendor_hsn_or_sac'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='OrdersAndProjectMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_order_ids', models.JSONField(blank=True, default=list)),
                ('sales_order_ids', models.JSONField(blank=True, default=list)),
                ('project', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.project')),
                ('schedular_project', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schedularApi.schedularproject')),
            ],
        ),
    ]
