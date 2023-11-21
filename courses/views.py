from django.shortcuts import render

# Create your views here.
from rest_framework import generics, serializers, status
from .models import Course, TextLesson, Lesson, LiveSession, LaserCoachingSession
from rest_framework.response import Response
from .serializers import (
    CourseSerializer,
    TextLessonCreateSerializer,
    TextLessonSerializer,
    LessonSerializer,
    LiveSessionSerializer,
    LessonSerializer,
    LiveSessionSerializerDepthOne,
    LaserSessionSerializerDepthOne,
    LaserCoachingSessionSerializer,
)
from rest_framework.decorators import api_view, permission_classes


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
        elif lesson_type == "live_session":
            live_session = LiveSession.objects.get(lesson=lesson)
            serializer = LiveSessionSerializer(live_session)
        elif lesson_type == "laser_coaching":
            laser_coaching = LaserCoachingSession.objects.get(lesson=lesson)
            serializer = LaserSessionSerializerDepthOne(laser_coaching)
        else:
            return Response({"error": f"Failed to get the lessons"}, status=400)

        return Response(serializer.data)


@api_view(["POST"])
def create_lesson_with_live_session(request):
    lesson_data = request.data.get("lesson")
    live_session_data = request.data.get("live_session")

    lesson_serializer = LessonSerializer(data=lesson_data)
    lesson_serializer.is_valid(raise_exception=True)
    lesson_instance = lesson_serializer.save()  # Save Lesson

    # Update live_session_data to include lesson_id
    live_session_data["lesson"] = lesson_instance.id

    live_session_serializer = LiveSessionSerializer(data=live_session_data)
    live_session_serializer.is_valid(raise_exception=True)
    live_session_instance = (
        live_session_serializer.save()
    )  # Save LiveSession linked to Lesson

    return Response(
        {
            "lesson_id": lesson_instance.id,
            "live_session_id": live_session_instance.id,
            "message": "Lesson and LiveSession created successfully!",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def get_live_sessions_for_lesson(request, lesson_id, course_id):
    try:
        live_sessions = LiveSession.objects.filter(
            lesson__id=lesson_id, lesson__course__id=course_id
        )
        serializer = LiveSessionSerializerDepthOne(live_sessions, many=True)
        return Response(serializer.data)
    except LiveSession.DoesNotExist:
        return Response(status=404)


@api_view(["PUT"])
def update_live_session(request, course_id, lesson_id):
    try:
        lesson = Lesson.objects.get(pk=lesson_id, course__id=course_id)
        live_session = LiveSession.objects.get(lesson=lesson)
    except (Lesson.DoesNotExist, LiveSession.DoesNotExist):
        return Response(
            {"message": "Live session does not exist for this lesson"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "PUT":
        lesson_data = request.data.get("lesson")
        live_session_data = request.data.get("live_session")

        # Update Lesson instance fields
        lesson.name = lesson_data.get("name")
        lesson.status = lesson_data.get("status")
        lesson.lesson_type = lesson_data.get("lesson_type")
        lesson.save()

        # Update LiveSession instance fields
        live_session.description = live_session_data.get("description")
        live_session.meeting_link = live_session_data.get("meeting_link")
        live_session.date = live_session_data.get("date")
        live_session.start_time = live_session_data.get("start_time")
        live_session.end_time = live_session_data.get("end_time")
        live_session.save()

        # Update Lesson status based on incoming data
        lesson_status = lesson_data.get("status")
        if lesson_status:
            lesson.status = lesson_status
            lesson.save()

        # Serialize the updated LiveSession instance
        serializer = LiveSessionSerializer(live_session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["POST"])
def create_laser_booking_lesson(request):
    lesson_data = request.data.get("lesson")
    coaching_session_data = request.data.get("laser_coaching_session")

    # Create a Lesson instance
    lesson = Lesson.objects.create(
        course_id=lesson_data["course"],
        name=lesson_data["name"],
        status=lesson_data["status"],
        lesson_type=lesson_data["lesson_type"],
    )

    # Create a LaserCoachingSession instance associated with the created Lesson
    coaching_session = LaserCoachingSession.objects.create(
        lesson=lesson,
        description=coaching_session_data["description"],
        booking_link=coaching_session_data["booking_link"],
    )

    # Optionally, return a success response
    return Response(
        "Laser coaching lesson created successfully", status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
def get_laser_coaching_sessions(request, lesson_id, course_id):
    try:
        laser_sessions = LaserCoachingSession.objects.filter(
            lesson__id=lesson_id, lesson__course__id=course_id
        )
        serializer = LaserSessionSerializerDepthOne(laser_sessions, many=True)
        return Response(serializer.data)
    except LaserCoachingSession.DoesNotExist:
        return Response(status=404)


@api_view(["PUT"])
def update_laser_coaching_session(request, course_id, lesson_id, session_id):
    try:
        lesson = Lesson.objects.get(course_id=course_id, id=lesson_id)
        coaching_session = LaserCoachingSession.objects.get(
            lesson_id=lesson_id, id=session_id
        )
    except (Lesson.DoesNotExist, LaserCoachingSession.DoesNotExist):
        return Response(
            "Lesson or Laser Coaching Session not found",
            status=status.HTTP_404_NOT_FOUND,
        )

    lesson_data = request.data.get("lesson")
    session_data = request.data.get("laser_coaching_session")

    lesson_serializer = LessonSerializer(lesson, data=lesson_data, partial=True)
    session_serializer = LaserCoachingSessionSerializer(
        coaching_session, data=session_data, partial=True
    )

    if lesson_serializer.is_valid() and session_serializer.is_valid():
        lesson_serializer.save()
        session_serializer.save()
        return Response(
            {
                "lesson": lesson_serializer.data,
                "laser_coaching_session": session_serializer.data,
            }
        )

    return Response(
        {
            "lesson_errors": lesson_serializer.errors,
            "session_errors": session_serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )
