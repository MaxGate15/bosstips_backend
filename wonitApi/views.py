import datetime

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
# Create your views here.
from .models import *
from rest_framework.response import Response
from rest_framework.views import APIView


# Create your views here.

from rest_framework.decorators import api_view

@api_view(['GET'])
def get_todays_games(request):
    today = datetime.date.today()
    print(today)
    games = Games.objects.filter(prediction_time=today)
    data = [
        {
            'league': g.league,
            'teams': g.teams,
            'prediction': g.prediction,
            'result': g.result,
            'resultClass': g.resultClass
        }
        for g in games
    ]
    print(data)
    return Response({'data': data})


