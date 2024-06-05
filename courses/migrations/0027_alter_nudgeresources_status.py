# Generated by Django 4.1.7 on 2024-06-04 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0026_nudgeresources_curriculum_nudgeresources_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nudgeresources',
            name='status',
            field=models.CharField(blank=True, choices=[('draft', 'Draft'), ('public', 'Public')], default='draft', max_length=50, null=True),
        ),
    ]
