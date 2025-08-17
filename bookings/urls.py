from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='booking'),
    path('available-time-slots/', views.available_time_slots, name='available_time_slots'),
    path('book-time-slot/', views.book_time_slot, name='book_time_slot'),
    path('user-bookings/', views.user_bookings, name='user_bookings'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
   
    # Staff urls
    path('staff-create-slot/', views.staff_create_slot, name='staff_create_slot'),
    path('staff-cancel-booking/', views.staff_cancel_booking, name='staff_cancel_booking'),
    path('staff-book-slot/', views.staff_book_slot, name='staff_book_slot'),
    path('staff-create-template-slots/', views.staff_create_template_slots, name='staff_create_template_slots'),
]