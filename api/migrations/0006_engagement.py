# Generated by Django 4.1.7 on 2023-06-15 09:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_sessionrequestcaas_is_archive'),
    ]

    operations = [
        migrations.CreateModel(
            name='Engagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed')], max_length=20)),
                ('project_structure', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('coach', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.coach')),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.project')),
            ],
        ),
    ]
