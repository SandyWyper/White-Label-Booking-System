# bookings/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('available-time-slots/', views.available_time_slots, name='available_time_slots'),
    path('book-time-slot/', views.book_time_slot, name='book_time_slot'),
]