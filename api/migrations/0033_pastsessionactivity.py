# Generated by Django 4.1.7 on 2023-11-30 10:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0032_deletecoachprofileactivity'),
    ]

    operations = [
        migrations.CreateModel(
            name='PastSessionActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('coach', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.coach')),
                ('coachee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.project')),
                ('user_who_added', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
