from rest_framework import serializers
from .models import (
    SchedularProject,
    LiveSession,
    CoachingSession,
    SchedularBatch,
    EmailTemplate,
    SentEmail,
    CoachSchedularAvailibilty,
    RequestAvailibilty,
    SchedularSessions,
    FacilitatorPricing,
    CoachPricing,
    SchedularUpdate,
    Expense,
    HandoverDetails,
    Task,
    Assets,
    GmSheet,
    Offering,
    Benchmark,
)
from api.models import Coach
from api.models import Sales
from zohoapi.models import SalesOrder

class SchedularProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularProject
        fields = "__all__"
        depth = 1


class SchedularProjectSerializerArchiveCheck(serializers.ModelSerializer):
    is_archive_enabled = serializers.BooleanField()

    class Meta:
        model = SchedularProject
        fields = "__all__"
        depth = 1


class SessionItemSerializer(serializers.Serializer):
    session_type = serializers.CharField()
    duration = serializers.IntegerField()
    order = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True, required=False
    )


class SchedularBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularBatch
        fields = "__all__"


class SchedularBatchDepthSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularBatch
        fields = "__all__"
        depth = 1


class LiveSessionSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = "__all__"
        depth = 1


class LiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = "__all__"


class CoachingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachingSession
        fields = "__all__"


class LearnerDataUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularBatch
        fields = "__all__"


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = "__all__"


class SentEmailDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentEmail
        fields = "__all__"
        depth = 1


class CoachSchedularAvailibiltySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachSchedularAvailibilty
        fields = "__all__"


class CoachSchedularAvailibiltySerializer2(serializers.ModelSerializer):
    class Meta:
        model = RequestAvailibilty
        fields = "__all__"
        depth = 1


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularBatch
        fields = "__all__"


class CoachBasicDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "active_inactive",
            "phone_country_code",
        ]


class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachSchedularAvailibilty
        fields = "__all__"


class SchedularSessionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularSessions
        fields = "__all__"


class CoachSchedularGiveAvailibiltySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachSchedularAvailibilty
        fields = "__all__"


class CoachSchedularGiveAvailibiltySerializer2(serializers.ModelSerializer):
    class Meta:
        model = CoachSchedularAvailibilty
        fields = "__all__"
        depth = 1


class RequestAvailibiltySerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = RequestAvailibilty
        fields = "__all__"
        depth = 1


class RequestAvailibiltySerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestAvailibilty
        fields = "__all__"


class UpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularUpdate
        fields = "__all__"


class SchedularUpdateDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularUpdate
        fields = "__all__"
        depth = 1


class SchedularBatchDepthTwoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedularBatch
        fields = "__all__"
        depth = 2


class FacilitatorPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilitatorPricing
        fields = "__all__"


class CoachPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachPricing
        fields = "__all__"


class ExpenseSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"
        depth = 1


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"


class HandoverDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandoverDetails
        fields = "__all__"

class AssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = "__all__"

class GmSheetDetailedSerializer(serializers.ModelSerializer):
    sales_name = serializers.CharField(source="sales.name", allow_null=True)   
    class Meta:
        model = GmSheet
        fields = "__all__"

class GmSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = GmSheet
        fields = '__all__'

class GmSheetSalesOrderExistsSerializer(serializers.ModelSerializer):
    sales_order_exists = serializers.SerializerMethodField()

    class Meta:
        model = GmSheet
        fields = '__all__'

    def get_sales_order_exists(self, obj):
        return SalesOrder.objects.filter(gm_sheet_id=obj.id).exists()


class OfferingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offering
        fields = '__all__'


class HandoverDetailsSerializerWithOrganisationName(serializers.ModelSerializer):
    organisation_name = serializers.SerializerMethodField()
    pmo_name = serializers.SerializerMethodField()

    def get_organisation_name(self, obj):
        if obj.organisation:
            return obj.organisation.name
        return None

    def get_pmo_name(self, obj):
        if obj.pmo:
            return obj.pmo.name
        return None

    class Meta:
        model = HandoverDetails
        fields = "__all__"

