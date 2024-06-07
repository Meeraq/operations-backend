# Generated by Django 4.1.7 on 2024-06-07 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0070_facilitator_remarks'),
        ('schedularApi', '0041_schedularproject_unique_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='FacilitatorContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_inputed', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(blank=True, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=50)),
                ('send_date', models.DateField(auto_now_add=True)),
                ('response_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('facilitator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.facilitator')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.project')),
                ('project_contract', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.projectcontract')),
                ('schedular_project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.schedularproject')),
            ],
        ),
    ]
