from .models import Affiliate
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