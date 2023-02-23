from datetime import date
from os import name
from django.shortcuts import render
from django.db import transaction
from .serializers import CoachSerializer
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from .models import Profile,Pmo, Coach, Project, Organisation, HR, Participant
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
# Create your views here.

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
            pmo_user = Pmo.objects.create(profile=pmo_profile, name=name, email=email, phone=phone)
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
    if not all([name, email, meet_link, phone, level, rating, area_of_expertise, username, password]):
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
    pmo = Pmo.objects.get(profile=user.profile)

    return Response({
        'token': token.key,
        'pmo': {
            'name': pmo.name,
            'email': pmo.email,
            'phone': pmo.phone
        }
    })




@api_view(['POST'])
def create_project(request):
    # date= date.today()
    # organisation= Organisation.objects.get(organisation_id=id)
    # organisation_name= 
    # organisation_image= 

    # print(organisation_name,organisation_image)
    organisation= Organisation(
        name=request.data['organisation_name'], image_url=request.data['image_url']
    )
    organisation.save()

    # hr= HR.objects.get(hr_id=id)
    # coach= Coach.objects.get(coach_id=id)
    project= Project(
    name= request.data['project_name'],
    organisation= organisation,
    # coach_assigned= coach_assigned,
    total_sessions= request.data['total_session'],
    # project_validity= date ,
    cost_per_session= request.data['cost_per_session'],
    # currency= request.data['currency'],
    sessions_per_employee= request.data['sessions_per_employee']
)
    project.save()
    # print(project,project.coaches)

    for coach in request.data["coach_id"]:
        single_coach = Coach.objects.get(id=coach)
        print(single_coach)
        project.coaches.add(single_coach)

    # for participant in request.data['participant']:
    #     data = Participant(

    #     )
    #     data.save()
    #     project.participant.add(data)


    # if  create_project.save():
    #     return Response({'message': "Project saved Successfully"}, status=200)
    # else:
    #     return Response({'error': "Project couldn't be save sucessfully"}, status=400)
    return Response({'message': "Project saved Successfully"}, status=200)
    
    
# Create participant user
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
            participant_user = Participant.objects.create(user=learner_profile, name=name, email=email, phone=phone)
        # Return success response
        return Response({'message': 'Participant user created successfully.'}, status=201)

    except Exception as e:
        # Return error response if any exception occurs
        return Response({'error': str(e)}, status=500)

