from rest_framework import serializers
from .models import Pmo,Coach,Profile,Project,HR,Organisation
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'is_staff']

class PmoDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pmo
        fields = '__all__'
        depth=1

class CoachDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = '__all__'
        depth=1

# class HrDepthOneSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = HR
#         fields = '__all__'
#         depth=1

# class LearnerDepthOneSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Learner
#         fields = '__all__'
#         depth=1

class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = '__all__'

# class LearnerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Learner
#         fields = '__all__'
        
# class ProjectSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Project
#         fields = '__all__'
        
class ProjectDepthTwoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        depth = 2
      
# class AvailibilitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Availibility
#         fields = '__all__'
      
# class SessionRequestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SessionRequest
#         fields = '__all__'
      

# class SessionRequestDepthOneSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SessionRequest
#         fields = '__all__'
#         depth = 1


# class SessionRequestDepthTwoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SessionRequest
#         fields = '__all__'
#         depth = 2


# class SessionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Session
#         fields = '__all__'


# class SessionsDepthTwoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Session
#         fields = '__all__'
#         depth = 2


# class CoachInvitesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CoachInvites
#         fields = '__all__'


class HrSerializer(serializers.ModelSerializer):
    class Meta:
        model = HR
        fields = '__all__'

class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = '__all__'

# class SessionRequestCaasSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SessionRequestCaas
#         fields = '__all__'
        
# class SessionRequestCaasDepthOneSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SessionRequestCaas
#         fields = '__all__'
#         depth=1
        
# class SessionRequestCaasDepthTwoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SessionRequestCaas
#         fields = '__all__'
#         depth = 2
