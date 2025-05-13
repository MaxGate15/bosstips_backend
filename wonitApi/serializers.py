from rest_framework import serializers
from .models import Games,Slips


class GamesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Games
        fields = [
            'game_id',
            'matchday',
            'time_created',
            'game_type',
            'team1',
            'team2',
            'prediction',
            'result',
            'odd',
        ]

class SlipSerializer(serializers.ModelSerializer):
    games = GamesSerializer(many=True)  # nested serialization

    class Meta:
        model = Slips
        fields = [
            'slip_id',
            'games',
            'results',
            'total_odd',
            'price',
            'booking_code',
            'match_day',
            'start_time',
            'date_created',
        ]

