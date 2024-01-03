# Generated by Django 4.1.7 on 2024-01-03 06:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0035_trim_emails'),
        ('courses', '0006_alter_lesson_lesson_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
            ],
        ),
        migrations.AlterField(
            model_name='lesson',
            name='lesson_type',
            field=models.CharField(choices=[('text', 'Text Lesson'), ('quiz', 'Quiz Lesson'), ('live_session', 'Live Session'), ('laser_coaching', 'Laser Coaching Session'), ('feedback', 'Feedback'), ('assessment', 'Assessment'), ('video', 'Video'), ('ppt', 'PPT'), ('downloadable_file', 'Downloadable File'), ('assignment', 'Assignment')], max_length=20),
        ),
        migrations.CreateModel(
            name='AssignmentLessonResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='assignment-files/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('edited_at', models.DateTimeField(auto_now=True)),
                ('assignment_lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.assignmentlesson')),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.learner')),
            ],
        ),
        migrations.AddField(
            model_name='assignmentlesson',
            name='lesson',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='courses.lesson'),
        ),
    ]
