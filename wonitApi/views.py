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
        serializer = SlipSerializer(slips,many=True)
        return Response(serializer.data)


class TomorrowGamesView(APIView):
    def get(self, request):
        tomorrow = date.today() + timedelta(days=1)
        games = Slips.objects.filter(match_day=tomorrow, category='free')
        serializer = SlipSerializer(games,many=True)
        return Response(serializer.data)


class YesterdayGamesView(APIView):
    def get(self, request):
        yesterday = date.today() - timedelta(days=1)
        games = Slips.objects.filter(match_day=yesterday, category='free')
        serializer = SlipSerializer(games,many=True)
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

        games = Games.objects.filter(matchday=matchday).first()

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
        username = request.headers.get('X-Username')
        user = AuthUser.objects.get(username=username)
        purchased_games = Purchase.objects.filter(user=user, purchase_date=today)
        games = [p.slip for p in purchased_games]
        serializer = VIPSerializer(games, many=True)
        return Response(serializer.data)


from django.http import JsonResponse

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import hashlib
import hmac
import json
import os
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def paystack_webhook(request):
    today = date.today()
    """Handle Paystack webhook POSTs.

    We *only* act when we can match an existing user/slip/purchase.
    Otherwise we log it and still return 200 so Paystack doesn’t retry.
    """
    secret_key = os.getenv("PAYSTACK_SK")
    if not secret_key:
        logger.error("Missing PAYSTACK_SK env var")
        return HttpResponse("Missing PAYSTACK_SK", status=500)

    secret_key = secret_key.encode()

    # 1️⃣  Verify signature ---------------------------------------------------
    signature = request.headers.get("x-paystack-signature")
    payload = request.body
    expected_signature = hmac.new(secret_key, msg=payload, digestmod=hashlib.sha512).hexdigest()

    if signature != expected_signature:
        logger.warning("Webhook signature mismatch")
        return HttpResponseForbidden()

    # 2️⃣  Parse event --------------------------------------------------------
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in webhook")
        return HttpResponse(status=400)

    if event.get("event") != "charge.success":
        return HttpResponse(status=200)  # ignore other events

    data = event["data"]
    reference = data.get("reference")
    amount = data.get("amount")
    email = data.get("customer", {}).get("email")
    custom_fields = data.get("metadata", {}).get("custom_fields", [])
    game_category = ''
    username = None
    for field in custom_fields:
        if field.get("display_name") and field.get('game_category'):  # or "Username"
            username = field.get("display_name")
            game_category=field.get('game_category')
            break

    # 3️⃣  Update database safely -------------------------------------------

    user = AuthUser.objects.get(username=username['username'])

    slip = Slips.objects.get(match_day=today,category=game_category)



    try:
        # If purchase already exists we just ignore – idempotent.
        Purchase.objects.get(reference=reference)
        logger.info("Duplicate webhook for %s – already processed", reference)
        return HttpResponse(status=200)
    except Purchase.DoesNotExist:
        pass

    try:
        p= Purchase(
            reference=reference,
            user=user,
            slip=slip)

        p.save()
    except IntegrityError:
        logger.exception("Could not create Purchase for %s", reference)

    return HttpResponse(status=200)

@api_view(['GET'])
def currentPurchasedGames(request):
    username = request.headers.get('X-Username')
    today = date.today()

    try:
        user = AuthUser.objects.get(username=username)
    except AuthUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    purchases = Purchase.objects.filter(user=user,purchase_date=today, slip__category__icontains='vip')
    slips = [purchase.slip for purchase in purchases]

    serializer = SlipSerializer(slips, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['GET'])
def previousPurchasedGames(request):
    username = request.headers.get('X-Username')
    today = date.today()-timedelta(days=1)

    try:
        user = AuthUser.objects.get(username=username)
    except AuthUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    purchases = Purchase.objects.filter(user=user, purchase_date=today, slip__category__icontains='vip')
    slips = [purchase.slip for purchase in purchases]

    serializer = SlipSerializer(slips, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['GET'])
def goToPurchasedGames(request):
    username = request.headers.get('x-username')
    date_ = request.GET.get('date')
    try:
        user = AuthUser.objects.get(username=username)
    except AuthUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    purchases = Purchase.objects.filter(user=user, purchase_date=date_, slip__category__icontains='vip')
    slips = [purchase.slip for purchase in purchases]

    serializer = SlipSerializer(slips, many=True)
    return JsonResponse(serializer.data, safe=False)




