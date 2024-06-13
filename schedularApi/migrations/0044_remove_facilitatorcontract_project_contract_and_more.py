# Generated by Django 4.1.7 on 2024-06-11 07:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0070_facilitator_remarks'),
        ('schedularApi', '0043_facilitatorcontract_is_archive'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='facilitatorcontract',
            name='project_contract',
        ),
        migrations.AddField(
            model_name='facilitatorcontract',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.template'),
        ),
    ]