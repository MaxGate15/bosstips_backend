from rest_framework import serializers
from .models import Games


class GamesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Games
        fields = [
            'game_id',
            'date_created',
            'time_created',
            'game_type',
            'team1',
            'team2',
            'prediction',
        ]
