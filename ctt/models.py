# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AdminLocation(models.Model):
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey("Admins", models.DO_NOTHING)
    location = models.ForeignKey("Locations", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "admin_location"


class Admins(models.Model):
    id = models.BigAutoField(primary_key=True)
    country = models.ForeignKey("Countries", models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey("Locations", models.DO_NOTHING, blank=True, null=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(unique=True, max_length=64)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    password = models.CharField(max_length=255)
    country_code = models.CharField(max_length=8, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.CharField(max_length=64, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    remember_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False
        db_table = "admins"


class Agreements(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=9)

    class Meta:
        managed = False

        db_table = "agreements"


class Announcements(models.Model):
    id = models.BigAutoField(primary_key=True)
    program = models.ForeignKey("Programs", models.DO_NOTHING)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "announcements"


class AssignmentDocuments(models.Model):
    id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey("Assignments", models.DO_NOTHING)
    name = models.CharField(max_length=255, blank=True, null=True)
    document = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "assignment_documents"


class Assignments(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=13)
    name = models.CharField(max_length=255)
    batch = models.ForeignKey("Batches", models.DO_NOTHING)
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "assignments"


class BatchAnnouncements(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch = models.ForeignKey("Batches", models.DO_NOTHING)
    announcement = models.ForeignKey(Announcements, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "batch_announcements"


class BatchFaculty(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch = models.ForeignKey("Batches", models.DO_NOTHING)
    faculty = models.ForeignKey("Faculties", models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "batch_faculty"


class BatchJourneys(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    batch = models.ForeignKey("Batches", models.DO_NOTHING)
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False

        db_table = "batch_journeys"


class BatchMentorCoach(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch = models.ForeignKey("Batches", models.DO_NOTHING)
    faculty = models.ForeignKey("Faculties", models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "batch_mentor_coach"


class BatchUsers(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch = models.ForeignKey("Batches", models.DO_NOTHING)
    parent_batch = models.ForeignKey(
        "Batches", models.DO_NOTHING, blank=True, null=True, related_name="parent_batch"
    )
    user = models.ForeignKey("Users", models.DO_NOTHING)
    accept_agreement = models.IntegerField(blank=True, null=True)
    certificate = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=9)

    class Meta:
        managed = False

        db_table = "batch_users"


class Batches(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=7, blank=True, null=True)
    type_2 = models.CharField(max_length=64, blank=True, null=True)
    program = models.ForeignKey("Programs", models.DO_NOTHING)
    country = models.ForeignKey("Countries", models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey("Locations", models.DO_NOTHING, blank=True, null=True)
    company = models.ForeignKey("Companies", models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=64, blank=True, null=True)
    contact_email = models.CharField(max_length=32, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    reg_start_date = models.DateField(blank=True, null=True)
    reg_end_date = models.DateField(blank=True, null=True)
    duration_hr = models.PositiveIntegerField(blank=True, null=True)
    duration_min = models.PositiveIntegerField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    frequency = models.CharField(max_length=64, blank=True, null=True)
    session_information = models.CharField(max_length=255, blank=True, null=True)
    zero_cost_electives = models.PositiveIntegerField(blank=True, null=True)
    mentor_coach_meetings = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=9)

    class Meta:
        managed = False
        db_table = "batches"


class CertificationLevels(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "certification_levels"


class CoachTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    code = models.CharField(unique=True, max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "coach_types"


class Companies(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=64, blank=True, null=True)
    contact_email = models.CharField(max_length=32, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "companies"


class Countries(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=5, blank=True, null=True)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "countries"


class Currencies(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    code = models.CharField(unique=True, max_length=16, blank=True, null=True)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "currencies"


class CurrentCredentials(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "current_credentials"


class CurrentFunctions(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "current_functions"


class CurrentRoles(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "current_roles"


class Faculties(models.Model):
    id = models.BigAutoField(primary_key=True)
    country = models.ForeignKey(Countries, models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey("Locations", models.DO_NOTHING, blank=True, null=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(unique=True, max_length=64)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    password = models.CharField(max_length=255)
    country_code = models.CharField(max_length=8, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.CharField(max_length=64, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    last_logged_in_at = models.DateTimeField(blank=True, null=True)
    logged_in_at = models.DateTimeField(blank=True, null=True)
    remember_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "faculties"


class FacultyCoachType(models.Model):
    id = models.BigAutoField(primary_key=True)
    faculty = models.ForeignKey(Faculties, models.DO_NOTHING)
    coach_type = models.ForeignKey(CoachTypes, models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "faculty_coach_type"


class FacultyLocation(models.Model):
    id = models.BigAutoField(primary_key=True)
    faculty = models.ForeignKey(Faculties, models.DO_NOTHING)
    location = models.ForeignKey("Locations", models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "faculty_location"


class FailedJobs(models.Model):
    id = models.BigAutoField(primary_key=True)
    uuid = models.CharField(unique=True, max_length=255)
    connection = models.TextField()
    queue = models.TextField()
    payload = models.TextField()
    exception = models.TextField()
    failed_at = models.DateTimeField()

    class Meta:
        managed = False

        db_table = "failed_jobs"


class GlobalAnnouncements(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "global_announcements"


class Invoices(models.Model):
    id = models.BigAutoField(primary_key=True)
    payment = models.ForeignKey("Payments", models.DO_NOTHING)
    currency = models.ForeignKey(Currencies, models.DO_NOTHING, blank=True, null=True)
    invoice_no = models.CharField(max_length=64, blank=True, null=True)
    invoice_date = models.DateTimeField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=6)

    class Meta:
        managed = False

        db_table = "invoices"


class Jobs(models.Model):
    id = models.BigAutoField(primary_key=True)
    queue = models.CharField(max_length=255)
    payload = models.TextField()
    attempts = models.PositiveIntegerField()
    reserved_at = models.PositiveIntegerField(blank=True, null=True)
    available_at = models.PositiveIntegerField()
    created_at = models.PositiveIntegerField()

    class Meta:
        managed = False

        db_table = "jobs"


class Labels(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "labels"


class Locations(models.Model):
    id = models.BigAutoField(primary_key=True)
    country = models.ForeignKey(Countries, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=64)
    popular = models.IntegerField()
    sort_order = models.SmallIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "locations"


class MentorCoachSessions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    batch = models.ForeignKey(Batches, models.DO_NOTHING)
    faculty = models.ForeignKey(Faculties, models.DO_NOTHING)
    session_no = models.SmallIntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=7)

    class Meta:
        managed = False
        db_table = "mentor_coach_sessions"


class Migrations(models.Model):
    migration = models.CharField(max_length=255)
    batch = models.IntegerField()

    class Meta:
        managed = False

        db_table = "migrations"


class Options(models.Model):
    id = models.BigAutoField(primary_key=True)
    key = models.CharField(unique=True, max_length=64)
    value = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False

        db_table = "options"


class PasswordResets(models.Model):
    email = models.CharField(max_length=255)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False

        db_table = "password_resets"


class Payments(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    currency = models.ForeignKey(Currencies, models.DO_NOTHING, blank=True, null=True)
    payment_uid = models.CharField(unique=True, max_length=32, blank=True, null=True)
    payment_mode = models.CharField(max_length=7, blank=True, null=True)
    for_field = models.CharField(
        db_column="for", max_length=8, blank=True, null=True
    )  # Field renamed because it was a Python reserved word.
    program = models.ForeignKey("Programs", models.DO_NOTHING, blank=True, null=True)
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    pg_response = models.JSONField(blank=True, null=True)
    pg_payment_status = models.CharField(max_length=7, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "payments"


class ProgramFaculty(models.Model):
    id = models.BigAutoField(primary_key=True)
    program = models.ForeignKey("Programs", models.DO_NOTHING)
    faculty = models.ForeignKey(Faculties, models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "program_faculty"


class ProgramFeedback(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    program = models.ForeignKey("Programs", models.DO_NOTHING)
    feedback = models.TextField(blank=True, null=True)
    emoticon = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "program_feedback"


class ProgramMentorCoach(models.Model):
    id = models.BigAutoField(primary_key=True)
    program = models.ForeignKey("Programs", models.DO_NOTHING)
    faculty = models.ForeignKey(Faculties, models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "program_mentor_coach"


class ProgramResource(models.Model):
    id = models.BigAutoField(primary_key=True)
    program = models.ForeignKey("Programs", models.DO_NOTHING)
    resource = models.ForeignKey("Resources", models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "program_resource"


class Programs(models.Model):
    id = models.BigAutoField(primary_key=True)
    agreement = models.ForeignKey(Agreements, models.DO_NOTHING, blank=True, null=True)
    certification_level = models.ForeignKey(
        CertificationLevels, models.DO_NOTHING, blank=True, null=True
    )
    label = models.ForeignKey(Labels, models.DO_NOTHING, blank=True, null=True)
    currency = models.ForeignKey(Currencies, models.DO_NOTHING, blank=True, null=True)
    type = models.CharField(max_length=8)
    type_2 = models.CharField(max_length=64, blank=True, null=True)
    name = models.CharField(max_length=255)
    code = models.CharField(unique=True, max_length=32, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=64, blank=True, null=True)
    prerequisites = models.TextField(blank=True, null=True)
    capacity = models.PositiveSmallIntegerField(blank=True, null=True)
    zero_cost_electives = models.PositiveIntegerField(blank=True, null=True)
    who_is_it_for = models.TextField(blank=True, null=True)
    what_you_will_gain = models.TextField(blank=True, null=True)
    payment_mode = models.CharField(max_length=7, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mentor_coach_meetings = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False
        db_table = "programs"


class Recordings(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=4, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file = models.CharField(max_length=64, blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "recordings"


class Resources(models.Model):
    id = models.BigAutoField(primary_key=True)
    visibility = models.CharField(max_length=7, blank=True, null=True)
    format = models.CharField(max_length=8, blank=True, null=True)
    type = models.CharField(max_length=4, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file = models.CharField(max_length=64, blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "resources"


class SessionRecording(models.Model):
    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey("Sessions", models.DO_NOTHING)
    recording = models.ForeignKey(Recordings, models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "session_recording"


class Sessions(models.Model):
    id = models.BigAutoField(primary_key=True)
    batch = models.ForeignKey(Batches, models.DO_NOTHING)
    type = models.CharField(max_length=9, blank=True, null=True)
    session_no = models.SmallIntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=9)

    class Meta:
        managed = False

        db_table = "sessions"


class UserAssignments(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    assignment = models.ForeignKey(Assignments, models.DO_NOTHING)
    document_name = models.CharField(max_length=255, blank=True, null=True)
    document = models.CharField(max_length=64, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=11)

    class Meta:
        managed = False

        db_table = "user_assignments"


class UserCurrentCredential(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    current_credential = models.ForeignKey(CurrentCredentials, models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "user_current_credential"


class UserLocation(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    location = models.ForeignKey(Locations, models.DO_NOTHING)

    class Meta:
        managed = False

        db_table = "user_location"


class UserResources(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("Users", models.DO_NOTHING)
    resource = models.ForeignKey(Resources, models.DO_NOTHING)
    batch = models.ForeignKey(Batches, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=9)

    class Meta:
        managed = False

        db_table = "user_resources"


class Users(models.Model):
    id = models.BigAutoField(primary_key=True)
    country = models.ForeignKey(Countries, models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey(Locations, models.DO_NOTHING, blank=True, null=True)
    current_function = models.ForeignKey(
        CurrentFunctions, models.DO_NOTHING, blank=True, null=True
    )
    current_role = models.ForeignKey(
        CurrentRoles, models.DO_NOTHING, blank=True, null=True
    )
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(unique=True, max_length=64)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    password = models.CharField(max_length=255)
    country_code = models.CharField(max_length=8, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.CharField(max_length=64, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    current_organisation_name = models.CharField(max_length=255, blank=True, null=True)
    current_organisation_website = models.CharField(
        max_length=255, blank=True, null=True
    )
    facebook_profile_url = models.CharField(max_length=255, blank=True, null=True)
    linkedin_profile_url = models.CharField(max_length=255, blank=True, null=True)
    instagram_profile_url = models.CharField(max_length=255, blank=True, null=True)
    twitter_profile_url = models.CharField(max_length=255, blank=True, null=True)
    last_logged_in_at = models.DateTimeField(blank=True, null=True)
    logged_in_at = models.DateTimeField(blank=True, null=True)
    remember_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=8)

    class Meta:
        managed = False

        db_table = "users"
