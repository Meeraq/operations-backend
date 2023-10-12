from django.db import models

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
    questions = models.ManyToManyField(Question)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Questionnaire {self.id}"
    

