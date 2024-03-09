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
    Feedback
)


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


class TextLessonCreateSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer()

    class Meta:
        model = TextLesson
        fields = ["lesson", "content"]

    def create(self, validated_data):
        lesson_data = validated_data.pop("lesson")
        lesson = Lesson.objects.create(**lesson_data)
        text_lesson = TextLesson.objects.create(lesson=lesson, **validated_data)
        return text_lesson

    def update(self, instance, validated_data):
        lesson_data = validated_data.pop("lesson")
        lesson_instance = instance.lesson

        lesson_instance.course = lesson_data.get("course", lesson_instance.course)
        lesson_instance.name = lesson_data.get("name", lesson_instance.name)
        lesson_instance.status = lesson_data.get("status", lesson_instance.status)
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
        ]


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
    class Meta:
        model = Video
        fields = "__all__"


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
    class Meta:
        model = Resources
        fields = "__all__"


class PdfLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfLesson
        fields = "__all__"
        depth = 1


class LessonUpdateSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    status = serializers.CharField(max_length=20)


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"


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

        if lesson_data:
            lesson_instance = instance.lesson
            course_template = lesson_data.pop("course_template", None)
            course = lesson_data.pop("course", None)
            lesson_serializer = LessonSerializer(
                lesson_instance, data=lesson_data, partial=True
            )
            lesson_serializer.is_valid(raise_exception=True)
            lesson_serializer.save()

        instance.description = validated_data.get("description", instance.description)
        instance.file = validated_data.get("file", instance.file)
        instance.save()
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

