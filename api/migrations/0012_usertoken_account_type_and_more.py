# Generated by Django 4.1.7 on 2023-09-16 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_usertoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='usertoken',
            name='account_type',
            field=models.CharField(blank=True, choices=[('google', 'Google'), ('microsoft', 'Microsoft')], max_length=50),
        ),
        migrations.AlterField(
            model_name='usertoken',
            name='access_token_expiry',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='usertoken',
            name='authorization_code',
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.TextField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('start_datetime', models.CharField(blank=True, max_length=255, null=True)),
                ('end_datetime', models.CharField(blank=True, max_length=255, null=True)),
                ('attendee', models.CharField(blank=True, max_length=255, null=True)),
                ('creator', models.CharField(blank=True, max_length=255, null=True)),
                ('account_type', models.CharField(blank=True, choices=[('google', 'Google'), ('microsoft', 'Microsoft')], max_length=50)),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.sessionrequestcaas')),
            ],
        ),
    ]
