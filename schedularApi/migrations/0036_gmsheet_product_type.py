# Generated by Django 5.0.4 on 2024-05-24 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0035_assets_benchmark_gmsheet_offering'),
    ]

    operations = [
        migrations.AddField(
            model_name='gmsheet',
            name='product_type',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
    ]
