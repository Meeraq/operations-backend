# Generated by Django 4.1.7 on 2024-05-02 10:19

from django.db import migrations, models


def copy_pre_post_assessment_to_pre_and_post(apps, schema_editor):
    HandoverDetails = apps.get_model("schedularApi", "HandoverDetails")
    SchedularProject = apps.get_model("schedularApi", "SchedularProject")

    # Copy pre_post_assessment values to pre_assessment and post_assessment
    for handover_details in HandoverDetails.objects.all():
        handover_details.pre_assessment = handover_details.pre_post_assessment
        handover_details.post_assessment = handover_details.pre_post_assessment
        handover_details.save()

    for schedular_project in SchedularProject.objects.all():
        schedular_project.pre_assessment = schedular_project.pre_post_assessment
        schedular_project.post_assessment = schedular_project.pre_post_assessment
        schedular_project.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "schedularApi",
            "0025_remove_handoverdetails_billing_process_details_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="handoverdetails",
            name="post_assessment",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name="handoverdetails",
            name="pre_assessment",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name="schedularproject",
            name="post_assessment",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name="schedularproject",
            name="pre_assessment",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.RunPython(copy_pre_post_assessment_to_pre_and_post),
        migrations.RemoveField(
            model_name="handoverdetails",
            name="pre_post_assessment",
        ),
        migrations.RemoveField(
            model_name="schedularproject",
            name="pre_post_assessment",
        ),
    ]
