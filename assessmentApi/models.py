from django.db import models
from api.models import Learner, Profile, Organisation, HR
from django.contrib.auth.models import User

# Create your models here.


class Behavior(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Competency(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    behaviors = models.ManyToManyField(Behavior, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    QUESTION_TYPES = [
        ("self", "Self"),
        ("360", "360"),
    ]
    RATING_CHOICES = [
        ("1-5", "1-5"),
        ("1-10", "1-10"),
    ]

    RESPONSE_CHOICES = [
        ("correct_answer", "Correct Answer"),
        ("rating_type", "Rating Type"),
    ]

    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=QUESTION_TYPES, blank=True)
    self_question = models.TextField()
    observer_question = models.TextField(blank=True, null=True)
    reverse_question = models.BooleanField(blank=True, default=False)
    behavior = models.ForeignKey(Behavior, on_delete=models.CASCADE, blank=True)
    rating_type = models.CharField(max_length=5, choices=RATING_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    label = models.JSONField(blank=True, null=True)
    correct_answer = models.JSONField(default=list, blank=True)
    response_type = models.CharField(max_length=50, choices=RESPONSE_CHOICES, blank=True)

    def __str__(self):
        return self.self_question


class Questionnaire(models.Model):
    QUESTIONNAIRE_TYPES = [
        ("self", "Self"),
        ("360", "360"),
    ]
    QUESTIONS_TYPE = [
        ("correct_answer_type", " Correct Answer Type"),
        ("rating_type", "Rating Type"),
    ]
    name = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=10, choices=QUESTIONNAIRE_TYPES, blank=True)
    questions = models.ManyToManyField(Question, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


class Observer(models.Model):
    name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=25, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ParticipantObserverMapping(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE, blank=True)
    observers = models.ManyToManyField(Observer, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mapping for {self.participant}"


class ObserverTypes(models.Model):
    type = models.CharField(max_length=225, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ParticipantObserverType(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE, blank=True)
    observers = models.ForeignKey(Observer, on_delete=models.CASCADE, blank=True)
    type = models.ForeignKey(ObserverTypes, on_delete=models.CASCADE, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Type of {self.observers.name} for {self.participant.name} is {self.type}"
        )


class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ("self", "Self"),
        ("360", "360"),
    ]
    RATING_CHOICES = [
        ("1-5", "1-5"),
        ("1-10", "1-10"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
    ]

    ASSESSMENT_TIMING_CHOICES = [
        ("pre", "Pre-Assessment"),
        ("post", "Post-Assessment"),
        ("none", "None"),
    ]

    name = models.CharField(max_length=255, blank=True)
    participant_view_name = models.CharField(max_length=255, blank=True)
    assessment_type = models.CharField(
        max_length=10, choices=ASSESSMENT_TYPES, blank=True
    )
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    hr = models.ManyToManyField(HR, blank=True)
    number_of_observers = models.PositiveIntegerField(null=True, blank=True)
    assessment_start_date = models.CharField(max_length=255, blank=True)
    assessment_end_date = models.CharField(max_length=255, blank=True)
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, blank=True
    )
    descriptive_questions = models.JSONField(default=list, blank=True)
    participants_observers = models.ManyToManyField(
        ParticipantObserverMapping, blank=True
    )
    observer_types = models.ManyToManyField(ObserverTypes, blank=True)
    # rating_type = models.CharField(max_length=5, choices=RATING_CHOICES, blank=True)
    automated_reminder = models.BooleanField(blank=True, default=False)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="draft")
    result_released = models.BooleanField(blank=True, default=False)
    assessment_timing = models.CharField(
        max_length=255, choices=ASSESSMENT_TIMING_CHOICES, default="none"
    )
    pre_assessment = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True
    )
    initial_reminder = models.BooleanField(blank=True, default=False)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    instructions = models.TextField(blank=True,default="")

    def __str__(self):
        return self.name


class ParticipantResponse(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, blank=True)
    participant_response = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Response for {self.participant.name} in Assessment {self.assessment.name}"
        )


class ObserverResponse(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE, blank=True)
    observer = models.ForeignKey(Observer, on_delete=models.CASCADE, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, blank=True)
    observer_response = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response for Observer {self.observer.name} in Assessment {self.assessment.name} participant is {self.participant.name}"


class ObserverUniqueId(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE, blank=True)
    observer = models.ForeignKey(Observer, on_delete=models.CASCADE, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, blank=True)
    unique_id = models.CharField(max_length=225, unique=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Unique Id for Observer {self.observer.name} in Assessment {self.assessment.name} participant is {self.participant.name}"


class AssessmentNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    path = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True)
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class ParticipantUniqueId(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, blank=True)
    unique_id = models.CharField(max_length=225, unique=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Unique Id for Participant {self.participant.name} in Assessment {self.assessment.name}."


class ParticipantReleasedResults(models.Model):
    participants = models.ManyToManyField(Learner, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
