# Generated by Django 3.2.13 on 2023-08-11 13:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_projectcontract_template_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coachcontract',
            name='coach',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.coach'),
        ),
    ]
