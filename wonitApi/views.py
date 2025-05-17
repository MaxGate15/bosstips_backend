from .models import *
from decimal import Decimal
from rest_framework.decorators import api_view
from datetime import date, timedelta, datetime
from .models import Games
from .serializers import GamesSerializer, SlipSerializer, VIPSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.middleware.csrf import get_token
from django.contrib.auth.models import User
from django.db import IntegrityError
import os


class TodaysGamesView(APIView):
    def get(self, request):
        today = date.today()
        slips = Slips.objects.filter(match_day=today, category='free')
        serializer = SlipSerializer(slips, many=True)
        return Response(serializer.data)


class TomorrowGamesView(APIView):
    def get(self, request):
        tomorrow = date.today() + timedelta(days=1)
        games = Slips.objects.filter(match_day=tomorrow, category='free')
        serializer = SlipSerializer(games, many=True)
        return Response(serializer.data)


class YesterdayGamesView(APIView):
    def get(self, request):
        yesterday = date.today() - timedelta(days=1)
        games = Slips.objects.filter(match_day=yesterday, category='free')
        serializer = SlipSerializer(games, many=True)
        return Response(serializer.data)


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
        return Response(data=serializer, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_booking_code(request):
    b = BookingCode.objects.filter(bc_id=1)
    data = [
        {'code': c.code}
        for c in b
    ]
    return Response({'codes': data})


def get_csrf(request):
    return Response({'csrfToken': get_token(request)})


@api_view(['GET'])
def freeSlip(request):
    slip = Slips.objects.filter(price=0.00).first()
    serializer = SlipSerializer(slip)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def signup_view(request):
    data = request.data
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return Response({'error': 'Username, email, and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(
            first_name=data.get('f_name', ''),
            last_name=data.get('l_name', ''),
            username=username,
            email=email,
            password=password,
            is_staff=False,
            date_joined=now()
        )
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
    except IntegrityError as e:
        if "UNIQUE constraint failed: auth_user.username" in str(e):
            return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
        elif "UNIQUE constraint failed: auth_user.email" in str(e):
            return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Database error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


import requests
from django.http import JsonResponse


def verify_payment(request, reference):
    headers = {
        "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_CODE')}"
    }
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    response = requests.get(url, headers=headers)
    result = response.json()

    if result['data']['status'] == 'success':
        # mark payment as successful in your DB
        return JsonResponse({'status': f'success'})
    return JsonResponse({'status': 'failed'})


# class YesterdayGamesVip(APIView):
#     def get(self, request):
#         yesterday = date.today() - timedelta(days=1)
#         games = Slips.objects.filter(match_day=yesterday,category='paid')
#         serializer = SlipSerializer(games, many=True)
#         return Response(serializer.data)
class TodayGamesVip(APIView):
    def get(self, request):
        today = date.today()
        games = Slips.objects.filter(match_day=today, category='paid')
        serializer = VIPSerializer(games, many=True)
        return Response(serializer.data)


import json
import hashlib
import hmac

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse


@csrf_exempt
def paystack_webhook(request):
    secret_key = b"sk_live_496e4ae1cb9d821a2d38402c56f0832039461bd0"  # Use your Paystack SECRET key

    # Step 1: Verify signature
    signature = request.headers.get('x-paystack-signature')
    payload = request.body

    expected_signature = hmac.new(
        secret_key,
        msg=payload,
        digestmod=hashlib.sha512
    ).hexdigest()

    if signature != expected_signature:
        return HttpResponse(status=401)

    # Step 2: Parse event
    event = json.loads(payload)

    if event['event'] == 'charge.success':
        data = event['data']
        reference = data['reference']
        amount = data['amount']  # in kobo or pesewas
        email = data['customer']['email']

        # 🧠 Now update your database (e.g., mark as paid)
        user = AuthUser.objects.get(email=email)
        slip = Slips.objects.get(slip_id=6)
        p = Purchase(
            user=user,
            slip=slip,

        )
        print(f"✅ Payment received: {reference}, {amount}, {email}")
        # e.g., Payment.objects.filter(reference=reference).update(status='confirmed')

    return HttpResponse(status=200)
