# Generated by Django 4.1.7 on 2024-05-29 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0064_project_nudge_frequency_project_nudge_periodic_task_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='standardizedfield',
            name='field',
            field=models.CharField(blank=True, choices=[('location', 'Work Location'), ('other_certification', 'Assessment Certification'), ('area_of_expertise', 'Industry'), ('job_roles', 'Job roles'), ('companies_worked_in', 'Companies worked in'), ('language', 'Language Proficiency'), ('education', 'Education Institutions'), ('domain', 'Functional Domain'), ('client_companies', 'Client companies'), ('educational_qualification', 'Educational Qualification'), ('city', 'City'), ('country', 'Country'), ('topic', 'Topic'), ('product_type', 'Product Type'), ('category', 'Category'), ('project_type', 'Project Type')], max_length=50),
        ),
    ]
