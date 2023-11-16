# Generated by Django 4.1.7 on 2023-11-16 05:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('public', 'Public')], max_length=20)),
                ('lesson_type', models.CharField(choices=[('text', 'Text Lesson'), ('quiz', 'Quiz Lesson'), ('live_session', 'Live Session'), ('laser_coaching', 'Laser Coaching Session'), ('feedback', 'Feedback'), ('assessment', 'Assessment'), ('video', 'Video')], max_length=20)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course')),
            ],
        ),
        migrations.CreateModel(
            name='TextLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='courses.lesson')),
            ],
        ),
    ]
