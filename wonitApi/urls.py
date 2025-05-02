from django.urls import path,include
from .views import *

urlpatterns = [
    path('today-games/',TodaysGamesView.as_view(),name='todays-game'),
    path('tomorrow-games/',TomorrowGamesView.as_view(),name='tomorrows-game'),
    path('yesterdays-games/',YesterdayGamesView.as_view(),name='yesterdays-game'),
    path('other-games',YesterdayGamesView.as_view()),
    path('codes/',get_booking_code)
]