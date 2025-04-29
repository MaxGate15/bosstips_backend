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

    # Case-insensitive exclusion
    games = Games.objects.exclude(game_type__iexact='paid')

    data = [
        {
            'league': g.league,
            'teams': g.teams,
            'prediction': g.prediction,
            'result': g.result,
            'resultClass': g.resultClass,
            'prediction_day': "today"if g.prediction_time == today else "not_today",
            'game_type':g.game_type
    }
    for g in games
    ]
    return Response({'data': data})
@api_view(['GET'])
def get_booking_code(request):
    b = BookingCode.objects.filter(bc_id=1)
    data = [
        {'code':c.code}
        for c in b
    ]
    return Response({'codes':data})
