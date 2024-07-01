# Generated by Django 4.1.7 on 2024-06-30 13:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0076_alter_standardizedfield_field'),
        ('schedularApi', '0047_mentoringsessions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('batch', models.IntegerField(blank=True, null=True)),
                ('organisation', models.CharField(choices=[('ctt', 'CTT'), ('meeraq', 'Meeraq')], default='ctt', max_length=6)),
                ('inactive', models.BooleanField(default=False)),
                ('caas_project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='caas_groups', to='api.project')),
            ],
        ),
        migrations.AddField(
            model_name='employee',
            name='active_inactive',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='function',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='organisation',
            field=models.CharField(choices=[('ctt', 'CTT'), ('meeraq', 'Meeraq')], default='meeraq', max_length=6),
        ),
        migrations.AddField(
            model_name='employee',
            name='role',
            field=models.CharField(choices=[('head', 'Head'), ('team_member', 'Team Member')], default='team_member', max_length=11),
        ),
        migrations.AddField(
            model_name='employee',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile'),
        ),
        migrations.CreateModel(
            name='ManagementTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, max_length=255, null=True)),
                ('start_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('deadline', models.DateTimeField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('not_started', 'Not Started'), ('ongoing', 'Ongoing'), ('completed', 'Completed')], default='not_started', max_length=20)),
                ('effort', models.CharField(blank=True, max_length=25, null=True)),
                ('actual_effort', models.CharField(blank=True, max_length=25, null=True)),
                ('actual_start_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('actual_end_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('priority', models.CharField(choices=[('high', 'High'), ('low', 'Low'), ('medium', 'Medium')], default='low', max_length=20)),
                ('employee', models.ManyToManyField(blank=True, null=True, to='schedularApi.employee')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.group')),
            ],
        ),
        migrations.AddField(
            model_name='group',
            name='employees',
            field=models.ManyToManyField(related_name='groups', to='schedularApi.employee'),
        ),
        migrations.AddField(
            model_name='group',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedularApi.employee'),
        ),
        migrations.AddField(
            model_name='group',
            name='seeq_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='seeq_groups', to='schedularApi.schedularproject'),
        ),
    ]