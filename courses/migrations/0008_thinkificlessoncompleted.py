# Generated by Django 4.1.7 on 2024-01-18 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_feedbacklesson_unique_id_alter_question_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThinkificLessonCompleted',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_name', models.TextField(blank=True)),
                ('lesson_name', models.TextField(blank=True)),
                ('student_name', models.TextField(blank=True)),
                ('completion_data', models.JSONField(blank=True)),
            ],
        ),
    ]
