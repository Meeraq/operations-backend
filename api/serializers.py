from rest_framework import serializers
from .models import (
    Pmo,
    Coach,
    Profile,
    Project,
    HR,
    Finance,
    Organisation,
    Learner,
    SessionRequestCaas,
    Availibility,
    Notification,
    Engagement,
    Goal,
    Competency,
    ActionItem,
    ProfileEditActivity,
    UserLoginActivity,
    AddGoalActivity,
    AddCoachActivity,
    SentEmailActivity,
    CoachProfileTemplate,
    StandardizedField,
    StandardizedFieldRequest,
    SessionRequestedActivity,
    DeleteCoachProfileActivity,
    RemoveCoachActivity,
    PastSessionActivity,
    Template,
    ProjectContract,
    CoachContract,
    Update,
    UserToken,
    CalendarEvent,
    ShareCoachProfileActivity,
    CreateProjectActivity,
    FinalizeCoachActivity,
    SuperAdmin,
    Facilitator,
    APILog
)
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password", "is_staff"]


class PmoDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pmo
        fields = "__all__"
        depth = 1


class SuperAdminDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperAdmin
        fields = "__all__"
        depth = 1


class FinanceDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finance
        fields = "__all__"
        depth = 1


class CoachDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = "__all__"
        depth = 1


class HrDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = HR
        fields = "__all__"
        depth = 1


class LearnerDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Learner
        fields = "__all__"
        depth = 1


class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = "__all__"


class LearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Learner
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ProjectDepthTwoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        depth = 2


class UpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Update
        fields = "__all__"


class UpdateDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Update
        fields = "__all__"
        depth = 1


class AvailibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availibility
        fields = "__all__"


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
        fields = "__all__"
        depth = 1


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = "__all__"


class SessionRequestCaasSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionRequestCaas
        fields = "__all__"


class SessionRequestCaasDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionRequestCaas
        fields = "__all__"
        depth = 2


class SessionRequestWithEngagementCaasDepthOneSerializer(serializers.ModelSerializer):
    engagement_status = serializers.CharField()

    class Meta:
        model = SessionRequestCaas
        fields = "__all__"
        depth = 2


class SessionRequestWithEngagementCaasAndIsSeeqProjectDepthOneSerializer(
    serializers.ModelSerializer
):
    engagement_status = serializers.CharField()
    is_seeq_project = serializers.BooleanField()

    class Meta:
        model = SessionRequestCaas
        fields = "__all__"
        depth = 2


class SessionRequestCaasDepthTwoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionRequestCaas
        fields = "__all__"
        depth = 2


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class EngagementDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engagement
        fields = "__all__"
        depth = 1


class EngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engagement
        fields = "__all__"
        depth = 2


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ["id", "name", "status", "engagement"]


class GetGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = "__all__"


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"


class CompetencyDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"
        depth = 1


class ActionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionItem
        fields = ["id", "name", "status", "competency"]


class PendingActionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionItem
        fields = "__all__"
        depth = 2


class GetActionItemDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionItem
        fields = "__all__"


class ProfileEditActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ProfileEditActivity
        fields = "__all__"


class UserLoginActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserLoginActivity
        fields = "__all__"


class AddGoalActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = AddGoalActivity
        fields = "__all__"


class AddCoachActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = AddCoachActivity
        fields = "__all__"


class SentEmailActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = SentEmailActivity
        fields = "__all__"


class CoachProfileTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachProfileTemplate
        fields = "__all__"


class StandardizedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardizedField
        fields = "__all__"


class StandardizedFieldRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardizedFieldRequest
        fields = "__all__"


class StandardizedFieldRequestDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardizedFieldRequest
        fields = "__all__"
        depth = 1


class SessionRequestedActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionRequestedActivity
        fields = "__all__"
        depth = 1


class DeleteCoachProfileActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeleteCoachProfileActivity
        fields = "__all__"
        depth = 1


class RemoveCoachActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoveCoachActivity
        fields = "__all__"
        depth = 1


class PastSessionActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PastSessionActivity
        fields = "__all__"
        depth = 1


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = "__all__"


class ProjectContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContract
        fields = "__all__"


class CoachContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachContract
        fields = "__all__"


class UserTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserToken
        fields = "__all__"


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = "__all__"


class ShareCoachProfileActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareCoachProfileActivity
        fields = "__all__"
        depth = 1


class CreateProjectActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CreateProjectActivity
        fields = "__all__"
        depth = 1


class FinalizeCoachActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FinalizeCoachActivity
        fields = "__all__"
        depth = 1


class SessionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionRequestCaas
        fields = "__all__"


class PmoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pmo
        fields = ["name", "email", "phone","sub_role"]

class PmoSerializerAll(serializers.ModelSerializer):
    class Meta:
        model = Pmo
        fields = "__all__"

class FacilitatorDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facilitator
        fields = "__all__"
        depth = 1


class FacilitatorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Facilitator
        fields = "__all__"

class FacilitatorSerializerIsVendor(serializers.ModelSerializer):
    is_vendor = serializers.BooleanField()
    vendor_id = serializers.CharField()
    purchase_order_id = serializers.CharField()
    purchase_order_no = serializers.CharField()
    class Meta:
        model = Facilitator
        fields = "__all__"

class FacilitatorBasicDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = ["id", "first_name", "last_name", "email", "phone"]



class APILogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)

    class Meta:
        model = APILog
        fields = ['path', 'username', 'created_at', 'method']
