from django.db import models
from api.models import Learner
# Create your models here.

class Competency(models.Model):
    name = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Question(models.Model):
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    self_question = models.TextField()
    observer_question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.self_question 
    

class Questionnaire(models.Model):
    name = models.CharField(max_length=255,blank=True,null=True)
    questions = models.ManyToManyField(Question,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
    
    
class Observer(models.Model):
    name = models.CharField(max_length=255,blank=True)
    email = models.CharField(max_length=255,blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)



class ParticipantObserverMapping(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE)
    observers = models.ManyToManyField(Observer,blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('self', 'Self'),
        ('360', '360'),
    ]
    RATING_CHOICES = [
        ('1-5', '1-5'),
        ('1-10', '1-10'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=255,blank=True)
    assessment_type = models.CharField(max_length=10, choices=ASSESSMENT_TYPES,blank=True)
    number_of_observers = models.PositiveIntegerField(null=True,blank=True)
    assessment_end_date = models.CharField(max_length=255,blank=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE,blank=True)
    descriptive_questions = models.JSONField(default=list, blank=True) 
    participants_observers = models.ManyToManyField(ParticipantObserverMapping,blank=True)
    rating_type = models.CharField(max_length=5, choices=RATING_CHOICES,blank=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='draft')  
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Response(models.Model):
    participant = models.ForeignKey(Learner, on_delete=models.CASCADE,blank=True)
    observer =  models.ForeignKey(Observer, on_delete=models.CASCADE,blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE,blank=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE,blank=True)
    participant_response = models.JSONField(default=dict, blank=True)
    observer_response = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Response for {self.participant} in Assessment {self.assessment.name}"