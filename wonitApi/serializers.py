from rest_framework import serializers
from .models import Games,Slips,BookingCode,Notifications


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
# # Serializer for Slips model that includes only the price  fields 
class SlipPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slips
        fields = [
            'slip_id',
            'total_odd',
            'price',
            'match_day',
            'start_time',
            'category',
        ]
# Serializer for Slips model that includes all fields except games

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
            'category'
        ]
class VIPSerializer(serializers.ModelSerializer):
    games = GamesSerializer(many=True, read_only=True)
    class Meta:
        model = Slips
        fields = [
            'slip_id',
            'games',
            'total_odd',
            'price',
            'match_day',
            'start_time',
        ]


class NotificationsS(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = [
            'notification_id',
            'title',
            'body',
            'notification_date',
            'seen',
            'cleared'
        ]
