from django.shortcuts import render
from django.db import transaction
from .serializers import CoachSerializer
import jwt
import uuid
from datetime import datetime, timedelta
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from .models import Profile,Pmo, Coach
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

# Create your views here.

import environ

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
