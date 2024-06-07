# Generated by Django 4.1.7 on 2024-06-05 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0069_curriculum'),
        ('assessmentApi', '0021_actionitem_remarks_assessment_automated_result'),
        ('courses', '0024_nudge_caas_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nudge',
            name='content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='nudge',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='NudgeResources',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('file', models.FileField(blank=True, null=True, upload_to='nudge_files/')),
                ('status', models.CharField(blank=True, choices=[('Draft', 'Draft'), ('Open', 'Open')], default='Draft', max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('behavior', models.ManyToManyField(to='assessmentApi.behavior')),
                ('competency', models.ManyToManyField(to='assessmentApi.competency')),
                ('curriculum', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.curriculum')),
            ],
        ),
        migrations.AddField(
            model_name='nudge',
            name='nudge_resources',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.nudgeresources'),
        ),
    ]