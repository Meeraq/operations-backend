# Generated by Django 4.1.7 on 2024-05-14 09:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0032_handoverdetails_is_drafted_handoverdetails_pmo_and_more'),
        ('api', '0061_remove_projectcontract_project_delete_coachcontract_and_more'),
        ('zohoapi', '0015_alter_bill_options_alter_clientinvoice_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='caas_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.project'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='coach',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.coach'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='engagements',
            field=models.ManyToManyField(blank=True, to='api.engagement'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='facilitator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.facilitator'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='schedular_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schedularApi.schedularproject'),
        ),
    ]
