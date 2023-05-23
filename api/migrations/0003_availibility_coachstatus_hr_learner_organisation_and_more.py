# Generated by Django 4.1.7 on 2023-05-23 09:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0002_coach_fee_remark'),
    ]

    operations = [
        migrations.CreateModel(
            name='Availibility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.CharField(max_length=30)),
                ('end_time', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='CoachStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.JSONField(blank=True, default=dict)),
                ('learner_id', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('consent_expiry_date', models.DateField(blank=True, null=True)),
                ('coach', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.coach')),
            ],
        ),
        migrations.CreateModel(
            name='HR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=25)),
            ],
        ),
        migrations.CreateModel(
            name='Learner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=25)),
                ('area_of_expertise', models.CharField(blank=True, max_length=100)),
                ('years_of_experience', models.IntegerField(blank=True, default=0)),
                ('user', models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('image_url', models.ImageField(blank=True, upload_to='post_images')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('project_type', models.CharField(choices=[('COD', 'COD'), ('4+2', '4+2'), ('CAAS', 'CAAS')], default='cod', max_length=50)),
                ('start_date', models.DateField(auto_now_add=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('session_duration', models.CharField(max_length=20)),
                ('total_sessions', models.IntegerField(blank=True, default=0)),
                ('cost_per_session', models.IntegerField(blank=True, default=0)),
                ('currency', models.CharField(default='Rupees', max_length=30)),
                ('sessions_per_employee', models.IntegerField(blank=True, default=0)),
                ('steps', models.JSONField(default=dict)),
                ('project_structure', models.JSONField(blank=True, default=list)),
                ('specific_coach', models.BooleanField(blank=True, default=False)),
                ('empanelment', models.BooleanField(blank=True, default=False)),
                ('interview_allowed', models.BooleanField(blank=True, default=False)),
                ('chemistry_allowed', models.BooleanField(blank=True, default=False)),
                ('tentative_start_date', models.DateField(blank=True, default=None)),
                ('mode', models.CharField(max_length=100)),
                ('location', models.CharField(blank=True, default=None, max_length=100)),
                ('coaches', models.ManyToManyField(blank=True, to='api.coach')),
                ('coaches_status', models.ManyToManyField(blank=True, to='api.coachstatus')),
                ('hr', models.ManyToManyField(blank=True, to='api.hr')),
                ('learner', models.ManyToManyField(blank=True, to='api.learner')),
                ('organisation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.organisation')),
            ],
        ),
        migrations.CreateModel(
            name='SessionRequestCaas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_booked', models.BooleanField(blank=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session_type', models.CharField(default='', max_length=50)),
                ('reschedule_request', models.JSONField(blank=True, default=list)),
                ('availibility', models.ManyToManyField(related_name='requested_availability', to='api.availibility')),
                ('coach', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.coach')),
                ('confirmed_availability', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='confirmed_availability', to='api.availibility')),
                ('hr', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.hr')),
                ('learner', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
                ('project', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='api.project')),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(blank=True, default='', max_length=255)),
                ('message', models.TextField(blank=True)),
                ('read_status', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='hr',
            name='organisation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.organisation'),
        ),
        migrations.AddField(
            model_name='hr',
            name='user',
            field=models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile'),
        ),
    ]
