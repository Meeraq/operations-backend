from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Competency
from .serializers import CompetencySerializer
# Create your views here.



class CompetencyView(APIView):
    def get(self, request):
        competencies = Competency.objects.all()
        serializer = CompetencySerializer(competencies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CompetencySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Competency created successfully'}, status=status.HTTP_201_CREATED)
        return Response({'error': f'{serializer.errors}',}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        competency_id=request.data.get("id")
        try:
            competency = Competency.objects.get(id=competency_id)
        except Competency.DoesNotExist:
            return Response({'message': 'Competency not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CompetencySerializer(competency, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Competency updated successfully'}, status=status.HTTP_200_OK)
        return Response({'error': f'{serializer.errors}',}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        competency_id=request.data.get("id")
        try:
            competency = Competency.objects.get(id=competency_id)
        except Competency.DoesNotExist:
            return Response({'message': 'Competency not found'}, status=status.HTTP_404_NOT_FOUND)
       
        competency.delete()
        return Response({'message': 'Competency deleted successfully'}, status=status.HTTP_204_NO_CONTENT)