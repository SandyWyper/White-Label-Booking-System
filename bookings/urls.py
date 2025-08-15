# bookings/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('available-time-slots/', views.available_time_slots, name='available_time_slots'),
]