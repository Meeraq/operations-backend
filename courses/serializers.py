# serializers.py
from rest_framework import serializers
from .models import (
    Course,
    Lesson,
    TextLesson,
    Question,
    QuizLesson,
    LiveSessionLesson,
    LaserCoachingSession,
    FeedbackLesson,
    Assessment,
    CourseEnrollment,
    Answer,
    Certificate,
    Video,
    VideoLesson,
    CourseTemplate,
    Resources,
    PdfLesson,
    File,
    DownloadableLesson,
    Nudge,
    AssignmentLesson,
    AssignmentLessonResponse,
    FacilitatorLesson,
    Feedback,
    CttFeedback,
    NudgeResources,
)
from schedularApi.models import LiveSession
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from urllib.parse import urlparse
import requests


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


class CourseTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseTemplate
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class NudgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nudge
        fields = "__all__"



class NudgeSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Nudge
        fields = "__all__"
        depth=1

class NudgeResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NudgeResources
        fields = "__all__"


class NudgeResourcesSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = NudgeResources
        fields = "__all__"
        depth = 1

class NudgeResourcesSerializerDepthOneProjectNames(serializers.ModelSerializer):
    project_names = serializers.CharField()
    class Meta:
        model = NudgeResources
        fields = "__all__"
        depth = 1



class TextLessonCreateSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer()

    class Meta:
        model = TextLesson
        fields = ["lesson", "content"]

    def create(self, validated_data):
        try:
            lesson_data = validated_data.pop("lesson")
            lesson = Lesson.objects.create(**lesson_data)
            text_lesson = TextLesson.objects.create(lesson=lesson, **validated_data)
            return text_lesson
        except Exception as e:
            print(str(e))

    def update(self, instance, validated_data):
        lesson_data = validated_data.pop("lesson")
        lesson_instance = instance.lesson
        lesson_instance.course = lesson_data.get("course", lesson_instance.course)
        lesson_instance.name = lesson_data.get("name", lesson_instance.name)
        lesson_instance.status = lesson_data.get("status", lesson_instance.status)
        lesson_instance.drip_date = lesson_data.get("drip_date", None)
        live_session = lesson_data.get("live_session")
        if live_session:
            lesson_instance.live_session = live_session
        else:
            lesson_instance.live_session = None

        lesson_instance.lesson_type = lesson_data.get(
            "lesson_type", lesson_instance.lesson_type
        )
        lesson_instance.save()

        instance.content = validated_data.get("content", instance.content)
        instance.save()

        return instance


class TextLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextLesson
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "name",
            "status",
            "lesson_type",
            "order",
            "course_template",
            "drip_date",
            "live_session",
        ]


class LessonSerializerForLiveSessionDateTime(serializers.ModelSerializer):
    live_session_date_time = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "name",
            "status",
            "lesson_type",
            "order",
            "course_template",
            "drip_date",
            "live_session",
            "live_session_date_time",
        ]

    def get_live_session_date_time(self, obj):
        if obj.live_session:
            return obj.live_session.date_time
        return None


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class QuizLessonDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizLesson
        fields = "__all__"
        depth = 1


class FeedbackLessonDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackLesson
        fields = "__all__"
        depth = 1


class LiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSessionLesson
        fields = "__all__"


class LiveSessionSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = LiveSessionLesson
        fields = "__all__"
        depth = 1


class LaserSessionSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = LaserCoachingSession
        fields = "__all__"
        depth = 1


class LaserCoachingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaserCoachingSession
        fields = "__all__"


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"


class AssessmentSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"
        depth = 1


class VideoSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ["id", "name", "video", "file_size_mb"]

    def get_file_size_mb(self, obj):
        if obj.video:  # Assuming 'video' is the attribute for the video FileField
            return self.get_video_file_size(obj.video)
        else:
            return None

    def get_video_file_size(self, video_field):
        # Check if it's a FieldFile
        if hasattr(video_field, "size"):
            try:
                # Convert file size from bytes to MB
                file_size_mb = video_field.size / (1024 * 1024)
                return round(file_size_mb, 2)  # Round to 2 decimal places
            except Exception as e:
                # Handle any errors, such as file not found
                print(f"Error calculating file size: {e}")
                return None
        else:
            return None


class VideoLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoLesson
        fields = "__all__"


class VideoLessonSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = VideoLesson
        fields = "__all__"
        depth = 1


class CourseEnrollmentDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = "__all__"
        depth = 1


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class CertificateSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"
        depth = 1


class ResourcesSerializer(serializers.ModelSerializer):
    file_size_kb = serializers.SerializerMethodField()

    class Meta:
        model = Resources
        fields = ["id", "name", "pdf_file", "file_size_kb"]

    def get_file_size_kb(self, obj):
        try:
            if obj.pdf_file and hasattr(obj.pdf_file, "size"):
                return obj.pdf_file.size / 1024.0
        except Exception as e:  # Catching more general exceptions
            # Handle exceptions appropriately, like logging or returning a specific error message
            pass
        return None


class PdfLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfLesson
        fields = "__all__"
        depth = 1


class LessonUpdateSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    status = serializers.CharField(max_length=20)


class FileSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ["id", "name", "file", "file_size_mb"]

    def get_file_size_mb(self, obj):
        if obj.file:
            file_size_bytes = obj.file.size
            file_size_mb = file_size_bytes / (1024 * 1024)  # Convert bytes to MB
            return round(file_size_mb, 2)  # Round to 2 decimal places
        else:
            return None


class DownloadableLessonSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer()

    class Meta:
        model = DownloadableLesson
        fields = ["id", "lesson", "description", "file"]

    def create(self, validated_data):
        lesson_data = validated_data.pop("lesson")
        lesson_instance = Lesson.objects.create(**lesson_data)
        downloadable_lesson_instance = DownloadableLesson.objects.create(
            lesson=lesson_instance, **validated_data
        )
        return downloadable_lesson_instance

    def update(self, instance, validated_data):
        lesson_data = validated_data.pop("lesson", None)
        try:
            if lesson_data:
                lesson_instance = instance.lesson
                course_template = lesson_data.pop("course_template", None)
                course = lesson_data.pop("course", None)
                lesson_data["live_session"] = (
                    lesson_data["live_session"].id
                    if lesson_data["live_session"]
                    else None
                )
                lesson_serializer = LessonSerializer(
                    lesson_instance, data=lesson_data, partial=True
                )
                lesson_serializer.is_valid(raise_exception=True)
                lesson_serializer.save()

            instance.description = validated_data.get(
                "description", instance.description
            )
            instance.file = validated_data.get("file", instance.file)
            instance.save()
            return instance
        except Exception as e:
            print(str(e))
            return instance


class AssignmentSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = AssignmentLesson
        fields = "__all__"
        depth = 1


class FacilitatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilitatorLesson
        fields = "__all__"
        depth = 1


class AssignmentResponseSerializerDepthSix(serializers.ModelSerializer):
    class Meta:
        model = AssignmentLessonResponse
        fields = "__all__"
        depth = 6


class AssignmentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentLessonResponse
        fields = "__all__"


class FeedbackDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"
        depth = 1


class CourseEnrollmentWithNamesSerializer(serializers.ModelSerializer):
    learner_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "course",
            "learner",
            "learner_name",
            "course_name",
            "enrollment_date",
            "completed_lessons",
            "is_certificate_allowed",
        ]

    def get_learner_name(self, obj):
        return obj.learner.name

    def get_course_name(self, obj):
        return obj.course.name


class CttFeedbackDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CttFeedback
        fields = "__all__"
