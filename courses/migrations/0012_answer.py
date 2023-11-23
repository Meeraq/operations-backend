# Generated by Django 4.1.7 on 2023-11-22 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_standardizedfield_standardizedfieldrequest'),
        ('courses', '0011_courseenrollment_completed_lessons'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_answer', models.TextField(blank=True, null=True)),
                ('selected_options', models.JSONField(default=list)),
                ('rating', models.IntegerField(blank=True, null=True)),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.question')),
            ],
        ),
    ]
