# Generated by Django 4.1.7 on 2024-05-16 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedularApi', '0034_alter_actionitem_created_at'),
    ]

    operations = [
        migrations.RenameField(
            model_name='actionitem',
            old_name='status',
            new_name='initial_status',
        ),
        migrations.AddField(
            model_name='actionitem',
            name='current_status',
            field=models.CharField(choices=[('not_started', 'Not Started'), ('occasionally_doing', 'Occasionally Doing'), ('regularly_doing', 'Regularly Doing'), ('actively_pursuing', 'Actively Pursuing'), ('consistently_achieving', 'Consistently Achieving')], default='not_started', max_length=50),
        ),
        migrations.AddField(
            model_name='actionitem',
            name='status_updates',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
