# Generated by Django 4.1.7 on 2023-06-16 12:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_engagement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='engagement',
            name='coach',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.coach'),
        ),
    ]
