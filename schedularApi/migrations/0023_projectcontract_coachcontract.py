# Generated by Django 4.1.7 on 2024-03-30 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0022_schedularbatch_nudge_frequency_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_id', models.IntegerField(null=True)),
                ('title', models.CharField(blank=True, max_length=100)),
                ('content', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reminder_timestamp', models.CharField(blank=True, max_length=30)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.project')),
                ('schedular_project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.schedularproject')),
            ],
        ),
        migrations.CreateModel(
            name='CoachContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_inputed', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(blank=True, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=50)),
                ('send_date', models.DateField(auto_now_add=True)),
                ('response_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('coach', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.coach')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.project')),
                ('project_contract', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.projectcontract')),
                ('schedular_project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.schedularproject')),
            ],
        ),
    ]
