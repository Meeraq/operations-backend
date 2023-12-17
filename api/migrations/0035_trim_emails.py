# Generated by Django 4.1.7 on 2023-12-13 14:14

from django.db import migrations


def trim_emails(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Learner = apps.get_model("api", "Learner")
    Pmo = apps.get_model("api", "Pmo")
    Coach = apps.get_model("api", "Coach")
    Hr = apps.get_model("api", "Hr")
    Vendor = apps.get_model("zohoapi", "Vendor")
    # Trim emails for the User model
    for user in User.objects.all():
        if user.email:
            user.email = user.email.strip()
        if user.username:
            user.username = user.username.strip()
        user.save()

    # Trim emails for other models
    for model in [Learner, Pmo, Coach, Hr, Vendor]:
        for instance in model.objects.all():
            if instance.email:
                instance.email = instance.email.strip()
            instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0034_role_remove_profile_type_profile_roles"),
    ]

    operations = [
        migrations.RunPython(trim_emails),
    ]