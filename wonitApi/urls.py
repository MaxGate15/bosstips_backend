from django.urls import path,include
from .views import *

urlpatterns = [
    path('games/',get_todays_games),
    path('codes/',get_booking_code)
]