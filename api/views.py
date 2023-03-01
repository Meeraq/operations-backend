from datetime import date
from os import name
from django.shortcuts import render, get_object_or_404
from django.db import transaction,IntegrityError
from django.core.mail import EmailMessage
from rest_framework.exceptions import ParseError, ValidationError
from operationsBackend import settings
from .serializers import CoachSerializer,LearnerSerializer,ProjectSerializer,ProjectDepthTwoSerializer,SessionRequestSerializer,AvailibilitySerializer,SessionRequestDepthOneSerializer,SessionSerializer,SessionsDepthTwoSerializer
from django.utils.crypto import get_random_string
import jwt
import uuid
from django.db.models import IntegerField
from django.db.models.functions import Cast
from rest_framework.exceptions import AuthenticationFailed
from datetime import datetime, timedelta
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from .models import Profile, Pmo, Coach, OTP, Learner, Project, Organisation, HR, Availibility,SessionRequest, Session
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.mail import send_mail

from django.utils import timezone


# Create your views here.

import environ

from api import serializers

env = environ.Env()

# Create pmo user
@api_view(['POST'])
def create_pmo(request):
    # Get data from request
    name = request.data.get('name')
    email = request.data.get('email')
    phone = request.data.get('phone')
    username = request.data.get('email') # username and email are same
    password = request.data.get('password')
    # Check if required data is provided
    if not all([name, email, phone, username, password]):
        return Response({'error': 'All required fields must be provided.'}, status=400)

    try:
        with transaction.atomic():
            # Create the Django User
            user = User.objects.create_user(username=username, password=password,email=email)
            # Create the PMO Profile linked to the User
            pmo_profile = Profile.objects.create(user=user, type='pmo')
            # Create the PMO User using the Profile
            pmo_user = Pmo.objects.create(user=pmo_profile, name=name, email=email, phone=phone)
        # Return success response
        return Response({'message': 'PMO user created successfully.'}, status=201)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def coach_signup(request):
    # Get data from request
    name = request.data.get('name')
    email = request.data.get('email')
    meet_link = request.data.get('meet_link')
    phone = request.data.get('phone')
    level = request.data.get('level')
    rating = request.data.get('rating')
    area_of_expertise = request.data.get('area_of_expertise')
    username = request.data.get('email') # keeping username and email same
    password = request.data.get('password')


    # Check if required data is provided
    if not all([name, email, meet_link, phone, level, area_of_expertise, username, password]):
        return Response({'error': 'All required fields must be provided.'}, status=400)

    try:
        # Create the Django User
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password,email=email)

            # Create the Coach Profile linked to the User
            coach_profile = Profile.objects.create(user=user, type='coach')

            # Create the Coach User using the Profile
            coach_user = Coach.objects.create(user=coach_profile, name=name, email=email, meet_link=meet_link, phone=phone, level=level, rating=rating, area_of_expertise=area_of_expertise)

						# approve coach
            coach = Coach.objects.get(id=coach_user.id)
            # Change the is_approved field to True
            coach.is_approved = True
            coach.save()	
            

            # Send email notification to the coach
            subject = 'Welcome to our coaching platform'
            message = f'Dear {name},\n\nThank you for signing up to our coaching platform. Your profile has been registered and approved by PMO. Best of luck!'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            # Send email notification to the admin
            admin_email = 'jatin@meeraq.com'
            admin_message = f'A new coach {name} has signed up on our coaching platform. Please login to the admin portal to review and approve their profile.'
            send_mail(subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email])			

            # Return success response
        return Response({'message': 'Coach user created successfully.'}, status=201)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({'error': str(e)}, status=500)


@api_view(['PUT'])
def approve_coach(request, coach_id):
    try:
        # Get the Coach object
        coach = Coach.objects.get(id=coach_id)

        # Change the is_approved field to True
        coach.is_approved = True
        coach.save()

        # Return success response
        return Response({'message': 'Coach approved successfully.'}, status=200)

    except Coach.DoesNotExist:
        # Return error response if Coach with the provided ID does not exist
        return Response({'error': 'Coach does not exist.'}, status=404)

    except Exception as e:
        # Return error response if any other exception occurs
        return Response({'error': str(e)}, status=500)



@api_view(['GET'])
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
        return Response({'error': str(e)}, status=500)



@api_view(['POST'])
def pmo_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if email is None or password is None:
        return Response({'error': 'Please provide both email and password'},
                        status=400)

    user = authenticate(username=email, password=password,type="pmo")
    if not user:
        return Response({'error': 'Invalid credentials'},
                        status=401)

    token, _ = Token.objects.get_or_create(user=user)
    pmo = Pmo.objects.get(user=user.profile)

    return Response({
        'token': token.key,
        'pmo': {
            'name': pmo.name,
            'email': pmo.email,
            'phone': pmo.phone
        }
    })



@api_view(['POST'])
def coach_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if email is None or password is None:
        return Response({'error': 'Please provide both email and password'},
                        status=400)

    user = authenticate(username=email, password=password)

    if not user:
        return Response({'error': 'Invalid credentials'},
                        status=401)

    try:
        coach = Coach.objects.get(user=user.profile)
    except Coach.DoesNotExist:
        return Response({'error': 'Coach not found'},
                        status=404)

    # Return the coach information in the response
    coach_data = {
        'id': coach.id,
        'name': coach.name,
        'email': coach.email,
        'meet_link': coach.meet_link,
        'phone': coach.phone,
        'level': coach.level,
        'rating': coach.rating,
        'area_of_expertise': coach.area_of_expertise,
        'completed_sessions': coach.completed_sessions,
        'is_approved': coach.is_approved
    }
    
    return Response({'coach': coach_data}, status=200)


def generateManagementToken():
    expires = 24 * 3600
    now = datetime.utcnow()
    exp = now + timedelta(seconds=expires)
    return jwt.encode(payload={
        'access_key': env('100MS_APP_ACCESS_KEY'),
        'type': 'management',
        'version': 2,
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': exp,
        'nbf': now
    }, key=env('100MS_APP_SECRET'))


@api_view(["GET"])
def getManagementToken(request):
    management_token = generateManagementToken()
    return Response({"message": "Success", "management_token": management_token}, status=200)


@api_view(['POST'])
def create_user_without_password(request):
    try:
        with transaction.atomic():
            # Check if username field is provided
            if 'username' not in request.data:
                raise ValueError('Username field is required')
            # Create user object with unusable password
            user = User.objects.create_user(
                username=request.data['username'],
                email=request.data['username'])
            user.set_unusable_password()
            user.save()

            # Create the learner profile
            learner_profile = Profile.objects.create(user=user, type='learner')

            # Create the learner object
            learner = Learner.objects.create(user=learner_profile, name=request.data.get('name'), email=request.data['username'], phone=request.data.get('phone'))

            # Return success response
            return Response({}, status=200)

    except ValueError as e:
        # Handle missing or invalid request data
        return Response({'error': str(e)}, status=400)

    except IntegrityError:
        # Handle username or email already exists
        return Response({'error': 'Username or email already exists'}, status=409)

    except Exception as e:
        # Handle any other exceptions
        transaction.set_rollback(True) # Rollback the transaction
        return Response({'error': str(e)}, status=500) 


@api_view(['POST'])
def otp_generation(request):
    try:
        learner = Learner.objects.get(email=request.data['email'])
        try:
            # Check if OTP already exists for the learner
            otp_obj = OTP.objects.get(learner=learner)
            otp_obj.delete()
        except OTP.DoesNotExist:
            pass

        # Generate OTP and save it to the database
        otp = get_random_string(length=6, allowed_chars='0123456789')
        created_otp = OTP.objects.create(learner=learner, otp=otp)

        return Response({'success': True,'otp':created_otp.otp})

    except Learner.DoesNotExist:
        # Handle the case where the learner with the given email does not exist
        return Response({'error': 'Learner with the given email does not exist.'}, status=400)

    except Exception as e:
        # Handle any other exceptions
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def otp_validation(request):
    otp_obj = OTP.objects.filter(learner__email=request.data['email'], otp=request.data['otp']).order_by('-created_at').first()

    if otp_obj is None:
        raise AuthenticationFailed('Invalid OTP')

    learner = otp_obj.learner
    token, created = Token.objects.get_or_create(user=learner.user.user)

    # Delete the OTP object after it has been validated
    otp_obj.delete()

    learner_data = {'id':learner.id,'name':learner.name,'email': learner.email,'phone': learner.email, 'token': token.key}

    return Response({ 'learner': learner_data},status=200)


@api_view(['POST'])
def create_project(request):
    organisation= Organisation(
        name=request.data['organisation_name'], image_url=request.data['image_url']
    )
    organisation.save()
    project= Project(
        name=request.data['project_name'],
        organisation=organisation,
        total_sessions=request.data['total_session'],
        cost_per_session=request.data['cost_per_session'],
        sessions_per_employee=request.data['sessions_per_employee']
    )
    project.save()
    for coach in request.data["coach_id"]:
        single_coach = Coach.objects.get(id=coach)
        project.coaches.add(single_coach)

    try:
        learners = create_learners(request.data['learners'])
        for learner in learners:
            project.learner.add(learner)
    except Exception as e:
        # Handle any exceptions from create_learners
        return Response({'error': str(e)}, status=500)

    return Response({'message': "Project saved Successfully"}, status=200)


def create_learners(learners_data):
    try:
        with transaction.atomic():
            if not learners_data:
                raise ValueError('Learners data is required')
            learners = []
            for learner_data in learners_data:
                # Check if username field is provided
                if 'email' not in learner_data:
                    raise ValueError('Username field is required')

                # Check if user already exists
                user = User.objects.filter(username=learner_data['email']).first()
                if user:
                    # If user exists, check if learner already exists
                    learner_profile = Profile.objects.filter(user=user, type='learner').first()
                    if learner_profile:
                        learners.append(learner_profile.learner)
                        continue

                # If learner does not exist, create the user object with an unusable password
                user = User.objects.create_user(
                    username=learner_data['email'],
                    email=learner_data.get('email', learner_data['email'])
                    )
                user.set_unusable_password()
                user.save()

                # Create the learner profile
                learner_profile = Profile.objects.create(user=user, type='learner')

                # Create the learner object
                learner = Learner.objects.create(user=learner_profile, name=learner_data.get('name'), email=learner_data['email'], phone=learner_data.get('phone'))
                learners.append(learner)

            # Return response with learners created or already existing
            serializer = LearnerSerializer(learners, many=True)
            return learners

    except ValueError as e:
        # Handle missing or invalid request data
        raise ValueError(str(e))

    except Exception as e:
        # Handle any other exceptions
        transaction.set_rollback(True) # Rollback the transaction
        raise Exception(str(e))

# Create learner user
@api_view(['POST'])
def create_learner(request):
    # Get data from request
    name = request.data.get('name')
    email = request.data.get('email')
    phone = request.data.get('phone')
    area_of_expertise= request.data.get('area_of_expertise')
    years_of_experience=request.data.get('years_of_experience')
    username = request.data.get('email') # username and email are same
    password = request.data.get('password')
    # Check if required data is provided
    if not all([name, email, phone, area_of_expertise, years_of_experience, username, password]):
        return Response({'error': 'All required fields must be provided.'}, status=400)

    try:
        with transaction.atomic():
            # Create the Django User
            user = User.objects.create_user(username=username, password=password,email=email)
            # Create the learner Profile linked to the User
            learner_profile = Profile.objects.create(user=user, type='learner')
            # Create the learner User using the Profile
            learner = Learner.objects.create(user=learner_profile, name=name, email=email, phone=phone)
        # Return success response
        return Response({'message': 'Learner user created successfully.'}, status=201)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({'error': str(e)}, status=500)


@api_view(["POST"])
def get_coaches_by_project(request):
    project_id = request.data['project_id']
    project= Project.objects.get(id=project_id)
    coaches= project.coaches.name
    return Response({"message": "Success"}, status=200)

@api_view(["POST"])
def get_learners_by_project(request):
    project_id = request.data['project_id']
    project= Project.objects.get(id=project_id)
    learner= project.learner.name
    return Response({"message": "Success"}, status=200)
    

#get projects details


@api_view(["GET"])
def project_details(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"message": "Project does not exist"}, status=400)
    serializer =  ProjectDepthTwoSerializer(project)
    return Response(serializer.data, status=200)


@api_view(['GET'])
def get_projects(request):
    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_projects_of_learner(request,learner_id):
    projects = Project.objects.filter(learner__id = learner_id)
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_session_request(request):
    time_arr = []
    for time in request.data['availibility']:
        availibility_serilizer = AvailibilitySerializer(data = time)
        if availibility_serilizer.is_valid():
            avil_id = availibility_serilizer.save()
            time_arr.append(avil_id.id) 
        else:
            return Response({"message": str(availibility_serilizer.errors),}, status=401)
    session = {
           "learner": request.data['learner'],
           "project": request.data['project'],
           "availibility":time_arr
		      }
    session_serilizer = SessionRequestSerializer(data = session)
    if session_serilizer.is_valid():
        session_serilizer.save()
        return Response({"message": "Success"}, status=201)
    else:
        return Response({"message": str(session_serilizer.errors),}, status=401)
   

#Coach- view session request
@api_view(["GET"])
def session_requests_by_coach(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)
    session_requests = SessionRequest.objects.filter(project__coaches=coach, is_booked=False)
    serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
    return Response(serializer.data, status=200)

@api_view(['POST'])
def book_session(request):
    serializer = SessionSerializer(data=request.data)
    if serializer.is_valid():
        session = serializer.save()
        # Mark the session request as booked
        session_request = session.session_request
        session_request.is_booked = True
        session_request.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
    

@api_view(["GET"])
def get_upcoming_session_coach(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)
    current_timestamp =  int(timezone.now().timestamp() * 1000)
    sessions = Session.objects.annotate(start_time_int=Cast('confirmed_availability__start_time', IntegerField()))
    res = sessions.filter(coach=coach,start_time_int__gt=current_timestamp)
    # print((res[0].start_time_int < current_timestamp),'res')
    serializer = SessionsDepthTwoSerializer(res, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_past_session_coach(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)
    current_timestamp = int(timezone.now().timestamp() * 1000)
    sessions = Session.objects.annotate(start_time_int=Cast('confirmed_availability__start_time', IntegerField())).filter(start_time_int__lt=current_timestamp,coach=coach)
    serializer = SessionsDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)



@api_view(["GET"])
def get_upcoming_session_learner(request, learner_id):
    learner = get_object_or_404(Learner, id=learner_id)
    current_timestamp =  int(timezone.now().timestamp() * 1000)
    sessions = Session.objects.annotate(start_time_int=Cast('confirmed_availability__start_time', IntegerField())).filter(start_time_int__gt=current_timestamp,session_request__learner=learner)
    serializer = SessionsDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_past_session_learner(request, learner_id):
    learner = get_object_or_404(Learner, id=learner_id)
    current_timestamp = int(timezone.now().timestamp() * 1000)
    sessions = Session.objects.annotate(start_time_int=Cast('confirmed_availability__start_time', IntegerField())).filter(start_time_int__lt=current_timestamp,session_request__learner=learner)
    serializer = SessionsDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)

@api_view(["POST"])
def add_learner(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise ParseError("Invalid project id provided.")

    email = request.data.get('email')
    if not email:
        raise ValidationError("Email is required.")

    with transaction.atomic():
        # Create user and learner profile
        user = User.objects.create_user(username=email, email=email)
        learner_profile = Profile.objects.create(user=user, type='learner')

        # Create learner
        learner_data = {'name': request.data.get('name'), 'email': email, 'phone': request.data.get('phone')}
        learner = Learner.objects.create(user=learner_profile, **learner_data)

        # Add learner to project
        project.learner.add(learner)
        project.save()

    serializer = ProjectSerializer(project)
    return Response(serializer.data, status=201)

# def add_learner(request, project_id):
#     project= Project.objects.get(id=project_id)

#     user = User.objects.create_user(
#         username=request.data['email'],
#         email= request.data['email']
#         )
#     user.set_unusable_password()
#     user.save()

#     # Create the learner Profile linked to the User
#     learner_profile = Profile.objects.create(user=user, type='learner')
#     # Create the learner User using the Profile
#     learner = Learner.objects.create(user=learner_profile, name=request.data['name'], email=request.data['email'], phone=request.data['phone'])
#     project.learner.add(learner)
#     project.save()
#     serializers= ProjectSerializer(project)
#     return Response(serializers.data, status=201)




@api_view(["POST"])
def add_learner(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise ParseError("Invalid project id provided.")

    email = request.data.get('email')
    if not email:
        raise ValidationError("Email is required.")

    with transaction.atomic():
        # Create user and learner profile
        user = User.objects.create_user(username=email, email=email)
        learner_profile = Profile.objects.create(user=user, type='learner')

        # Create learner
        learner_data = {'name': request.data.get('name'), 'email': email, 'phone': request.data.get('phone')}
        learner = Learner.objects.create(user=learner_profile, **learner_data)

        # Add learner to project
        project.learner.add(learner)
        project.save()

    serializer = ProjectSerializer(project)
    return Response(serializer.data, status=201)


@api_view(["GET"])
def get_upcoming_session(request):
    current_timestamp =  int(timezone.now().timestamp() * 1000)
    sessions = Session.objects.annotate(start_time_int=Cast('confirmed_availability__start_time', IntegerField())).filter(start_time_int__gt=current_timestamp)
    serializer = SessionsDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_past_session(request):
    current_timestamp = int(timezone.now().timestamp() * 1000)
    sessions = Session.objects.annotate(start_time_int=Cast('confirmed_availability__start_time', IntegerField())).filter(start_time_int__lt=current_timestamp)
    serializer = SessionsDepthTwoSerializer(sessions, many=True)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def get_session_requests(request):
    session_requests = SessionRequest.objects.filter(is_booked=False)
    serializer = SessionRequestDepthOneSerializer(session_requests, many=True)
    return Response(serializer.data, status=200)
