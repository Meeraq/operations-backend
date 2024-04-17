from rest_framework import serializers
from .models import Batches


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batches
        fields = "__all__"
