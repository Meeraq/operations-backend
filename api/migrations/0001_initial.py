# Generated by Django 4.1.7 on 2023-02-23 12:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('meet_link', models.CharField(blank=True, max_length=50)),
                ('phone', models.CharField(max_length=25)),
                ('level', models.CharField(max_length=50)),
                ('rating', models.CharField(max_length=20)),
                ('area_of_expertise', models.CharField(max_length=50)),
                ('completed_sessions', models.IntegerField(blank=True, default=0)),
                ('is_approved', models.BooleanField(blank=True, default=False)),
            ],
        ),
        migrations.CreateModel(
            name='HR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('meet_link', models.CharField(max_length=50)),
                ('phone', models.CharField(max_length=25)),
                ('level', models.CharField(max_length=50)),
                ('rating', models.CharField(max_length=20)),
                ('area_of_expertise', models.CharField(max_length=50)),
                ('completed_sessions', models.IntegerField(blank=True, default=0)),
                ('is_approved', models.BooleanField(blank=True, default=False)),
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
            ],
        ),
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('image_url', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('project_type', models.CharField(choices=[('cod', 'cod'), ('4+2', '4+2'), ('cas', 'cas')], default='cod', max_length=50)),
                ('start_date', models.DateField(auto_now_add=True)),
                ('end_date', models.DateField(auto_now_add=True)),
                ('total_sessions', models.IntegerField(blank=True, default=0)),
                ('cost_per_session', models.IntegerField(blank=True, default=0)),
                ('sessions_per_employee', models.IntegerField(blank=True, default=0)),
                ('coaches', models.ManyToManyField(to='api.coach')),
                ('hr', models.ManyToManyField(to='api.hr')),
                ('learner', models.ManyToManyField(to='api.learner')),
                ('organisation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.organisation')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('pmo', 'pmo'), ('coach', 'coach'), ('learner', 'learner'), ('hr', 'hr')], max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pmo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=25)),
                ('user', models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile')),
            ],
        ),
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
            ],
        ),
        migrations.AddField(
            model_name='learner',
            name='user',
            field=models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile'),
        ),
        migrations.AddField(
            model_name='hr',
            name='user',
            field=models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile'),
        ),
        migrations.AddField(
            model_name='coach',
            name='user',
            field=models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.profile'),
        ),
    ]
