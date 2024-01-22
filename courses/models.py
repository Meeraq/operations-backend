from django.db import models
from api.models import Learner
from schedularApi.models import SchedularBatch, LiveSession, CoachingSession
import os
from django.core.exceptions import ValidationError
from django_celery_beat.models import PeriodicTask
import uuid

# Create your models here.


class CourseTemplate(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("public", "Public"),
    )
    name = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return self.name


class Course(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("public", "Public"),
    )
    name = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    course_template = models.ForeignKey(CourseTemplate, on_delete=models.CASCADE)
    batch = models.ForeignKey(SchedularBatch, on_delete=models.CASCADE)
    nudge_start_date = models.DateField(default=None, blank=True, null=True)
    nudge_frequency = models.CharField(max_length=50, default="", blank=True, null=True)
    nudge_periodic_task = models.ForeignKey(
        PeriodicTask, blank=True, null=True, on_delete=models.SET_NULL
    )

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
        ("ppt", "PPT"),
        ("downloadable_file", "Downloadable File"),
    )
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("public", "Public"),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    course_template = models.ForeignKey(
        CourseTemplate, on_delete=models.CASCADE, blank=True, null=True
    )
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES)
    order = models.PositiveIntegerField(default=0)


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
        ("rating_0_to_10", "0 to 10 Rating"),
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
    unique_id = models.CharField(
        max_length=225,
        blank=True,
    )


class LiveSessionLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    live_session = models.ForeignKey(LiveSession, on_delete=models.CASCADE)
    # description = models.TextField()
    # meeting_link = models.URLField()
    # date = models.DateField()
    # start_time = models.DateTimeField()
    # end_time = models.DateTimeField()


class LaserCoachingSession(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    coaching_session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE)


class Assessment(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)


class Video(models.Model):
    # lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    name = models.TextField()
    video = models.FileField(upload_to="videos/")


class VideoLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)


class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="file-uploads/")

    def __str__(self):
        return self.name


class DownloadableLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    description = models.TextField(default="", blank=True)
    file = models.ForeignKey(File, on_delete=models.CASCADE)

    def __str__(self):
        return f"File lesson {self.lesson.name}"


class CourseEnrollment(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completed_lessons = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.learner.name} enrolled in {self.course.name}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True, null=True)  # For descriptive answers
    selected_options = models.JSONField(
        default=list
    )  # For single/multiple choice answers
    rating = models.IntegerField(blank=True, null=True)  # For rating type answers

    def __str__(self):
        return f"Answer for {self.question.text}"


class Certificate(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    courses = models.ManyToManyField(Course, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


class QuizLessonResponse(models.Model):
    quiz_lesson = models.ForeignKey(QuizLesson, on_delete=models.CASCADE)
    answers = models.ManyToManyField(Answer)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)


class FeedbackLessonResponse(models.Model):
    feedback_lesson = models.ForeignKey(FeedbackLesson, on_delete=models.CASCADE)
    answers = models.ManyToManyField(Answer)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)


def validate_pdf_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if not ext == ".pdf":
        raise ValidationError("Only PDF files are allowed.")


class Resources(models.Model):
    # lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    name = models.TextField()
    pdf_file = models.FileField(
        upload_to="pdf_files", blank=True, validators=[validate_pdf_extension]
    )


class PdfLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    pdf = models.ForeignKey(Resources, on_delete=models.CASCADE)


class ThinkificLessonCompleted(models.Model):
    course_name = models.TextField(blank=True)
    lesson_name = models.TextField(blank=True)
    student_name = models.TextField(blank=True)
    completion_data = models.JSONField(blank=True)

    def __str__(self):
        return f"{self.student_name} completed {self.lesson_name} in {self.course_name}"


class Nudge(models.Model):
    name = models.CharField(max_length=255)
    content = models.TextField()
    file = models.FileField(upload_to="nudge_files/", blank=True, null=True)
    order = models.IntegerField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
