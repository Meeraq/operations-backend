# Generated by Django 4.1.7 on 2023-12-13 07:17

import courses.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_livesessionlesson_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Resources',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('pdf_file', models.FileField(blank=True, upload_to='pdf_files', validators=[courses.models.validate_pdf_extension])),
            ],
        ),
        migrations.CreateModel(
            name='PdfLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='courses.lesson')),
                ('pdf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.resources')),
            ],
        ),
    ]