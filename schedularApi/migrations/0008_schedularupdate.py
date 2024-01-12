# Generated by Django 4.1.7 on 2024-01-11 13:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0035_trim_emails'),
        ('schedularApi', '0007_calendarinvites'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchedularUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('edited_at', models.DateTimeField(auto_now=True)),
                ('pmo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.pmo')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schedularApi.schedularproject')),
            ],
        ),
    ]