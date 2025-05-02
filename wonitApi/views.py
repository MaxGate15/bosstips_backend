from .models import *
from rest_framework.decorators import api_view
from datetime import date, timedelta, datetime
from .models import Games
from .serializers import GamesSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class TodaysGamesView(APIView):
    def get(self, request):
        today = date.today()
        games = Games.objects.filter(matchday=today)
        serializer = GamesSerializer(games, many=True)
        return Response({'data': serializer.data})


class TomorrowGamesView(APIView):
    def get(self, request):
        tomorrow = date.today() + timedelta(days=1)
        games = Games.objects.filter(matchday=tomorrow)
        serializer = GamesSerializer(games, many=True)
        return Response({'data': serializer.data})


class YesterdayGamesView(APIView):
    def get(self, request):
        yesterday = date.today() - timedelta(days=1)
        games = Games.objects.filter(matchday=yesterday)
        serializer = GamesSerializer(games, many=True)
        return Response({'data': serializer.data})


class AnotherDayGamesView(APIView):
    def get(self, request):
        formatted_date = request.query_params.get('formattedDate')

        if not formatted_date:
            return Response(
                {'error': 'formattedDate query parameter is required. Format: YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            matchday = datetime.strptime(formatted_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        games = Games.objects.filter(matchday=matchday)

        if not games.exists():
            return Response({'message': f'No games found for {formatted_date}'}, status=status.HTTP_200_OK)

        serializer = GamesSerializer(games, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_booking_code(request):
    b = BookingCode.objects.filter(bc_id=1)
    data = [
        {'code': c.code}
        for c in b
    ]
    return Response({'codes': data})
