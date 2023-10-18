# Generated by Django 4.1.7 on 2023-10-17 10:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_coachingsession_coachschedularavailibilty_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='schedularproject',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='schedularbatch',
            name='name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='schedularproject',
            name='name',
            field=models.CharField(default=None, max_length=100, unique=True),
        ),
        migrations.AddField(
            model_name='schedularproject',
            name='organisation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.organisation'),
        ),
        migrations.RemoveField(
            model_name='schedularproject',
            name='hr',
        ),
        migrations.AddField(
            model_name='schedularproject',
            name='hr',
            field=models.ManyToManyField(blank=True, to='api.hr'),
        ),
    ]
