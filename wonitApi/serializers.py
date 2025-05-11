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
    class Meta:
        model = Games
        fields = [
            'game_id',
            'matchday',
            'time_created',
            'team1',
            'team2',
            'prediction',
            'result',
            'odd',
        ]
