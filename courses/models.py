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


class Lesson(models.Model):
    LESSON_TYPES = (
        ("text", "Text Lesson"),
        ("quiz", "Quiz Lesson"),
        ("live_session", "Live Session"),
        ("laser_coaching", "Laser Coaching Session"),
        ("feedback", "Feedback"),
        ("assessment", "Assessment"),
        ("video", "Video"),
    )
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("public", "Public"),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES)


class TextLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    content = models.TextField(default="", blank=True)


# class QuizLesson(models.Model):
#     lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
#     questions = models.TextField()
#     answers = models.TextField()


class LiveSession(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    description = models.TextField()
    meeting_link = models.URLField()
    date = models.DateField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(auto_now_add=True)


# class LaserCoachingSession(models.Model):
#     lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
#     description = models.TextField()
#     booking_link = models.URLField()


# class Feedback(models.Model):
#     lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     questions = (
#         models.TextField()
#     )  # JSONField or separate models for questions can be considered


# class Assessment(models.Model):
#     lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
#     message = models.TextField()


# class Video(models.Model):
#     lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
#     video = models.FileField(upload_to="videos/")
