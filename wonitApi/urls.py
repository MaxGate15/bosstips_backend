from django.urls import path,include
from .views import *

urlpatterns = [
    path('todays-prediction/',get_todays_games)
]