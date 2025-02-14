from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def about(request):
    return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def technologies(request):
    return Response(status=status.HTTP_404_NOT_FOUND)
