# Generated by Django 4.1.7 on 2024-02-27 08:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0041_remove_coach_coach_id'),
        ('schedularApi', '0020_facilitatorpricing_coachpricing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coachpricing',
            name='coach',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.coach'),
        ),
        migrations.AlterField(
            model_name='facilitatorpricing',
            name='facilitator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.facilitator'),
        ),
    ]