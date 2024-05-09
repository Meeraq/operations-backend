# Generated by Django 4.1.7 on 2024-05-06 11:40

from django.db import migrations, models
import django.db.models.deletion
from django.db import transaction


def populate_engagement_in_session(apps, schema_editor):
    try:
        with transaction.atomic():

            SessionRequestCaas = apps.get_model("api", "SessionRequestCaas")
            Engagement = apps.get_model("api", "Engagement")
            for session in SessionRequestCaas.objects.all():
                engagement = Engagement.objects.filter(
                    learner=session.learner, project=session.project
                ).first()
                session.engagement = engagement
                session.save()

            for engagement in Engagement.objects.all():
                if engagement.project.is_project_structure:
                    engagement.type = "caas"
                else:
                    engagement.type = "cod"

                engagement.save()

    except Exception as e:
        print(str(e))

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0055_hr_profile_pic_pmo_profile_pic_sales_business_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='engagement',
            name='type',
            field=models.CharField(blank=True, choices=[('cod', 'COD'), ('caas', 'CAAS')], max_length=225, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='credit_history',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='project',
            name='duration_of_each_session',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='is_project_structure',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='project',
            name='is_session_expiry',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='project',
            name='request_expiry_time',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='total_credits',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='sessionrequestcaas',
            name='engagement',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.engagement'),
        ),
        migrations.AddField(
            model_name='sessionrequestcaas',
            name='requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(populate_engagement_in_session),
    ]
