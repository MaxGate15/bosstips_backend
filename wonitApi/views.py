from .models import *
from decimal import Decimal
from rest_framework.decorators import api_view
from datetime import date, timedelta, datetime
from .models import Games, BookingCode, Slips, AuthUser, Purchase, Notifications
from .serializers import GamesSerializer, SlipSerializer, VIPSerializer,NotificationsS,SlipPriceSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.middleware.csrf import get_token
from django.contrib.auth.models import User
from django.db import IntegrityError
import os
from .sporty import get_booking
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model




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

        if not games:
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
        return Response({'message': 'Account created successfully'}, status=status.HTTP_201_CREATED)
    except IntegrityError as e:
        if "username" in str(e):
            return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
        elif "email" in str(e):
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
def goToFreeGames(request):
    date_ = request.GET.get('date')
    purchases = Slips.objects.filter(match_day=date_, category__icontains='free')
    

    serializer = SlipSerializer(purchases, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['GET'])
def goToPurchasedGames(request):
    date_ = request.GET.get('date')
    purchases = Slips.objects.filter(match_day=date_, category__icontains='vip')
    

    serializer = SlipSerializer(purchases, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['get'])
def checkToday(request):
    updates = {
        'vip': False,
        'vvip1': False,
        'vvip2': False,
        'vvip3': False
    }

    today = date.today()
    now = timezone.now().time()
    todays_slip = Slips.objects.filter(
        match_day=today,
        category__in=['vip', 'vvip1', 'vvip2', 'vvip3'],
        start_time__gt=now
    )

    if not todays_slip.exists():
        return JsonResponse(updates, safe=False)

    for slip in todays_slip:
        cat = slip.category.lower()
        if cat in updates:
            updates[cat] = True

    return JsonResponse(updates)

@api_view(['get'])
def checkUserPurchases(request):
    updates = {
        'vip': False,
        'vvip1': False,
        'vvip2': False,
        'vvip3': False
    }
    today = date.today()
    username = request.headers.get('x-username')
    purchasedGame = Purchase.objects.filter(user__username=username, purchase_date=today)
    if not purchasedGame.exists():
        return JsonResponse(updates, safe=False)

    for slip in purchasedGame:
        cat = slip.slip.category.lower()
        if cat in updates:
            updates[cat] = True

    return JsonResponse(updates)

@api_view(['get'])
def purchasedGames(request):
    username = request.headers.get('x-username')
    thirty_days_ago = date.today() - timedelta(days=30)
    purchasedGame = Purchase.objects.filter(user__username=username, purchase_date__gte=thirty_days_ago)
    slips = [purchase.slip for purchase in purchasedGame]

    serializer = SlipSerializer(slips, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['get'])
def notification(request):
    notifications = Notifications.objects.filter(cleared=False)
    serializer = NotificationsS(notifications,many=True)
    return JsonResponse(serializer.data,safe=False)
@api_view(['get'])
def yesterdayVVIPGames(request):
    yesterday = date.today() - timedelta(days=1)
    vvip_slips = Slips.objects.filter(match_day=yesterday, category__icontains='vvip')
    serializer = SlipSerializer(vvip_slips, many=True)
    return JsonResponse(serializer.data, safe=False)

@api_view(['get'])
def vvipPrice(request):
    today = date.today()
    vvip_slips = Slips.objects.filter(match_day=today, category__icontains='vvip')
    serializer = SlipPriceSerializer(vvip_slips, many=True)
    return JsonResponse(serializer.data, safe=False)

from django.shortcuts import redirect
from django.http import HttpResponse
from django.utils import timezone

def admin_redirect_view(request):
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Go to Admin</title>
        <style>
            body {
                background: #f4f6fb;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            .container {
                background: #fff;
                padding: 2rem 3rem;
                border-radius: 12px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.08);
                text-align: center;
            }
            h1 {
                color: #22223b;
                margin-bottom: 1.5rem;
            }
            .admin-btn {
                background: #2d6cdf;
                color: #fff;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: 6px;
                font-size: 1.1rem;
                cursor: pointer;
                transition: background 0.2s;
                box-shadow: 0 2px 8px rgba(45,108,223,0.08);
            }
            .admin-btn:hover {
                background: #1b4fa0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to the Admin Portal</h1>
            <form action="/admin/" method="get">
                <button class="admin-btn" type="submit">Go to Admin Site</button>
            </form>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

def get_total_number_of_users(request):
    total_users = AuthUser.objects.count()
    return JsonResponse({"total_users": total_users})

def get_number_of_pending_slips(request):
    pending_slips = Slips.objects.filter(status='pending').count()
    return JsonResponse({"pending_slips": pending_slips})

def get_number_of_purchased_slips(request):
    purchased_slips = Purchase.objects.all().count()
    return JsonResponse({"purchased_slips": purchased_slips})

def load_booking_data(request, code):
    try:
        data = get_booking(code)
        # JsonResponse requires safe=True for dicts, safe=False for lists
        if isinstance(data, dict):
            return JsonResponse(data)
        return JsonResponse(data, safe=False)
    except Exception as e:
        # log if you have logging configured, return 500 with error info
        return JsonResponse({'error': 'Failed to load booking data'}, status=500)

@api_view(['POST'])
def upload_slip(request):
    """
    Accepts a JSON payload for a bet slip, validates required fields,
    creates a Slips record and related Games records, then returns the saved ids.
    """
    payload = request.data or {}
    required = ['sportyCode', 'msportCode', 'totalOdds', 'games', 'price']
    missing = [f for f in required if not payload.get(f) and payload.get(f) != 0]
    if missing:
        return Response({'error': 'Missing required fields', 'missing': missing}, status=status.HTTP_400_BAD_REQUEST)

    games_payload = payload.get('games')
    if not isinstance(games_payload, list) or len(games_payload) == 0:
        return Response({'error': 'games must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        price = Decimal(str(payload.get('price')))
    except Exception:
        return Response({'error': 'price must be numeric'}, status=status.HTTP_400_BAD_REQUEST)

    total_odds = str(payload.get('totalOdds'))
    sporty_code = str(payload.get('sportyCode'))
    msport_code = str(payload.get('msportCode'))
    slip_result = payload.get('slipResult', '')
    category_in = str(payload.get('category', '') or '').strip()

    # Normalize and map possible human-readable category strings to internal category keys
    cat_norm = category_in.lower()
    if not cat_norm:
        category = 'free'
    elif 'vvip' in cat_norm:
        # Examples: 'DAILY VVIP PLAN', 'DAILY VVIP2 PLAN', 'VVIP 3', 'vvip1'
        import re
        m = re.search(r'vvip\s*([1-3])', cat_norm)
        if m:
            category = f"vvip{m.group(1)}"
        else:
            # Try to find a digit anywhere (e.g. 'vvip2')
            m2 = re.search(r'([1-3])', cat_norm)
            if m2:
                category = f"vvip{m2.group(1)}"
            else:
                # default mapping for generic vvip mentions
                category = 'vvip1'
    elif 'vip' in cat_norm:
        category = 'vip'
    else:
        category = 'free'

    today = date.today()
    now_time = timezone.now().time()

    try:
        with transaction.atomic():
            booking, _ = BookingCode.objects.get_or_create(
                sportyBet_code=sporty_code,
                defaults={'betWay_code': msport_code}
            )

            slip = Slips.objects.create(
                results=slip_result,
                total_odd=total_odds,
                status='available',
                price=price,
                booking_code=booking,
                match_day=today,
                start_time=now_time,
                category=category,
                date_created=today
            )

            # prepare Games instances for bulk_create
            game_objs = []
            for g in games_payload:
                team1 = g.get('home') or ''
                team2 = g.get('away') or ''
                prediction = g.get('prediction') or ''
                odds = str(g.get('odds') or '')
                league = g.get('category') or ''
                result = g.get('result') or ''
                game_objs.append(
                    Games(
                        league=league,
                        team1=team1,
                        team2=team2,
                        prediction=prediction,
                        prediction_type=prediction,
                        result=result,
                        odd=odds,
                        matchday=today,
                        time_created=now_time,
                        date_created=today,
                        game_type=''
                    )
                )

            created_games = Games.objects.bulk_create(game_objs)

            # Associate games with the slip (ManyToMany)
            slip.games.set(created_games)

    except Exception as exc:
        return Response({'error': 'Failed to save slip'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Build response payload
    resp = {
        'slip': {
            'slip_id': slip.slip_id,
            'total_odd': slip.total_odd,
            'price': str(slip.price),
            'category': slip.category,
            'booking_code': booking.sportyBet_code
        },
        'games': [
            {
                'game_id': g.game_id,
                'team1': g.team1,
                'team2': g.team2,
                'prediction': g.prediction,
                'odd': g.odd,
                'league': g.league,
                'result': g.result
            } for g in created_games
        ]
    }

    return Response({'message': 'Saved slip and games', 'data': resp}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_all_slips(request):
    slips = Slips.objects.all().order_by('-match_day', '-start_time')
    serializer = SlipSerializer(slips, many=True)
    slips = serializer.data
    return Response({'slips': slips}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_avaliable_vip_plans(request):
    today = date.today()
    plan_keys = ["vip", "vvip1", "vvip2", "vvip3"]
    result = {k: False for k in plan_keys}
    try:
        # Single query to fetch today's categories, normalize to avoid casing/whitespace mismatches
        categories = Slips.objects.filter(match_day=today).values_list('category', flat=True)
        print( categories)
        normalized = { (c or '').strip().lower() for c in categories }

        for plan in plan_keys:
            result[plan] = plan.lower() in normalized

        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Failed to check plans", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def get_slip_for_todays_status(request, category):
    today = date.today()
    try:
        slip = Slips.objects.get(match_day=today, category__iexact=category)
        serializer = SlipSerializer(slip)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Slips.DoesNotExist:
        return Response({"error": "Slip not found for today with the specified category"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Failed to retrieve slip", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def mark_slip_as_sold_out(request, slip_id):
    
    if not slip_id:
        return Response({"error": "slip_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        slip = Slips.objects.get(slip_id=slip_id)
        slip.status = "sold"
        slip.save()
        return Response({"message": f"Slip {slip_id} marked as sold"}, status=status.HTTP_200_OK)
    except Slips.DoesNotExist:
        return Response({"error": "Slip not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Failed to update slip", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(["POST"])
def mark_slip_as_available(request, slip_id):
    
    if not slip_id:
        return Response({"error": "slip_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        slip = Slips.objects.get(slip_id=slip_id)
        slip.status = "available"
        slip.save()
        return Response({"message": f"Slip {slip_id} marked as available"}, status=status.HTTP_200_OK)
    except Slips.DoesNotExist:
        return Response({"error": "Slip not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Failed to update slip", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def mark_slip_as_updated(request, slip_id):
    slip = Slips.objects.filter(slip_id=slip_id).first()
    if not slip:
        return Response({"error": "Slip not found"}, status=status.HTTP_404_NOT_FOUND)
    slip.results = "updated"
    slip.save()
    return Response({"message": f"Slip {slip_id} marked as updated"}, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def game_results(request, game_id, result):
    game = Games.objects.filter(game_id=game_id).first()
    if not game:
        return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)
    game.result=result
    try:
        game.save()
        return Response({"message": f"Game {game_id} result updated to {result}"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Failed to update game result", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_slip_status(request):

    today = date.today()
    try:
        slips = Slips.objects.filter(match_day=today).all()
        slip_statuses = [
            {"category": slip.category, "status": slip.status, "slip_id": slip.slip_id}
            for slip in slips
        ]
        return Response(slip_statuses, status=status.HTTP_200_OK)
    except Slips.DoesNotExist:
        return Response({"error": "Slip not found for today with the specified category"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Failed to retrieve slip", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'username', 'email', 'phone', 'status', 'initials')

    def get_name(self, obj):
        first = (getattr(obj, 'first_name', '') or '').strip()
        last = (getattr(obj, 'last_name', '') or '').strip()
        return f"{first} {last}".strip()

    def get_username(self, obj):
        uname = getattr(obj, 'username', '') or ''
        return f"@{uname.lstrip('@')}" if uname else ""

    def get_phone(self, obj):
        # common phone field names — return empty string if not present
        for attr in ('phone', 'phone_number', 'mobile'):
            if hasattr(obj, attr):
                return getattr(obj, attr) or ""
        return ""

    def get_status(self, obj):
        return "Active" if getattr(obj, 'is_active', False) else "Inactive"

    def get_initials(self, obj):
        fn = (getattr(obj, 'first_name', '') or '').strip()
        ln = (getattr(obj, 'last_name', '') or '').strip()
        initials = ""
        if fn:
            initials += fn[0].upper()
        if ln:
            initials += ln[0].upper()
        return initials

@api_view(['GET'])
def api_users_list(request):
    """
    GET /api/users/  -> returns list of users with computed name, initials, etc.
    """
    User = get_user_model()
    users_qs = User.objects.all().order_by('id')
    serializer = UserListSerializer(users_qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

def get_all_users_phone_numbers(request):
    """
    GET /api/users/phone-numbers/  -> returns list of users with their phone numbers
    """
    
    users_qs = AuthUser.objects.all().order_by('id')
    phone_numbers = [
        {"id": user.id, "phone": user.phone}
        for user in users_qs if user.phone
    ]
    return Response(phone_numbers, status=status.HTTP_200_OK)

def send_sms(recipient:list, message:str):
    endPoint = 'https://api.mnotify.com/api/sms/quick'
    apiKey = 'xmI6Ky5UWpQJJnKgzPrWlD07B'
    url = endPoint + '?key=' + apiKey

    data = {
        "recipient": recipient,
        "sender": "Bozz-tips",
        "message": message,
        "is_schedule": False,
        "schedule_date": "",
    }

    response = requests.post(url, json=data)
    return response.json()

@api_view(['POST'])
def send_bulk_sms(request):
    numbers = get_all_users_phone_numbers(request).data
    phone_list = [entry['phone'] for entry in numbers if entry['phone']]
    message = request.data.get("message", "")
    response = send_sms(phone_list, message)
    return Response(response, status=status.HTTP_200_OK)

@api_view(['GET'])
def is_admin_user(request):
    username = request.headers.get('X-Username')
    try:
        user = AuthUser.objects.get(username=username)
        return Response({'is_admin': user.is_superuser}, status=status.HTTP_200_OK)
    except AuthUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
def add_admin_user(request, username, is_superuser, is_staff):
    try:
        user = AuthUser.objects.get(username=username)
        user.is_superuser = is_superuser
        user.is_staff = is_staff
        user.save()
        return Response({'message': f'User {username} promoted to { "admin" if is_superuser else "staff" }'}, status=status.HTTP_200_OK)
    except AuthUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
def demote_admin_user(request, username):
    try:
        user = AuthUser.objects.get(username=username)
        user.is_superuser = False
        user.is_staff = False
        user.save()
        return Response({'message': f'User {username} demoted from admin/staff'}, status=status.HTTP_200_OK)
    except AuthUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_user_by_username(request, username):
    try:
        user = AuthUser.objects.get(username=username)
        serializer = UserListSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except AuthUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
def get_admins(request):
    from django.db.models import Q
    admins = AuthUser.objects.filter(Q(is_superuser=True) | Q(is_staff=True))
    
    admin_list = []
    for admin in admins:
        first = (admin.first_name or '').strip()
        last = (admin.last_name or '').strip()
        name = f"{first} {last}".strip() or admin.username
        
        initials = ""
        if first:
            initials += first[0].upper()
        if last:
            initials += last[0].upper()
        if not initials:
            initials = admin.username[:2].upper()
        
        role = "Super Admin" if admin.is_superuser else "Staff"
        admin_status = "Active" if admin.is_active else "Inactive"
        
        admin_list.append({
            "id": admin.id,
            "initials": initials,
            "name": name,
            "email": admin.email,
            "role": role,
            "status": admin_status
        })
    
    return Response(admin_list, status=status.HTTP_200_OK)
