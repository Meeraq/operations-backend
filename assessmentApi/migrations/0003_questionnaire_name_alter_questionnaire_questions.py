# Generated by Django 4.1.7 on 2023-10-13 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessmentApi', '0002_question_questionnaire'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='questions',
            field=models.ManyToManyField(blank=True, null=True, to='assessmentApi.question'),
        ),
    ]
