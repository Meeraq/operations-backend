from django.shortcuts import render

# Create your views here.
from rest_framework import generics, serializers
from rest_framework.decorators import api_view
from rest_framework import status
from .models import Course, TextLesson, Lesson, Question, QuizLesson
from .serializers import (
    CourseSerializer,
    TextLessonCreateSerializer,
    TextLessonSerializer,
    LessonSerializer,
    QuestionSerializer,
    QuizLessonDepthOneSerializer,
)
from rest_framework.response import Response


class CourseListView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        name = serializer.validated_data.get("name", None)
        if name and Course.objects.filter(name=name.strip()).exists():
            raise serializers.ValidationError("Course with this name already exists.")
        serializer.save()


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_update(self, serializer):
        name = serializer.validated_data.get("name", None)
        instance = self.get_object()
        if (
            name
            and Course.objects.exclude(pk=instance.pk)
            .filter(name=name.strip())
            .exists()
        ):
            raise serializers.ValidationError("Course with this name already exists.")
        serializer.save()


class TextLessonCreateView(generics.CreateAPIView):
    queryset = TextLesson.objects.all()
    serializer_class = TextLessonCreateSerializer


class TextLessonEditView(generics.RetrieveUpdateAPIView):
    queryset = TextLesson.objects.all()
    serializer_class = TextLessonCreateSerializer


class LessonListView(generics.ListAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        # Retrieve lessons for a specific course based on the course ID in the URL
        course_id = self.kwargs.get("course_id")
        return Lesson.objects.filter(course__id=course_id)


class LessonDetailView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        lesson_id = self.kwargs.get("lesson_id", None)
        lesson_type = self.kwargs.get("lesson_type", None)
        print(lesson_id, lesson_type)

        if lesson_id is None or lesson_type is None:
            return Response(
                {"error": "Both lesson_id and type parameters are required."},
                status=400,
            )

        try:
            lesson = Lesson.objects.get(id=lesson_id, lesson_type=lesson_type)
        except Lesson.DoesNotExist:
            return Response(
                {"error": f"Lesson doesn't exists."},
                status=404,
            )

        if lesson_type == "text":
            text_lesson = TextLesson.objects.get(lesson=lesson)
            serializer = TextLessonSerializer(text_lesson)
        elif lesson_type == "quiz":
            quiz_lesson = QuizLesson.objects.get(lesson=lesson)
            serializer = QuizLessonDepthOneSerializer(quiz_lesson)
        else:
            return Response({"error": f"Failed to get the lessons"}, status=400)

        return Response(serializer.data)


@api_view(["POST"])
def create_quiz_lesson(request):
    # Deserialize the incoming data
    data = request.data
    lesson_data = data.get("lesson")
    questions_data = data.get("questions")

    # Create the Lesson
    lesson_serializer = LessonSerializer(data=lesson_data)
    if lesson_serializer.is_valid():
        lesson = lesson_serializer.save()

        # Create Questions and associate them with the Lesson
        questions = []
        for question_data in questions_data:
            question_serializer = QuestionSerializer(data=question_data)
            if question_serializer.is_valid():
                question = question_serializer.save()
                questions.append(question)
            else:
                # If any question is invalid, delete the created lesson and return an error
                lesson.delete()
                return Response(
                    question_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        # Create QuizLesson and associate it with the Lesson
        quiz_lesson = QuizLesson.objects.create(lesson=lesson)
        quiz_lesson.questions.set(questions)

        return Response(
            {"message": "Lesson and Quiz created successfully"},
            status=status.HTTP_201_CREATED,
        )
    else:
        return Response(lesson_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
