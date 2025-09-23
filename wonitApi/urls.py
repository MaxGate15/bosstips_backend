from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
router = DefaultRouter()

urlpatterns = [
    path("csrf/",get_csrf),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/signup/',signup_view),
    path('api/',include(router.urls)),
    path('', admin_redirect_view),
    path('today-games/',TodaysGamesView.as_view(),name='todays-game'),
    path('tomorrow-games/',TomorrowGamesView.as_view(),name='tomorrows-game'),
    path('yesterday-games/',YesterdayGamesView.as_view(),name='yesterdays-game'),
    path('other-games',YesterdayGamesView.as_view()),
    path('codes/',get_booking_code),
    path('vvip-today/',TodayGamesVip.as_view()),
    path('vvip-price/',vvipPrice),
    path('vvip-yesterday/',yesterdayVVIPGames),
    path('paystack/webhook/', paystack_webhook, name='paystack_webhook'),
    path('current-purchased-games/',currentPurchasedGames),
    path('previous-purchased-games/',previousPurchasedGames),
    path('free-games/',goToFreeGames),
    path('goto-purchased-games/',goToPurchasedGames),
    path('check-today/',checkToday),
    path('check-user-purchases/',checkUserPurchases),
    path('purchased-games/',purchasedGames),
    path('notifications/',notification),
    path('total-users/',get_total_number_of_users),
    path('pending-slips/',get_number_of_pending_slips),
    path('purchased-slips/',get_number_of_purchased_slips),
    path('load-booking/<str:code>/',load_booking_data),
    path('api/upload-slip/', upload_slip),
    path("get-all-slips/", get_all_slips),
    path("get-available-plans/", get_avaliable_vip_plans),
    path("mark-slip-as-sold/<int:slip_id>/", mark_slip_as_sold_out),
    path("mark-slip-as-available/<int:slip_id>/", mark_slip_as_available),
    path("get-slip-status-for-today/", get_slip_for_todays_status),
    path("update-slip/<int:slip_id>/", mark_slip_as_sold_out),
    path("update-game-result/<int:game_id>/<str:result>/", game_results),
    path("mark-slip-as-updated/<int:slip_id>/", mark_slip_as_updated),
    path("get-slip-status/",get_slip_status),
    path('api/users/', api_users_list),  # new endpoint
    path("send-sms/", send_bulk_sms),
]