# serializers.py
from rest_framework import serializers
from .models import Course, LiveSession, Lesson, TextLesson


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
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
        fields = ["id", "course", "name", "status", "lesson_type"]


class LiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = "__all__"


class LiveSessionSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = "__all__"
        depth = 1
