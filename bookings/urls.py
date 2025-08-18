from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='booking'),
    path('available-time-slots/', views.available_time_slots, name='available_time_slots'),
    path('book-time-slot/', views.book_time_slot, name='book_time_slot'),
    path('user-bookings/', views.user_bookings, name='user_bookings'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
   
    # Staff management URLs
    path('staff-create-slot/', views.staff_create_slot, name='staff_create_slot'),
    path('staff-cancel-booking/', views.staff_cancel_booking, name='staff_cancel_booking'),
    path('staff-book-slot/', views.staff_book_slot, name='staff_book_slot'),
    path('staff-create-template-slots/', views.staff_create_template_slots, name='staff_create_template_slots'),
    
    # Template management and slot deletion URLs
    path('delete-slot/', views.delete_slot, name='delete_slot'),
    path('save-template/', views.save_template, name='save_template'),
    path('get-saved-templates/', views.get_saved_templates, name='get_saved_templates'),
    path('delete-template/', views.delete_template, name='delete_template'),
    path('delete-all-slots-for-day/', views.delete_all_slots_for_day, name='delete_all_slots_for_day'),
]