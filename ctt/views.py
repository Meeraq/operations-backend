from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .serializers import BatchSerializer
from .models import Batches


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_batches(request):
    batches = Batches.objects.using("ctt").all()
    serializer = BatchSerializer(batches, many=True)
    return Response(serializer.data)
