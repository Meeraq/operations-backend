from .models import Affiliate, Lead
from django.contrib.auth.models import User
from rest_framework import serializers

class AffiliateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliate
        fields = "__all__"

class AffiliateDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliate
        fields = "__all__"
        depth = 1

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        depth = 1


class LeadDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        depth = 1