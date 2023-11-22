from django.db import models
from api.models import Learner

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


class Question(models.Model):
    QUESTION_TYPES = [
        ("single_correct_answer", "Single Correct Answer"),
        ("multiple_correct_answer", "Multiple Correct Answers"),
        ("rating_1_to_5", "1 to 5 Rating"),
        ("rating_1_to_10", "1 to 10 Rating"),
        ("descriptive_answer", "Descriptive Answer"),
    ]
    text = models.CharField(max_length=255)
    options = models.JSONField(default=list)
    type = models.CharField(max_length=255, choices=QUESTION_TYPES)


class QuizLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question)


class FeedbackLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question)


class LiveSession(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    description = models.TextField()
    meeting_link = models.URLField()
    date = models.DateField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class LaserCoachingSession(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    description = models.TextField()
    booking_link = models.URLField()


class Assessment(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)


# class Video(models.Model):
#     lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
#     video = models.FileField(upload_to="videos/")


class CourseEnrollment(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.learner.name} enrolled in {self.course.name}"


class Certificate(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    courses = models.ManyToManyField(Course, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"