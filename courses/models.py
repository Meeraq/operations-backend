from django.db import models

# Create your models here.


class Course(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("public", "Public"),
    )
    name = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return self.name
