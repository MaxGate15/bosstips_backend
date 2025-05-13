from rest_framework import serializers
from .models import Games,Slips,BookingCode


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
class BookingCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingCode
        fields = ['bc_id', 'sportyBet_code', 'betWay_code']

class SlipSerializer(serializers.ModelSerializer):
    games = GamesSerializer(many=True, read_only=True)
    booking_code = BookingCodeSerializer(read_only=True)

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
