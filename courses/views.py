from django.shortcuts import render

# Create your views here.
from rest_framework import generics, serializers, status
from .models import (
    Course,
    TextLesson,
    Lesson,
    LiveSession,
    LaserCoachingSession,
    Question,
    QuizLesson,
    FeedbackLesson,
    Assessment,
    CourseEnrollment,
    Answer,
    Certificate,
    QuizLessonResponse,
    FeedbackLessonResponse,
)
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .serializers import (
    CourseSerializer,
    TextLessonCreateSerializer,
    TextLessonSerializer,
    LessonSerializer,
    LiveSessionSerializer,
    LiveSessionSerializerDepthOne,
    QuestionSerializer,
    QuizLessonDepthOneSerializer,
    LaserSessionSerializerDepthOne,
    LaserCoachingSessionSerializer,
    FeedbackLessonDepthOneSerializer,
    AssessmentSerializerDepthOne,
    AssessmentSerializer,
    CourseEnrollmentDepthOneSerializer,
    AnswerSerializer,
    CertificateSerializerDepthOne,
    VideoLessonSerializerDepthOne,
)
from rest_framework.views import APIView
from api.models import User, Learner, Profile
from schedularApi.models import SchedularParticipants, SchedularBatch
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
import random
import string
import pdfkit
import os
from django.http import HttpResponse
from django.template.loader import render_to_string
import base64
from openpyxl import Workbook


wkhtmltopdf_path = os.environ.get("WKHTMLTOPDF_PATH", r"/usr/local/bin/wkhtmltopdf")

pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")


def create_learner(learner_name, learner_email, learner_phone):
    try:
        with transaction.atomic():
            learner_email = learner_email.strip()
            temp_password = "".join(
                random.choices(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits,
                    k=8,
                )
            )
            user = User.objects.create_user(
                username=learner_email,
                password=temp_password,
                email=learner_email,
            )
            user.save()
            learner_profile = Profile.objects.create(user=user, type="learner")
            learner = Learner.objects.create(
                user=learner_profile,
                name=learner_name,
                email=learner_email,
                phone=learner_phone,
            )
            return learner

    except Exception as e:
        return None


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
        queryset = Lesson.objects.filter(course__id=course_id)
        status = self.request.query_params.get("status", None)
        if status:
            queryset = queryset.filter(status=status)

        return queryset


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
        elif lesson_type == "quiz":
            quiz_lesson = QuizLesson.objects.get(lesson=lesson)
            serializer = QuizLessonDepthOneSerializer(quiz_lesson)
        elif lesson_type == "laser_coaching":
            laser_coaching = LaserCoachingSession.objects.get(lesson=lesson)
            serializer = LaserSessionSerializerDepthOne(laser_coaching)
        elif lesson_type == "assessment":
            laser_coaching = Assessment.objects.get(lesson=lesson)
            serializer = AssessmentSerializerDepthOne(laser_coaching)
        elif lesson_type == "feedback":
            laser_coaching = FeedbackLesson.objects.get(lesson=lesson)
            serializer = FeedbackLessonDepthOneSerializer(laser_coaching)
        elif lesson_type == "video":
            video = VideoLesson.objects.get(lesson=lesson)
            serializer = VideoLessonSerializerDepthOne(video)
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
        lesson_serializer = LessonSerializer(lesson)
        response_data = {
            "message": "Lesson and Quiz created successfully",
            "lesson": lesson_serializer.data,
        }

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )
    else:
        return Response(lesson_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def edit_quiz_lesson(request, quiz_lesson_id):
    try:
        quiz_lesson = QuizLesson.objects.get(id=quiz_lesson_id)
    except QuizLesson.DoesNotExist:
        return Response(
            {"message": "Quiz Lesson not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Deserialize the incoming data
    data = request.data
    lesson_data = data.get("lesson")
    questions_data = data.get("questions")

    # Update Lesson details
    lesson = quiz_lesson.lesson
    lesson_serializer = LessonSerializer(lesson, data=lesson_data)
    if lesson_serializer.is_valid():
        lesson = lesson_serializer.save()
    else:
        return Response(lesson_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Remove existing questions from QuizLesson
    quiz_lesson.questions.clear()

    # Update or create new questions and add them to the QuizLesson
    for question_data in questions_data:
        question_id = question_data.get("_id")
        if question_id:
            try:
                existing_question = Question.objects.get(id=question_id)
                question_serializer = QuestionSerializer(
                    existing_question, data=question_data
                )
                if question_serializer.is_valid():
                    question = question_serializer.save()
                    quiz_lesson.questions.add(question)
                else:
                    return Response(
                        question_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            except Question.DoesNotExist:
                # If question does not exist, create a new one
                question_serializer = QuestionSerializer(data=question_data)
                if question_serializer.is_valid():
                    question = question_serializer.save()
                    quiz_lesson.questions.add(question)
                else:
                    return Response(
                        question_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            # If no question ID is provided, create a new question
            question_serializer = QuestionSerializer(data=question_data)
            if question_serializer.is_valid():
                question = question_serializer.save()
                quiz_lesson.questions.add(question)
            else:
                return Response(
                    question_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
    lesson_serializer = LessonSerializer(lesson)
    response_data = {
        "message": "Quiz Lesson updated successfully",
        "lesson": lesson_serializer.data,
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
def create_feedback_lesson(request):
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
        feedback_lesson = FeedbackLesson.objects.create(lesson=lesson)
        feedback_lesson.questions.set(questions)
        lesson_serializer = LessonSerializer(lesson)
        response_data = {
            "message": "Lesson and Feedback created successfully",
            "lesson": lesson_serializer.data,
        }

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )
    else:
        return Response(lesson_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def edit_feedback_lesson(request, feedback_lesson_id):
    try:
        feedback_lesson = FeedbackLesson.objects.get(id=feedback_lesson_id)
    except QuizLesson.DoesNotExist:
        return Response(
            {"message": "Feedback Lesson not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Deserialize the incoming data
    data = request.data
    lesson_data = data.get("lesson")
    questions_data = data.get("questions")

    # Update Lesson details
    lesson = feedback_lesson.lesson
    lesson_serializer = LessonSerializer(lesson, data=lesson_data)
    if lesson_serializer.is_valid():
        lesson = lesson_serializer.save()
    else:
        return Response(lesson_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Remove existing questions from QuizLesson
    feedback_lesson.questions.clear()

    # Update or create new questions and add them to the QuizLesson
    for question_data in questions_data:
        question_id = question_data.get("_id")
        if question_id:
            try:
                existing_question = Question.objects.get(id=question_id)
                question_serializer = QuestionSerializer(
                    existing_question, data=question_data
                )
                if question_serializer.is_valid():
                    question = question_serializer.save()
                    feedback_lesson.questions.add(question)
                else:
                    return Response(
                        question_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            except Question.DoesNotExist:
                # If question does not exist, create a new one
                question_serializer = QuestionSerializer(data=question_data)
                if question_serializer.is_valid():
                    question = question_serializer.save()
                    feedback_lesson.questions.add(question)
                else:
                    return Response(
                        question_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            # If no question ID is provided, create a new question
            question_serializer = QuestionSerializer(data=question_data)
            if question_serializer.is_valid():
                question = question_serializer.save()
                feedback_lesson.questions.add(question)
            else:
                return Response(
                    question_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
    lesson_serializer = LessonSerializer(lesson)
    response_data = {
        "message": "Feedback Lesson updated successfully",
        "lesson": lesson_serializer.data,
    }

    return Response(response_data, status=status.HTTP_200_OK)


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


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Course, Lesson
from .serializers import LessonSerializer


@api_view(["POST"])
def create_assessment_and_lesson(request):
    lesson_data = request.data.get("lesson")
    # coaching_session_data = request.data.get("assessment_lesson")

    # Create a Lesson instance
    lesson = Lesson.objects.create(
        course_id=lesson_data["course"],
        name=lesson_data["name"],
        status=lesson_data["status"],
        lesson_type=lesson_data["lesson_type"],
    )

    # Create a LaserCoachingSession instance associated with the created Lesson
    assessment = Assessment.objects.create(
        lesson=lesson,
        # message=coaching_session_data["message"],
    )

    # Optionally, return a success response
    return Response(
        "Assessment lesson created successfully", status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
def get_assessment_lesson(request, lesson_id, course_id):
    try:
        assessment = Assessment.objects.filter(
            lesson__id=lesson_id, lesson__course__id=course_id
        )
        serializer = AssessmentSerializerDepthOne(assessment, many=True)
        return Response(serializer.data)
    except Assessment.DoesNotExist:
        return Response(status=404)


@api_view(["PUT"])
def update_assessment_lesson(request, course_id, lesson_id, session_id):
    print(course_id, lesson_id, session_id)
    try:
        lesson = Lesson.objects.get(course_id=course_id, id=lesson_id)
        assessment = Assessment.objects.get(lesson_id=lesson_id, id=session_id)
    except (Lesson.DoesNotExist, Assessment.DoesNotExist):
        return Response(
            "Assessment lesson not found",
            status=status.HTTP_404_NOT_FOUND,
        )

    lesson_data = request.data.get("lesson")

    # Check if 'lesson' data is provided in the request and update the lesson name
    if lesson_data and "name" in lesson_data:
        lesson.name = lesson_data["name"]

    # Update other fields of the lesson if present in the request
    if lesson_data:
        lesson_serializer = LessonSerializer(lesson, data=lesson_data, partial=True)
        if lesson_serializer.is_valid():
            lesson_serializer.save()
        else:
            return Response(
                {"lesson_errors": lesson_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    session_data = (
        {}
    )  # Empty data for assessment session as not specified in the request

    session_serializer = AssessmentSerializer(
        assessment, data=session_data, partial=True
    )

    if session_serializer.is_valid():
        session_serializer.save()
        return Response(
            {
                "lesson": LessonSerializer(lesson).data,
                "assessment_lesson": session_serializer.data,
            }
        )

    return Response(
        {
            "session_errors": session_serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
def enroll_participants_to_course(request, course_id, schedular_batch_id):
    try:
        course = Course.objects.get(id=course_id)
        batch = SchedularBatch.objects.get(id=schedular_batch_id)
        batch_participants = batch.participants.all()
        learners = []
        not_enrolled_learner_emails = []
        for participant in batch_participants:
            # check if same email user exists or not
            user = User.objects.filter(username=participant.email).first()
            if user:
                if user.profile.type == "learner":
                    learner = Learner.objects.get(user=user.profile)
                    learners.append(learner)
                else:
                    not_enrolled_learner_emails.append(participant.email)
            else:
                learner = create_learner(
                    participant.name, participant.email, participant.phone
                )
                if learner:
                    learners.append(learner)
                else:
                    not_enrolled_learner_emails.append(participant.email)

        for learner in learners:
            course_enrollments = CourseEnrollment.objects.filter(
                learner=learner, course=course
            )
            if not course_enrollments.exists():
                datetime = timezone.now()
                CourseEnrollment.objects.create(
                    learner=learner, course=course, enrollment_date=datetime
                )
        course_serializer = CourseSerializer(course)
        return Response(
            {
                "message": "Participant enrolled successfully",
                "not_enrolled_learner_emails": not_enrolled_learner_emails,
                "course": course_serializer.data,
            }
        )
    except LaserCoachingSession.DoesNotExist:
        return Response(status=404)


@api_view(["GET"])
def get_course_enrollment(request, course_id, learner_id):
    try:
        course_enrollment = CourseEnrollment.objects.get(
            course__id=course_id, learner__id=learner_id
        )
        course_enrollment_serializer = CourseEnrollmentDepthOneSerializer(
            course_enrollment
        )
        lessons = Lesson.objects.filter(
            course=course_enrollment.course, status="public"
        )
        lessons_serializer = LessonSerializer(lessons, many=True)

        return Response(
            {
                "course_enrollment": course_enrollment_serializer.data,
                "lessons": lessons_serializer.data,
            }
        )
    except CourseEnrollment.DoesNotExist:
        return Response(status=404)


@api_view(["GET"])
def get_course_enrollment_for_pmo_preview(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        course_serializer = CourseSerializer(course)
        lessons = Lesson.objects.filter(course=course, status="public")
        lessons_serializer = LessonSerializer(lessons, many=True)
        completed_lessons = []
        return Response(
            {
                "course_enrollment": {
                    "completed_lessons": completed_lessons,
                    "course": course_serializer.data,
                },
                "lessons": lessons_serializer.data,
            }
        )
    except Course.DoesNotExist:
        return Response(status=404)


@api_view(["GET"])
def get_course_enrollments_of_learner(request, learner_id):
    try:
        course_enrollments = CourseEnrollment.objects.filter(
            learner__id=learner_id, course__status="public"
        )
        res = []
        for course_enrollment in course_enrollments:
            course_enrollment_serializer = CourseEnrollmentDepthOneSerializer(
                course_enrollment
            )
            lessons = Lesson.objects.filter(
                course=course_enrollment.course, status="public"
            )
            lessons_serializer = LessonSerializer(lessons, many=True)
            data = {
                "course_enrollment": course_enrollment_serializer.data,
                "lessons": lessons_serializer.data,
            }
            res.append(data)
        return Response(res)
    except CourseEnrollment.DoesNotExist:
        return Response(status=404)


@api_view(["POST"])
def submit_quiz_answers(request, quiz_lesson_id, learner_id):
    try:
        quiz_lesson = get_object_or_404(QuizLesson, id=quiz_lesson_id)
        course_enrollment = get_object_or_404(
            CourseEnrollment, course=quiz_lesson.lesson.course, learner__id=learner_id
        )
        learner = get_object_or_404(Learner, id=learner_id)
    except (
        QuizLesson.DoesNotExist,
        CourseEnrollment.DoesNotExist,
        Learner.DoesNotExist,
    ) as e:
        return Response(
            {"error": "Failed to submit quiz."}, status=status.HTTP_404_NOT_FOUND
        )

    answers_data = request.data
    serializer = AnswerSerializer(data=answers_data, many=True)

    if serializer.is_valid():
        answers = serializer.save()
        quiz_lesson_response = QuizLessonResponse.objects.create(
            quiz_lesson=quiz_lesson, learner=learner
        )
        quiz_lesson_response.answers.set(answers)
        quiz_lesson_response.save()
        course_enrollment.completed_lessons.append(quiz_lesson.lesson.id)
        course_enrollment.save()
        return Response(
            {"detail": "Quiz submitted successfully"}, status=status.HTTP_200_OK
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def calculate_quiz_result(quiz_lesson, quiz_lesson_response):
    correct_answers = 0
    total_questions = quiz_lesson.questions.count()
    for question in quiz_lesson.questions.all():
        is_correct = False
        try:
            answer = quiz_lesson_response.answers.get(question=question)
            selected_options = answer.selected_options
        except Answer.DoesNotExist:
            selected_options = []

        if question.type == "single_correct_answer":
            correct_option = next(
                (opt["option"] for opt in question.options if opt["is_correct"]), None
            )
            is_correct = correct_option in selected_options
        elif question.type == "multiple_correct_answer":
            correct_options = [
                opt["option"] for opt in question.options if opt["is_correct"]
            ]
            is_correct = set(selected_options) == set(correct_options)
        if is_correct:
            correct_answers += 1
    return {
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "percentage": round((correct_answers / total_questions) * 100),
    }


@api_view(["GET"])
def get_quiz_result(request, quiz_lesson_id, learner_id):
    quiz_lesson = QuizLesson.objects.get(id=quiz_lesson_id)
    quiz_lesson_response = QuizLessonResponse.objects.get(
        learner__id=learner_id, quiz_lesson=quiz_lesson
    )
    quiz_result = calculate_quiz_result(quiz_lesson, quiz_lesson_response)
    return Response(
        {
            "correct_answers": quiz_result["correct_answers"],
            "total_questions": quiz_result["total_questions"],
        }
    )


@api_view(["POST"])
def submit_feedback_answers(request, feedback_lesson_id, learner_id):
    try:
        feedback_lesson = get_object_or_404(FeedbackLesson, id=feedback_lesson_id)
        course_enrollment = get_object_or_404(
            CourseEnrollment,
            course=feedback_lesson.lesson.course,
            learner__id=learner_id,
        )
        learner = get_object_or_404(Learner, id=learner_id)
    except (
        FeedbackLesson.DoesNotExist,
        CourseEnrollment.DoesNotExist,
        Learner.DoesNotExist,
    ) as e:
        return Response(
            {"error": "Failed to submit feedback."}, status=status.HTTP_404_NOT_FOUND
        )

    answers_data = request.data
    serializer = AnswerSerializer(data=answers_data, many=True)

    if serializer.is_valid():
        answers = serializer.save()
        feedback_lesson_response = FeedbackLessonResponse.objects.create(
            feedback_lesson=feedback_lesson, learner=learner
        )
        feedback_lesson_response.answers.set(answers)
        feedback_lesson_response.save()
        course_enrollment.completed_lessons.append(feedback_lesson.lesson.id)
        course_enrollment.save()
        return Response(
            {"detail": "Feedback submitted successfully"}, status=status.HTTP_200_OK
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CertificateListAPIView(APIView):
    def get(self, request, format=None):
        certificates = Certificate.objects.all()
        serializer = CertificateSerializerDepthOne(certificates, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            name = request.data["name"]
            content = request.data["content"]

            if Certificate.objects.filter(name=name).exists():
                return Response(
                    {"error": f"Certificate with the name '{name}' already exists."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            new_certificate = Certificate.objects.create(name=name, content=content)
            new_certificate.save()
            return Response(
                {
                    "message": "Created Sucessfully.",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to create cretificate."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            name = request.data["name"]
            content = request.data["content"]
            certificate_id = request.data.get("certificate_id")
            if (
                Certificate.objects.filter(name=name)
                .exclude(id=certificate_id)
                .exists()
            ):
                return Response(
                    {"error": f"Certificate with the name '{name}' already exists."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            certificate = Certificate.objects.get(id=certificate_id)
            certificate.name = name
            certificate.content = content
            certificate.save()
            return Response(
                {
                    "message": "Certificate updated Sucessfully.",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to update cretificate."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetFilteredCoursesForCertificate(APIView):
    def get(self, request):
        certificates = Certificate.objects.all()
        all_courses = Course.objects.all()

        courses_in_certificates = set()
        for certificate in certificates:
            courses_in_certificates.update(
                certificate.courses.values_list("id", flat=True)
            )

        available_courses = all_courses.exclude(id__in=courses_in_certificates)

        serializer = CourseSerializer(available_courses, many=True)
        return Response(serializer.data)


class AssignCoursesToCertificate(APIView):
    def post(self, request):
        try:
            courses = request.data.get("courses", [])
            certificate_id = request.data.get("certificate_id")

            certificate = Certificate.objects.get(id=certificate_id)

            courses_to_assign = Course.objects.filter(id__in=courses)

            certificate.courses.add(*courses_to_assign)

            serializers = CertificateSerializerDepthOne(certificate)
            return Response(
                {
                    "message": "Courses assigned successfully.",
                    "certificate_data": serializers.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to assign courses."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeleteCourseFromCertificate(APIView):
    def delete(self, request):
        try:
            course_id = request.data.get("course_id")
            certificate_id = request.data.get("certificate_id")

            certificate = Certificate.objects.get(id=certificate_id)

            course = Course.objects.get(id=course_id)

            certificate.courses.remove(course)

            serializer = CertificateSerializerDepthOne(certificate)

            return Response(
                {
                    "message": "Course removed successfully.",
                    "certificate_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to remove the course."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LessonMarkAsCompleteAndNotComplete(APIView):
    def post(self, request):
        try:
            lesson_id = request.data.get("lesson_id")
            learner_id = request.data.get("learner_id")

            lesson = Lesson.objects.get(id=lesson_id)
            course_enrollment = CourseEnrollment.objects.get(
                course=lesson.course, learner__id=learner_id
            )
            completed_lessons = course_enrollment.completed_lessons

            if lesson_id in completed_lessons:
                completed_lessons.remove(lesson_id)
                message = "Lesson marked as Incomplete."
            else:
                completed_lessons.append(lesson_id)
                message = "Lesson marked as Completed."

            course_enrollment.save()

            return Response({"message": message}, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to update lesson status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DownlaodLessonCertificate(APIView):
    def get(self, request, lesson_id, learner_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            content = {}
            course_enrollment = CourseEnrollment.objects.get(
                course=lesson.course, learner__id=learner_id
            )

            content["learner_name"] = course_enrollment.learner.name
            content["course_name"] = lesson.course.name
            try:
                certificate = Certificate.objects.filter(courses=lesson.course).first()
            except Certificate.DoesNotExist:
                return Response(
                    {"error": "Certificate not found for the given course"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            email_message = certificate.content
            for key, value in content.items():
                email_message = email_message.replace(f"{{{{{key}}}}}", str(value))

            pdf = pdfkit.from_string(
                email_message,
                False,
                configuration=pdfkit_config,
                options={"orientation": "Landscape"},
            )
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="Certificate.pdf"'
            return response

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to downlaod certificate."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetCertificateForCourse(APIView):
    def get(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)

            certificate = Certificate.objects.filter(courses=course).first()

            if certificate:
                return Response({"certificate_present": True})
            else:
                return Response({"certificate_present": False})
        except Exception as e:
            return Response(
                {"error": "Failed to retrieve certificates for the given course."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Video
from .serializers import VideoSerializer  # Import your Video model serializer


@api_view(["POST"])
def create_videos(request):
    name = request.data.get("name")  # Extract 'name' from request data
    video_file = request.data.get("video")  # Extract 'video' file from request data

    # You can perform validation or error checking here as needed

    # Assuming you have a VideoSerializer defined, you can create a new Video instance
    video_instance = Video(name=name, video=video_file)

    # Save the video instance to the database
    video_instance.save()

    # Serialize the newly created video instance
    serialized_video = VideoSerializer(video_instance)

    return Response(serialized_video.data)


# views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Video
from .serializers import VideoSerializer


@api_view(["GET"])
def get_all_videos(request):
    videos = Video.objects.all()  # Retrieve all videos from the database

    # Serialize the video queryset
    serializer = VideoSerializer(videos, many=True)

    return Response(serializer.data)


# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Lesson, Video, VideoLesson
from .serializers import LessonSerializer, VideoLessonSerializer


@api_view(["POST"])
def create_video_lesson(request):
    if request.method == "POST":
        lesson_data = request.data.get("lesson")
        video_id = request.data.get("video")

        # Create or update lesson
        lesson_serializer = LessonSerializer(data=lesson_data)
        if not lesson_serializer.is_valid():
            return Response(
                lesson_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        # Save the lesson instance
        lesson_instance = lesson_serializer.save()

        try:
            # Retrieve video instance
            video_instance = Video.objects.get(id=video_id)

            # Create VideoLesson object
            video_lesson_data = {
                "lesson": lesson_instance.id,
                "video": video_instance.id,
            }
            video_lesson_serializer = VideoLessonSerializer(data=video_lesson_data)
            if video_lesson_serializer.is_valid():
                video_lesson_serializer.save()
                return Response(
                    video_lesson_serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                video_lesson_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        except Video.DoesNotExist:
            return Response(
                {"error": "Video does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


# views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Video
from .serializers import VideoSerializer


@api_view(["GET"])
def get_all_videos(request):
    if request.method == "GET":
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import VideoLesson, Lesson, Video
from .serializers import VideoLessonSerializer, LessonSerializer


@api_view(["PUT"])
def update_video_lesson(request, lesson_id):
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        return Response(
            {"message": "Lesson does not exist"}, status=status.HTTP_404_NOT_FOUND
        )

    video_id = request.data.get("video")

    try:
        video = Video.objects.get(pk=video_id)
    except Video.DoesNotExist:
        return Response(
            {"message": "Video does not exist"}, status=status.HTTP_404_NOT_FOUND
        )

    lesson_data = request.data.get("lesson")
    if lesson_data:
        lesson_serializer = LessonSerializer(lesson, data=lesson_data, partial=True)
        if lesson_serializer.is_valid():
            lesson_serializer.save()

    video_lesson_data = {"lesson": lesson_id, "video": video_id}

    try:
        video_lesson = VideoLesson.objects.get(lesson_id=lesson_id)
        serializer = VideoLessonSerializer(video_lesson, data=video_lesson_data)
    except VideoLesson.DoesNotExist:
        serializer = VideoLessonSerializer(data=video_lesson_data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Video
from .serializers import VideoSerializer


@api_view(["PUT"])
def update_video(request, pk):
    try:
        video = Video.objects.get(pk=pk)
    except Video.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = VideoSerializer(video, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_all_courses_progress(request):
    res = []
    courses = Course.objects.filter(status="public")
    for course in courses:
        course_serializer = CourseSerializer(course)
        lessons = Lesson.objects.filter(status="public", course=course)
        course_enrollments = CourseEnrollment.objects.filter(course=course)
        total_lessons_completed_by_learner = 0
        for course_enrollment in course_enrollments:
            total_lessons_completed_by_learner += len(
                course_enrollment.completed_lessons
            )
        completion_percentage = (
            (
                total_lessons_completed_by_learner
                / (lessons.count() * course_enrollments.count())
            )
            * 100
            if course_enrollments.count() > 0
            else 0
        )

        res.append(
            {
                **course_serializer.data,
                "total_learners": course_enrollments.count(),
                "completion_percentage": completion_percentage,
            }
        )
    return Response(res)


@api_view(["GET"])
def get_course_progress(request, course_id):
    course_enrollments = CourseEnrollment.objects.filter(course__id=course_id)
    course_enrollments_serializer = CourseEnrollmentDepthOneSerializer(
        course_enrollments, many=True
    )
    lessons_count = Lesson.objects.filter(course__id=course_id, status="public").count()
    res = []
    for course_enrollment in course_enrollments_serializer.data:
        res.append({**course_enrollment, "total_lessons": lessons_count})
    return Response(res)


@api_view(["GET"])
def course_report_download(request, course_id):
    course_enrollments = CourseEnrollment.objects.filter(course__id=course_id)
    course_enrollments_serializer = CourseEnrollmentDepthOneSerializer(
        course_enrollments, many=True
    )
    lessons_count = Lesson.objects.filter(course__id=course_id, status="public").count()
    res = []
    for course_enrollment in course_enrollments_serializer.data:
        res.append(
            {
                **course_enrollment,
                "total_lessons": lessons_count,
                "progress": round(
                    (len(course_enrollment["completed_lessons"]) / lessons_count) * 100
                ),
            }
        )

    # Create a new workbook and add a worksheet
    wb = Workbook()
    ws = wb.active

    # Write headers to the worksheet
    headers = [
        "Participant Name",
        "Completed Lessons",
        "Total Lessons",
        "Progress",
    ]

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    # Write data to the worksheet
    for row_num, course_enrollment_data in enumerate(res, 2):
        ws.append(
            [
                course_enrollment_data["learner"]["name"],
                len(course_enrollment_data["completed_lessons"]),
                course_enrollment_data["total_lessons"],
                str(course_enrollment_data["progress"]) + "%",
            ]
        )

    # Create a response with the Excel file
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=course_report.xlsx"
    wb.save(response)

    return response


@api_view(["GET"])
def get_all_quizes_report(request):
    res = []
    quizes = QuizLesson.objects.filter(
        lesson__status="public", lesson__course__status="public"
    )
    for quiz in quizes:
        course_enrollments = CourseEnrollment.objects.filter(course=quiz.lesson.course)
        total_participants = course_enrollments.count()
        quiz_lesson_responses = QuizLessonResponse.objects.filter(quiz_lesson=quiz)
        total_responses = quiz_lesson_responses.count()
        total_percentage = 0
        for quiz_lesson_response in quiz_lesson_responses:
            quiz_result = calculate_quiz_result(quiz, quiz_lesson_response)
            print(total_percentage)
            print(quiz_result["percentage"])
            total_percentage += quiz_result["percentage"]
        average_percentage = total_percentage / total_responses
        res.append(
            {
                "id": quiz.id,
                "quiz_name": quiz.lesson.name,
                "course_name": quiz.lesson.course.name,
                "total_participants": total_participants,
                "total_responses": total_responses,
                "average_percentage": average_percentage,
            }
        )

    return Response(res)


def get_quiz_report_data(quiz_lesson):
    quiz_lesson_responses = QuizLessonResponse.objects.filter(quiz_lesson=quiz_lesson)
    res = []
    for quiz_lesson_response in quiz_lesson_responses:
        quiz_result = calculate_quiz_result(quiz_lesson, quiz_lesson_response)
        res.append({"learner": quiz_lesson_response.learner.name, **quiz_result})
    return res


@api_view(["GET"])
def get_quiz_report(request, quiz_id):
    quiz_lesson = QuizLesson.objects.get(id=quiz_id)
    data = get_quiz_report_data(quiz_lesson)
    return Response(data)


@api_view(["GET"])
def quiz_report_download(request, quiz_id):
    quiz_lesson = QuizLesson.objects.get(id=quiz_id)
    quiz_data = get_quiz_report_data(quiz_lesson)
    # Create a new workbook and add a worksheet
    wb = Workbook()
    ws = wb.active

    # Write headers to the worksheet
    headers = [
        "Participant Name",
        "Correct Answers",
        "Total Questions",
        "Percentage",
    ]

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    # Write data to the worksheet
    for row_num, quiz_data_item in enumerate(quiz_data, 2):
        ws.append(
            [
                quiz_data_item["learner"],
                quiz_data_item["correct_answers"],
                quiz_data_item["total_questions"],
                str(quiz_data_item["percentage"]) + "%",
            ]
        )

    # Create a response with the Excel file
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=quiz_report.xlsx"
    wb.save(response)

    return response
