from datetime import date
import requests
from os import name
from django.shortcuts import render, get_object_or_404
from django.db import transaction, IntegrityError
from django.core.mail import EmailMessage
from rest_framework.exceptions import ParseError, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from operationsBackend import settings
from .serializers import (
    CoachSerializer,
    UserSerializer,
    LearnerSerializer,
    PmoDepthOneSerializer,
    SessionRequestCaasSerializer,
    CoachDepthOneSerializer,
    ProjectDepthTwoSerializer,
    HrSerializer,
    OrganisationSerializer,
    LearnerDepthOneSerializer,
    HrDepthOneSerializer,
    SessionRequestCaasDepthOneSerializer,
    SessionRequestCaasDepthTwoSerializer,
    AvailibilitySerializer,
    NotificationSerializer,
    EngagementDepthOneSerializer,
    GoalSerializer,
    GetGoalSerializer,
    CompetencySerializer,
    CompetencyDepthOneSerializer,
    ActionItemSerializer,
    GetActionItemDepthOneSerializer,
)

from django.utils.crypto import get_random_string
import jwt
import jwt
import uuid
import pytz
from django.db.models import IntegerField
from django.db.models.functions import Cast
from rest_framework.exceptions import AuthenticationFailed
from datetime import datetime, timedelta
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import (
    Profile,
    Pmo,
    Coach,
    OTP,
    Project,
    HR,
    Organisation,
    SessionRequestCaas,
    Availibility,
    Learner,
    CoachStatus,
    Notification,
    Engagement,
    Goal,
    Competency,
    ActionItem,
)
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import string
import random
from django.db.models import Q
from collections import defaultdict
from django.db.models import Avg


# Create your views here.

import environ

env = environ.Env()


def create_notification(user, path, message):
    notification = Notification.objects.create(user=user, path=path, message=message)
    return notification


def format_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)  # Convert milliseconds to seconds
    return dt.strftime("%d-%m-%Y %I:%M %p")
def generateManagementToken():
    expires = 24 * 3600
    now = datetime.utcnow()
    exp = now + timedelta(seconds=expires)
    return jwt.encode(
        payload={
            "access_key": env("100MS_APP_ACCESS_KEY"),
            "type": "management",
            "version": 2,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": exp,
            "nbf": now,
        },
        key=env("100MS_APP_SECRET"),
    )

def generate_room_id(email):
    
    management_token = generateManagementToken()
    try:
        payload = {
            "name": email.replace(".", "-").replace("@", ""),
            "description": "This is a sample description for the room",
            "region": "in",
        }

        response_from_100ms = requests.post(
            "https://api.100ms.live/v2/rooms",
            headers={
                "Authorization": f"Bearer {management_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if response_from_100ms.status_code == 200:
            room_id = response_from_100ms.json().get("id")
            return room_id
        else:
            return None
    except Exception as e:
        print(f"Error while generating meeting link: {str(e)}")
        return None

@api_view(["POST"])
@permission_classes([AllowAny])
def create_pmo(request):
    # Get data from request
    name = request.data.get("name")
    email = request.data.get("email")
    phone = request.data.get("phone")
    username = email  # username and email are the same
    password = request.data.get("password")

    room_id = generate_room_id(email)

    # Check if required data is provided
    if not all([name, email, phone, username, password,room_id]):
        return Response({"error": "All required fields must be provided."}, status=400)

    try:
        with transaction.atomic():
         
            user = User.objects.create_user(username=username, password=password, email=email)
      
            pmo_profile = Profile.objects.create(user=user, type="pmo")
          
            pmo_user = Pmo.objects.create(user=pmo_profile, name=name, email=email, phone=phone,room_id=room_id)

            
                # Return success response without room_id
            return Response({"message": "PMO added successfully."}, status=201)

    except IntegrityError as ie:
        return Response({"error": "User with this email already exists."}, status=400)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)
    

# room_id = ""
# management_token = generateManagementToken()
# try:
#     response_from_100ms = requests.post(
#     "https://api.100ms.live/v2/rooms",
#                         headers={
#                             "Authorization": f"Bearer {management_token}",
#                             "Content-Type": "application/json",
#                         },
#                         json={
#                             "name": email.replace(".", "-").replace("@", ""),
#                             "description": "This is a sample description for the room",
#                             "region": "in",
#                         },
#                     )
#     if response_from_100ms.status_code == 200:
#         room_id = response_from_100ms.json().get("id")
# except Exception as e:
#     print(f"Error while generating meeting link, {str(e)}")

# # Create pmo user
# @api_view(["POST"])
# def create_pmo(request):
#     # Get data from request
#     name = request.data.get("name")
#     email = request.data.get("email")
#     phone = request.data.get("phone")
#     username = request.data.get("email")  # username and email are same
#     password = request.data.get("password")
#     # Check if required data is provided
#     if not all([name, email, phone, username, password]):
#         return Response({"error": "All required fields must be provided."}, status=400)

#     try:
#         with transaction.atomic():
#             # Create the Django User
#             user = User.objects.create_user(
#                 username=username, password=password, email=email
#             )
#             # Create the PMO Profile linked to the User
#             pmo_profile = Profile.objects.create(user=user, type="pmo")
#             # Create the PMO User using the Profile
#             pmo_user = Pmo.objects.create(
#                 user=pmo_profile, name=name, email=email, phone=phone
#             )
#         # Return success response
#         return Response({"message": "PMO added successfully."}, status=201)

#     except Exception as e:
#         # Return error response if any exception occurs
#         return Response({"error": str(e)}, status=500)


@api_view(["POST"])
def coach_signup(request):
    # Get data from request
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    email = request.data.get("email")
    age = request.data.get("age")
    gender = request.data.get("gender")
    domain = request.data.get("domain")
    room_id = request.data.get("room_id")
    phone = request.data.get("phone")
    level = request.data.get("level")
    education = request.data.get("education")
    rating = request.data.get("rating")
    area_of_expertise = request.data.get("area_of_expertise")
    years_of_coaching_experience = request.data.get("years_of_coaching_experience")
    years_of_corporate_experience = request.data.get("years_of_corporate_experience")
    username = request.data.get("email")  # keeping username and email same
    password = request.data.get("password")

    # print(first_name, last_name, email, age, gender, domain, room_id, phone, level, area_of_expertise, username, password)

    # Check if required data is provided
    if not all(
        [
            first_name,
            last_name,
            email,
            age,
            gender,
            domain,
            room_id,
            phone,
            years_of_coaching_experience,
            years_of_corporate_experience,
            level,
            education,
            username,
            password,
        ]
    ):
        return Response({"error": "All required fields must be provided."}, status=400)

    try:
        # Create the Django User
        with transaction.atomic():
            user = User.objects.create_user(
                username=username, password=password, email=email
            )

            # Create the Coach Profile linked to the User
            coach_profile = Profile.objects.create(user=user, type="coach")

            # Create the Coach User using the Profile
            coach_user = Coach.objects.create(
                user=coach_profile,
                first_name=first_name,
                domain=domain,
                age=age,
                gender=gender,
                last_name=last_name,
                email=email,
                room_id=room_id,
                phone=phone,
                level=level,
                education=education,
                rating=rating,
                area_of_expertise=area_of_expertise,
                years_of_corporate_experience=years_of_corporate_experience,
                years_of_coaching_experience=years_of_coaching_experience,
            )

            # approve coach
            coach = Coach.objects.get(id=coach_user.id)
            # Change the is_approved field to True
            coach.is_approved = True
            coach.save()

            # Send email notification to the coach
            subject = "Welcome to our coaching platform"
            message = f"Dear {name},\n\nThank you for signing up to our coaching platform. Your profile has been registered and approved by PMO. Best of luck!"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            # Send email notification to the admin
            admin_email = "jatin@meeraq.com"
            admin_message = f"A new coach {name} has signed up on our coaching platform. Please login to the admin portal to review and approve their profile."
            send_mail(
                subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email]
            )

            # Return success response
        return Response({"message": "Signed up successfully."}, status=201)

    except IntegrityError:
        return Response({"error": "A user with this email already exists."}, status=400)
    except Exception as e:
        # Return error response if any other exception occurs
        return Response(
            {"error": "An error occurred while creating the coach user."}, status=500
        )


@api_view(["PUT"])
def approve_coach(request, coach_id):
    try:
        # Get the Coach object
        _mysql.connection.query(self, query)
        coach = Coach.objects.get(id=coach_id)

        # Change the is_approved field to True
        coach.is_approved = True
        coach.save()

        # Return success response
        return Response({"message": "Coach approved successfully."}, status=200)

    except Coach.DoesNotExist:
        # Return error response if Coach with the provided ID does not exist
        return Response({"error": "Coach does not exist."}, status=404)

    except Exception as e:
        # Return error response if any other exception occurs
        return Response({"error": str(e)}, status=500)


@api_view(["PUT"])
def update_coach_profile(request, coach_id):
    try:
        coach = Coach.objects.get(id=coach_id)
    except Coach.DoesNotExist:
        return Response(status=404)

    serializer = CoachSerializer(
        coach, data=request.data, partial=True
    )  # partial argument added here
    if serializer.is_valid():
        serializer.save()
        depth_serializer = CoachDepthOneSerializer(coach)
        return Response(depth_serializer.data, status=200)

    return Response(serializer.errors, status=400)


@api_view(["GET"])
def get_coaches(request):
    try:
        # Get all the Coach objects
        coaches = Coach.objects.all()

        # Serialize the Coach objects
        serializer = CoachSerializer(coaches, many=True)

        # Return the serialized Coach objects as the response
        return Response(serializer.data, status=200)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


def updateLastLogin(email):
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = User.objects.get(username=email)
    user.last_login = today
    user.save()


@api_view(["POST"])
def pmo_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if email is None or password is None:
        return Response({"error": "Please provide both email and password"}, status=400)

    user = authenticate(username=email, password=password, type="pmo")
    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    pmo = Pmo.objects.get(user=user.profile)

    updateLastLogin(pmo.email)
    return Response(
        {
            "token": token.key,
            "pmo": {
                "name": pmo.name,
                "email": pmo.email,
                "phone": pmo.phone,
                "last_login": pmo.user.user.last_login,
            },
        }
    )


@api_view(["POST"])
def coach_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if email is None or password is None:
        return Response({"error": "Please provide both email and password"}, status=400)

    user = authenticate(username=email, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    try:
        coach = Coach.objects.get(user=user.profile)
    except Coach.DoesNotExist:
        return Response({"error": "Coach not found"}, status=404)

    # Return the coach information in the response
    coach_serializer = CoachSerializer(coach)
    updateLastLogin(coach.email)
    return Response({"coach": coach_serializer.data}, status=200)



@api_view(["GET"])
def get_management_token(request):
    management_token = generateManagementToken()
    return Response(
        {"message": "Success", "management_token": management_token}, status=200
    )


# @api_view(['POST'])
# def create_user_without_password(request):
#     try:
#         with transaction.atomic():
#             # Check if username field is provided
#             if 'username' not in request.data:
#                 raise ValueError('Username field is required')
#             # Create user object with unusable password
#             user = User.objects.create_user(
#                 username=request.data['username'],
#                 email=request.data['username'])
#             user.set_unusable_password()
#             user.save()

#             # Create the learner profile
#             learner_profile = Profile.objects.create(user=user, type='learner')

#             # Create the learner object
#             learner = Learner.objects.create(user=learner_profile, name=request.data.get('name'), email=request.data['username'], phone=request.data.get('phone'))

#             # Return success response
#             return Response({}, status=200)

#     except ValueError as e:
#         # Handle missing or invalid request data
#         return Response({'error': str(e)}, status=400)

#     except IntegrityError:
#         # Handle username or email already exists
#         return Response({'error': 'Username or email already exists'}, status=409)

#     except Exception as e:
#         # Handle any other exceptions
#         transaction.set_rollback(True) # Rollback the transaction
#         return Response({'error': str(e)}, status=500)


# @api_view(['POST'])
# def otp_generation(request):
#     try:
#         learner = Learner.objects.get(email=request.data['email'])
#         try:
#             # Check if OTP already exists for the learner
#             otp_obj = OTP.objects.get(learner=learner)
#             otp_obj.delete()
#         except OTP.DoesNotExist:
#             pass

#         # Generate OTP and save it to the database
#         otp = get_random_string(length=6, allowed_chars='0123456789')
#         created_otp = OTP.objects.create(learner=learner, otp=otp)

#         # Send OTP on email to learner
#         subject = f'Meeraq Login Otp'
#         message = f'Dear {learner.name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [learner.email])

#         return Response({'success': True,'otp':created_otp.otp})


#     except Learner.DoesNotExist:
#         # Handle the case where the learner with the given email does not exist
#         return Response({'error': 'Learner with the given email does not exist.'}, status=400)

#     except Exception as e:
#         # Handle any other exceptions
#         return Response({'error': str(e)}, status=500)

# @api_view(['POST'])
# def otp_validation(request):
#     otp_obj = OTP.objects.filter(learner__email=request.data['email'], otp=request.data['otp']).order_by('-created_at').first()

#     if otp_obj is None:
#         raise AuthenticationFailed('Invalid OTP')

#     learner = otp_obj.learner
#     token, created = Token.objects.get_or_create(user=learner.user.user)

#     # Delete the OTP object after it has been validated
#     otp_obj.delete()

#     learner_data = {'id':learner.id,'name':learner.name,'email': learner.email,'phone': learner.email,'last_login': learner.user.user.last_login ,'token': token.key}
#     updateLastLogin(learner.email)
#     return Response({ 'learner': learner_data},status=200)


@api_view(["POST"])
def create_project_cass(request):
    organisation = Organisation.objects.filter(
        id=request.data["organisation_name"]
    ).first()
    if not organisation:
        organisation = Organisation(
            name=request.data["organisation_name"], image_url=request.data["image_url"]
        )
    organisation.save()
    # print(organisation.name, organisation.image_url, "details of org")
    project = Project(
        name=request.data["project_name"],
        organisation=organisation,
        currency=request.data["currency"],
        price_per_hour=request.data["price_per_hour"],
        coach_fees_per_hour=request.data["coach_fees_per_hour"],
        project_type="CAAS",
        interview_allowed=request.data["interview_allowed"],
        # chemistry_allowed= request.data['chemistry_allowed'],
        specific_coach=request.data["specific_coach"],
        empanelment=request.data["empanelment"],
        end_date=datetime.now() + timedelta(days=365),
        tentative_start_date=request.data["tentative_start_date"],
        mode=request.data["mode"],
        sold=request.data["sold"],
        # updated_to_sold= request.data['updated_to_sold'],
        location=request.data.get("location", None),
        steps=dict(
            project_structure={"status": "pending"},
            coach_list={"status": "pending"},
            coach_consent={"status": "pending"},
            coach_list_to_hr={"status": "pending"},
            interviews={"status": "pending"},
            add_learners={"status": "pending"},
            coach_approval={"status": "pending"},
            chemistry_session={"status": "pending"},
            coach_selected={"status": "pending"},
            final_coaches={"status": "pending"},
            project_live="pending",
        ),
    )
    hr_emails = []
    project.save()
    project_name = project.name
    print(request.data["hr"], "HR ID")
    for hr in request.data["hr"]:
        single_hr = HR.objects.get(id=hr)
        # print(single_hr)
        project.hr.add(single_hr)
        # Send email notification to the HR
        # subject = f'Hey HR! You have been assigned to a project {project_name}'
        # message = f'Dear {single_hr.first_name},\n\n You can use your email to log-in via OTP.'
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [single_hr.email])

    # hrs= create_hr(request.data['hr'])
    # for hr in hrs:
    #     project.hr.add(hr)

    try:
        path = f"/projects/caas/progress/{project.id}"
        message = f"A new project - {project.name} has been created for the organisation - {project.organisation.name}"
        create_notification(project.hr.first().user.user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Project created succesfully"}, status=200)


# @api_view(['POST'])
# def create_project(request):
#     organisation = Organisation.objects.filter(name=request.data['organisation_name']).first()
#     if not organisation:
#         organisation= Organisation(
#             name=request.data['organisation_name'], image_url=request.data['image_url']
#         )
#     organisation.save()


#     project= Project(
#         project_type = request.data['project_type'],
#         name=request.data['project_name'],
#         organisation=organisation,
#         total_sessions=request.data['total_session'],
# 		end_date=request.data['end_date'],
#         cost_per_session=request.data['cost_per_session'],
#         currency=request.data['currency'],
#         sessions_per_employee=request.data['sessions_per_employee'],
#         session_duration= request.data['session_duration'],
#         status=dict(project_live='pending')
#     )
#     hr_emails=[]
#     coach_emails=[]
#     project.save()
#     project_name= project.name
#     for coach in request.data["coach_id"]:
#         single_coach = Coach.objects.get(id=coach)
#         coach_emails.append(single_coach.email)
#         project.coaches.add(single_coach)

#     # Send email notification to the coach
#     subject = f'Hey Coach! You have assigned to a project {project_name}'
#     message = f'Dear {coach_emails},\n\nPlease be there to book slots requested by learner in this {project_name}. Best of luck!'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, coach_emails)


#     project_name= project.name
#     print(project_name)
#     for hr in request.data["hr_id"]:
#         single_hr = HR.objects.get(id=hr)
#         print(single_hr)
#         hr_emails.append(single_hr.email)
#         project.hr.add(single_hr)


#     hrs= create_hr(request.data['hr'])
#     for hr in hrs:
#         project.hr.add(hr)

#     try:
#         learners = create_learners(request.data['learners'])
#         for learner in learners:
#             project.learner.add(learner)
#     except Exception as e:
#         # Handle any exceptions from create_learners
#         return Response({'error': str(e)}, status=500)

#     return Response({'message': "Project created!"}, status=200)


def create_learners(learners_data):
    try:
        with transaction.atomic():
            if not learners_data:
                raise ValueError("Learners data is required")
            learners = []
            for learner_data in learners_data:
                # Check if username field is provided
                if "email" not in learner_data:
                    raise ValueError("Username field is required")

                # Check if user already exists
                user = User.objects.filter(username=learner_data["email"]).first()
                if user:
                    # If user exists, check if learner already exists
                    learner_profile = Profile.objects.filter(
                        user=user, type="learner"
                    ).first()
                    if learner_profile:
                        learners.append(learner_profile.learner)
                        continue

                else:
                    # If learner does not exist, create the user object with an unusable password

                    temp_password = "".join(
                        random.choices(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits,
                            k=8,
                        )
                    )
                    user = User.objects.create_user(
                        username=learner_data["email"],
                        password=temp_password,
                        email=learner_data.get("email", learner_data["email"]),
                    )
                    # user.set_unusable_password()
                    user.save()

                    # Create the learner profile
                    learner_profile = Profile.objects.create(user=user, type="learner")

                    # Create the learner object
                    # subject = 'Welcome to Meeraq'
                    # message = f'Dear {learner_data.get("name")},\n\nYour Account has been created with Meeraq your username is {learner_data["email"]} and temporary password is {temp_password} please log into our system and change your password to avoid any inconvenience'
                    # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [learner_data['email']])
                    learner = Learner.objects.create(
                        user=learner_profile,
                        name=learner_data.get("name"),
                        email=learner_data["email"],
                        phone=learner_data.get("phone"),
                    )
                    learners.append(learner)

            # Return response with learners created or already existing
            serializer = LearnerSerializer(learners, many=True)
            return learners

    except ValueError as e:
        # Handle missing or invalid request data
        raise ValueError(str(e))

    except Exception as e:
        # Handle any other exceptions
        # transaction.set_rollback(True) # Rollback the transaction
        raise Exception(str(e))


# Create learner user
# @api_view(['POST'])
# def create_learner(request):
#     # Get data from request
#     name = request.data.get('name')
#     email = request.data.get('email')
#     phone = request.data.get('phone')
#     area_of_expertise= request.data.get('area_of_expertise')
#     years_of_experience=request.data.get('years_of_experience')
#     username = request.data.get('email') # username and email are same
#     password = request.data.get('password')
#     # Check if required data is provided
#     if not all([name, email, phone, area_of_expertise, years_of_experience, username, password]):
#         return Response({'error': 'All required fields must be provided.'}, status=400)

#     try:
#         with transaction.atomic():
#             # Create the Django User
#             user = User.objects.create_user(username=username, password=password,email=email)
#             # Create the learner Profile linked to the User
#             learner_profile = Profile.objects.create(user=user, type='learner')
#             # Create the learner User using the Profile
#             learner = Learner.objects.create(user=learner_profile, name=name, email=email, phone=phone)
#         # Return success response
#         return Response({'message': 'Learner added successfully.'}, status=201)

#     except Exception as e:
#         # Return error response if any exception occurs
#         return Response({'error': str(e)}, status=500)


# @api_view(["POST"])
# def get_coaches_by_project(request):
#     project_id = request.data['project_id']
#     project= Project.objects.get(id=project_id)
#     coaches= project.coaches.name
#     return Response({"message": "Success"}, status=200)

# @api_view(["POST"])
# def get_learners_by_project(request):
#     project_id = request.data['project_id']
#     project= Project.objects.get(id=project_id)
#     learner= project.learner.name
#     return Response({"message": "Success"}, status=200)


# get projects details


# @api_view(["GET"])
# def project_details(request, project_id):
#     try:
#         project = Project.objects.get(id=project_id)
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     serializer =  ProjectDepthTwoSerializer(project)
#     return Response(serializer.data, status=200)


# @api_view(['GET'])
# def get_projects(request):
#     projects = Project.objects.all()
#     serializer = ProjectSerializer(projects, many=True)
#     return Response(serializer.data)


@api_view(["GET"])
def get_ongoing_projects(request):
    projects = Project.objects.filter(steps__project_live="pending")
    serializer = ProjectDepthTwoSerializer(projects, many=True)
    return Response(serializer.data)


# @api_view(['GET'])
# def get_completed_projects(request):
#     projects = Project.objects.filter(steps__project_live="complete")
#     serializer = ProjectSerializer(projects, many=True)
#     return Response(serializer.data)


@api_view(["GET"])
def get_projects_of_learner(request, learner_id):
    projects = Project.objects.filter(engagement__learner__id=learner_id)
    serializer = ProjectDepthTwoSerializer(projects, many=True)
    return Response(serializer.data)


# @api_view(['POST'])
# def create_session_request(request):
#     time_arr = []
#     for time in request.data['availibility']:
#         availibility_serilizer = AvailibilitySerializer(data = time)
#         if availibility_serilizer.is_valid():
#             avil_id = availibility_serilizer.save()
#             time_arr.append(avil_id.id)
#         else:
#             return Response({"message": str(availibility_serilizer.errors),}, status=401)
#     session = {
#            "learner": request.data['learner'],
#            "project": request.data['project'],
#            "availibility":time_arr
# 		      }
#     session_serilizer = SessionRequestSerializer(data = session)
#     if session_serilizer.is_valid():
#         session_serilizer.save()
#         return Response({"message": "Success"}, status=201)
#     else:
#         return Response({"message": str(session_serilizer.errors),}, status=401)


# Coach- view session request
# @api_view(["GET"])
# def session_requests_by_coach(request, coach_id):
#     coach = get_object_or_404(Coach, id=coach_id)
#     session_requests = SessionRequest.objects.filter(project__coaches=coach, is_booked=False)
#     serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)

# @api_view(['POST'])
# def book_session(request):
#     serializer = SessionSerializer(data=request.data)
#     if serializer.is_valid():
#         session = serializer.save()
#         # Mark the session request as booked
#         session_request = session.session_request
#         session_request.is_booked = True
#         session_request.save()

#         coach=session.coach
#         coach_email=coach.email
#         learner=session.session_request.learner
#         learner_email= learner.email

#     # Send email notification to the coach
#     subject = 'Hello coach your session is booked.'
#     message = f'Dear {coach.first_name},\n\nThank you booking slots of learner.Please be ready on date and time to complete session. Best of luck!'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [coach_email])


#     # Send email notification to the learner
#     subject = 'Hello learner your session is booked.'
#     message = f'Dear {learner.name},\n\nThank you booking slots of learner.Please be ready on date and time to complete session. Best of luck!'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [learner_email])

#     return Response({'message':'','details':serializer.data}, status=201)
#     return Response(serializer.errors, status=400)


# @api_view(["GET"])
# def get_upcoming_session_coach(request, coach_id):
#     coach = get_object_or_404(Coach, id=coach_id)
#     current_timestamp =  int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(coach=coach,end_time_int__gt=current_timestamp)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_past_session_coach(request, coach_id):
#     coach = get_object_or_404(Coach, id=coach_id)
#     current_timestamp = int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__lt=current_timestamp,coach=coach)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_upcoming_session_learner(request, learner_id):
#     learner = get_object_or_404(Learner, id=learner_id)
#     current_timestamp =  int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__gt=current_timestamp,session_request__learner=learner)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_past_session_learner(request, learner_id):
#     learner = get_object_or_404(Learner, id=learner_id)
#     current_timestamp = int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__lt=current_timestamp,session_request__learner=learner)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)

# @api_view(["POST"])
# def add_learner(request, project_id):
#     try:
#         project = Project.objects.get(id=project_id)
#     except Project.DoesNotExist:
#         raise ParseError("Invalid project id provided.")

#     email = request.data.get('email')
#     if not email:
#         raise ValidationError("Email is required.")

#     with transaction.atomic():
#         # Create user and learner profile
#         user = User.objects.create_user(username=email, email=email)
#         learner_profile = Profile.objects.create(user=user, type='learner')

#         # Create learner
#         learner_data = {'name': request.data.get('name'), 'email': email, 'phone': request.data.get('phone')}
#         learner = Learner.objects.create(user=learner_profile, **learner_data)

#         # Add learner to project
#         project.learner.add(learner)
#         project.save()

#     serializer = ProjectSerializer(project)
#     return Response({'message':'Learner added successfully','details':serializer.data}, status=201)


# @api_view(["GET"])
# def get_upcoming_session(request):
#     current_timestamp =  int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__gt=current_timestamp)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
# return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_past_session(request):
#     current_timestamp = int(timezone.now().timestamp() * 1000)
#     sessions = Session.objects.annotate(end_time_int=Cast('confirmed_availability__end_time', IntegerField())).filter(end_time_int__lt=current_timestamp)
#     serializer = SessionsDepthTwoSerializer(sessions, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_session_requests(request):
#     session_requests = SessionRequest.objects.filter(is_booked=False)
#     serializer = SessionRequestDepthTwoSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)


# @api_view(['POST'])
# def complete_project(request):
#     project = get_object_or_404(Project, id=request.data['project_id'])
#     project.status = 'Completed'
#     project.save()
#     project_serializer = ProjectSerializer(project)
#     return Response({'message':'Project marked as complete!','details':project_serializer.data},status=200)


# @api_view(['POST'])
# def mark_coach_joined_session(request):
#     session = get_object_or_404(Session, id=request.data['session_id'])
#     session.coach_joined = True
#     session.save()
#     session_serializer = SessionSerializer(session)
#     return Response({"message":"","details":session_serializer.data},status=200)


# @api_view(['POST'])
# def mark_learner_joined_session(request):
#     session = get_object_or_404(Session, id=request.data['session_id'])
#     session.learner_joined = True
#     session.save()
#     session_serializer = SessionSerializer(session)
#     return Response({'message':'','details':session_serializer.data},status=200)

# @api_view(['GET'])
# def get_session_request_count(request):
#     session_requests = SessionRequest.objects.filter(is_booked=False)
#     count = len(session_requests)
#     return Response({'session_request_count':count },status=200)


# @api_view(["GET"])
# def get_pending_session_requests_by_learner(request,learner_id):
#     session_requests = SessionRequest.objects.filter(is_booked=False,learner__id=learner_id)
#     serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)


# @api_view(["GET"])
# def get_all_session_requests_by_learner(request,learner_id):
#     session_requests = SessionRequest.objects.filter(learner__id=learner_id)
#     serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
#     return Response(serializer.data, status=200)


# @api_view(['POST'])
# def forgot_password(request):
#     reset_password_request = ResetPasswordRequestTokenView.as_view()

#     response = reset_password_request(request)
#     if response.status_code == 200:
#         email = request.data.get('email')
#         token = response.data.get('token')
#         print(token)
#     return Response(response.data, status=response.status_code)


# @api_view(['POST'])
# def otp_generation_hr(request):
#     try:
#         hr = HR.objects.get(email=request.data['email'])
#         try:
#             # Check if OTP already exists for the hr
#             otp_obj = OTP_HR.objects.get(hr=hr)
#             otp_obj.delete()
#         except OTP_HR.DoesNotExist:
#             pass

#         # Generate OTP and save it to the database
#         otp = get_random_string(length=6, allowed_chars='0123456789')
#         created_otp = OTP_HR.objects.create(hr=hr, otp=otp)

#         # Send OTP on email to hr
#         subject = f'Meeraq Login Otp'
#         message = f'Dear {hr.first_name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [hr.email])

#         return Response({'success': True,'otp':created_otp.otp})


#     except HR.DoesNotExist:
#         # Handle the case where the hr with the given email does not exist
#         return Response({'error': 'HR with the given email does not exist.'}, status=400)

#     except Exception as e:
#         # Handle any other exceptions
#         return Response({'error': str(e)}, status=500)


# @api_view(['POST'])
# def otp_validation_hr(request):
#     otp_obj = OTP_HR.objects.filter(hr__email=request.data['email'], otp=request.data['otp']).order_by('-created_at').first()

#     if otp_obj is None:
#         raise AuthenticationFailed('Invalid OTP')

#     hr = otp_obj.hr
#     token, created = Token.objects.get_or_create(user=hr.user.user)

#     # Delete the OTP object after it has been validated
#     otp_obj.delete()

#     hr_data = {'id':hr.id,'name':hr.first_name,'email': hr.email,'phone': hr.phone,'last_login': hr.user.user.last_login ,'token': token.key}
#     updateLastLogin(hr.email)
#     return Response({ 'hr': hr_data},status=200)


@api_view(["GET"])
def get_ongoing_projects_of_hr(request, hr_id):
    projects = Project.objects.filter(hr__id=hr_id, steps__project_live="pending")
    serializer = ProjectDepthTwoSerializer(projects, many=True)
    return Response(serializer.data, status=200)


# @api_view(['GET'])
# def get_completed_projects_of_hr(request,hr_id):
#     projects = Project.objects.filter(hr__id = hr_id, steps__project_live="complete")
#     serializer = ProjectDepthTwoSerializer(projects, many=True)
#     return Response(serializer.data, status=200)

# @api_view(['POST'])
# def add_coach(request):
#     # Get data from request
#     first_name = request.data.get('first_name')
#     last_name = request.data.get('last_name')
#     email = request.data.get('email')
#     age = request.data.get('age')
#     gender = request.data.get('gender')
#     domain = request.data.get('domain')
#     room_id = request.data.get('room_id')
#     phone = request.data.get('phone')
#     level = request.data.get('level')
#     rating = "5"
#     area_of_expertise = request.data['area_of_expertise']
#     username = request.data.get('email') # keeping username and email same
#     password = request.data.get('password')

#     print(first_name, last_name, email, age, gender, domain, room_id, phone, level,  username, password)

#     # Check if required data is provided
#     if not all([first_name, last_name, email, age, gender, domain, room_id, phone, level,  username, password]):
#         return Response({'error': 'All required fields must be provided.'}, status=400)

#     try:
#         # Create the Django User
#         with transaction.atomic():
#             user = User.objects.create_user(username=username, password=password,email=email)

#             # Create the Coach Profile linked to the User
#             coach_profile = Profile.objects.create(user=user, type='coach')

#             # Create the Coach User using the Profile
#             coach_user = Coach.objects.create(user=coach_profile, first_name= first_name, last_name=last_name, email=email, room_id=room_id, phone=phone, level=level, rating=rating, area_of_expertise=area_of_expertise)

# 			# approve coach
#             coach = Coach.objects.get(id=coach_user.id)
#             # Change the is_approved field to True
#             coach.is_approved = True
#             coach.save()

#             full_name = coach_user.first_name + " " + coach_user.last_name


#             # Send email notification to the coach
#             subject = 'Welcome to our coaching platform'
#             message = f'Dear {full_name},\n\n You have been added to the Meeraq portal as a coach. \n Here is your credentials. \n\n Username: {email} \n Password: {password}\n\n Click on the link to login or reset the password http://localhost:3003/'
#             send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

#             # # Send email notification to the admin
#             admin_email = 'jatin@meeraq.com'
#             admin_message = f'Dear PMO! \n\n A new coach {full_name} has been added on our coaching platform.'
#             send_mail(subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email])

#             # Return success response
#         return Response({'message': 'Coach added successfully.'}, status=201)

#     except IntegrityError:
#         return Response({'error': 'A coach user with this email already exists.'}, status=400)

#     except Exception as e:
#         # Return error response if any other exception occurs
#         return Response({'error': 'An error occurred while creating the coach user.'}, status=500)


@api_view(["GET"])
def get_hr(request):
    try:
        # Get all the Coach objects
        hr = HR.objects.all()

        # Serialize the Coach objects
        serializer = HrSerializer(hr, many=True)

        # Return the serialized Coach objects as the response
        return Response(serializer.data, status=200)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({"error": str(e)}, status=500)


# def create_hr(hrs_data):
#     try:
#             if not hrs_data:
#                 raise ValueError('HR data is required')
#             hrs = []
#             for hr_data in hrs_data:
#                 print('email',hr_data)
#                 # Check if username field is provided
#                 # if 'email' not in hr_data:
#                 #     raise ValueError('Username field is required')

#                 # Check if user already exists
#                 user = User.objects.filter(username=hr_data).first()
#                 if user:
#                     # If user exists, check if hr already exists
#                     print('user exists',user)
#                     hr_profile = HR.objects.get(user__user=user)
#                     print(hr_profile,'hr_profile')
#                     if hr_profile:
#                         hrs.append(hr_profile)
#                         continue
#                 else:
#                 # If HR does not exist, create the user object with an unusable password
#                     user = User.objects.create_user(
#                         username=hr_data,
#                         email=hr_data
#                         )
#                     user.set_unusable_password()
#                     user.save()

#                 # Create the hr profile
#                     hr_profile = Profile.objects.create(user=user, type='hr')

#                 # Create the hr object
#                     hr = HR.objects.create(user=hr_profile , email=hr_data)
#                     hrs.append(hr)

#             # Return response with hr created or already existing
#             serializer = HrSerializer(hrs, many=True)
#             print(hrs,'helloo')
#             return hrs


#     except ValueError as e:
#         # Handle missing or invalid request data
#         raise ValueError(str(e))

#     except Exception as e:
#         # Handle any other exceptions
#         # transaction.set_rollback(True) # Rollback the transaction
#         raise Exception(str(e))


# @api_view(['POST'])
# def change_password(request):
#     return ResetPasswordConfirmTokenView.as_view()(request)


# @api_view(['POST'])
# def edit_project(request,project_id):
# 		print(project_id)
# 		organisation= Organisation(
#         name=request.data['organisation_name'], image_url=request.data['image_url']
#     )
# 		organisation.save()
# 		project = Project.objects.get(id=project_id)
# 		project.name = request.data['project_name']
# 		project.organisation = organisation
# 		project.total_sessions = request.data['total_sessions']
# 		project.cost_per_session = request.data['cost_per_session']
# 		project.session_duration = request.data['session_duration']
# 		project.sessions_per_employee = request.data['sessions_per_employee']
# 		project.currency=request.data['currency']
# 		project.end_date = request.data['end_date']
# 		project.coaches.clear()
# 		for coach_id in request.data['coach_id']:
# 				coach = Coach.objects.get(id = coach_id)
# 				project.coaches.add(coach)
# 		project.save()
# 		return Response({'message':'Project details updated!','details':{}},status=200)


# @api_view(['POST'])
# def delete_session_request(request, session_request_id):
# 		session_request = SessionRequest.objects.get(id = session_request_id)
# 		session_request.delete()
# 		return Response({'message':'','details':{'deleted_session_request_id': session_request_id}})


# @api_view(['GET'])
# def get_dashboard_details(request):
#     local_time = timezone.localtime(timezone.now())
#     india_tz = pytz.timezone('Asia/Kolkata')
#     india_time = local_time.astimezone(india_tz)
#     print(india_time)
#     current_datetime = timezone.localtime(timezone.now())
#     print(current_datetime)
#     start_of_day = india_time.replace(hour=0, minute=0, second=0, microsecond=0)
#     end_of_day = start_of_day + timedelta(days=1)
#     today_sessions = Session.objects.filter(
#         confirmed_availability__start_time__gte=start_of_day.timestamp() * 1000,
#         confirmed_availability__start_time__lt=end_of_day.timestamp() * 1000
#     )
#     sessions_serializer = SessionsDepthTwoSerializer(today_sessions,many=True)
#     session_requests = SessionRequest.objects.filter(is_booked=False)
#     # session_requests_serializer = SessionRequestDepthTwoSerializer(session_requests, many=True)
#     return Response({'todays_sessions': sessions_serializer.data,'session_requests_count': len(session_requests)})


# @api_view(['POST'])
# def invite_coach(request):
#     serializer = CoachInvitesSerializer(data=request.data)
#     if serializer.is_valid():
#         invite = serializer.save()
#         subject = f'Meeraq Portal invitation'
#         message = f'Dear {invite.name} \n\n Sign up on Meeraq coach portal'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invite.email])
#         return Response({'message':'Coach invited successfully!','details':serializer.data}, status=201)
#     return Response(serializer.errors, status=400)


# @api_view(['GET'])
# def get_coach_invites(request):
#     invites = CoachInvites.objects.order_by('-created_at')
#     serializer = CoachInvitesSerializer(invites, many=True)
#     return Response(serializer.data)


@api_view(["GET"])
def get_projects_and_sessions_by_coach(request, coach_id):
    projects = Project.objects.filter(coaches_status__coach__id=coach_id)
    # sessions = Session.objects.filter(session_request__project__in=projects,coach__id=coach_id)
    # session_serializer = SessionsDepthTwoSerializer(sessions, many=True)
    # sessions_dict = {}
    # for session in session_serializer.data:
    #     project_id = session['session_request']['project']['id']
    #     if project_id in sessions_dict:
    #         sessions_dict[project_id].append(session)
    #     else:
    #         sessions_dict[project_id] = [session]
    project_serializer = ProjectDepthTwoSerializer(projects, many=True)
    return Response({"projects": project_serializer.data})


# @api_view(['POST'])
# def otp_generation_hr(request):
#     try:
#         hr = HR.objects.get(email=request.data['email'])
#         try:
#             # Check if OTP already exists for the hr
#             otp_obj = OTP_HR.objects.get(hr=hr)
#             otp_obj.delete()
#         except OTP_HR.DoesNotExist:
#             pass

#         # Generate OTP and save it to the database
#         otp = get_random_string(length=6, allowed_chars='0123456789')
#         created_otp = OTP_HR.objects.create(hr=hr, otp=otp)

#         # Send OTP on email to hr
#         subject = f'Meeraq Login Otp'
#         message = f'Dear {hr.first_name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}'
#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [hr.email])

#         return Response({'success': True,'otp':created_otp.otp})


#     except HR.DoesNotExist:
#         # Handle the case where the hr with the given email does not exist
#         return Response({'error': 'HR with the given email does not exist.'}, status=400)

#     except Exception as e:
#         # Handle any other exceptions
#         return Response({'error': str(e)}, status=500)


# @api_view(['POST'])
# def otp_validation_hr(request):
#     otp_obj = OTP_HR.objects.filter(hr__email=request.data['email'], otp=request.data['otp']).order_by('-created_at').first()

#     if otp_obj is None:
#         raise AuthenticationFailed('Invalid OTP')

#     hr = otp_obj.hr
#     token, created = Token.objects.get_or_create(user=hr.user.user)

#     # Delete the OTP object after it has been validated
#     otp_obj.delete()

#     hr_data = {'id':hr.id,'name':hr.first_name,'email': hr.email,'phone': hr.phone,'last_login': hr.user.user.last_login ,'token': token.key}
#     updateLastLogin(hr.email)
#     return Response({ 'hr': hr_data},status=200)


# @api_view(['GET'])
# def get_ongoing_projects_of_hr(request,hr_id):
#     projects = Project.objects.filter(hr__id = hr_id,steps__project_live="pending")
#     serializer = ProjectDepthTwoSerializer(projects, many=True)
#     return Response(serializer.data, status=200)


# @api_view(['GET'])
# def get_completed_projects_of_hr(request,hr_id):
#     projects = Project.objects.filter(hr__id = hr_id, steps__project_live="complete")
#     serializer = ProjectDepthTwoSerializer(projects, many=True)
#     return Response(serializer.data, status=200)


def coach_exists(coach_id):
    return Coach.objects.filter(coach_id=coach_id).exists()


@api_view(["POST"])
def add_coach(request):
    # Get data from request
    coach_id = request.data.get("coach_id")
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    email = request.data.get("email")
    age = request.data.get("age")
    gender = request.data.get("gender")
    domain = request.data.get("domain")
    room_id = request.data.get("room_id")
    phone = request.data.get("phone")
    level = request.data.get("level")
    education = request.data.get("education")
    rating = "5"
    min_fees = request.data["min_fees"]
    fee_remark = request.data.get("fee_remark", "")
    coaching_hours = request.data.get("coaching_hours")
    # created_at = request.data('created_at')
    # edited_at = request.data('edited_at')
    linkedin_profile_link = request.data["linkedin_profile_link"]
    companies_worked_in = json.loads(request.data["companies_worked_in"])
    other_certification = json.loads(request.data["other_certification"])
    active_inactive = json.loads(request.data["active_inactive"])
    area_of_expertise = json.loads(request.data["area_of_expertise"])
    location = json.loads(request.data["location"])
    language = json.loads(request.data["language"])
    job_roles = json.loads(request.data["job_roles"])
    ctt_nctt = json.loads(request.data["ctt_nctt"])
    years_of_coaching_experience = request.data.get("years_of_coaching_experience")
    years_of_corporate_experience = request.data.get("years_of_corporate_experience")
    username = request.data.get("email")  # keeping username and email same
    # password = request.data.get('password')
    profile_pic = request.data.get("profile_pic", None)
    corporate_experience = request.data.get("corporate_experience", "")
    coaching_experience = request.data.get("coaching_experience", "")

    # return Response({'error': 'A coach user with this email already exists.'}, status=400)

    # print('ctt not ctt', json.loads(  request.data['ctt_nctt']),type(json.loads(request.data['ctt_nctt'])))

    # Check if required data is provided
    if not all(
        [
            coach_id,
            first_name,
            last_name,
            email,
            gender,
            phone,
            level,
            username,
            room_id,
        ]
    ):
        return Response({"error": "All required fields must be provided."}, status=400)

    try:
        # Create the Django User
        if coach_exists(coach_id):
            return Response({"error": "Coach with this ID already exists."}, status=400)

        with transaction.atomic():
            temp_password = "".join(
                random.choices(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits, k=8
                )
            )
            user = User.objects.create_user(
                username=username, password=temp_password, email=email
            )

            # Create the Coach Profile linked to the User
            coach_profile = Profile.objects.create(user=user, type="coach")

            # Create the Coach User using the Profile
            coach_user = Coach.objects.create(
                user=coach_profile,
                coach_id=coach_id,
                room_id=room_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                level=level,
                education=education,
                rating=rating,
                area_of_expertise=area_of_expertise,
                age=age,
                gender=gender,
                domain=domain,
                years_of_corporate_experience=years_of_corporate_experience,
                ctt_nctt=ctt_nctt,
                years_of_coaching_experience=years_of_coaching_experience,
                profile_pic=profile_pic,
                language=language,
                min_fees=min_fees,
                fee_remark=fee_remark,
                job_roles=job_roles,
                location=location,
                coaching_hours=coaching_hours,
                linkedin_profile_link=linkedin_profile_link,
                companies_worked_in=companies_worked_in,
                other_certification=other_certification,
                active_inactive=active_inactive,
                corporate_experience=corporate_experience,
                coaching_experience=coaching_experience,
            )

            # approve coach
            coach = Coach.objects.get(id=coach_user.id)
            # Change the is_approved field to True
            coach.is_approved = True
            coach.save()

            full_name = coach_user.first_name + " " + coach_user.last_name

            # Send email notification to the coach
            # subject = 'Welcome to our coaching platform'
            # message = f'Dear {full_name},\n\n You have been added to the Meeraq portal as a coach. \n Here is your credentials. \n\n Username: {email} \n Password: {temp_password}\n\n Click on the link to login or reset the password http://localhost:3003/'
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            # # Send email notification to the admin
            # admin_email = 'jatin@meeraq.com'
            # admin_message = f'Dear PMO! \n\n A new coach {full_name} has been added on our coaching platform.'
            # send_mail(subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email])

            # Return success response
        return Response({"message": "Coach added successfully."}, status=201)

    except IntegrityError as e:
        print(e)
        return Response(
            {"error": "A coach user with this email already exists."}, status=400
        )

    except Exception as e:
        # Return error response if any other exception occurs
        print(e)
        return Response(
            {"error": "An error occurred while creating the coach user."}, status=500
        )


@api_view(["POST"])
def delete_coach(request):
    coach_id = request.data.get("coach_id", None)
    if coach_id:
        try:
            coach = Coach.objects.get(id=coach_id)
            user = coach.user.user
            user.delete()
            return Response({"message": "Coach deleted."}, status=200)
        except ObjectDoesNotExist:
            return Response({"message": "Failed to delete coach profile"}, status=400)
    else:
        return Response({"message": "Failed to delete coach profile"}, status=400)


# @api_view(['GET'])
# def get_hr(request):
#     try:
#         # Get all the Coach objects
#         hr = HR.objects.all()

#         # Serialize the Coach objects
#         serializer = HrSerializer(hr, many=True)

#         # Return the serialized Coach objects as the response
#         return Response(serializer.data, status=200)

#     except Exception as e:
#         # Return error response if any exception occurs
#         return Response({'error': str(e)}, status=500)

# def create_hr(hrs_data):
#     try:
#             if not hrs_data:
#                 raise ValueError('HR data is required')
#             hrs = []
#             for hr_data in hrs_data:
#                 print('email',hr_data)
#                 # Check if username field is provided
#                 # if 'email' not in hr_data:
#                 #     raise ValueError('Username field is required')

#                 # Check if user already exists
#                 user = User.objects.filter(username=hr_data).first()
#                 if user:
#                     # If user exists, check if hr already exists
#                     print('user exists',user)
#                     hr_profile = HR.objects.get(user__user=user)
#                     print(hr_profile,'hr_profile')
#                     if hr_profile:
#                         hrs.append(hr_profile)
#                         continue
#                 else:
#                 # If HR does not exist, create the user object with an unusable password
#                     user = User.objects.create_user(
#                         username=hr_data,
#                         email=hr_data
#                         )
#                     user.set_unusable_password()
#                     user.save()

#                 # Create the hr profile
#                     hr_profile = Profile.objects.create(user=user, type='hr')

#                 # Create the hr object
#                     hr = HR.objects.create(user=hr_profile , email=hr_data)
#                     hrs.append(hr)

#             # Return response with hr created or already existing
#             serializer = HrSerializer(hrs, many=True)
#             print(hrs,'helloo')
#             return hrs


#     except ValueError as e:
#         # Handle missing or invalid request data
#         raise ValueError(str(e))

#     except Exception as e:
#         # Handle any other exceptions
#         # transaction.set_rollback(True) # Rollback the transaction
#         raise Exception(str(e))


@api_view(["GET"])
@permission_classes([AllowAny])
def get_csrf(request):
    response = Response({"detail": "CSRF cookie set"})
    response["X-CSRFToken"] = get_token(request)
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    if username is None or password is None:
        raise ValidationError({"detail": "Please provide username and password."})
    user = authenticate(request, username=username, password=password)
    # check_user = Profile.objects.get(user__username=username)
    # if check_user:
    #     if check_user.type == 'hr':
    #         raise AuthenticationFailed({'detail': 'Try login with OTP.'})

    if user is None:
        raise AuthenticationFailed({"detail": "Invalid credentials."})

    login(request, user)
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user.last_login = today
    user.save()
    user_data = get_user_data(user)
    if user_data:
        return Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": user.last_login},
            }
        )
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    if not request.user.is_authenticated:
        raise AuthenticationFailed({"detail": "You're not logged in."})

    logout(request)
    return Response({"detail": "Successfully logged out."})


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def session_view(request):
    user = request.user
    user_data = get_user_data(user)
    if user_data:
        return Response({"isAuthenticated": True, "user": user_data})
    else:
        return Response({"error": "Invalid user type"}, status=400)


def get_user_data(user):
    if not user.profile:
        return None
    elif user.profile.type == "coach":
        serializer = CoachDepthOneSerializer(user.profile.coach)
    elif user.profile.type == "pmo":
        serializer = PmoDepthOneSerializer(user.profile.pmo)
    elif user.profile.type == "learner":
        serializer = LearnerDepthOneSerializer(user.profile.learner)
    elif user.profile.type == "hr":
        serializer = HrDepthOneSerializer(user.profile.hr)
    else:
        return None
    return serializer.data


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_otp(request):
    try:
        user = User.objects.get(username=request.data["email"])
        try:
            # Check if OTP already exists for the user
            otp_obj = OTP.objects.get(user=user)
            otp_obj.delete()
        except OTP.DoesNotExist:
            pass

        # Generate OTP and save it to the database
        otp = get_random_string(length=6, allowed_chars="0123456789")
        created_otp = OTP.objects.create(user=user, otp=otp)
        user_data = get_user_data(user)
        name = user_data.get("name") or user_data.get("first_name") or "User"
        # Send OTP on email to learner
        subject = f"Meeraq Login OTP"
        message = (
            f"Dear {name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.username])

        return Response({"message": f"OTP has been sent to {user.username}!"})

    except User.DoesNotExist:
        # Handle the case where the user with the given email does not exist
        return Response(
            {"error": "User with the given email does not exist."}, status=400
        )

    except Exception as e:
        # Handle any other exceptions
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_otp(request):
    otp_obj = (
        OTP.objects.filter(
            user__username=request.data["email"], otp=request.data["otp"]
        )
        .order_by("-created_at")
        .first()
    )

    if otp_obj is None:
        raise AuthenticationFailed("Invalid OTP")

    user = otp_obj.user
    # token, created = Token.objects.get_or_create(user=learner.user.user)

    # Delete the OTP object after it has been validated
    otp_obj.delete()
    login(request, user)
    user_data = get_user_data(user)
    if user_data:
        return Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": user.last_login},
            }
        )
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)

    # learner_data = {'id':learner.id,'name':learner.name,'email': learner.email,'phone': learner.email,'last_login': learner.user.user.last_login ,'token': token.key}
    # updateLastLogin(learner.email)
    # return Response({ 'learner': learner_data},status=200)


@api_view(["GET"])
def get_organisation(request):
    orgs = Organisation.objects.all()
    serializer = OrganisationSerializer(orgs, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def add_organisation(request):
    print(request.data.get("image_url", ""))
    org = Organisation.objects.create(
        name=request.data.get("name", ""), image_url=request.data.get("image_url", "")
    )
    orgs = Organisation.objects.all()
    serializer = OrganisationSerializer(orgs, many=True)
    return Response(
        {"message": "Organisation added successfully.", "details": serializer.data},
        status=200,
    )


@api_view(["POST"])
def add_hr(request):
    try:
        # Check if user with given email already exists
        if User.objects.filter(email=request.data.get("email")).exists():
            raise ValueError("User with given email already exists")
        # Create the Django User

        temp_password = "".join(
            random.choices(
                string.ascii_uppercase + string.ascii_lowercase + string.digits, k=8
            )
        )
        user = User.objects.create_user(
            username=request.data.get("email"),
            password=temp_password,
            email=request.data.get("email"),
        )
        user.save()
        # Create the PMO Profile linked to the User
        hr_profile = Profile.objects.create(user=user, type="hr")
        # Get organization
        organisation = Organisation.objects.filter(
            id=request.data.get("organisation")
        ).first()
        # Create the PMO User using the Profile
        hr = HR.objects.create(
            user=hr_profile,
            first_name=request.data.get("first_name"),
            last_name=request.data.get("last_name"),
            email=request.data.get("email"),
            phone=request.data.get("phone"),
            organisation=organisation,
        )
        # subject = 'Welcome to Meeraq'
        # message = f'Dear {request.data.get("first_name")},\n\nYour Account has been created with Meeraq your username is {request.data.get("email")} and temporary password is {temp_password} please log into our system and change your password to avoid any inconvenience'
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.data.get('email')])
        hrs = HR.objects.all()
        serializer = HrSerializer(hrs, many=True)
        return Response(
            {"message": "HR added successfully", "details": serializer.data}, status=200
        )
    except Exception as e:
        return Response({"error": str(e)}, status=400)


# Filter API for Coaches
# Expected input "filters": [{"key":"area_of_expertise","value":"test"},...]
# @api_view(['POST'])
# def filter_coach(request):
#     filters=request.data.get('filters',[])
#     temp={}
#     for filter in filters:
#         print(filter)
#         if filter['key'] in ["area_of_expertise", "years_of_coaching_experience", "gender"] and filter['value'] is not None and filter['value']!='':
#             temp[filter['key']] = filter['value']
#     coaches = Coach.objects.filter(**temp).all()
#     serializer = CoachSerializer(coaches, many=True)
#     return Response(serializer.data, status=200)


@api_view(["POST"])
def add_project_struture(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.project_structure = request.data.get("project_structure", [])
    # project.status['project_structure'] = 'complete'
    project.save()
    return Response({"message": "Structure added", "details": ""}, status=200)


@api_view(["POST"])
def send_consent(request):
    # Get all the Coach objects
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    coaches = Coach.objects.filter(id__in=request.data.get("coach_list", [])).all()
    coach_status = []
    for coach in coaches:
        if not CoachStatus.objects.filter(coach=coach, project=project).exists():
            status = CoachStatus.objects.create(
                coach=coach,
                status=dict(
                    consent={
                        "status": "sent",
                        "response_date": None,
                    },
                    project_structure={
                        "status": "sent",
                        "response_date": None,
                    },
                    hr={
                        "status": None,
                        "session_id": None,
                        "response_date": None,
                    },
                    learner={
                        "status": None,
                        "session_id": None,
                        "response_date": None,
                    },
                ),
                consent_expiry_date=request.data["consent_expiry_date"],
            )
            status.save()
            coach_status.append(status)
        # subject = 'Consent for {project.name} Project'
        # message = f'Dear {coach.first_name},\n\nPlease provide your consent for above mentioned project by logging into your Dashboard'
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [coach.email])
    # project.coaches = coach_list
    project.coaches_status.add(*coach_status)
    project.steps["coach_list"]["status"] = "complete"
    project.save()
    try:
        path = f"/projects"
        message = f"Admin has requested your consent to share profile for new project."
        for coach in coaches:
            create_notification(coach.user.user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Consent sent successfully", "details": ""}, status=200)


# @api_view(['POST'])
# def select_coaches(request):
#     # Get all the Coach objects
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     coaches = Coach.objects.filter(id__in=request.data.get('coach_list',[])).all()
#     coach_status = []
#     for coach in coaches:
#         status = project.coaches_status.get(coach=coach)
#         status.status['hr'] = "Selected"
#         status.save()
#     # project.coaches = coach_list
#     project.status['coach_list_to_hr'] = 'complete'
#     project.save()
#     return Response({"message":"Coaches selected successfully"},status=200)


@api_view(["GET"])
def get_project_details(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        serializer = ProjectDepthTwoSerializer(project)
        return Response(serializer.data)
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)


# Filter API for Coaches
# Expected input
# "project_id": 1
# "coach_id": 1
# "status": Consent Approved/Consent Rejected
@api_view(["POST"])
def receive_coach_consent(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    for coach_status in project.coaches_status.all():
        try:
            if coach_status.coach.id == request.data.get("coach_id", ""):
                # coach_status.status[request.data.get('status','').split(" ")[0].lower()]=request.data.get('status','').split(" ")[1].lower()
                # if request.data.get('status','').split(" ")[0].lower()=='contract':
                #     coach_status.status['consent'] = "approved"
                # coach_status.save()
                coach_status.status["consent"]["status"] = request.data["status"]
                if project.steps["project_structure"]["status"] == "complete":
                    coach_status.status["project_structure"]["status"] = request.data[
                        "status"
                    ]
                coach_status.save()
                try:
                    if request.data["status"] == "select":
                        pmo_user = User.objects.filter(profile__type="pmo").first()
                        if pmo_user:
                            path = f"/projects/caas/progress/{project.id}"
                            coach_name = (
                                coach_status.coach.first_name
                                + " "
                                + coach_status.coach.last_name
                            )
                            message = f"{coach_name.title() } has accepted your consent request for Project - {project.name}"
                            create_notification(pmo_user, path, message)
                except Exception as e:
                    print(f"Error occurred while creating notification: {str(e)}")
                    continue

        except Exception as e:
            print(e)
            return Response({"message": "Coach not Found"}, status=400)
    return Response({"message": request.data.get("status", "")}, status=200)


@api_view(["POST"])
def update_project_structure_consent_by_coach(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    for coach_status in project.coaches_status.all():
        try:
            if coach_status.coach.id == request.data.get("coach_id", ""):
                # coach_status.status[request.data.get('status','').split(" ")[0].lower()]=request.data.get('status','').split(" ")[1].lower()
                # if request.data.get('status','').split(" ")[0].lower()=='contract':
                #     coach_status.status['consent'] = "approved"
                # coach_status.save()
                coach_status.status["project_structure"]["status"] = request.data[
                    "status"
                ]
                coach_status.save()
                try:
                    if request.data["status"] == "select":
                        pmo_user = User.objects.filter(profile__type="pmo").first()
                        if pmo_user:
                            path = f"/projects/caas/progress/{project.id}"
                            coach_name = (
                                coach_status.coach.first_name
                                + " "
                                + coach_status.coach.last_name
                            )
                            message = f"{coach_name.title() } has agreed to the project structure for Project - {project.name}"
                            create_notification(pmo_user, path, message)
                except Exception as e:
                    print(f"Error occurred while creating notification: {str(e)}")
                    continue

        except Exception as e:
            print(e)
            return Response({"message": "Coach not Found"}, status=400)
    return Response({"message": "Status updated."}, status=200)


@api_view(["POST"])
def complete_coach_consent(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.status["coach_consent"] = "complete"
    project.save()
    return Response({"message": "Coach list sent to HR", "details": ""}, status=200)


@api_view(["POST"])
def complete_coach_list_to_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["coach_list_to_hr"]["status"] = "complete"
    project.steps["coach_consent"]["status"] = "complete"
    if not project.empanelment:
        for coach_status in project.coaches_status.all():
            if coach_status.status["hr"]["status"] == "select":
                coach_status.status["learner"]["status"] = "sent"
                coach_status.save()
    project.save()
    return Response({"message": "Step marked as complete.", "details": {}}, status=200)


@api_view(["POST"])
def complete_interviews_step(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["interviews"]["status"] = "complete"
    project.steps["coach_consent"]["status"] = "complete"
    if not project.empanelment:
        for coach_status in project.coaches_status.all():
            if coach_status.status["hr"]["status"] == "select":
                coach_status.status["learner"]["status"] = "sent"
                coach_status.save()
    project.save()
    return Response({"message": "Step marked as complete.", "details": {}}, status=200)


@api_view(["POST"])
def complete_empanelment(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["add_learners"]["status"] = "complete"
    project.save()
    return Response({"message": "Empanelement completed.", "details": ""}, status=200)


# @api_view(['POST'])
# def complete_interview(request):
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     project.steps['interviews']['status'] = 'complete'
#     project.save()
#     return Response({'message': "Interviews completed."},status=200)


@api_view(["POST"])
def complete_project_structure(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.status["project_structure"] = "complete"
    project.save()
    return Response({"message": "Project structure approved."}, status=200)


# @api_view(['POST'])
# def complete_coach_approval(request):
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     project.status['coach_approval'] = 'complete'
#     project.save()
#     return Response({'message': "Coach approval completed."},status=200)


# @api_view(['POST'])
# def complete_chemistry_sessions(request):
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)
#     project.steps['chemistry_session']['status'] = 'complete'
#     project.save()
#     return Response({'message': "Chemistry sessions completed."},status=200)


@api_view(["GET"])
def get_interview_data(request, project_id):
    sessions = SessionRequestCaas.objects.filter(
        project__id=project_id, session_type="interview"
    ).all()
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_chemistry_session_data(request, project_id):
    sessions = SessionRequestCaas.objects.filter(
        project__id=project_id, session_type="chemistry"
    ).exclude(status="pending")
    serializer = SessionRequestCaasDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_session_requests_of_hr(request, hr_id):
    sessions = SessionRequestCaas.objects.filter(hr__id=hr_id).all()
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_session_requests_of_learner(request, learner_id):
    sessions = SessionRequestCaas.objects.filter(learner__id=learner_id).all()
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_upcoming_booked_session_of_coach(request, coach_id):
    current_time = int(timezone.now().timestamp() * 1000)
    # convert current time to milliseconds
    sessions = SessionRequestCaas.objects.filter(
        coach__id=coach_id,
        is_booked=True,
        confirmed_availability__start_time__gt=current_time,
    ).all()
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def book_session_caas(request):
    print(request.data)
    session_request = SessionRequestCaas.objects.get(
        id=request.data.get("session_request")
    )
    session_request.confirmed_availability = Availibility.objects.get(
        id=request.data.get("confirmed_availability")
    )
    session_request.is_booked = True
    session_request.status = "booked"
    for email in request.data.get("invitees", []):
        session_request.invitees.append(email.strip())
    session_request.save()
    # if serializer.is_valid():
    #     session = serializer.save()
    #     # Mark the session request as booked
    #     session_request = session.session_request
    #     session_request.is_booked = True
    #     session_request.save()

    #     coach=session.coach
    #     coach_email=coach.email
    #     hr=session.session_request.hr
    #     he_email= hr.email
    # else:
    #     print(serializer.errors)
    #     return Response(serializer.errors,status=400)

    # Send email notification to the coach
    # subject = 'Hello coach your session is booked.'
    # message = f'Dear {session_request.coach.first_name},\n\nThank you booking slots of hr.Please be ready on date and time to complete session. Best of luck!'
    # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [session_request.coach.email])

    # # Send email notification to the learner
    if session_request.session_type == "interview":
        subject = "Hello hr your session is booked."
        message = f"Dear {session_request.hr.first_name},\n\nThank you booking slots of hr.Please be ready on date and time to complete session. Best of luck!"
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [session_request.hr.email])
    if session_request.session_type == "chemistry":
        subject = "Hello learner your session is booked."
        message = f"Dear {session_request.learner.name},\n\nThank you booking slots of hr.Please be ready on date and time to complete session. Best of luck!"
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [session_request.learner.email])
    try:
        pmo_user = User.objects.filter(profile__type="pmo").first()
        project = session_request.project
        coach = session_request.coach
        if pmo_user:
            path = f"/projects/caas/progress/{project.id}"
            coach_name = coach.first_name + " " + coach.last_name
            start_time = format_timestamp(
                int(session_request.confirmed_availability.start_time)
            )
            end_time = format_timestamp(
                int(session_request.confirmed_availability.end_time)
            )
            slot_message = f"{start_time} - {end_time}"
            if session_request.session_type == "interview":
                hr_user = session_request.hr.user.user
                message = f"{coach_name.title()} has booked the interview session for Project - {project.name}.The booked slot is "
                message_for_hr = f"{coach_name.title()} has booked the slot {slot_message} from your interview request. You can join the meeting on scheduled time."
                create_notification(hr_user, path, message_for_hr)
            if session_request.session_type == "chemistry":
                learner_user = session_request.learner.user.user
                message = f"{coach_name.title()} has booked the chemistry session for Project - {project.name}.The booked slot is "
                message_for_learner = f"{coach_name.title()} has booked the slot {slot_message} from your chemistry session request. You can join the meeting on scheduled time."
                message_for_hr = f"{coach_name.title()} has booked the slot {slot_message} as per the request from {session_request.learner.name.title()} for the project - {session_request.project.name}"
                create_notification(learner_user, path, message_for_learner)
            message += slot_message
            create_notification(pmo_user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")

    return Response({"message": "Session booked successfully!"}, status=201)


def create_time_arr(availability):
    time_arr = []
    for time in availability:
        availibility_serilizer = AvailibilitySerializer(data=time)
        if availibility_serilizer.is_valid():
            avil_id = availibility_serilizer.save()
            time_arr.append(avil_id.id)
        else:
            return Response(
                {
                    "message": str(availibility_serilizer.errors),
                },
                status=401,
            )
    return time_arr


def get_slot_message(availability):
    slot_message = ""
    for i, slot in enumerate(availability):
        start_time = format_timestamp(slot["start_time"])
        end_time = format_timestamp(slot["end_time"])
        slot_message += f"Slot {i+1}: {start_time} - {end_time}"
        if i == (len(availability) - 1):
            slot_message += ". "
        elif i == (len(availability) - 2):
            slot_message += " and "
        else:
            slot_message += ", "
    return slot_message


@api_view(["POST"])
def create_session_request_caas(request):
    time_arr = create_time_arr(request.data["availibility"])

    try:
        if request.data["session_type"] == "chemistry":
            session = SessionRequestCaas.objects.get(
                learner__id=request.data["learner_id"],
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        else:
            session = SessionRequestCaas.objects.get(
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        session.availibility.set(time_arr)
        session.save()
        return Response({"message": "Session updated successfully."}, status=201)
    except SessionRequestCaas.DoesNotExist:
        session = {
            "project": request.data["project_id"],
            "availibility": time_arr,
            "coach": request.data["coach_id"],
            "session_type": request.data["session_type"],
        }
        if session["session_type"] == "interview":
            session["hr"] = request.data["hr_id"]
        elif session["session_type"] == "chemistry":
            session["learner"] = request.data["learner_id"]
        session_serilizer = SessionRequestCaasSerializer(data=session)
        if session_serilizer.is_valid():
            session_created = session_serilizer.save()
            try:
                pmo_user = User.objects.filter(profile__type="pmo").first()
                project = Project.objects.get(id=request.data["project_id"])
                coach = Coach.objects.get(id=request.data["coach_id"])
                if pmo_user:
                    path = f"/projects/caas/progress/{project.id}"
                    path_for_coach = f"/sessions"
                    coach_name = coach.first_name + " " + coach.last_name
                    slot_message = get_slot_message(request.data["availibility"])
                    if session["session_type"] == "interview":
                        message = f"HR has requested interview session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                        message_for_coach = f"HR has requested for {slot_message} for Interview for Project - {project.name}. Please book one of the requested slots now"
                    elif session["session_type"] == "chemistry":
                        hr_user_in_project = (
                            session_created.project.hr.first().user.user
                        )
                        message_for_hr = f"{session_created.learner.name.title()} has requested for Chemistry session to the Coach - {coach_name.title()} for {slot_message} for the Project - {project.name}"
                        message_for_coach = f"Coachee has requested {slot_message} for Chemistry session for the Project - {project.name}. Please book one of the requested slots now"
                        create_notification(hr_user_in_project, path, message_for_hr)
                        message = f"Coachee has requested chemistry session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                    message += " " + slot_message
                    create_notification(pmo_user, path, message)
                    create_notification(
                        coach.user.user, path_for_coach, message_for_coach
                    )
            except Exception as e:
                print(f"Error occurred while creating notification: {str(e)}")
            return Response({"message": "Session sequested successfully."}, status=201)
        else:
            return Response(
                {
                    "message": str(session_serilizer.errors),
                },
                status=401,
            )


@api_view(["GET"])
def get_session_requests_of_coach(request, coach_id):
    sessions = SessionRequestCaas.objects.filter(coach__id=coach_id).all()
    serializer = SessionRequestCaasDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def accept_coach_caas_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    for coach in project.coaches_status.all():
        if coach.coach_id == request.data.get("coach_id"):
            if (
                coach.status["consent"]["status"] == "select"
                and coach.status["hr"]["status"] == "sent"
            ):
                coach.status["hr"]["status"] = request.data["status"]
                coach.save()
            else:
                return Response({"error": "Failed to update status."}, status=400)
            # print(coach.id)
            # print(coach.status)
            # if coach.status not in ["HR Selected","HR Rejected"]:
            #     coach.status['hr']=request.data.get('status').split(" ")[1].lower()
            #     coach.save()
            #     print("->")
            #     print(coach.status)
            # else:
            #     return Response({"error": "Status Already Updated"}, status=400)
    project.save()
    message = ""
    if request.data.get("status") == "select":
        try:
            pmo_user = User.objects.filter(profile__type="pmo").first()
            coach = Coach.objects.get(id=request.data["coach_id"])
            if pmo_user:
                path = f"/projects/caas/progress/{project.id}"
                coach_name = coach.first_name + " " + coach.last_name
                message = f"HR has selected {coach_name.title()} for the Project - {project.name}"
                message_for_coach = f"Congratulations! You have been selected by HR for the Project - {project.name}"
                create_notification(pmo_user, path, message)
                create_notification(coach.user.user, path, message)
        except Exception as e:
            print(f"Error occurred while creating notification: {str(e)}")
        message = "Coach selected."
    elif request.data.get("status") == "reject":
        try:
            coach = Coach.objects.get(id=request.data["coach_id"])
            path = f"/projects/caas/progress/{project.id}"
            message_for_coach = f"Unfortunately, your profile is not selected for the Project - {project.name}"
            create_notification(coach.user.user, path, message_for_coach)
        except Exception as e:
            print(f"Error occurred while creating notification: {str(e)}")
        message = "Coach rejected."
    return Response({"message": message}, status=200)


@api_view(["POST"])
def add_learner_to_project(request):
    try:
        project = Project.objects.get(id=request.data["project_id"])
    except Project.DoesNotExist:
        return Response({"error": "Project does not exist."}, status=404)
    try:
        learners = create_learners(request.data["learners"])
        for learner in learners:
            create_engagement(learner, project)
            # project.learner.add(learner)
            try:
                path = f"/projects/caas/progress/{project.id}"
                message = f"You have been added to Project - {project.name}"
                create_notification(learner.user.user, path, message)
            except Exception as e:
                print(f"Error occurred while creating notification: {str(e)}")
                continue
    except Exception as e:
        # Handle any exceptions from create_learners
        return Response({"error": str(e)}, status=500)
    try:
        pmo_user = User.objects.filter(profile__type="pmo").first()
        if pmo_user:
            path = f"/projects/caas/progress/{project.id}"
            message = f"HR has added Coachees to the Project - {project.name}"
            create_notification(pmo_user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Coachee added succesfully", "details": ""}, status=201)


def transform_project_structure(sessions):
    # convert project level project structure to engagement level project structure
    # argument
    # sessions - array of objects where object has price, no. of sessions, session type, session durations
    # returns:
    # sessions - array of objects where object has - session type, session name (session type + n (numbered)) , session duration, status (pending)
    session_counts = {}
    transformed_sessions = []

    for session in sessions:
        session_type = session["session_type"]
        session_duration = session["session_duration"]
        if session_type not in session_counts:
            session_counts[session_type] = 1

        for i in range(session["no_of_sessions"]):
            session_name = f"{session_type}_{session_counts[session_type]}"
            transformed_session = {
                "session_name": session_name,
                "session_number": session_counts[session_type],
                "session_type": session_type,
                "session_duration": session_duration,
                "status": "pending",
            }
            transformed_sessions.append(transformed_session)
            session_counts[session_type] += 1

    return transformed_sessions


def create_engagement(learner, project):
    existing_engagement = Engagement.objects.filter(
        learner__id=learner.id, project__id=project.id
    )
    if len(existing_engagement) == 0:
        engagemenet_project_structure = transform_project_structure(
            project.project_structure
        )
        for index, session in enumerate(engagemenet_project_structure):
            session_data = SessionRequestCaas.objects.create(
                learner=learner,
                project=project,
                session_duration=session["session_duration"],
                session_number=session["session_number"],
                session_type=session["session_type"],
                status="pending",
                order=index + 1,
            )
        engagement = Engagement(learner=learner, project=project, status="active")
        engagement.save()
        return engagement
    return existing_engagement


@api_view(["POST"])
def accept_coach_caas_learner(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    cnt = len(
        project.coaches_status.filter(
            learner_id__contains=request.data.get("learner_id")
        )
    )
    if cnt == 0:
        for coach in project.coaches_status.filter(
            coach__id=request.data.get("coach_id")
        ):
            coach.status["learner"]["status"] = request.data.get("status")
            if request.data.get("status") == "select":
                learner = Learner.objects.get(id=request.data.get("learner_id"))
                engagement = Engagement.objects.get(
                    learner__id=request.data.get("learner_id"), project__id=project.id
                )
                engagement.coach = coach.coach
                engagement.save()
                sessions = SessionRequestCaas.objects.filter(
                    learner__id=request.data.get("learner_id"),
                    session_type="chemistry_session",
                    project=project,
                ).exclude(coach=coach.coach)
                for session in sessions:
                    session.is_archive = True
                    session.save()
                coach.learner_id.append(request.data.get("learner_id"))
            coach.save()
    else:
        return Response({"error": "Coach Already Selected"}, status=400)
    message = ""
    if request.data.get("status") == "select":
        try:
            pmo_user = User.objects.filter(profile__type="pmo").first()
            coach = Coach.objects.get(id=request.data["coach_id"])
            if pmo_user:
                path = f"/projects/caas/progress/{project.id}"
                coach_name = coach.first_name + " " + coach.last_name
                message = f"Coachee has selected {coach_name.title()} for the Project - {project.name}"
                create_notification(pmo_user, path, message)
                learner = Learner.objects.get(id=request.data.get("learner_id"))
                message_for_hr = f"{learner.name.title()} has selected {coach_name.title()} as their coach for the project - {project.name} "
                create_notification(learner.user.user, path, message_for_hr)
                message_for_coach = f"Congratulations! Coachee has selected you as their coach for the Project - {project.name}"
                create_notification(coach.user.user, path, message_for_coach)
        except Exception as e:
            print(f"Error occurred while creating notification: {str(e)}")
        message = "Coach selected succesfully."
    else:
        message = "Coach rejected."
    return Response({"message": message}, status=200)


# @api_view(['POST'])
# def send_contract(request):
#     # Get all the Coach objects
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)

#     coach_statuses = project.coaches_status.filter(coach__id__in=request.data.get('coach_list',[]))
#     for status in coach_statuses:
#         status.status['contract']="sent"
#         status.save()

#     return Response({"message":"Contract sent successfully",'details':''},status=200)


# @api_view(['POST'])
# def approve_contract(request):
#     # Get all the Coach objects
#     try:
#         project = Project.objects.get(id=request.data.get('project_id',''))
#     except Project.DoesNotExist:
#         return Response({"message": "Project does not exist"}, status=400)

#     status = project.coaches_status.get(coach__id=request.data.get('coach_id',[]))
#     status.status['contract']="approved"
#     status.save()
#     return Response({"message":"Contract approved.",'details':''},status=200)


@api_view(["POST"])
def complete_cass_step(request):
    try:
        step = request.data.get("step")
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps[step]["status"] = "complete"
    project.save()
    return Response({"message": "Marked as completed."}, status=200)


@api_view(["POST"])
def mark_as_incomplete(request):
    stepList = [
        "coach_list",
        "coach_consent",
        "coach_list_to_hr",
        "interviews",
        "add_learners",
        "chemistry_session",
        "coach_selected",
        "final_coaches",
    ]
    try:
        step = request.data.get("step")
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    flag = False
    steps = project.steps
    for item in stepList:
        print(item == step)
        print(flag)
        if step == item:
            flag = True
        if flag:
            if (steps[item]["status"]) == "complete":
                steps[item]["status"] = "incomplete"
    # print(statuses)
    project.steps = steps
    project.save()
    return Response({"message": "Marked as Incomplete."}, status=200)


@api_view(["POST"])
def send_project_strure_to_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["project_structure"]["status"] = "complete"
    project.save()
    try:
        path = f"/projects/caas/progress/{project.id}"
        message = f"Project structure has been added to the project - {project.name}."
        create_notification(project.hr.first().user.user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Sent to HR."}, status=200)


@api_view(["POST"])
def send_reject_reason(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["project_structure"]["status"] = "pending"
    rejection = dict(
        reason=request.data.get("reject_reason", ""),
        project_structure=request.data.get("project_structure", []),
    )
    if "details" not in project.steps["project_structure"]:
        project.steps["project_structure"]["details"] = []
    project.steps["project_structure"]["details"].append(rejection)
    project.save()
    return Response({"message": "Rejected."}, status=200)


@api_view(["POST"])
def project_structure_agree_by_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["project_structure"]["status"] = "complete"
    project.save()
    return Response({"message": "Agreed."}, status=200)


@api_view(["POST"])
def request_more_profiles_by_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    if (
        request.data["step"] == "coach_list_to_hr"
        or request.data["step"] == "interviews"
    ):
        if "request_details" in project.steps["coach_consent"]:
            project.steps["coach_consent"]["request_details"].append(
                {"message": request.data["message"]}
            )
        else:
            project.steps["coach_consent"]["request_details"] = [
                {"message": request.data["message"]}
            ]
    project.steps["coach_consent"]["status"] = "incomplete"
    project.save()
    try:
        pmo_user = User.objects.filter(profile__type="pmo").first()
        if pmo_user:
            path = f"/projects/caas/progress/{project.id}"
            message = (
                f"HR has requested for more coach profiles for Project - {project.name}"
            )
            create_notification(pmo_user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Request sent successfully"})


@api_view(["POST"])
def edit_learner(request):
    try:
        learner = Learner.objects.get(id=request.data.get("learner_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Learner does not exist"}, status=400)
    user = learner.user.user
    user.username = request.data["email"]
    user.email = request.data["email"]
    user.save()
    learner.email = request.data["email"]
    learner.name = request.data["name"]
    learner.phone = request.data["phone"]
    learner.save()
    return Response({"message": "Learner details updated.", "details": ""}, status=200)


@api_view(["POST"])
def mark_finalized_list_complete(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.steps["final_coaches"]["status"] = "complete"
    project.save()
    return Response({"message": "Step marked as Complete", "details": ""}, status=200)


@api_view(["POST"])
def send_list_to_hr(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    # project.status['coach_list_to_hr'] = 'pending'

    for coach_id in request.data["coach_list"]:
        coach_status = project.coaches_status.get(coach__id=coach_id)
        print(coach_status.status)
        coach_status.status["hr"]["status"] = "sent"
        coach_status.save()
    project.save()
    try:
        path = f"/projects/caas/progress/{project.id}"
        message = f"Admin has shared {len(request.data['coach_list'])} coach profile with you for the Project - {project.name}."
        create_notification(project.hr.first().user.user, path, message)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Sent Successfully", "details": {}}, status=200)


@api_view(["POST"])
def finalized_coach_from_coach_consent(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)

    for coach_id in request.data["coach_list"]:
        coach_status = project.coaches_status.get(coach__id=coach_id)
        coach_status.status["hr"]["status"] = "select"
        coach_status.save()

    project.steps["coach_consent"]["status"] = "complete"
    project.save()

    return Response({"message": "Sent Successfully", "details": {}}, status=200)


@api_view(["GET"])
def get_coach_field_values(request):
    job_roles = set()
    languages = set()
    educations = set()
    locations = set()
    companies_worked_in = set()
    other_certifications = set()
    domains = set()
    industries = set()
    for coach in Coach.objects.all():
        # 1st coach
        for role in coach.job_roles:
            job_roles.add(role)
        for language in coach.language:
            languages.add(language)
        for location in coach.location:
            locations.add(location)
        for company in coach.companies_worked_in:
            companies_worked_in.add(company)
        for certificate in coach.other_certification:
            other_certifications.add(certificate)
        for industry in coach.area_of_expertise:
            industries.add(industry)
        domains.add(coach.domain)
        educations.add(coach.education)
    return Response(
        {
            "job_roles": list(job_roles),
            "languages": list(languages),
            "educations": list(educations),
            "locations": list(locations),
            "companies_worked_in": list(companies_worked_in),
            "other_certifications": list(other_certifications),
            "domains": list(domains),
            "industries": list(industries),
        },
        status=200,
    )


@api_view(["POST"])
def add_mulitple_coaches(request):
    # Get data from request
    coaches = request.data.get("coaches")

    # Check if coaches data is provided
    if not coaches or not isinstance(coaches, list):
        return Response(
            {"error": "Coaches data must be provided as a list."}, status=400
        )

    try:
        for coach_data in coaches:
            with transaction.atomic():
                # Extract coach details from the coach_data dictionary
                coach_id = coach_data.get("coach_id")
                first_name = coach_data.get("first_name")
                last_name = coach_data.get("last_name")
                age = coach_data.get("age", "")
                gender = coach_data.get("gender")
                level = coach_data.get("level")
                min_fees = coach_data.get("min_fees", "")
                active_inactive = coach_data.get("active_inactive")
                corporate_yoe = coach_data.get("corporate_yoe", "")
                coaching_yoe = coach_data.get("coaching_yoe", "")
                domain = coach_data.get("functional_domain", "")
                email = coach_data.get("email")
                phone = coach_data.get("mobile")
                job_roles = coach_data.get("job_roles", [])
                companies_worked_in = coach_data.get("companies_worked_in", [])
                language = coach_data.get("language", [])
                area_of_expertise = coach_data.get("industries", [])
                location = coach_data.get("location", [])
                linkedin_profile_link = coach_data.get("linkedin_profile", "")
                coaching_hours = coach_data.get("coaching_hours", "")
                fee_remark = coach_data.get("fee_remark", "")

                if coach_data.get("ctt_nctt") == "Yes":
                    ctt_nctt = True
                else:
                    ctt_nctt = False
                if coach_data.get("active_inactive") == "Yes":
                    active_inactive = True
                else:
                    active_inactive = False

                # Perform validation on required fields
                if not all(
                    [coach_id, first_name, last_name, gender, level, email, phone]
                ):
                    return Response(
                        {
                            "error": "All required fields must be provided for each coach."
                        },
                        status=400,
                    )

                # Create the Django User
                if coach_exists(coach_id):
                    return Response(
                        {"error": f"Coach with ID {coach_id} already exists."},
                        status=400,
                    )

                temp_password = "".join(
                    random.choices(
                        string.ascii_uppercase + string.ascii_lowercase + string.digits,
                        k=8,
                    )
                )
                user = User.objects.create_user(
                    username=email, password=temp_password, email=email
                )

                # Create the Coach Profile linked to the User
                coach_profile = Profile.objects.create(user=user, type="coach")

                # api call
                room_id = ""
                management_token = generateManagementToken()
                try:
                    response_from_100ms = requests.post(
                        "https://api.100ms.live/v2/rooms",
                        headers={
                            "Authorization": f"Bearer {management_token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "name": email.replace(".", "-").replace("@", ""),
                            "description": "This is a sample description for the room",
                            "region": "in",
                        },
                    )
                    if response_from_100ms.status_code == 200:
                        room_id = response_from_100ms.json().get("id")
                except Exception as e:
                    print(f"Error while generating meeting link, {str(e)}")

                # Create the Coach User using the Profile
                coach_user = Coach.objects.create(
                    user=coach_profile,
                    coach_id=coach_id,
                    first_name=first_name,
                    last_name=last_name,
                    age=age,
                    gender=gender,
                    level=level,
                    room_id=room_id,
                    min_fees=min_fees,
                    fee_remark=fee_remark,
                    ctt_nctt=ctt_nctt,
                    active_inactive=active_inactive,
                    years_of_corporate_experience=corporate_yoe,
                    years_of_coaching_experience=coaching_yoe,
                    domain=domain,
                    email=email,
                    phone=phone,
                    job_roles=job_roles,
                    companies_worked_in=companies_worked_in,
                    language=language,
                    area_of_expertise=area_of_expertise,
                    location=location,
                    linkedin_profile_link=linkedin_profile_link,
                    coaching_hours=coaching_hours,
                )

                # Approve coach
                coach = Coach.objects.get(id=coach_user.id)
                coach.is_approved = True
                coach.save()
        return Response({"message": "Coaches added successfully."}, status=201)
    except IntegrityError as e:
        print(e)
        return Response(
            {"error": "A coach user with this email already exists."}, status=400
        )

    except Exception as e:
        # Return error response if any other exception occurs
        print(e)
        return Response(
            {"error": "An error occurred while creating the coach user."}, status=500
        )


@api_view(["GET"])
def get_notifications(request, user_id):
    notifications = Notification.objects.filter(user__id=user_id).order_by(
        "-created_at"
    )
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(["PUT"])
def mark_notifications_as_read(request):
    notifications = Notification.objects.filter(
        read_status=False, user__id=request.data["user_id"]
    )
    notifications.update(read_status=True)
    return Response("Notifications marked as read.")


@api_view(["GET"])
def unread_notification_count(request, user_id):
    count = Notification.objects.filter(user__id=user_id, read_status=False).count()
    return Response({"count": count})


@api_view(["POST"])
def mark_project_as_sold(request):
    try:
        project = Project.objects.get(id=request.data.get("project_id", ""))
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    project.updated_to_sold = True
    project.steps["project_structure"]["status"] = "complete"
    project.save()
    try:
        path = f"/projects/caas/progress/{project.id}"
        message = f"Project structure has been added to the project - {project.name}."
        message_for_coach = f"Admin has added project structure. Please agree to the project structure to go forward with the Project - {project.name}"
        create_notification(project.hr.first().user.user, path, message)
        for coach_status in project.coaches_status.all():
            create_notification(coach_status.coach.user.user, path, message_for_coach)
    except Exception as e:
        print(f"Error occurred while creating notification: {str(e)}")
    return Response({"message": "Project marked as sold"}, status=200)


@api_view(["GET"])
def get_session_requests_of_user_on_date(request, user_type, user_id, date):
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    start_time = date_obj.replace(hour=0, minute=0, second=0)
    # Set the end time of the given date at 23:59:59
    end_time = date_obj.replace(hour=23, minute=59, second=59)
    # Convert the datetime objects to timestamps
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())

    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            hr__id=user_id,
            availibility__start_time__range=(start_timestamp, end_timestamp),
        )
    elif user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            learner__id=user_id,
            availibility__start_time__range=(start_timestamp, end_timestamp),
        )
    elif user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            coach__id=user_id,
            availibility__start_time__range=(start_timestamp, end_timestamp),
        )
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def request_reschedule(request, session_id):
    session = SessionRequestCaas.objects.get(id=session_id)
    session.reschedule_request.append(
        {
            "requested_by": "coach",
            "requested_on_timestamp": request.data["requested_on"],
            "message": request.data["message"],
        }
    )
    session.save()
    return Response({"message": "Requested for reschedule"})


@api_view(["POST"])
def reschedule_session(request):
    existing_session = SessionRequestCaas.objects.get(
        id=request.data["existing_session_id"]
    )
    existing_session.is_archive = True
    existing_session.save()
    time_arr = create_time_arr(request.data["availibility"])

    try:
        if request.data["session_type"] == "chemistry":
            session = SessionRequestCaas.objects.get(
                learner__id=request.data["learner_id"],
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        else:
            session = SessionRequestCaas.objects.get(
                project__id=request.data["project_id"],
                coach__id=request.data["coach_id"],
                session_type=request.data["session_type"],
                is_archive=False,
            )
        session.availibility.set(time_arr)
        session.save()
        return Response({"message": "Session updated successfully."}, status=201)
    except SessionRequestCaas.DoesNotExist:
        session = {
            "project": request.data["project_id"],
            "availibility": time_arr,
            "coach": request.data["coach_id"],
            "session_type": request.data["session_type"],
        }
        if session["session_type"] == "interview":
            session["hr"] = request.data["hr_id"]
        elif session["session_type"] == "chemistry":
            session["learner"] = request.data["learner_id"]
        session_serilizer = SessionRequestCaasSerializer(data=session)
        if session_serilizer.is_valid():
            session_created = session_serilizer.save()
            try:
                pmo_user = User.objects.filter(profile__type="pmo").first()
                project = Project.objects.get(id=request.data["project_id"])
                coach = Coach.objects.get(id=request.data["coach_id"])
                if pmo_user:
                    path = f"/projects/caas/progress/{project.id}"
                    coach_name = coach.first_name + " " + coach.last_name
                    slot_message = get_slot_message(request.data["availibility"])
                    if session["session_type"] == "interview":
                        message = f"HR has requested interview session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                        message_for_coach = f"HR has requested for {slot_message} for Interview for Project - {project.name}. Please book one of the requested slots now"
                    elif session["session_type"] == "chemistry":
                        hr_user_in_project = (
                            session_created.project.hr.first().user.user
                        )
                        message_for_hr = f"{session_created.learner.name.title()} has requested for Chemistry session to the Coach - {coach_name.title()} for {slot_message} for the Project - {project.name}"
                        message_for_coach = f"Coachee has requested {slot_message} for Chemistry session for the Project - {project.name}. Please book one of the requested slots now"
                        create_notification(hr_user_in_project, path, message_for_hr)
                        message = f"Coachee has requested chemistry session to {coach_name.title()} for Project - {project.name}. The requested slots are "
                    message += " " + slot_message
                    create_notification(pmo_user, path, message)
                    create_notification(coach.user.user, path, message_for_coach)
            except Exception as e:
                print(f"Error occurred while creating notification: {str(e)}")
            return Response({"message": "Session sequested successfully."}, status=201)
        else:
            return Response(
                {
                    "message": str(session_serilizer.errors),
                },
                status=401,
            )


@api_view(["GET"])
def get_engagement_in_projects(request, project_id):
    engagements = Engagement.objects.filter(project__id=project_id)
    serializer = EngagementDepthOneSerializer(engagements, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_learner_engagement_of_project(request, project_id, learner_id):
    engagement = Engagement.objects.get(learner__id=learner_id, project__id=project_id)
    serializer = EngagementDepthOneSerializer(engagement)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_learners_engagement(request, learner_id):
    engagements = Engagement.objects.filter(learner__id=learner_id)
    serializer = EngagementDepthOneSerializer(engagements, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def create_session_request_by_learner(request, session_id):
    # print(request.user)
    # if request.user.profile.type != "learner":
    #     return Response({"message": "Unauthorized"}, status=401)
    time_arr = create_time_arr(request.data["availibility"])
    session = SessionRequestCaas.objects.get(id=session_id)
    session.availibility.set(time_arr)
    session.status = "requested"
    session.save()
    return Response({"message": "Session requested successfully"})


@api_view(["GET"])
def get_session_requests_of_user(request, user_type, user_id):
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None) & ~Q(status="pending")
        )
    if user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None)
            & Q(learner__id=user_id)
            & ~Q(session_type="chemistry")
            & ~Q(status="pending")
        )
    if user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None) & Q(coach__id=user_id) & ~Q(status="pending")
        )
    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            Q(confirmed_availability=None)
            & Q(project__hr__id=user_id)
            & ~Q(status="pending")
        )
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_upcoming_sessions_of_user(request, user_type, user_id):
    current_time = int(timezone.now().timestamp() * 1000)
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            ~Q(status="completed"),
        )
    if user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            Q(learner__id=user_id),
            ~Q(session_type="chemistry"),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    if user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            Q(coach__id=user_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__gt=current_time),
            Q(project__hr__id=user_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_past_sessions_of_user(request, user_type, user_id):
    current_time = int(timezone.now().timestamp() * 1000)
    session_requests = []
    if user_type == "pmo":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
        )
    if user_type == "learner":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
            Q(learner__id=user_id),
            ~Q(session_type="chemistry"),
            Q(is_archive=False),
        )
    if user_type == "coach":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
            Q(coach__id=user_id),
            Q(is_archive=False),
        )
    if user_type == "hr":
        session_requests = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__end_time__lt=current_time)
            | Q(status="completed"),
            Q(project__hr__id=user_id),
            Q(is_archive=False),
        )
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def edit_session_status(request, session_id):
    try:
        session_request = SessionRequestCaas.objects.get(id=session_id)
    except SessionRequestCaas.DoesNotExist:
        return Response({"error": "Session request not found."}, status=404)
    new_status = request.data.get("status")
    if not new_status:
        return Response({"error": "Status field is required."}, status=400)
    session_request.status = new_status
    session_request.save()
    return Response({"message": "Session status updated successfully."}, status=200)


@api_view(["POST"])
def edit_session_availability(request, session_id):
    time_arr = create_time_arr(request.data["availibility"])
    try:
        # changing availability - edit request.
        session = SessionRequestCaas.objects.get(id=session_id)
        if session.is_booked:
            return Response({"message": "Session edit failed."}, status=401)
        session.availibility.set(time_arr)
        session.save()
        return Response({"message": "Session updated successfully."}, status=201)
    except:
        return Response({"message": "Session edit failed."}, status=401)


@api_view(["GET"])
def get_coachee_of_user(request, user_type, user_id):
    learners_data = []
    if user_type == "pmo":
        learners = Learner.objects.all()
    elif user_type == "coach":
        learners = Learner.objects.filter(engagement__coach__id=user_id).distinct()
    elif user_type == "hr":
        learners = Learner.objects.filter(
            engagement__project__hr__id=user_id
        ).distinct()
    for learner in learners:
        learner_dict = {
            "id": learner.id,
            "name": learner.name,
            "email": learner.email,
            "phone": learner.phone,
            "area_of_expertise": learner.area_of_expertise,
            "years_of_experience": learner.years_of_experience,
            "projects": [],
            "organisation": set(),
        }
        if user_type == "pmo":
            projects = Project.objects.filter(engagement__learner=learner)
        elif user_type == "coach":
            projects = Project.objects.filter(
                Q(engagement__learner=learner) & Q(engagement__coach__id=user_id)
            )
        elif user_type == "hr":
            projects = Project.objects.filter(
                Q(engagement__learner=learner) & Q(hr__id=user_id)
            )
        # project_data = []
        # organisation = set()
        for project in projects:
            project_dict = {
                "name": project.name,
            }
            learner_dict["organisation"].add(project.organisation.name)
            learner_dict["projects"].append(project_dict)
        learners_data.append(learner_dict)
    # serializer = LearnerSerializer(learners,many=True)
    return Response(learners_data)


@api_view(["GET"])
def get_learner_data(request, learner_id):
    learner = Learner.objects.get(id=learner_id)
    serializer = LearnerSerializer(learner)
    return Response(serializer.data)


# updating the availability and coach in the first pending chemistry available for learner
@api_view(["POST"])
def request_chemistry_session(request, project_id, learner_id):
    session = SessionRequestCaas.objects.filter(
        learner__id=learner_id,
        project__id=project_id,
        session_type="chemistry",
        status="pending",
    )
    print(session)
    if len(session) == 0:
        return Response({"error": "Max sessions exceeded."}, status=400)
    else:
        coach = Coach.objects.get(id=request.data["coach_id"])
        time_arr = create_time_arr(request.data["availibility"])
        session_to_update = session[0]
        session_to_update.availibility.set(time_arr)
        session_to_update.coach = coach
        session_to_update.status = "requested"
        session_to_update.save()
        path_for_coach = f"/sessions"
        slot_message = get_slot_message(request.data["availibility"])
        message_for_coach = f"Coachee has requested {slot_message} for Chemistry session for the Project - {session_to_update.project.name}. Please book one of the requested slots now"
        create_notification(coach.user.user, path_for_coach, message_for_coach)
    return Response({"message": "Session requested successfully"}, status=200)


@api_view(["GET"])
def get_learner_sessions_in_project(request, project_id, learner_id):
    sessions = SessionRequestCaas.objects.filter(
        project__id=project_id, learner__id=learner_id
    ).order_by("order")
    serializer = SessionRequestCaasDepthOneSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def request_session(request, session_id, coach_id):
    session = SessionRequestCaas.objects.get(id=session_id)
    coach = Coach.objects.get(id=coach_id)
    time_arr = create_time_arr(request.data["availibility"])
    session.availibility.set(time_arr)
    session.coach = coach
    session.status = "requested"
    session.save()
    return Response({"message": "Session requested successfully"}, status=200)


@api_view(["POST"])
def reschedule_session_of_coachee(request, session_id):
    session = SessionRequestCaas.objects.get(id=session_id)
    session.is_archive = True
    time_arr = create_time_arr(request.data["availibility"])
    new_session = SessionRequestCaas.objects.create(
        learner=session.learner,
        project=session.project,
        coach=session.coach,
        session_type=session.session_type,
        status="requested",
        session_number=session.session_number,
        session_duration=session.session_duration,
        order=session.order,
    )
    new_session.availibility.set(time_arr)
    new_session.save()
    session.save()
    return Response({"message": "Session reschedule successfully"}, status=200)


@api_view(["POST"])
def create_goal(request):
    serializer = GoalSerializer(data=request.data)
    goal_name = request.data["name"]
    if not Goal.objects.filter(
        name=goal_name, engagement__id=request.data["engagement"]
    ).exists():
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Goal created successfully."}, status=201)
        return Response(serializer.errors, status=400)
    else:
        return Response({"error": "Goal already exists"}, status=400)


@api_view(["GET"])
def get_engagement_goals(request, engagement_id):
    goals = Goal.objects.filter(engagement__id=engagement_id)
    serializer = GetGoalSerializer(goals, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def edit_goal(request, goal_id):
    try:
        goal = Goal.objects.get(id=goal_id)
    except Goal.DoesNotExist:
        return Response({"error": "Goal not found."}, status=404)

    serializer = GoalSerializer(instance=goal, data=request.data)
    goal_name = request.data.get("name", goal.name)
    engagement_id = request.data.get("engagement", goal.engagement.id)

    if (
        not Goal.objects.filter(name=goal_name, engagement_id=engagement_id)
        .exclude(id=goal_id)
        .exists()
    ):
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Goal updated successfully."}, status=200)
        return Response(serializer.errors, status=400)
    else:
        return Response(
            {
                "error": "Another goal with the same name already exists in the engagement."
            },
            status=400,
        )


@api_view(["POST"])
def create_competency(request):
    serializer = CompetencySerializer(data=request.data)
    if serializer.is_valid():
        competency = serializer.save()
        return Response(
            {"message": "Competency added successfully"},
            status=201,
        )
    return Response(
        serializer.errors, {"error": "Competency was not added"}, status=400
    )


@api_view(["POST"])
def edit_competency(request, competency_id):
    try:
        competency = Competency.objects.get(id=competency_id)
    except Competency.DoesNotExist:
        return Response({"error": "Competency not found."}, status=404)

    serializer = CompetencySerializer(instance=competency, data=request.data)
    competency_name = request.data["name"]
    if (
        not Competency.objects.filter(name=competency_name, goal__id=competency.goal.id)
        .exclude(id=competency.goal.id)
        .exists()
    ):
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Competency updated successfully."}, status=200)
        return Response(serializer.errors, status=400)
    else:
        return Response(
            {
                "error": "Another competency with the same name already exists in the goal."
            },
            status=400,
        )


@api_view(["GET"])
def get_engagement_competency(request, engagement_id):
    competentcy = Competency.objects.filter(goal__engagement__id=engagement_id)
    serializer = CompetencyDepthOneSerializer(competentcy, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def add_score_to_competency(request, competency_id):
    try:
        competency = Competency.objects.get(id=competency_id)
        scoring_data = {
            "date": request.data.get("date"),
            "score": request.data.get("score"),
        }
        competency.scoring.append(scoring_data)
        competency.save()
        return Response(
            {"message": "Competency scoring updated successfully."}, status=201
        )
    except Competency.DoesNotExist:
        return Response({"error": "Competency not found."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
def get_competency_by_goal(request, goal_id):
    competentcy = Competency.objects.filter(goal__id=goal_id)
    serializer = CompetencyDepthOneSerializer(competentcy, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def create_action_item(request):
    serializer = ActionItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Action created successfully."}, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
def get_engagement_action_items(request, engagement_id):
    action_items = ActionItem.objects.filter(
        competency__goal__engagement__id=engagement_id
    )
    serializer = GetActionItemDepthOneSerializer(action_items, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_action_items_by_competency(request, competency_id):
    action_items = ActionItem.objects.filter(competency__id=competency_id)
    serializer = GetActionItemDepthOneSerializer(action_items, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def edit_action_item(request, action_item_id):
    try:
        action_item = ActionItem.objects.get(id=action_item_id)
    except ActionItem.DoesNotExist:
        return Response({"error": "Action item not found."}, status=404)
    serializer = ActionItemSerializer(instance=action_item, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Action item updated successfully."}, status=200)
    return Response(serializer.errors, status=400)


@api_view(["POST"])
def mark_session_as_complete(request, session_id):
    try:
        session = SessionRequestCaas.objects.get(id=session_id)
    except ActionItem.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)
    session.status = "completed"
    session.save()
    return Response({"message": "Session marked as complete."}, status=201)


@api_view(["POST"])
def complete_engagement(request, engagement_id):
    try:
        engagement = Engagement.objects.get(id=engagement_id)
    except Engagement.DoesNotExist:
        return Response({"error": "Engagement not found."}, status=404)
    engagement.status = "completed"
    engagement.save()
    return Response({"message": "Engagement is completed."}, status=201)


@api_view(["GET"])
def get_all_competencies(request):
    competencies = Competency.objects.all()
    competency_list = []

    for competency in competencies:
        goal_name = (competency.goal.name if competency.goal else "N/A",)
        project_name = (
            competency.goal.engagement.project.name
            if competency.goal and competency.goal.engagement.project
            else "N/A"
        )
        coachee_name = (
            competency.goal.engagement.learner.name
            if competency.goal and competency.goal.engagement.learner
            else "N/A"
        )
        competency_data = {
            "id": competency.id,
            "goal_id": goal_name,
            "name": competency.name,
            "scoring": competency.scoring,
            "created_at": competency.created_at.isoformat(),
            "project_name": project_name,
            "learner_name": coachee_name,
        }
        competency_list.append(competency_data)

    return Response({"competencies": competency_list})


@api_view(["GET"])
def get_current_session(request, user_type, room_id, user_id):
    five_minutes_in_milliseconds = 300000
    current_time = int(timezone.now().timestamp() * 1000)
    five_minutes_plus_current_time = current_time + five_minutes_in_milliseconds
    if user_type == "coach":
        sessions = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
            & Q(confirmed_availability__end_time__gt=current_time),
            Q(coach__id=user_id),
            Q(coach__room_id=room_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    elif user_type == "learner":
        sessions = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
            & Q(confirmed_availability__end_time__gt=current_time),
            Q(learner__id=user_id),
            Q(coach__room_id=room_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    elif user_type == "hr":
        sessions = SessionRequestCaas.objects.filter(
            Q(is_booked=True),
            Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
            & Q(confirmed_availability__end_time__gt=current_time),
            Q(hr__id=user_id),
            Q(coach__room_id=room_id),
            Q(is_archive=False),
            ~Q(status="completed"),
        )
    if len(sessions) == 0:
        return Response({"error": "You don't have any sessions right now."}, status=404)
    return Response({"message": "success"}, status=200)


# @api_view(["POST"])
# def get_current_session_of_stakeholder(request, room_id):
#     five_minutes_in_milliseconds = 300000
#     current_time = int(timezone.now().timestamp() * 1000)
#     five_minutes_plus_current_time = current_time + five_minutes_in_milliseconds
#     sessions = SessionRequestCaas.objects.filter(
#         Q(is_booked=True),
#         Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
#         & Q(confirmed_availability__end_time__gt=current_time),
#         Q(coach__room_id=room_id),
#         Q(session_type="tripartite")
#         | Q(session_type="mid_review")
#         | Q(session_type="end_review"),
#         Q(invitees__contains=request.data["email"]),
#         Q(is_archive=False),
#         ~Q(status="completed"),
#     )
#     if len(sessions) == 0:
#         return Response({"error": "You don't have any sessions right now."}, status=404)
#     return Response({"message": "success"}, status=200)


@api_view(["POST"])
def get_current_session_of_stakeholder(request, room_id):
    five_minutes_in_milliseconds = 300000
    current_time = int(timezone.now().timestamp() * 1000)
    five_minutes_plus_current_time = current_time + five_minutes_in_milliseconds
    sessions = SessionRequestCaas.objects.filter(
        Q(is_booked=True),
        Q(confirmed_availability__start_time__lt=five_minutes_plus_current_time)
        & Q(confirmed_availability__end_time__gt=current_time),
        (Q(coach__room_id=room_id) | Q(pmo__room_id=room_id)),
        Q(session_type="tripartite")
        | Q(session_type="mid_review")
        | Q(session_type="end_review")  | Q(session_type="stakeholder_without_coach"),
        Q(invitees__contains=request.data["email"]),
        Q(is_archive=False),
        ~Q(status="completed"),
    )
    if len(sessions) == 0:
        return Response({"error": "You don't have any sessions right now."}, status=404)
    return Response({"message": "success"}, status=200)


# @api_view(["POST"])
# def schedule_session_directly(request, session_id):
#     try:
#         session = SessionRequestCaas.objects.get(id=session_id)
#     except SessionRequestCaas.DoesNotExist:
#         return Response({"error": "Session not found."}, status=404)
#     time_arr = create_time_arr(request.data.get("availability", []))
#     if len(time_arr) == 0:
#         return Response({"error": "Please provide the availability."}, status=404)
#     availability = Availibility.objects.get(id=time_arr[0])
#     coach = Coach.objects.get(id=request.data["coach_id"])
#     session.availibility.add(availability)
#     session.confirmed_availability = availability
#     session.is_booked = True
#     session.coach = coach
#     session.status = "booked"
#     for email in request.data.get("invitees", []):
#         session.invitees.append(email.strip())
#     session.save()
#     return Response({"message": "Session booked successfully."})

@api_view(["POST"])
def schedule_session_directly(request, session_id):
    try:
        session = SessionRequestCaas.objects.get(id=session_id)
    except SessionRequestCaas.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)

    time_arr = create_time_arr(request.data.get("availability", []))
    if len(time_arr) == 0:
        return Response({"error": "Please provide the availability."}, status=404)

    availability = Availibility.objects.get(id=time_arr[0])
    if request.data["user_type"] == 'pmo':
        pmo = Pmo.objects.get(id=request.data["user_id"])
        session.pmo = pmo 
    
    if request.data["user_type"] == 'coach':
        coach = Coach.objects.get(id=request.data["user_id"])
        session.coach = coach
    
    session.availibility.add(availability)
    session.confirmed_availability = availability
    session.is_booked = True
    
    session.status = "booked"

    for email in request.data.get("invitees", []):
        session.invitees.append(email.strip())
    session.save()

    return Response({"message": "Session booked successfully."})

@api_view(["POST"])
def delete_learner_from_project(request, engagement_id):
    try:
        engagement = Engagement.objects.get(id=engagement_id)
    except Engagement.DoesNotExist:
        return Response({"error": "Learner not found in project."}, status=404)
    try:
        print("outside the for loop ")
        # removing the learner id from the project coaches statuses
        for coach_statuses in engagement.project.coaches_status.all():
            print("inside for loop")
            if engagement.learner.id in coach_statuses.learner_id:
                coach_statuses.learner_id.remove(engagement.learner.id)
            coach_statuses.save()
        sessions_to_delete = SessionRequestCaas.objects.filter(
            learner__id=engagement.learner.id, project__id=engagement.project.id
        )
        sessions_to_delete.delete()
        engagement.delete()
        return Response({"message": "Learner deleted successfully"})
    except Exception as e:
        print(str(e))
        return Response(
            {"error": "Failed to remove learner from the project."}, status=400
        )


@api_view(["GET"])
def get_competency_averages(request, hr_id):
    # Step 1: Retrieve the data from the Competency model
    competencies = Competency.objects.filter(goal__engagement__project__hr__id=hr_id)
    # Step 2 and 3: Calculate the average score for each competency and store in a dictionary
    competency_averages = defaultdict(lambda: {"total_score": 0, "count": 0})
    for competency in competencies:
        competency_name = competency.name
        scoring_data = competency.scoring
        if scoring_data:
            total_score = sum(entry["score"] for entry in scoring_data)
            count = len(scoring_data)
            competency_averages[competency_name]["total_score"] += total_score
            competency_averages[competency_name]["count"] += count
    # Step 4: Calculate the final average for each competency, considering competencies with the same name
    final_averages = {}
    for competency_name, data in competency_averages.items():
        total_score = data["total_score"]
        count = data["count"]
        average_score = total_score / count if count > 0 else 0
        final_averages[competency_name] = average_score
    top_5_competencies = dict(
        sorted(final_averages.items(), key=lambda item: item[1], reverse=True)[:5]
    )
    return Response(top_5_competencies, status=200)


@api_view(["GET"])
def get_upcoming_session_count(request, hr_id):
    current_time = int(timezone.now().timestamp() * 1000)
    session_requests = []
    # Get the start and end of the current month
    current_month = timezone.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    current_month_timestamp = int(current_month.timestamp() * 1000)
    next_month = current_month.replace(month=current_month.month + 1, day=1)
    if current_month.month == 12:  # Handle December case
        next_month = next_month.replace(year=current_month.year + 1)
    next_month_timestamp = int(next_month.timestamp() * 1000)
    session_requests = SessionRequestCaas.objects.filter(
        Q(is_booked=True),
        Q(confirmed_availability__end_time__gt=current_time),
        Q(confirmed_availability__end_time__gte=current_month_timestamp),
        Q(confirmed_availability__end_time__lt=next_month_timestamp),
        Q(project__hr__id=hr_id),
        Q(is_archive=False),
        ~Q(status="completed"),
    )
    upcoming_session_count = session_requests.count()
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(
        {
            "upcoming_sessions": serializer.data,
            "upcoming_session_count": upcoming_session_count,
        },
        status=200,
    )


@api_view(["GET"])
def get_requests_count(request, hr_id):
    session_requests = SessionRequestCaas.objects.filter(
        Q(confirmed_availability=None) & Q(project__hr__id=hr_id) & ~Q(status="pending")
    )
    requests_count = session_requests.count()
    serializer = SessionRequestCaasDepthOneSerializer(session_requests, many=True)
    return Response(
        {
            "requestes": serializer.data,
            "requests_count": requests_count,
        },
        status=200,
    )


@api_view(["GET"])
def get_learners_without_sessions(request, hr_id):
    # Get the learners associated with the given hr_id who don't have any sessions with status = "requested" or "booked".
    learners = (
        Learner.objects.filter(engagement__project__hr__id=hr_id)
        .exclude(sessionrequestcaas__status__in=["requested", "booked"])
        .distinct()
    )
    # Serialize the filtered learner data.
    learners_count = learners.count()
    serializer = LearnerSerializer(learners, many=True)
    return Response(
        {"learners": serializer.data, "learners_count": learners_count}, status=200
    )


@api_view(["POST"])
def select_coach_for_coachee(request):
    try:
        coach_status = CoachStatus.objects.get(id=request.data["coach_status_id"])
    except CoachStatus.DoesNotExist:
        return Response({"error": "Coach not found"}, status=404)
    try:
        engagement = Engagement.objects.get(id=request.data["engagement_id"])
    except Engagement.DoesNotExist:
        return Response({"error": "Unable to find learner"}, status=404)
    coach_status.learner_id.append(engagement.learner.id)
    coach_status.save()
    engagement.coach = coach_status.coach
    engagement.save()
    return Response({"message": "Coach finalized for coachee"}, status=201)


@api_view(["POST"])
def add_past_session(request, session_id, coach_id):
    try:
        session = SessionRequestCaas.objects.get(id=session_id)
    except SessionRequestCaas.DoesNotExist:
        return Response({"error": "Session not found."}, status=404)
    time_arr = create_time_arr(request.data.get("availability", []))
    if len(time_arr) == 0:
        return Response({"error": "Please provide the availability."}, status=404)
    availability = Availibility.objects.get(id=time_arr[0])
    coach = Coach.objects.get(id=coach_id)
    session.availibility.add(availability)
    session.confirmed_availability = availability
    session.is_booked = True
    session.coach = coach
    session.status = "completed"
    for email in request.data.get("invitees", []):
        session.invitees.append(email.strip())
    session.save()
    return Response({"message": "Session booked successfully."})