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
    path('', include(router.urls)),
    path('today-games/',TodaysGamesView.as_view(),name='todays-game'),
    path('tomorrow-games/',TomorrowGamesView.as_view(),name='tomorrows-game'),
    path('yesterday-games/',YesterdayGamesView.as_view(),name='yesterdays-game'),
    path('other-games',YesterdayGamesView.as_view()),
    path('codes/',get_booking_code),
    path('free-slip/',freeSlip)
]